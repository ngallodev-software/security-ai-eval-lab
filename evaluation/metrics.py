from __future__ import annotations

from collections import Counter
from typing import Iterable, Tuple, Dict, List


def compute_accuracy(pairs: Iterable[Tuple[str, str]]) -> float:
    pairs = list(pairs)
    if not pairs:
        return 0.0
    correct = sum(1 for actual, predicted in pairs if actual == predicted)
    return correct / len(pairs)


def compute_label_stats(pairs: Iterable[Tuple[str, str]], positive_label: str):
    pairs = list(pairs)
    tp = sum(1 for actual, predicted in pairs if actual == positive_label and predicted == positive_label)
    fp = sum(1 for actual, predicted in pairs if actual != positive_label and predicted == positive_label)
    fn = sum(1 for actual, predicted in pairs if actual == positive_label and predicted != positive_label)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "label": positive_label,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def compute_confusion_matrix(
    pairs: Iterable[Tuple[str, str]],
    labels: List[str],
) -> Dict[str, Dict[str, int]]:
    matrix: Dict[str, Dict[str, int]] = {
        actual: {predicted: 0 for predicted in labels} for actual in labels
    }
    for actual, predicted in pairs:
        if actual not in matrix:
            matrix[actual] = {pred: 0 for pred in labels}
        if predicted not in matrix[actual]:
            matrix[actual][predicted] = 0
        matrix[actual][predicted] += 1
    return matrix


def compute_classification_metrics(
    pairs: Iterable[Tuple[str, str]],
    labels: List[str],
) -> Dict[str, Dict]:
    pairs = list(pairs)
    matrix = compute_confusion_matrix(pairs, labels)

    per_label: Dict[str, Dict[str, float]] = {}
    total_support = 0
    total_tp = 0
    total_fp = 0
    total_fn = 0

    for label in labels:
        support = sum(matrix.get(label, {}).values()) if label in matrix else 0
        tp = matrix.get(label, {}).get(label, 0)
        fp = sum(matrix.get(actual, {}).get(label, 0) for actual in matrix if actual != label)
        fn = support - tp
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        f1 = _safe_div(2 * precision * recall, precision + recall)
        per_label[label] = {
            "support": support,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
        total_support += support
        total_tp += tp
        total_fp += fp
        total_fn += fn

    macro_precision = _safe_div(sum(v["precision"] for v in per_label.values()), len(labels))
    macro_recall = _safe_div(sum(v["recall"] for v in per_label.values()), len(labels))
    macro_f1 = _safe_div(sum(v["f1"] for v in per_label.values()), len(labels))

    weighted_precision = _safe_div(
        sum(v["precision"] * v["support"] for v in per_label.values()),
        total_support,
    )
    weighted_recall = _safe_div(
        sum(v["recall"] * v["support"] for v in per_label.values()),
        total_support,
    )
    weighted_f1 = _safe_div(
        sum(v["f1"] * v["support"] for v in per_label.values()),
        total_support,
    )

    micro_precision = _safe_div(total_tp, total_tp + total_fp)
    micro_recall = _safe_div(total_tp, total_tp + total_fn)
    micro_f1 = _safe_div(2 * micro_precision * micro_recall, micro_precision + micro_recall)

    return {
        "accuracy": compute_accuracy(pairs),
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_f1": micro_f1,
        "weighted_precision": weighted_precision,
        "weighted_recall": weighted_recall,
        "weighted_f1": weighted_f1,
        "per_label": per_label,
        "labels": labels,
        "total_support": total_support,
    }
