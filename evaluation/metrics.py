from __future__ import annotations

from collections import Counter
from typing import Iterable, Tuple


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