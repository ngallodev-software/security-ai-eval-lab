from __future__ import annotations

from typing import Any, Dict, List, Tuple


def evaluate_explanation_support(result: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Lightweight evidence grounding check.

    Returns (status, notes) where status is one of:
    supported | weak | unsupported | unavailable
    """
    notes: List[str] = []

    explanation = result.get("explanation")
    signals = result.get("signals_json")
    predicted_label = result.get("predicted_label")

    if not explanation or not isinstance(explanation, str) or not explanation.strip():
        return "unavailable", ["missing or empty explanation"]
    if not isinstance(signals, dict):
        return "unavailable", ["missing signals_json"]

    urls = signals.get("urls") or []
    spf = signals.get("spf_result")
    dkim = signals.get("dkim_result")
    dmarc = signals.get("dmarc_result")
    domain_age_days = signals.get("domain_age_days")
    brand_similarity = signals.get("brand_similarity") or {}
    brand_score = brand_similarity.get("score")

    evidence_points = 0
    if isinstance(urls, list) and len(urls) > 0:
        evidence_points += 1
    if spf == "fail" or dkim == "fail" or dmarc == "fail":
        evidence_points += 1
    if isinstance(domain_age_days, int) and domain_age_days < 30:
        evidence_points += 1
    if isinstance(brand_score, (int, float)) and brand_score >= 0.7:
        evidence_points += 1

    explanation_lower = explanation.lower()
    mentions_link = ("link" in explanation_lower) or ("url" in explanation_lower)
    if mentions_link and not urls:
        notes.append("explanation references links but no urls were extracted")

    if predicted_label in ("phishing", "impersonation"):
        if evidence_points == 0:
            notes.append("high-risk label with no supporting signals")
            return "unsupported", notes
        if evidence_points == 1:
            notes.append("high-risk label with minimal supporting signals")
            return "weak", notes
        return "supported", notes

    if predicted_label == "benign":
        if evidence_points >= 2:
            notes.append("benign label despite multiple risk signals")
            return "weak", notes
        return "supported", notes

    return "weak", ["unknown label or insufficient context"]
