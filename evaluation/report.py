"""
Report writers for evaluation runs.

Produces:
  outputs/<run_name>.json   — full results + summary
  outputs/<run_name>.md     — human-readable markdown
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _format_generated_at(generated_at: str | None, fallback_format: str) -> str:
    if not generated_at:
        return "N/A"
    if "T" in generated_at:
        try:
            parsed = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            return parsed.strftime(fallback_format)
        except ValueError:
            return generated_at
    return generated_at


def write_json_report(
    results: list[dict[str, Any]],
    accuracy: float,
    label_stats: dict[str, dict],
    name: str,
    model: str,
    llm_summary: dict[str, Any] | None = None,
    classification_metrics: dict[str, Any] | None = None,
    confusion_matrix: dict[str, Any] | None = None,
    explanation_support: dict[str, Any] | None = None,
    generated_at: str | None = None,
    report_basename: str | None = None,
    outputs_dir: str = "outputs",
) -> Path:
    Path(outputs_dir).mkdir(parents=True, exist_ok=True)
    payload = {
        "run_name": name,
        "model": model,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_samples": len(results),
            "accuracy": round(accuracy, 4),
            "per_label": label_stats,
        },
        "results": results,
    }
    if classification_metrics:
        payload["summary"]["classification_metrics"] = classification_metrics
    if confusion_matrix:
        payload["summary"]["confusion_matrix"] = confusion_matrix
    if explanation_support:
        payload["summary"]["explanation_support"] = explanation_support
    if llm_summary:
        payload["summary"]["llm"] = llm_summary
    filename = report_basename or name
    path = Path(outputs_dir) / f"{filename}.json"
    path.write_text(json.dumps(payload, indent=2, default=str))
    return path


def write_markdown_report(
    results: list[dict[str, Any]],
    accuracy: float,
    label_stats: dict[str, dict],
    name: str,
    model: str,
    llm_summary: dict[str, Any] | None = None,
    classification_metrics: dict[str, Any] | None = None,
    confusion_matrix: dict[str, Any] | None = None,
    explanation_support: dict[str, Any] | None = None,
    generated_at: str | None = None,
    report_basename: str | None = None,
    outputs_dir: str = "outputs",
) -> Path:
    Path(outputs_dir).mkdir(parents=True, exist_ok=True)
    if generated_at:
        generated_at_str = _format_generated_at(generated_at, '%Y-%m-%d %H:%M UTC')
    else:
        generated_at_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    labels = ["phishing", "impersonation", "benign"]
    if classification_metrics and classification_metrics.get("labels"):
        labels = list(classification_metrics["labels"])

    lines = [
        f"# Evaluation Report: {name}",
        "",
        f"**Model:** {model}  ",
        f"**Generated:** {generated_at_str}  ",
        f"**Samples:** {len(results)}  ",
        f"**Accuracy:** {accuracy:.1%}",
        "",
        "## Classification Metrics",
        "",
        "| Label | Support | Precision | Recall | F1 | TP | FP | FN |",
        "|-------|---------|-----------|--------|----|----|----|----|",
    ]
    for label in labels:
        s = label_stats[label]
        support = None
        if classification_metrics:
            support = classification_metrics.get("per_label", {}).get(label, {}).get("support")
        support_str = str(support) if support is not None else "0"
        lines.append(
            f"| {label} | {support_str} | {s['precision']:.2f} | {s['recall']:.2f} | {s['f1']:.2f}"
            f" | {s['tp']} | {s['fp']} | {s['fn']} |"
        )
    if classification_metrics:
        lines += [
            "",
            f"Macro avg: P={classification_metrics['macro_precision']:.2f} "
            f"R={classification_metrics['macro_recall']:.2f} "
            f"F1={classification_metrics['macro_f1']:.2f}",
            f"Micro avg: P={classification_metrics['micro_precision']:.2f} "
            f"R={classification_metrics['micro_recall']:.2f} "
            f"F1={classification_metrics['micro_f1']:.2f}",
            f"Weighted avg: P={classification_metrics['weighted_precision']:.2f} "
            f"R={classification_metrics['weighted_recall']:.2f} "
            f"F1={classification_metrics['weighted_f1']:.2f}",
            f"Total support: {classification_metrics.get('total_support')}",
        ]
    if llm_summary:
        providers = llm_summary.get("providers", {})
        models = llm_summary.get("models", {})
        total_input_tokens = llm_summary.get("total_input_tokens")
        total_output_tokens = llm_summary.get("total_output_tokens")
        total_tokens = llm_summary.get("total_tokens")
        total_cost_usd = llm_summary.get("total_cost_usd")
        avg_latency_ms = llm_summary.get("avg_latency_ms")
        total_latency_ms = llm_summary.get("total_latency_ms")
        llm_call_count = llm_summary.get("llm_call_count")
        retry_count = llm_summary.get("retry_count")
        lines += [
            "",
            "## LLM Metadata",
            "",
            "Providers: " + (", ".join(f"{k} ({v})" for k, v in providers.items()) or "None"),
            "Models: " + (", ".join(f"{k} ({v})" for k, v in models.items()) or "None"),
            f"LLM calls: {llm_call_count}",
            f"Retries: {retry_count}",
            f"Total input tokens: {total_input_tokens}",
            f"Total output tokens: {total_output_tokens}",
            f"Total tokens: {total_tokens}",
            f"Total cost (USD): {total_cost_usd}",
            f"Total latency (ms): {total_latency_ms}",
            f"Avg latency (ms): {avg_latency_ms}",
        ]

    if confusion_matrix:
        labels = confusion_matrix.get("labels", [])
        rows = confusion_matrix.get("rows", {})
        header = "| Actual \\ Predicted | " + " | ".join(labels) + " |"
        divider = "|---" * (len(labels) + 1) + "|"
        lines += [
            "",
            "## Confusion Matrix",
            "",
            header,
            divider,
        ]
        for actual in labels:
            row = rows.get(actual, {})
            counts = " | ".join(str(row.get(pred, 0)) for pred in labels)
            lines.append(f"| {actual} | {counts} |")

    if explanation_support:
        lines += [
            "",
            "## Explanation Support",
            "",
            f"Supported: {explanation_support.get('supported_count', 0)}",
            f"Weak: {explanation_support.get('weak_count', 0)}",
            f"Unsupported: {explanation_support.get('unsupported_count', 0)}",
            f"Unavailable: {explanation_support.get('unavailable_count', 0)}",
        ]
        examples = explanation_support.get("examples", [])
        if examples:
            lines += [
                "",
                "| Sample | Actual | Predicted | Status | Notes |",
                "|--------|--------|-----------|--------|-------|",
            ]
            for ex in examples:
                notes = "; ".join(ex.get("notes", [])) if ex.get("notes") else ""
                lines.append(
                    f"| {ex.get('sample_id')} | {ex.get('actual_label')} | {ex.get('predicted_label')}"
                    f" | {ex.get('status')} | {notes} |"
                )

    lines += [
        "",
        "## Results",
        "",
        "| Sample | Actual | Predicted | Match | Risk | Confidence | Support |",
        "|--------|--------|-----------|-------|------|------------|---------|",
    ]
    for r in results:
        match = "+" if r["actual_label"] == r["predicted_label"] else "-"
        support_status = r.get("explanation_support_status", "")
        lines.append(
            f"| {r['sample_id']} | {r['actual_label']} | {r['predicted_label']}"
            f" | {match} | {r['risk_score']:.2f} | {r['confidence']:.2f} | {support_status} |"
        )

    lines += [
        "",
        "## Per-Sample Execution Details",
    ]
    for r in results:
        lines += [
            "",
            f"### {r.get('sample_id')}",
            f"- Provider: {r.get('provider')}",
            f"- Model: {r.get('model')}",
            f"- Latency (ms): {r.get('latency_ms')}",
            f"- Input tokens: {r.get('input_tokens')}",
            f"- Output tokens: {r.get('output_tokens')}",
            f"- Token cost (USD): {r.get('token_cost_usd')}",
            f"- Explanation support: {r.get('explanation_support_status')}",
        ]
        notes = r.get("explanation_support_notes") or []
        if notes:
            lines.append("- Explanation support notes:")
            for note in notes:
                lines.append(f"  - {note}")
        lines += [
            f"- Reliability run id: {r.get('reliability_run_id')}",
            f"- Reliability phase id: {r.get('reliability_phase_id')}",
            f"- Reliability prompt id: {r.get('reliability_prompt_id')}",
            f"- Reliability call id: {r.get('reliability_call_id')}",
        ]
    filename = report_basename or name
    path = Path(outputs_dir) / f"{filename}.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def _format_llm_list(items: dict[str, int] | None) -> str:
    if not items:
        return "None"
    return ", ".join(f"{html.escape(str(k))} ({v})" for k, v in items.items())


def _format_notes(notes: list[str] | None) -> str:
    if not notes:
        return ""
    return " ".join(html.escape(note) for note in notes)


def write_html_report(
    results: list[dict[str, Any]],
    accuracy: float,
    label_stats: dict[str, dict],
    name: str,
    model: str,
    llm_summary: dict[str, Any] | None = None,
    classification_metrics: dict[str, Any] | None = None,
    confusion_matrix: dict[str, Any] | None = None,
    explanation_support: dict[str, Any] | None = None,
    generated_at: str | None = None,
    report_basename: str | None = None,
    outputs_dir: str = "outputs",
) -> Path:
    Path(outputs_dir).mkdir(parents=True, exist_ok=True)
    generated_at_str = _format_generated_at(generated_at, '%Y-%m-%d %H:%M UTC')

    labels = ["phishing", "impersonation", "benign"]
    if classification_metrics and classification_metrics.get("labels"):
        labels = list(classification_metrics["labels"])

    providers = llm_summary.get("providers", {}) if llm_summary else {}
    models = llm_summary.get("models", {}) if llm_summary else {}

    def safe_value(value: Any) -> str:
        if value is None:
            return "N/A"
        return html.escape(str(value))

    html_parts = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"utf-8\" />",
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />",
        f"  <title>Evaluation Report: {html.escape(name)}</title>",
        "  <style>",
        "    :root {",
        "      --bg: #f7f7f5;",
        "      --card: #ffffff;",
        "      --text: #1f2328;",
        "      --muted: #5a6570;",
        "      --border: #e1e4e8;",
        "      --accent: #2f5fa8;",
        "      --success: #1f7a1f;",
        "      --warning: #b06a00;",
        "      --danger: #b32020;",
        "    }",
        "    body {",
        "      margin: 0;",
        "      font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;",
        "      background: var(--bg);",
        "      color: var(--text);",
        "      line-height: 1.5;",
        "    }",
        "    .container { max-width: 1100px; margin: 32px auto; padding: 0 24px 40px; }",
        "    header { background: var(--card); padding: 24px; border-radius: 12px; border: 1px solid var(--border); }",
        "    h1 { margin: 0 0 8px 0; font-size: 28px; }",
        "    h2 { margin: 28px 0 12px; font-size: 20px; }",
        "    h3 { margin: 20px 0 10px; font-size: 16px; }",
        "    .meta { display: flex; flex-wrap: wrap; gap: 16px; color: var(--muted); font-size: 14px; }",
        "    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-top: 16px; }",
        "    .card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }",
        "    .card .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.03em; }",
        "    .card .value { font-size: 18px; font-weight: 600; margin-top: 6px; }",
        "    table { width: 100%; border-collapse: collapse; background: var(--card); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }",
        "    th, td { padding: 10px 12px; border-bottom: 1px solid var(--border); text-align: left; font-size: 14px; }",
        "    th { background: #f1f3f5; font-weight: 600; }",
        "    tr:last-child td { border-bottom: none; }",
        "    .section { margin-top: 24px; }",
        "    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }",
        "    .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; background: #eef2f6; color: var(--muted); }",
        "    .match-yes { color: var(--success); font-weight: 600; }",
        "    .match-no { color: var(--danger); font-weight: 600; }",
        "    .status-unsupported { color: var(--danger); font-weight: 600; }",
        "    .status-weak { color: var(--warning); font-weight: 600; }",
        "    .row-unsupported { background: #fff5f5; }",
        "    .row-unsupported td { border-bottom-color: #f0d7d7; }",
        "    .sample-card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 12px; }",
        "    .sample-unsupported { border-color: #f0d7d7; background: #fffaf9; }",
        "    .sample-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 8px 16px; font-size: 13px; color: var(--muted); }",
        "    .sample-grid strong { color: var(--text); font-weight: 600; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <div class=\"container\">",
        "    <header>",
        f"      <h1>Evaluation Report: {html.escape(name)}</h1>",
        "      <div class=\"meta\">",
        f"        <div><strong>Model:</strong> {html.escape(model)}</div>",
        f"        <div><strong>Generated:</strong> {html.escape(generated_at_str)}</div>",
        f"        <div><strong>Samples:</strong> {len(results)}</div>",
        f"        <div><strong>Accuracy:</strong> {accuracy:.1%}</div>",
        "      </div>",
        "      <div class=\"cards\">",
        f"        <div class=\"card\"><div class=\"label\">Accuracy</div><div class=\"value\">{accuracy:.1%}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Samples</div><div class=\"value\">{len(results)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">LLM Calls</div><div class=\"value\">{safe_value(llm_summary.get('llm_call_count') if llm_summary else None)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Retries</div><div class=\"value\">{safe_value(llm_summary.get('retry_count') if llm_summary else None)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Total Tokens</div><div class=\"value\">{safe_value(llm_summary.get('total_tokens') if llm_summary else None)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Total Cost (USD)</div><div class=\"value\">{safe_value(llm_summary.get('total_cost_usd') if llm_summary else None)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Total Latency (ms)</div><div class=\"value\">{safe_value(llm_summary.get('total_latency_ms') if llm_summary else None)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Avg Latency (ms)</div><div class=\"value\">{safe_value(llm_summary.get('avg_latency_ms') if llm_summary else None)}</div></div>",
        "      </div>",
        "    </header>",
    ]

    html_parts += [
        "    <section class=\"section\">",
        "      <h2>Classification Metrics</h2>",
        "      <table>",
        "        <thead>",
        "          <tr>",
        "            <th>Label</th>",
        "            <th>Support</th>",
        "            <th>Precision</th>",
        "            <th>Recall</th>",
        "            <th>F1</th>",
        "            <th>TP</th>",
        "            <th>FP</th>",
        "            <th>FN</th>",
        "          </tr>",
        "        </thead>",
        "        <tbody>",
    ]
    for label in labels:
        stats = label_stats[label]
        support = None
        if classification_metrics:
            support = classification_metrics.get("per_label", {}).get(label, {}).get("support")
        support_str = support if support is not None else 0
        html_parts.append(
            "          <tr>"
            f"<td>{html.escape(label)}</td>"
            f"<td>{support_str}</td>"
            f"<td>{stats['precision']:.2f}</td>"
            f"<td>{stats['recall']:.2f}</td>"
            f"<td>{stats['f1']:.2f}</td>"
            f"<td>{stats['tp']}</td>"
            f"<td>{stats['fp']}</td>"
            f"<td>{stats['fn']}</td>"
            "</tr>"
        )
    html_parts += [
        "        </tbody>",
        "      </table>",
    ]
    if classification_metrics:
        html_parts += [
            "      <div class=\"grid\" style=\"margin-top: 12px;\">",
            f"        <div class=\"card\"><div class=\"label\">Macro Avg</div><div class=\"value\">P={classification_metrics['macro_precision']:.2f} R={classification_metrics['macro_recall']:.2f} F1={classification_metrics['macro_f1']:.2f}</div></div>",
            f"        <div class=\"card\"><div class=\"label\">Micro Avg</div><div class=\"value\">P={classification_metrics['micro_precision']:.2f} R={classification_metrics['micro_recall']:.2f} F1={classification_metrics['micro_f1']:.2f}</div></div>",
            f"        <div class=\"card\"><div class=\"label\">Weighted Avg</div><div class=\"value\">P={classification_metrics['weighted_precision']:.2f} R={classification_metrics['weighted_recall']:.2f} F1={classification_metrics['weighted_f1']:.2f}</div></div>",
            f"        <div class=\"card\"><div class=\"label\">Total Support</div><div class=\"value\">{classification_metrics.get('total_support')}</div></div>",
            "      </div>",
        ]
    html_parts.append("    </section>")

    html_parts += [
        "    <section class=\"section\">",
        "      <h2>LLM Metadata</h2>",
        "      <div class=\"grid\">",
        f"        <div class=\"card\"><div class=\"label\">Providers</div><div class=\"value\">{_format_llm_list(providers)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Models</div><div class=\"value\">{_format_llm_list(models)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">LLM Calls</div><div class=\"value\">{safe_value(llm_summary.get('llm_call_count') if llm_summary else None)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Retries</div><div class=\"value\">{safe_value(llm_summary.get('retry_count') if llm_summary else None)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Input Tokens</div><div class=\"value\">{safe_value(llm_summary.get('total_input_tokens') if llm_summary else None)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Output Tokens</div><div class=\"value\">{safe_value(llm_summary.get('total_output_tokens') if llm_summary else None)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Total Tokens</div><div class=\"value\">{safe_value(llm_summary.get('total_tokens') if llm_summary else None)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Total Cost (USD)</div><div class=\"value\">{safe_value(llm_summary.get('total_cost_usd') if llm_summary else None)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Total Latency (ms)</div><div class=\"value\">{safe_value(llm_summary.get('total_latency_ms') if llm_summary else None)}</div></div>",
        f"        <div class=\"card\"><div class=\"label\">Avg Latency (ms)</div><div class=\"value\">{safe_value(llm_summary.get('avg_latency_ms') if llm_summary else None)}</div></div>",
        "      </div>",
        "    </section>",
    ]

    if confusion_matrix:
        labels = confusion_matrix.get("labels", [])
        rows = confusion_matrix.get("rows", {})
        html_parts += [
            "    <section class=\"section\">",
            "      <h2>Confusion Matrix</h2>",
            "      <table>",
            "        <thead>",
            "          <tr>",
            "            <th>Actual \\ Predicted</th>",
        ]
        for label in labels:
            html_parts.append(f"            <th>{html.escape(label)}</th>")
        html_parts += [
            "          </tr>",
            "        </thead>",
            "        <tbody>",
        ]
        for actual in labels:
            html_parts.append("          <tr>")
            html_parts.append(f"            <td><strong>{html.escape(actual)}</strong></td>")
            row = rows.get(actual, {})
            for pred in labels:
                html_parts.append(f"            <td>{row.get(pred, 0)}</td>")
            html_parts.append("          </tr>")
        html_parts += [
            "        </tbody>",
            "      </table>",
            "    </section>",
        ]

    if explanation_support:
        html_parts += [
            "    <section class=\"section\">",
            "      <h2>Explanation Support</h2>",
            "      <div class=\"grid\">",
            f"        <div class=\"card\"><div class=\"label\">Supported</div><div class=\"value\">{explanation_support.get('supported_count', 0)}</div></div>",
            f"        <div class=\"card\"><div class=\"label\">Weak</div><div class=\"value\">{explanation_support.get('weak_count', 0)}</div></div>",
            f"        <div class=\"card\"><div class=\"label\">Unsupported</div><div class=\"value\">{explanation_support.get('unsupported_count', 0)}</div></div>",
            f"        <div class=\"card\"><div class=\"label\">Unavailable</div><div class=\"value\">{explanation_support.get('unavailable_count', 0)}</div></div>",
            "      </div>",
        ]
        examples = explanation_support.get("examples", [])
        if examples:
            html_parts += [
                "      <h3>Examples</h3>",
                "      <table>",
                "        <thead>",
                "          <tr>",
                "            <th>Sample</th>",
                "            <th>Actual</th>",
                "            <th>Predicted</th>",
                "            <th>Status</th>",
                "            <th>Notes</th>",
                "          </tr>",
                "        </thead>",
                "        <tbody>",
            ]
            for ex in examples:
                notes = _format_notes(ex.get("notes"))
                row_class = "row-unsupported" if ex.get("status") == "unsupported" else ""
                html_parts += [
                    f"          <tr class=\"{row_class}\">",
                    f"            <td>{html.escape(str(ex.get('sample_id')))}</td>",
                    f"            <td>{html.escape(str(ex.get('actual_label')))}</td>",
                    f"            <td>{html.escape(str(ex.get('predicted_label')))}</td>",
                    f"            <td>{html.escape(str(ex.get('status')))}</td>",
                    f"            <td>{notes}</td>",
                    "          </tr>",
                ]
            html_parts += [
                "        </tbody>",
                "      </table>",
            ]
        html_parts.append("    </section>")

    html_parts += [
        "    <section class=\"section\">",
        "      <h2>Results</h2>",
        "      <table>",
        "        <thead>",
        "          <tr>",
        "            <th>Sample</th>",
        "            <th>Actual</th>",
        "            <th>Predicted</th>",
        "            <th>Match</th>",
        "            <th>Risk</th>",
        "            <th>Confidence</th>",
        "            <th>Explanation Support</th>",
        "          </tr>",
        "        </thead>",
        "        <tbody>",
    ]
    for r in results:
        match = r["actual_label"] == r["predicted_label"]
        match_class = "match-yes" if match else "match-no"
        support_status = r.get("explanation_support_status") or ""
        status_class = ""
        if support_status == "unsupported":
            status_class = "status-unsupported"
        elif support_status == "weak":
            status_class = "status-weak"
        row_class = "row-unsupported" if support_status == "unsupported" else ""
        html_parts += [
            f"          <tr class=\"{row_class}\">",
            f"            <td>{html.escape(str(r['sample_id']))}</td>",
            f"            <td>{html.escape(str(r['actual_label']))}</td>",
            f"            <td>{html.escape(str(r['predicted_label']))}</td>",
            f"            <td class=\"{match_class}\">{'Yes' if match else 'No'}</td>",
            f"            <td>{r['risk_score']:.2f}</td>",
            f"            <td>{r['confidence']:.2f}</td>",
            f"            <td class=\"{status_class}\">{html.escape(str(support_status))}</td>",
            "          </tr>",
        ]
    html_parts += [
        "        </tbody>",
        "      </table>",
        "    </section>",
    ]

    html_parts += [
        "    <section class=\"section\">",
        "      <h2>Per-Sample Execution Details</h2>",
    ]
    for r in results:
        notes = r.get("explanation_support_notes") or []
        card_class = "sample-card"
        if r.get("explanation_support_status") == "unsupported":
            card_class = "sample-card sample-unsupported"
        html_parts += [
            f"      <div class=\"{card_class}\">",
            f"        <h3>{html.escape(str(r.get('sample_id')))}</h3>",
            "        <div class=\"sample-grid\">",
            f"          <div><strong>Provider:</strong> {safe_value(r.get('provider'))}</div>",
            f"          <div><strong>Model:</strong> {safe_value(r.get('model'))}</div>",
            f"          <div><strong>Latency (ms):</strong> {safe_value(r.get('latency_ms'))}</div>",
            f"          <div><strong>Input tokens:</strong> {safe_value(r.get('input_tokens'))}</div>",
            f"          <div><strong>Output tokens:</strong> {safe_value(r.get('output_tokens'))}</div>",
            f"          <div><strong>Token cost (USD):</strong> {safe_value(r.get('token_cost_usd'))}</div>",
            f"          <div><strong>Explanation support status:</strong> {safe_value(r.get('explanation_support_status'))}</div>",
            f"          <div><strong>Explanation support notes:</strong> {safe_value(_format_notes(notes) or 'N/A')}</div>",
            f"          <div><strong>Reliability run id:</strong> {safe_value(r.get('reliability_run_id'))}</div>",
            f"          <div><strong>Reliability phase id:</strong> {safe_value(r.get('reliability_phase_id'))}</div>",
            f"          <div><strong>Reliability prompt id:</strong> {safe_value(r.get('reliability_prompt_id'))}</div>",
            f"          <div><strong>Reliability call id:</strong> {safe_value(r.get('reliability_call_id'))}</div>",
            "        </div>",
            "      </div>",
        ]
    html_parts += [
        "    </section>",
        "  </div>",
        "</body>",
        "</html>",
    ]

    filename = report_basename or name
    path = Path(outputs_dir) / f"{filename}.html"
    path.write_text("\n".join(html_parts) + "\n")
    return path
