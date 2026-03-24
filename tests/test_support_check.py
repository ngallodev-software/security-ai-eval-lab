import unittest

from evaluation.support_check import evaluate_explanation_support


class SupportCheckTests(unittest.TestCase):
    def test_supported_high_risk(self):
        result = {
            "predicted_label": "phishing",
            "explanation": "Contains a suspicious login link.",
            "signals_json": {
                "urls": ["http://example.com/login"],
                "spf_result": "fail",
                "dkim_result": None,
                "dmarc_result": None,
                "domain_age_days": 7,
                "brand_similarity": {"score": 0.8},
            },
        }
        status, _ = evaluate_explanation_support(result)
        self.assertEqual(status, "supported")

    def test_unsupported_high_risk(self):
        result = {
            "predicted_label": "phishing",
            "explanation": "Suspicious login link detected.",
            "signals_json": {
                "urls": [],
                "spf_result": None,
                "dkim_result": None,
                "dmarc_result": None,
                "domain_age_days": None,
                "brand_similarity": {"score": 0.0},
            },
        }
        status, _ = evaluate_explanation_support(result)
        self.assertEqual(status, "unsupported")

    def test_empty_explanation(self):
        result = {"predicted_label": "benign", "explanation": "", "signals_json": {}}
        status, _ = evaluate_explanation_support(result)
        self.assertEqual(status, "unavailable")

    def test_missing_signals(self):
        result = {"predicted_label": "benign", "explanation": "Looks fine."}
        status, _ = evaluate_explanation_support(result)
        self.assertEqual(status, "unavailable")

    def test_weak_benign_with_signals(self):
        result = {
            "predicted_label": "benign",
            "explanation": "No issues found.",
            "signals_json": {
                "urls": ["http://example.com/login"],
                "spf_result": "fail",
                "dkim_result": None,
                "dmarc_result": None,
                "domain_age_days": 7,
                "brand_similarity": {"score": 0.2},
            },
        }
        status, _ = evaluate_explanation_support(result)
        self.assertEqual(status, "weak")


if __name__ == "__main__":
    unittest.main()
