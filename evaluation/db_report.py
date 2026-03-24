"""
DB-sourced report generator for evaluation runs.

Usage:
    python -m evaluation.db_report --run-id <uuid>
    python -m evaluation.db_report --run-name <name>
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from typing import Any
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from db.repository import EvalRepository
from db.session import async_session as eval_session
from evaluation.metrics import (
    compute_accuracy,
    compute_label_stats,
    compute_classification_metrics,
    compute_confusion_matrix,
)
from evaluation.support_check import evaluate_explanation_support
from evaluation.report import write_json_report, write_markdown_report, write_html_report


def _normalize_result(
    result,
    call_metadata: dict[uuid.UUID, dict[str, Any]],
) -> dict[str, Any]:
    meta = (
        call_metadata.get(result.reliability_call_id)
        if result.reliability_call_id
        else None
    )
    return {
        "sample_id": result.sample_id,
        "actual_label": result.actual_label,
        "predicted_label": result.predicted_label,
        "risk_score": float(result.risk_score),
        "confidence": float(result.confidence),
        "explanation": result.explanation,
        "signals_json": result.signals_json,
        "timeline_json": result.timeline_json,
        "reliability_run_id": str(result.reliability_run_id),
        "reliability_phase_id": str(result.reliability_phase_id),
        "reliability_prompt_id": str(result.reliability_prompt_id),
        "reliability_call_id": (
            str(result.reliability_call_id) if result.reliability_call_id else None
        ),
        "provider": meta["provider"] if meta else None,
        "model": meta["model"] if meta else None,
        "latency_ms": meta["latency_ms"] if meta else None,
        "input_tokens": meta["input_tokens"] if meta else None,
        "output_tokens": meta["output_tokens"] if meta else None,
        "token_cost_usd": meta["token_cost_usd"] if meta else None,
    }

def _apply_demo_safe(result: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(result)
    sanitized["explanation"] = None
    sanitized["signals_json"] = None
    sanitized["timeline_json"] = None
    return sanitized

def _compute_llm_summary(call_metadata: dict[uuid.UUID, dict[str, Any]]) -> dict[str, Any]:
    providers = Counter()
    models = Counter()
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost_usd = 0.0
    total_latency_ms = 0.0
    latency_count = 0
    retry_count = 0

    for meta in call_metadata.values():
        provider = meta.get("provider")
        model = meta.get("model")
        if provider:
            providers[provider] += 1
        if model:
            models[model] += 1

        input_tokens = meta.get("input_tokens")
        output_tokens = meta.get("output_tokens")
        token_cost_usd = meta.get("token_cost_usd")
        latency_ms = meta.get("latency_ms")
        retry_attempt_num = meta.get("retry_attempt_num")

        if isinstance(input_tokens, (int, float)):
            total_input_tokens += int(input_tokens)
        if isinstance(output_tokens, (int, float)):
            total_output_tokens += int(output_tokens)
        if isinstance(token_cost_usd, (int, float)):
            total_cost_usd += float(token_cost_usd)
        if isinstance(latency_ms, (int, float)):
            total_latency_ms += float(latency_ms)
            latency_count += 1
        if isinstance(retry_attempt_num, int) and retry_attempt_num > 0:
            retry_count += 1

    llm_call_count = len(call_metadata)
    avg_latency_ms = (total_latency_ms / latency_count) if latency_count else None
    total_tokens = total_input_tokens + total_output_tokens

    return {
        "providers": dict(providers),
        "models": dict(models),
        "llm_call_count": llm_call_count,
        "retry_count": retry_count,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost_usd, 6),
        "total_latency_ms": round(total_latency_ms, 2),
        "avg_latency_ms": round(avg_latency_ms, 2) if avg_latency_ms is not None else None,
    }

def _resolve_outputs_dir(snapshot: bool, snapshot_dir: str, run_name: str, outputs_dir: str) -> str:
    if snapshot:
        return str(Path(snapshot_dir) / run_name)
    return outputs_dir

def _resolve_generated_at(evaluation_run, generated_at: str | None, snapshot: bool) -> str | None:
    if generated_at:
        return generated_at
    if snapshot and evaluation_run and evaluation_run.started_at:
        started_at = evaluation_run.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        return started_at.isoformat()
    return None

def _derive_model_label(llm_summary: dict[str, Any]) -> str:
    providers = llm_summary.get("providers", {})
    models = llm_summary.get("models", {})
    if len(providers) == 1 and len(models) == 1:
        provider = next(iter(providers.keys()))
        model = next(iter(models.keys()))
        return f"{provider}:{model}"
    if len(models) == 1:
        return next(iter(models.keys()))
    return "mixed"

def _sanitize_basename(value: str) -> str:
    return (
        value.replace(":", "-")
        .replace("/", "-")
        .replace(" ", "-")
        .replace(".", "-")
    )


async def build_reports(
    *,
    run_id: uuid.UUID | None,
    run_name: str | None,
    outputs_dir: str,
    demo_safe: bool,
    snapshot: bool,
    snapshot_dir: str,
    generated_at: str | None,
) -> int:
    async with eval_session() as eval_db:
        repo = EvalRepository(eval_db)

        if run_id is not None:
            evaluation_run = await repo.get_evaluation_run(run_id)
        else:
            evaluation_run = await repo.get_evaluation_run_by_name(run_name or "")

        if evaluation_run is None:
            print("Evaluation run not found.", file=sys.stderr)
            return 1

        results = await repo.list_investigation_results_by_evaluation_run_id(
            evaluation_run.id
        )
        if not results:
            print("No investigation results found for this run.", file=sys.stderr)
            return 1

        outputs_dir = _resolve_outputs_dir(snapshot, snapshot_dir, evaluation_run.name, outputs_dir)
        generated_at = _resolve_generated_at(evaluation_run, generated_at, snapshot)
        if generated_at is None:
            generated_at = datetime.now(timezone.utc).isoformat()

        call_ids = [
            r.reliability_call_id for r in results if r.reliability_call_id is not None
        ]
        call_metadata = await repo.get_llm_call_metadata(call_ids)

        payloads = [_normalize_result(r, call_metadata) for r in results]

        support_counts = {
            "supported_count": 0,
            "weak_count": 0,
            "unsupported_count": 0,
            "unavailable_count": 0,
        }
        support_examples = []
        for payload in payloads:
            status, notes = evaluate_explanation_support(payload)
            payload["explanation_support_status"] = status
            payload["explanation_support_notes"] = notes
            support_counts[f"{status}_count"] += 1
            if status in ("weak", "unsupported") and len(support_examples) < 5:
                support_examples.append(
                    {
                        "sample_id": payload.get("sample_id"),
                        "actual_label": payload.get("actual_label"),
                        "predicted_label": payload.get("predicted_label"),
                        "status": status,
                        "notes": notes,
                    }
                )

        if demo_safe:
            payloads = [_apply_demo_safe(p) for p in payloads]

        pairs = [(r.actual_label, r.predicted_label) for r in results]
        accuracy = compute_accuracy(pairs)
        label_stats = {
            label: compute_label_stats(pairs, label)
            for label in ("phishing", "impersonation", "benign")
        }
        labels = ["benign", "phishing", "impersonation"]
        classification_metrics = compute_classification_metrics(pairs, labels)
        confusion_matrix = {
            "labels": labels,
            "rows": compute_confusion_matrix(pairs, labels),
        }

        llm_summary = _compute_llm_summary(call_metadata)
        explanation_support = {
            **support_counts,
            "examples": support_examples,
        }

        model_label = _derive_model_label(llm_summary)
        report_basename = None
        if snapshot:
            report_basename = _sanitize_basename(f"{model_label}-report")
        json_path = write_json_report(
            payloads,
            accuracy,
            label_stats,
            evaluation_run.name,
            model_label,
            llm_summary=llm_summary,
            classification_metrics=classification_metrics,
            confusion_matrix=confusion_matrix,
            explanation_support=explanation_support,
            generated_at=generated_at,
            report_basename=report_basename,
            outputs_dir=outputs_dir,
        )
        md_path = write_markdown_report(
            payloads,
            accuracy,
            label_stats,
            evaluation_run.name,
            model_label,
            llm_summary=llm_summary,
            classification_metrics=classification_metrics,
            confusion_matrix=confusion_matrix,
            explanation_support=explanation_support,
            generated_at=generated_at,
            report_basename=report_basename,
            outputs_dir=outputs_dir,
        )
        html_path = write_html_report(
            payloads,
            accuracy,
            label_stats,
            evaluation_run.name,
            model_label,
            llm_summary=llm_summary,
            classification_metrics=classification_metrics,
            confusion_matrix=confusion_matrix,
            explanation_support=explanation_support,
            generated_at=generated_at,
            report_basename=report_basename,
            outputs_dir=outputs_dir,
        )

        print("Reports written:")
        print(f"  {json_path}")
        print(f"  {md_path}")
        print(f"  {html_path}")
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate evaluation reports from persisted DB data"
    )
    parser.add_argument("--run-id", help="Evaluation run UUID")
    parser.add_argument("--run-name", help="Evaluation run name")
    parser.add_argument("--outputs-dir", default="outputs", help="Output directory")
    parser.add_argument("--demo-safe", action="store_true", help="Redact explanation and evidence fields")
    parser.add_argument("--snapshot", action="store_true", help="Write outputs to outputs/demo/<run_name>/")
    parser.add_argument("--snapshot-dir", default="outputs/demo", help="Snapshot base directory")
    parser.add_argument("--generated-at", help="Override generated_at timestamp (ISO-8601)")
    args = parser.parse_args()

    if not args.run_id and not args.run_name:
        print("Provide --run-id or --run-name.", file=sys.stderr)
        raise SystemExit(2)

    run_id = uuid.UUID(args.run_id) if args.run_id else None
    asyncio.run(
        build_reports(
            run_id=run_id,
            run_name=args.run_name,
            outputs_dir=args.outputs_dir,
            demo_safe=args.demo_safe,
            snapshot=args.snapshot,
            snapshot_dir=args.snapshot_dir,
            generated_at=args.generated_at,
        )
    )


if __name__ == "__main__":
    main()
