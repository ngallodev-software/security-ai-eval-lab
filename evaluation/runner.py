"""
Evaluation runner.

Loads JSON dataset samples, runs deterministic signal extraction,
calls the reliability adapter, stores investigation_results, and
prints a compact summary with accuracy / per-label metrics.

Usage::

    cd /lump/apps/security-ai-eval-lab
    python -m evaluation.runner --dataset datasets/ --name my-run-001

Environment variables required:
    DATABASE_URL   — shared Postgres URL (same as ai-reliability-fw)
    ANTHROPIC_API_KEY
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

from agents.reliability_adapter import PhaseExecutorAdapter
from db.repository import EvalRepository
from db.session import async_session as eval_session
from evaluation.metrics import compute_accuracy, compute_label_stats
from llm.anthropic_client import AnthropicClient


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_samples(dataset_root: str) -> list[dict]:
    root = Path(dataset_root)
    samples = []
    for path in sorted(root.rglob("*.json")):
        with open(path, "r", encoding="utf-8") as fh:
            samples.append(json.load(fh))
    return samples


# ---------------------------------------------------------------------------
# Single-sample investigation (async)
# ---------------------------------------------------------------------------

async def investigate_sample(
    sample: dict,
    adapter: PhaseExecutorAdapter,
) -> dict:
    """
    Run deterministic signals + LLM classification for one sample.

    Returns a flat dict ready to insert into investigation_results.
    """
    # EmailThreatInvestigationAgent is sync; the async adapter is called
    # directly here so we can await it properly.
    from agents.email_threat_agent import (
        extract_sender_domain,
        extract_urls,
        parse_auth_results,
        estimate_domain_age_days,
        compute_brand_similarity,
    )
    import time

    timeline: list[str] = []
    start = time.perf_counter()

    timeline.append("parse sender domain")
    sender_domain = extract_sender_domain(sample["email_text"])

    timeline.append("extract urls")
    urls = extract_urls(sample["email_text"])

    timeline.append("parse auth results")
    auth = parse_auth_results(sample["email_text"])

    timeline.append("estimate domain age")
    domain_age_days = estimate_domain_age_days(sender_domain)

    timeline.append("compute brand similarity")
    brand_similarity = compute_brand_similarity(sample["email_text"], sender_domain)

    signals = {
        "sender_domain": sender_domain,
        "urls": urls,
        "domain_age_days": domain_age_days,
        "spf_result": auth["spf_result"],
        "dkim_result": auth["dkim_result"],
        "dmarc_result": auth["dmarc_result"],
        "brand_similarity": {
            "matched_brand": brand_similarity.matched_brand,
            "score": brand_similarity.score,
        },
    }

    payload = {"email_text": sample["email_text"], "signals": signals}

    timeline.append("llm classification")
    fw_result = await adapter.execute_async(
        phase_id="email_threat_classification",
        prompt_id="email-threat-v1",
        payload=payload,
    )

    total_ms = int((time.perf_counter() - start) * 1000)
    timeline.append(f"complete ({total_ms} ms)")

    output = fw_result["output"]
    return {
        "sample_id": sample["id"],
        "actual_label": sample["label"],
        "predicted_label": output["predicted_label"],
        "risk_score": output["risk_score"],
        "confidence": output["confidence"],
        "explanation": output["explanation"],
        "signals_json": signals,
        "timeline_json": timeline,
        # These three are always set on success; adapter raises on non-success.
        "reliability_run_id": uuid.UUID(fw_result["reliability_run_id"]),
        "reliability_phase_id": uuid.UUID(fw_result["reliability_phase_id"]),
        "reliability_prompt_id": uuid.UUID(fw_result["reliability_prompt_id"]),
        # call_id is nullable per spec.
        "reliability_call_id": uuid.UUID(fw_result["call_id"]) if fw_result.get("call_id") else None,
    }


# ---------------------------------------------------------------------------
# Main async runner
# ---------------------------------------------------------------------------

async def run_evaluation(dataset_path: str, name: str, model: str, dry_run: bool) -> None:
    samples = load_samples(dataset_path)
    if not samples:
        print("No samples found.", file=sys.stderr)
        return

    print(f"Loaded {len(samples)} samples from {dataset_path}")

    llm_client = AnthropicClient(model=model)
    adapter = PhaseExecutorAdapter(llm_client=llm_client)
    results: list[dict] = []

    if dry_run:
        print("[dry-run] skipping evaluation_runs/investigation_results writes\n")
        for sample in samples:
            print(f"  investigating {sample['id']} (actual={sample['label']}) ...", end=" ", flush=True)
            try:
                result = await investigate_sample(sample, adapter)
            except RuntimeError as exc:
                print(f"FAILED — {exc}", file=sys.stderr)
                continue
            results.append(result)
            print(f"predicted={result['predicted_label']}  score={result['risk_score']:.2f}")
    else:
        async with eval_session() as eval_db:
            eval_repo = EvalRepository(eval_db)

            # Create the evaluation run record.
            evaluation_run_id = await eval_repo.create_evaluation_run(
                {
                    "name": name,
                    "dataset_path": dataset_path,
                    "model": model,
                    "created_at": datetime.utcnow(),
                }
            )
            print(f"evaluation_run_id: {evaluation_run_id}\n")

            for sample in samples:
                print(f"  investigating {sample['id']} (actual={sample['label']}) ...", end=" ", flush=True)
                try:
                    result = await investigate_sample(sample, adapter)
                except RuntimeError as exc:
                    print(f"FAILED — {exc}", file=sys.stderr)
                    continue
                results.append(result)
                print(f"predicted={result['predicted_label']}  score={result['risk_score']:.2f}")
                await eval_repo.save_investigation_result(
                    {**result, "evaluation_run_id": evaluation_run_id}
                )

    # -----------------------------------------------------------------------
    # Summary metrics
    # -----------------------------------------------------------------------
    pairs = [(r["actual_label"], r["predicted_label"]) for r in results]
    accuracy = compute_accuracy(pairs)

    print("\n" + "=" * 60)
    print(f"Evaluation: {name}")
    print(f"Model:      {model}")
    print(f"Samples:    {len(results)}")
    print(f"Accuracy:   {accuracy:.1%}")
    print()

    for label in ("phishing", "impersonation", "benign"):
        stats = compute_label_stats(pairs, label)
        print(
            f"  {label:<14}  P={stats['precision']:.2f}  R={stats['recall']:.2f}"
            f"  F1={stats['f1']:.2f}  (tp={stats['tp']} fp={stats['fp']} fn={stats['fn']})"
        )

    if dry_run:
        print("\n[dry-run: results were not persisted]")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="security-ai-eval-lab evaluation runner")
    parser.add_argument("--dataset", default="datasets", help="Path to dataset directory")
    parser.add_argument("--name", default=f"eval-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}", help="Evaluation run name")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001", help="Anthropic model ID")
    parser.add_argument("--dry-run", action="store_true", help="Skip DB writes")
    args = parser.parse_args()

    asyncio.run(run_evaluation(args.dataset, args.name, args.model, args.dry_run))


if __name__ == "__main__":
    main()
