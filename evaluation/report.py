"""
Report writers for evaluation runs.

Produces:
  outputs/<run_name>.json   — full results + summary
  outputs/<run_name>.md     — human-readable markdown
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_json_report(
    results: list[dict[str, Any]],
    accuracy: float,
    label_stats: dict[str, dict],
    name: str,
    model: str,
    outputs_dir: str = "outputs",
) -> Path:
    Path(outputs_dir).mkdir(parents=True, exist_ok=True)
    payload = {
        "run_name": name,
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_samples": len(results),
            "accuracy": round(accuracy, 4),
            "per_label": label_stats,
        },
        "results": results,
    }
    path = Path(outputs_dir) / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, default=str))
    return path


def write_markdown_report(
    results: list[dict[str, Any]],
    accuracy: float,
    label_stats: dict[str, dict],
    name: str,
    model: str,
    outputs_dir: str = "outputs",
) -> Path:
    Path(outputs_dir).mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Evaluation Report: {name}",
        "",
        f"**Model:** {model}  ",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Samples:** {len(results)}  ",
        f"**Accuracy:** {accuracy:.1%}",
        "",
        "## Per-Label Metrics",
        "",
        "| Label | Precision | Recall | F1 | TP | FP | FN |",
        "|-------|-----------|--------|----|----|----|----|",
    ]
    for label in ("phishing", "impersonation", "benign"):
        s = label_stats[label]
        lines.append(
            f"| {label} | {s['precision']:.2f} | {s['recall']:.2f} | {s['f1']:.2f}"
            f" | {s['tp']} | {s['fp']} | {s['fn']} |"
        )
    lines += [
        "",
        "## Results",
        "",
        "| Sample | Actual | Predicted | Match | Risk | Confidence |",
        "|--------|--------|-----------|-------|------|------------|",
    ]
    for r in results:
        match = "+" if r["actual_label"] == r["predicted_label"] else "-"
        lines.append(
            f"| {r['sample_id']} | {r['actual_label']} | {r['predicted_label']}"
            f" | {match} | {r['risk_score']:.2f} | {r['confidence']:.2f} |"
        )
    path = Path(outputs_dir) / f"{name}.md"
    path.write_text("\n".join(lines) + "\n")
    return path
