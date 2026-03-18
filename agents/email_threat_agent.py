from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import re
import time
import uuid
from urllib.parse import urlparse


# -----------------------------
# Result models
# -----------------------------

@dataclass
class BrandSimilarityResult:
    matched_brand: Optional[str]
    score: float


@dataclass
class Signals:
    sender_domain: Optional[str]
    urls: List[str]
    domain_age_days: Optional[int]
    spf_result: Optional[str]
    dkim_result: Optional[str]
    dmarc_result: Optional[str]
    brand_similarity: BrandSimilarityResult


@dataclass
class LLMMetadata:
    model: str
    call_id: Optional[str]
    latency_ms: Optional[int]
    token_cost_usd: Optional[float]


@dataclass
class InvestigationResult:
    sample_id: Optional[str]
    predicted_label: str
    risk_score: float
    confidence: float
    explanation: str
    signals: Dict[str, Any]
    llm: Dict[str, Any]
    timeline: List[str]


# -----------------------------
# Minimal signal helpers
# Replace these later with your
# real signal modules.
# -----------------------------

KNOWN_BRANDS = [
    "Microsoft",
    "DocuSign",
    "PayPal",
    "Zoom",
    "GitHub",
    "Okta",
    "Google",
]


def extract_sender_domain(email_text: str) -> Optional[str]:
    match = re.search(r"From:\s.*?<[^@]+@([^>]+)>", email_text, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return None


def extract_urls(email_text: str) -> List[str]:
    return re.findall(r"https?://[^\s]+", email_text, re.IGNORECASE)


def parse_auth_results(email_text: str) -> Dict[str, Optional[str]]:
    # MVP stub: parse only if present in text
    spf = None
    dkim = None
    dmarc = None

    lower = email_text.lower()

    if "spf=fail" in lower:
        spf = "fail"
    elif "spf=pass" in lower:
        spf = "pass"

    if "dkim=fail" in lower:
        dkim = "fail"
    elif "dkim=pass" in lower:
        dkim = "pass"

    if "dmarc=fail" in lower:
        dmarc = "fail"
    elif "dmarc=pass" in lower:
        dmarc = "pass"

    return {
        "spf_result": spf,
        "dkim_result": dkim,
        "dmarc_result": dmarc,
    }


def estimate_domain_age_days(sender_domain: Optional[str]) -> Optional[int]:
    # MVP stub:
    # Replace with real lookup later.
    if not sender_domain:
        return None

    suspicious_markers = ["support", "review", "reset", "secure", "login"]
    if any(marker in sender_domain for marker in suspicious_markers):
        return 7

    return 365


def compute_brand_similarity(email_text: str, sender_domain: Optional[str]) -> BrandSimilarityResult:
    haystack = f"{email_text} {sender_domain or ''}".lower()

    brand_hits = []
    for brand in KNOWN_BRANDS:
        if brand.lower() in haystack:
            brand_hits.append(brand)

    # crude lookalike heuristics for MVP
    if sender_domain:
        if "micr0soft" in sender_domain:
            return BrandSimilarityResult(matched_brand="Microsoft", score=0.93)
        if "paypa1" in sender_domain:
            return BrandSimilarityResult(matched_brand="PayPal", score=0.92)
        if "docusign" in sender_domain and not sender_domain.endswith("docusign.net"):
            return BrandSimilarityResult(matched_brand="DocuSign", score=0.88)

    if brand_hits:
        return BrandSimilarityResult(matched_brand=brand_hits[0], score=0.70)

    return BrandSimilarityResult(matched_brand=None, score=0.0)


# -----------------------------
# Reliability framework adapter
# -----------------------------

class ReliabilityExecutorProtocol:
    """
    Small adapter contract so this agent does not hard-couple
    itself to your current framework implementation details.
    """

    def execute(self, *, phase_id: str, prompt_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class FakeReliabilityExecutor(ReliabilityExecutorProtocol):
    """
    Temporary stub for MVP wiring and local testing.
    Replace with PhaseExecutor adapter from ai-reliability-fw.
    """

    def _build_result(self, *, phase_id: str, prompt_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        signals = payload["signals"]
        sender_domain = signals.get("sender_domain") or ""
        brand = signals.get("brand_similarity", {}).get("matched_brand")
        domain_age_days = signals.get("domain_age_days")
        urls = signals.get("urls", [])

        suspicious = False
        predicted_label = "benign"
        risk_score = 0.15
        confidence = 0.72
        explanation = "Low-risk message with limited suspicious indicators."

        if brand and domain_age_days is not None and domain_age_days < 30:
            suspicious = True

        if "gmail.com" in sender_domain and "quick favor" in payload["email_text"].lower():
            predicted_label = "impersonation"
            risk_score = 0.89
            confidence = 0.90
            explanation = "Likely impersonation: personal sender domain plus urgent social-engineering language."
        elif suspicious or any("login" in url.lower() or "verify" in url.lower() for url in urls):
            predicted_label = "phishing"
            risk_score = 0.93
            confidence = 0.91
            explanation = "Likely phishing: suspicious domain and credential/verification lure."
        else:
            predicted_label = "benign"

        response_raw = {
            "predicted_label": predicted_label,
            "risk_score": risk_score,
            "confidence": confidence,
            "explanation": explanation,
        }
        run_id = uuid.uuid5(uuid.NAMESPACE_URL, f"fake-run:{phase_id}:{prompt_id}:{payload.get('email_text', '')}")
        call_id = uuid.uuid5(uuid.NAMESPACE_URL, f"fake-call:{phase_id}:{prompt_id}:{payload.get('email_text', '')}")
        return {
            "predicted_label": predicted_label,
            "risk_score": risk_score,
            "confidence": confidence,
            "explanation": explanation,
            "output": response_raw,
            "reliability_run_id": str(run_id),
            "reliability_phase_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"fake-phase:{phase_id}")),
            "reliability_prompt_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"fake-prompt:{prompt_id}")),
            "reliability_call_id": str(call_id),
            "call_id": str(call_id),
            "provider": "fake-reliability",
            "model": "fake-llm",
            "latency_ms": 42,
            "input_tokens": 0,
            "output_tokens": 0,
            "token_cost_usd": 0.0,
        }

    def execute(self, *, phase_id: str, prompt_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._build_result(phase_id=phase_id, prompt_id=prompt_id, payload=payload)

    async def execute_async(
        self,
        *,
        phase_id: str,
        prompt_id: str,
        payload: Dict[str, Any] | None = None,
        evidence_bundle: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        structured_payload = evidence_bundle if evidence_bundle is not None else payload
        if structured_payload is None:
            raise ValueError("payload or evidence_bundle is required")
        return self._build_result(phase_id=phase_id, prompt_id=prompt_id, payload=structured_payload)


# -----------------------------
# Main agent
# -----------------------------

class EmailThreatInvestigationAgent:
    """
    MVP agent:
    1. collect deterministic signals
    2. send structured bundle to reliability framework
    3. return a simple, reproducible investigation result
    """

    def __init__(self, executor: ReliabilityExecutorProtocol) -> None:
        self.executor = executor

    def analyze(self, email_text: str, sample_id: Optional[str] = None) -> InvestigationResult:
        timeline: List[str] = []
        start = time.perf_counter()

        timeline.append("parse sender domain")
        sender_domain = extract_sender_domain(email_text)

        timeline.append("extract urls")
        urls = extract_urls(email_text)

        timeline.append("parse auth results")
        auth = parse_auth_results(email_text)

        timeline.append("estimate domain age")
        domain_age_days = estimate_domain_age_days(sender_domain)

        timeline.append("compute brand similarity")
        brand_similarity = compute_brand_similarity(email_text, sender_domain)

        signals = Signals(
            sender_domain=sender_domain,
            urls=urls,
            domain_age_days=domain_age_days,
            spf_result=auth["spf_result"],
            dkim_result=auth["dkim_result"],
            dmarc_result=auth["dmarc_result"],
            brand_similarity=brand_similarity,
        )

        payload = {
            "email_text": email_text,
            "signals": {
                "sender_domain": signals.sender_domain,
                "urls": signals.urls,
                "domain_age_days": signals.domain_age_days,
                "spf_result": signals.spf_result,
                "dkim_result": signals.dkim_result,
                "dmarc_result": signals.dmarc_result,
                "brand_similarity": asdict(signals.brand_similarity),
            },
        }

        timeline.append("llm classification")
        llm_result = self.executor.execute(
            phase_id="email_threat_classification",
            prompt_id="email-threat-v1",
            payload=payload,
        )

        total_ms = int((time.perf_counter() - start) * 1000)

        output = llm_result.get("output", llm_result)
        timeline.append(f"complete ({total_ms} ms)")

        return InvestigationResult(
            sample_id=sample_id,
            predicted_label=output["predicted_label"],
            risk_score=float(output["risk_score"]),
            confidence=float(output["confidence"]),
            explanation=output["explanation"],
            signals={
                "sender_domain": signals.sender_domain,
                "urls": signals.urls,
                "domain_age_days": signals.domain_age_days,
                "spf_result": signals.spf_result,
                "dkim_result": signals.dkim_result,
                "dmarc_result": signals.dmarc_result,
                "brand_similarity": asdict(signals.brand_similarity),
            },
            llm={
                "provider": llm_result.get("provider"),
                "model": llm_result.get("model"),
                "call_id": llm_result.get("call_id"),
                "latency_ms": llm_result.get("latency_ms"),
                "input_tokens": llm_result.get("input_tokens"),
                "output_tokens": llm_result.get("output_tokens"),
                "token_cost_usd": llm_result.get("token_cost_usd"),
            },
            timeline=timeline,
        )
