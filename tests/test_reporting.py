import json
import tempfile
import unittest
import uuid
from types import SimpleNamespace

from evaluation.db_report import _apply_demo_safe, _compute_llm_summary, _normalize_result
from evaluation.report import write_json_report, write_markdown_report, write_html_report


class ReportingTests(unittest.TestCase):
    def test_compute_llm_summary_empty(self):
        summary = _compute_llm_summary({})
        self.assertEqual(summary["llm_call_count"], 0)
        self.assertEqual(summary["retry_count"], 0)
        self.assertEqual(summary["total_input_tokens"], 0)
        self.assertEqual(summary["total_output_tokens"], 0)
        self.assertEqual(summary["total_tokens"], 0)
        self.assertEqual(summary["total_cost_usd"], 0.0)
        self.assertEqual(summary["total_latency_ms"], 0.0)
        self.assertIsNone(summary["avg_latency_ms"])

    def test_compute_llm_summary_partial(self):
        call_id = uuid.uuid4()
        summary = _compute_llm_summary(
            {
                call_id: {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "latency_ms": 120,
                    "input_tokens": 200,
                    "output_tokens": 80,
                    "token_cost_usd": 0.12,
                    "retry_attempt_num": 1,
                }
            }
        )
        self.assertEqual(summary["llm_call_count"], 1)
        self.assertEqual(summary["retry_count"], 1)
        self.assertEqual(summary["total_input_tokens"], 200)
        self.assertEqual(summary["total_output_tokens"], 80)
        self.assertEqual(summary["total_tokens"], 280)
        self.assertEqual(summary["total_latency_ms"], 120.0)
        self.assertEqual(summary["avg_latency_ms"], 120.0)

    def test_apply_demo_safe(self):
        payload = {
            "explanation": "Sensitive text",
            "signals_json": {"a": 1},
            "timeline_json": ["x"],
            "predicted_label": "benign",
        }
        sanitized = _apply_demo_safe(payload)
        self.assertIsNone(sanitized["explanation"])
        self.assertIsNone(sanitized["signals_json"])
        self.assertIsNone(sanitized["timeline_json"])
        self.assertEqual(sanitized["predicted_label"], "benign")

    def test_normalize_result_missing_call_id(self):
        result = SimpleNamespace(
            sample_id="s1",
            actual_label="benign",
            predicted_label="benign",
            risk_score=0.1,
            confidence=0.9,
            explanation="ok",
            signals_json={"a": 1},
            timeline_json=["t"],
            reliability_run_id=uuid.uuid4(),
            reliability_phase_id=uuid.uuid4(),
            reliability_prompt_id=uuid.uuid4(),
            reliability_call_id=None,
        )
        payload = _normalize_result(result, {})
        self.assertIsNone(payload["provider"])
        self.assertIsNone(payload["model"])
        self.assertIsNone(payload["latency_ms"])

    def test_json_schema_stability(self):
        results = [
            {
                "sample_id": "s1",
                "actual_label": "benign",
                "predicted_label": "benign",
                "risk_score": 0.1,
                "confidence": 0.9,
                "explanation": None,
                "signals_json": None,
                "timeline_json": None,
                "reliability_run_id": "r1",
                "reliability_phase_id": "p1",
                "reliability_prompt_id": "pr1",
                "reliability_call_id": None,
                "provider": None,
                "model": None,
                "latency_ms": None,
                "input_tokens": None,
                "output_tokens": None,
                "token_cost_usd": None,
            }
        ]
        label_stats = {
            "phishing": {"precision": 0, "recall": 0, "f1": 0, "tp": 0, "fp": 0, "fn": 0},
            "impersonation": {"precision": 0, "recall": 0, "f1": 0, "tp": 0, "fp": 0, "fn": 0},
            "benign": {"precision": 1, "recall": 1, "f1": 1, "tp": 1, "fp": 0, "fn": 0},
        }
        llm_summary = {
            "providers": {},
            "models": {},
            "llm_call_count": 0,
            "retry_count": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "total_latency_ms": 0.0,
            "avg_latency_ms": None,
        }
        classification_metrics = {
            "accuracy": 1.0,
            "macro_precision": 1.0,
            "macro_recall": 1.0,
            "macro_f1": 1.0,
            "micro_precision": 1.0,
            "micro_recall": 1.0,
            "micro_f1": 1.0,
            "weighted_precision": 1.0,
            "weighted_recall": 1.0,
            "weighted_f1": 1.0,
            "per_label": {
                "phishing": {"support": 0, "precision": 0, "recall": 0, "f1": 0},
                "impersonation": {"support": 0, "precision": 0, "recall": 0, "f1": 0},
                "benign": {"support": 1, "precision": 1, "recall": 1, "f1": 1},
            },
            "labels": ["benign", "phishing", "impersonation"],
            "total_support": 1,
        }
        confusion_matrix = {
            "labels": ["benign", "phishing", "impersonation"],
            "rows": {
                "benign": {"benign": 1, "phishing": 0, "impersonation": 0},
                "phishing": {"benign": 0, "phishing": 0, "impersonation": 0},
                "impersonation": {"benign": 0, "phishing": 0, "impersonation": 0},
            },
        }
        explanation_support = {
            "supported_count": 1,
            "weak_count": 0,
            "unsupported_count": 0,
            "unavailable_count": 0,
            "examples": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_json_report(
                results,
                accuracy=1.0,
                label_stats=label_stats,
                name="test-run",
                model="test-model",
                llm_summary=llm_summary,
                classification_metrics=classification_metrics,
                confusion_matrix=confusion_matrix,
                explanation_support=explanation_support,
                generated_at="2026-03-23T00:00:00Z",
                outputs_dir=tmpdir,
            )
            payload = json.loads(path.read_text())
        self.assertIn("summary", payload)
        self.assertIn("results", payload)
        self.assertIn("llm", payload["summary"])
        self.assertIn("classification_metrics", payload["summary"])
        self.assertIn("confusion_matrix", payload["summary"])
        self.assertIn("explanation_support", payload["summary"])

    def test_markdown_report_includes_sections_and_details(self):
        results = [
            {
                "sample_id": "s1",
                "actual_label": "benign",
                "predicted_label": "benign",
                "risk_score": 0.1,
                "confidence": 0.9,
                "explanation": None,
                "signals_json": None,
                "timeline_json": None,
                "reliability_run_id": "r1",
                "reliability_phase_id": "p1",
                "reliability_prompt_id": "pr1",
                "reliability_call_id": "c1",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "latency_ms": 120.0,
                "input_tokens": 200,
                "output_tokens": 80,
                "token_cost_usd": 0.12,
                "explanation_support_status": "supported",
                "explanation_support_notes": ["signal evidence present"],
            },
            {
                "sample_id": "s2",
                "actual_label": "phishing",
                "predicted_label": "phishing",
                "risk_score": 0.8,
                "confidence": 0.6,
                "explanation": None,
                "signals_json": None,
                "timeline_json": None,
                "reliability_run_id": "r2",
                "reliability_phase_id": "p2",
                "reliability_prompt_id": "pr2",
                "reliability_call_id": "c2",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "latency_ms": 220.0,
                "input_tokens": 180,
                "output_tokens": 60,
                "token_cost_usd": 0.09,
                "explanation_support_status": "unsupported",
                "explanation_support_notes": ["missing evidence for claim"],
            },
        ]
        label_stats = {
            "phishing": {"precision": 0, "recall": 0, "f1": 0, "tp": 0, "fp": 0, "fn": 0},
            "impersonation": {"precision": 0, "recall": 0, "f1": 0, "tp": 0, "fp": 0, "fn": 0},
            "benign": {"precision": 1, "recall": 1, "f1": 1, "tp": 1, "fp": 0, "fn": 0},
        }
        llm_summary = {
            "providers": {"openai": 1},
            "models": {"gpt-4o-mini": 1},
            "llm_call_count": 1,
            "retry_count": 0,
            "total_input_tokens": 200,
            "total_output_tokens": 80,
            "total_tokens": 280,
            "total_cost_usd": 0.12,
            "total_latency_ms": 120.0,
            "avg_latency_ms": 120.0,
        }
        classification_metrics = {
            "accuracy": 1.0,
            "macro_precision": 1.0,
            "macro_recall": 1.0,
            "macro_f1": 1.0,
            "micro_precision": 1.0,
            "micro_recall": 1.0,
            "micro_f1": 1.0,
            "weighted_precision": 1.0,
            "weighted_recall": 1.0,
            "weighted_f1": 1.0,
            "per_label": {
                "phishing": {"support": 0, "precision": 0, "recall": 0, "f1": 0},
                "impersonation": {"support": 0, "precision": 0, "recall": 0, "f1": 0},
                "benign": {"support": 1, "precision": 1, "recall": 1, "f1": 1},
            },
            "labels": ["benign", "phishing", "impersonation"],
            "total_support": 1,
        }
        confusion_matrix = {
            "labels": ["benign", "phishing", "impersonation"],
            "rows": {
                "benign": {"benign": 1, "phishing": 0, "impersonation": 0},
                "phishing": {"benign": 0, "phishing": 0, "impersonation": 0},
                "impersonation": {"benign": 0, "phishing": 0, "impersonation": 0},
            },
        }
        explanation_support = {
            "supported_count": 1,
            "weak_count": 0,
            "unsupported_count": 1,
            "unavailable_count": 0,
            "examples": [
                {
                    "sample_id": "s2",
                    "actual_label": "phishing",
                    "predicted_label": "phishing",
                    "status": "unsupported",
                    "notes": ["missing evidence for claim"],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_markdown_report(
                results,
                accuracy=1.0,
                label_stats=label_stats,
                name="test-run",
                model="test-model",
                llm_summary=llm_summary,
                classification_metrics=classification_metrics,
                confusion_matrix=confusion_matrix,
                explanation_support=explanation_support,
                generated_at="2026-03-23T00:00:00Z",
                outputs_dir=tmpdir,
            )
            content = path.read_text()

        self.assertIn("## Classification Metrics", content)
        self.assertIn("## LLM Metadata", content)
        self.assertIn("## Confusion Matrix", content)
        self.assertIn("## Explanation Support", content)
        self.assertIn("## Results", content)
        self.assertIn("## Per-Sample Execution Details", content)
        self.assertIn("| Actual \\ Predicted | benign | phishing | impersonation |", content)
        self.assertIn("Supported: 1", content)
        self.assertIn("signal evidence present", content)
        self.assertIn("### s1", content)
        self.assertIn("- Provider: openai", content)
        self.assertIn("- Model: gpt-4o-mini", content)
        self.assertIn("- Latency (ms): 120.0", content)
        self.assertIn("- Input tokens: 200", content)
        self.assertIn("- Output tokens: 80", content)
        self.assertIn("- Token cost (USD): 0.12", content)
        self.assertIn("- Reliability run id: r1", content)
        self.assertIn("- Reliability phase id: p1", content)
        self.assertIn("- Reliability prompt id: pr1", content)
        self.assertIn("- Reliability call id: c1", content)

        order = [
            content.index("## Classification Metrics"),
            content.index("## LLM Metadata"),
            content.index("## Confusion Matrix"),
            content.index("## Explanation Support"),
            content.index("## Results"),
            content.index("## Per-Sample Execution Details"),
        ]
        self.assertEqual(order, sorted(order))

    def test_html_report_includes_sections_and_details(self):
        results = [
            {
                "sample_id": "s1",
                "actual_label": "benign",
                "predicted_label": "benign",
                "risk_score": 0.1,
                "confidence": 0.9,
                "explanation": None,
                "signals_json": None,
                "timeline_json": None,
                "reliability_run_id": "r1",
                "reliability_phase_id": "p1",
                "reliability_prompt_id": "pr1",
                "reliability_call_id": "c1",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "latency_ms": 120.0,
                "input_tokens": 200,
                "output_tokens": 80,
                "token_cost_usd": 0.12,
                "explanation_support_status": "supported",
                "explanation_support_notes": ["signal evidence present"],
            },
            {
                "sample_id": "s2",
                "actual_label": "phishing",
                "predicted_label": "phishing",
                "risk_score": 0.8,
                "confidence": 0.6,
                "explanation": None,
                "signals_json": None,
                "timeline_json": None,
                "reliability_run_id": "r2",
                "reliability_phase_id": "p2",
                "reliability_prompt_id": "pr2",
                "reliability_call_id": "c2",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "latency_ms": 220.0,
                "input_tokens": 180,
                "output_tokens": 60,
                "token_cost_usd": 0.09,
                "explanation_support_status": "unsupported",
                "explanation_support_notes": ["missing evidence for claim"],
            },
        ]
        label_stats = {
            "phishing": {"precision": 0, "recall": 0, "f1": 0, "tp": 0, "fp": 0, "fn": 0},
            "impersonation": {"precision": 0, "recall": 0, "f1": 0, "tp": 0, "fp": 0, "fn": 0},
            "benign": {"precision": 1, "recall": 1, "f1": 1, "tp": 1, "fp": 0, "fn": 0},
        }
        llm_summary = {
            "providers": {"openai": 1},
            "models": {"gpt-4o-mini": 1},
            "llm_call_count": 1,
            "retry_count": 0,
            "total_input_tokens": 200,
            "total_output_tokens": 80,
            "total_tokens": 280,
            "total_cost_usd": 0.12,
            "total_latency_ms": 120.0,
            "avg_latency_ms": 120.0,
        }
        classification_metrics = {
            "accuracy": 1.0,
            "macro_precision": 1.0,
            "macro_recall": 1.0,
            "macro_f1": 1.0,
            "micro_precision": 1.0,
            "micro_recall": 1.0,
            "micro_f1": 1.0,
            "weighted_precision": 1.0,
            "weighted_recall": 1.0,
            "weighted_f1": 1.0,
            "per_label": {
                "phishing": {"support": 0, "precision": 0, "recall": 0, "f1": 0},
                "impersonation": {"support": 0, "precision": 0, "recall": 0, "f1": 0},
                "benign": {"support": 1, "precision": 1, "recall": 1, "f1": 1},
            },
            "labels": ["benign", "phishing", "impersonation"],
            "total_support": 1,
        }
        confusion_matrix = {
            "labels": ["benign", "phishing", "impersonation"],
            "rows": {
                "benign": {"benign": 1, "phishing": 0, "impersonation": 0},
                "phishing": {"benign": 0, "phishing": 0, "impersonation": 0},
                "impersonation": {"benign": 0, "phishing": 0, "impersonation": 0},
            },
        }
        explanation_support = {
            "supported_count": 1,
            "weak_count": 0,
            "unsupported_count": 1,
            "unavailable_count": 0,
            "examples": [
                {
                    "sample_id": "s2",
                    "actual_label": "phishing",
                    "predicted_label": "phishing",
                    "status": "unsupported",
                    "notes": ["missing evidence for claim"],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_html_report(
                results,
                accuracy=1.0,
                label_stats=label_stats,
                name="test-run",
                model="test-model",
                llm_summary=llm_summary,
                classification_metrics=classification_metrics,
                confusion_matrix=confusion_matrix,
                explanation_support=explanation_support,
                generated_at="2026-03-23T00:00:00Z",
                outputs_dir=tmpdir,
            )
            content = path.read_text()

        self.assertIn("Evaluation Report: test-run", content)
        self.assertIn("Classification Metrics", content)
        self.assertIn("LLM Metadata", content)
        self.assertIn("Confusion Matrix", content)
        self.assertIn("Explanation Support", content)
        self.assertIn("Per-Sample Execution Details", content)
        self.assertIn("Explanation Support</th>", content)
        self.assertIn("Explanation support status", content)
        self.assertIn("Explanation support notes", content)
        self.assertIn("missing evidence for claim", content)
        self.assertIn("2026-03-23 00:00 UTC", content)
        self.assertIn("Provider:", content)
        self.assertIn("Reliability run id", content)
        self.assertIn("row-unsupported", content)

        order = [
            content.index("Classification Metrics"),
            content.index("LLM Metadata"),
            content.index("Confusion Matrix"),
            content.index("Explanation Support"),
            content.index("Results"),
            content.index("Per-Sample Execution Details"),
        ]
        self.assertEqual(order, sorted(order))


if __name__ == "__main__":
    unittest.main()
