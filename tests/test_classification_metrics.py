import unittest

from evaluation.metrics import compute_classification_metrics, compute_confusion_matrix


class ClassificationMetricsTests(unittest.TestCase):
    def test_perfect_classification(self):
        pairs = [
            ("benign", "benign"),
            ("phishing", "phishing"),
            ("impersonation", "impersonation"),
        ]
        labels = ["benign", "phishing", "impersonation"]
        metrics = compute_classification_metrics(pairs, labels)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["macro_f1"], 1.0)
        self.assertEqual(metrics["micro_f1"], 1.0)
        self.assertEqual(metrics["weighted_f1"], 1.0)

    def test_mixed_classification(self):
        pairs = [
            ("benign", "phishing"),
            ("phishing", "phishing"),
            ("impersonation", "phishing"),
        ]
        labels = ["benign", "phishing", "impersonation"]
        metrics = compute_classification_metrics(pairs, labels)
        self.assertGreater(metrics["macro_f1"], 0.0)
        self.assertLess(metrics["accuracy"], 1.0)

    def test_zero_division_safe(self):
        pairs = [("benign", "benign")]
        labels = ["benign", "phishing", "impersonation"]
        metrics = compute_classification_metrics(pairs, labels)
        self.assertEqual(metrics["per_label"]["phishing"]["precision"], 0.0)
        self.assertEqual(metrics["per_label"]["impersonation"]["recall"], 0.0)

    def test_missing_label_matrix(self):
        pairs = [("benign", "benign"), ("benign", "phishing")]
        labels = ["benign", "phishing", "impersonation"]
        matrix = compute_confusion_matrix(pairs, labels)
        self.assertIn("benign", matrix)
        self.assertIn("impersonation", matrix)
        self.assertEqual(matrix["impersonation"]["benign"], 0)


if __name__ == "__main__":
    unittest.main()
