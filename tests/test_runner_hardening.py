from __future__ import annotations

import importlib
import json
import os
import tempfile
import unittest
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock, patch

from agents.email_threat_agent import (
    FakeReliabilityExecutor,
    bound_email_text_for_llm,
    build_llm_payload,
    extract_sender_domain,
    parse_auth_results,
)


def _load_runner():
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost/security_eval",
    )
    module = importlib.import_module("evaluation.runner")
    return importlib.reload(module)


class RunnerHardeningTests(unittest.IsolatedAsyncioTestCase):
    def test_load_samples_validates_schema(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = Path(tmpdir) / "sample.json"
            sample_path.write_text(
                json.dumps(
                    {
                        "id": "sample-1",
                        "label": "benign",
                        "email_text": "From: Example <example@example.com>\n\nHello",
                        "metadata": {"source": "test"},
                    }
                ),
                encoding="utf-8",
            )

            samples = runner.load_samples(tmpdir)

        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0]["id"], "sample-1")

    async def test_invalid_dataset_returns_before_db_access(self):
        runner = _load_runner()
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = Path(tmpdir) / "invalid.json"
            sample_path.write_text(
                json.dumps(
                    {
                        "id": "sample-1",
                        "email_text": "From: Example <example@example.com>\n\nHello",
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(runner, "eval_session") as eval_session_mock:
                await runner.run_evaluation(tmpdir, "run-name", "gpt-4o-mini", "openai", False)

        eval_session_mock.assert_not_called()

    async def test_failed_sample_marks_run_failed_and_uses_overridden_model(self):
        runner = _load_runner()
        sample = {
            "id": "sample-1",
            "label": "benign",
            "email_text": "From: Example <example@example.com>\n\nHello",
        }
        fake_run_id = uuid.uuid4()
        fake_repo = AsyncMock()
        fake_repo.create_evaluation_run.return_value = fake_run_id
        fake_repo.mark_evaluation_run_complete.return_value = fake_run_id

        @asynccontextmanager
        async def fake_eval_session():
            yield object()

        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = Path(tmpdir) / "sample.json"
            sample_path.write_text(json.dumps(sample), encoding="utf-8")

            with (
                patch.object(runner, "eval_session", fake_eval_session),
                patch.object(runner, "EvalRepository", return_value=fake_repo),
                patch.object(runner, "investigate_sample", AsyncMock(side_effect=RuntimeError("boom"))),
                patch.object(runner, "write_json_report", return_value=Path("/tmp/out.json")),
                patch.object(runner, "write_markdown_report", return_value=Path("/tmp/out.md")),
                patch.object(runner, "write_html_report", return_value=Path("/tmp/out.html")),
                patch.dict(
                    os.environ,
                    {
                        "CLASSIFICATION_PROVIDER": "openai",
                        "CLASSIFICATION_MODEL": "override-model",
                    },
                    clear=False,
                ),
            ):
                await runner.run_evaluation(tmpdir, "run-name", "gpt-4o-mini", "openai", False)

        fake_repo.create_evaluation_run.assert_awaited_once()
        create_kwargs = fake_repo.create_evaluation_run.await_args.args[0]
        self.assertEqual(create_kwargs["model_label"], "override-model")
        fake_repo.mark_evaluation_run_complete.assert_awaited_once()
        self.assertEqual(fake_repo.mark_evaluation_run_complete.await_args.kwargs["status"], "failed")


class AgentHardeningTests(unittest.TestCase):
    def test_sender_domain_ignores_body_spoofing(self):
        email_text = (
            "From: Legit Sender <alerts@example.com>\n"
            "Subject: Update\n\n"
            "From: Spoofed Sender <spoof@evil.com>\n"
            "This is body text."
        )

        self.assertEqual(extract_sender_domain(email_text), "example.com")

    def test_auth_results_use_headers_only(self):
        email_text = (
            "From: Legit Sender <alerts@example.com>\n"
            "Authentication-Results: mx.example.com; spf=pass dkim=fail dmarc=pass\n"
            "\n"
            "spf=fail dkim=pass dmarc=fail"
        )

        self.assertEqual(
            parse_auth_results(email_text),
            {
                "spf_result": "pass",
                "dkim_result": "fail",
                "dmarc_result": "pass",
            },
        )

    def test_email_payload_is_bounded_for_llm(self):
        email_text = (
            "From: Example <alerts@example.com>\n"
            "Subject: Password reset required\n\n"
            + "A" * 12_050
        )
        payload = build_llm_payload(
            email_text,
            {
                "sender_domain": "example.com",
                "urls": ["https://example.com/reset"],
            },
        )

        self.assertLess(len(payload["email_text"]), len(email_text))
        self.assertEqual(len(payload["email_text"]), len(bound_email_text_for_llm(payload["email_text"])))
        self.assertEqual(payload["email_context"]["subject"], "Password reset required")
        self.assertTrue(payload["email_body_truncated"])
        self.assertEqual(payload["raw_email_original_chars"], len(email_text))

    def test_fake_executor_flags_vendor_impersonation_without_urls(self):
        executor = FakeReliabilityExecutor()
        email_text = (
            "From: Vendor Relations <billing@paypa1-support-services.com>\n"
            "Subject: Invoice issue\n\n"
            "Confirm payment details."
        )
        payload = build_llm_payload(
            email_text,
            {
                "sender_domain": "paypa1-support-services.com",
                "urls": [],
                "domain_age_days": 7,
                "brand_similarity": {"matched_brand": "PayPal", "score": 0.92},
            },
        )

        result = executor.execute(
            phase_id="email_threat_classification",
            prompt_id="email-threat-v1",
            payload=payload,
        )

        self.assertEqual(result["predicted_label"], "impersonation")

    def test_fake_executor_flags_password_reset_lure_as_phishing(self):
        executor = FakeReliabilityExecutor()
        email_text = (
            "From: IT Service Desk <support@company-helpdesk-reset.com>\n"
            "Subject: Password reset required\n\n"
            "Reset now:\nhttps://company-helpdesk-reset.com/reset"
        )
        payload = build_llm_payload(
            email_text,
            {
                "sender_domain": "company-helpdesk-reset.com",
                "urls": ["https://company-helpdesk-reset.com/reset"],
                "domain_age_days": 7,
                "brand_similarity": {"matched_brand": None, "score": 0.0},
            },
        )

        result = executor.execute(
            phase_id="email_threat_classification",
            prompt_id="email-threat-v1",
            payload=payload,
        )

        self.assertEqual(result["predicted_label"], "phishing")


if __name__ == "__main__":
    unittest.main()
