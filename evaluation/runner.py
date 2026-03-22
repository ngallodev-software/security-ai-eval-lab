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
from datetime import datetime, timezone
from pathlib import Path

from agents.email_threat_agent import FakeReliabilityExecutor
from db.repository import EvalRepository
from db.session import async_session as eval_session
from evaluation.metrics import compute_accuracy, compute_label_stats
from evaluation.report import write_json_report, write_markdown_report


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


def _ensure_reliability_fw_on_path() -> None:
    for candidate in (
        Path("/lump/apps/ai-reliability-fw/src"),
        Path("/tmp/codex-worktrees/ai-reliability-fw/src"),
    ):
        if candidate.exists():
            candidate_str = str(candidate)
            if candidate_str not in sys.path:
                sys.path.insert(0, candidate_str)
            return
    raise RuntimeError("Could not locate ai-reliability-fw/src for the live runner path")


# ---------------------------------------------------------------------------
# Single-sample investigation (async)
# ---------------------------------------------------------------------------

async def investigate_sample(
    sample: dict,
    adapter,
) -> dict:
    """
    Run deterministic signals + LLM classification for one sample.

    Returns a flat dict ready to insert into investigation_results.
    """
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

    output = fw_result.get("output", fw_result)
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
        "provider": fw_result.get("provider"),
        "model": fw_result.get("model"),
        "latency_ms": fw_result.get("latency_ms"),
        "input_tokens": fw_result.get("input_tokens"),
        "output_tokens": fw_result.get("output_tokens"),
        "token_cost_usd": fw_result.get("token_cost_usd"),
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

    results: list[dict] = []

    if dry_run:
        adapter = FakeReliabilityExecutor()
        print("[dry-run] skipping evaluation_runs/investigation_results writes")
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
        _ensure_reliability_fw_on_path()
        from agents.reliability_adapter import PhaseExecutorAdapter
        from llm.openai_client import OpenAIClient

        adapter = PhaseExecutorAdapter(llm_client=OpenAIClient(model=model))
        async with eval_session() as eval_db:
            eval_repo = EvalRepository(eval_db)

            # Create the evaluation run record.
            evaluation_run_id = await eval_repo.create_evaluation_run(
                {
                    "name": name,
                    "dataset_name": dataset_path,
                    "model_label": model,
                    "started_at": datetime.now(timezone.utc),
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
                await eval_repo.insert_investigation_result(
                    {**result, "evaluation_run_id": evaluation_run_id}
                )

            await eval_repo.mark_evaluation_run_complete(evaluation_run_id)

    # -----------------------------------------------------------------------
    # Summary metrics
    # -----------------------------------------------------------------------
    pairs = [(r["actual_label"], r["predicted_label"]) for r in results]
    accuracy = compute_accuracy(pairs)

    print()
    print("=" * 60)
    print(f"Evaluation: {name}")
    print(f"Samples:    {len(results)}")
    print(f"Accuracy:   {accuracy:.1%}")

    label_stats = {
        label: compute_label_stats(pairs, label)
        for label in ("phishing", "impersonation", "benign")
    }
    for label, stats in label_stats.items():
        print(
            f"  {label:<14}  P={stats['precision']:.2f}  R={stats['recall']:.2f}"
            f"  F1={stats['f1']:.2f}  (tp={stats['tp']} fp={stats['fp']} fn={stats['fn']})"
        )

    if dry_run:
        print("[dry-run] results were not persisted")
    else:
        json_path = write_json_report(results, accuracy, label_stats, name, model)
        md_path = write_markdown_report(results, accuracy, label_stats, name, model)
        print(f"\nReports written:")
        print(f"  {json_path}")
        print(f"  {md_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="security-ai-eval-lab evaluation runner")
    parser.add_argument("--dataset", default="datasets", help="Path to dataset directory")
    parser.add_argument("--name", default=f"eval-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}", help="Evaluation run name")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model ID")
    parser.add_argument("--dry-run", action="store_true", help="Skip DB writes")
    args = parser.parse_args()

    asyncio.run(run_evaluation(args.dataset, args.name, args.model, args.dry_run))


if __name__ == "__main__":
    main()
