"""Reliability adapter for security-ai-eval-lab.

Wraps ai-reliability-fw's PhaseExecutor so the evaluation runner can call it
through the existing ReliabilityExecutorProtocol interface.

Responsibilities:
- Create or reuse the workflow, prompt, and workflow_run rows that
  PhaseExecutor requires before execute() is called.
- Serialize the evidence bundle deterministically.
- Call PhaseExecutor.execute().
- Normalize the returned artifact into the structured output the runner
  expects.
- Surface reliability metadata from the framework success payload.

What this adapter does NOT do:
- Persist llm_calls or escalation_records (PhaseExecutor handles that).
- Duplicate any reliability-layer table.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Dict

from src.db.repository import ReliabilityRepository
from src.db.session import get_db as reliability_get_db
from src.engine.decision_engine import RetryPolicy, RetryRule
from src.engine.phase_executor import PhaseExecutor
from src.core.models import FailureCategory
from src.validators.input_schema_validator import InputIntegrityValidator
from src.validators.json_schema_validator import JsonSchemaValidator

from agents.email_threat_agent import ReliabilityExecutorProtocol

# -----------------------------------------------------------------------
# Static UUIDs for the single workflow used by this lab.
# Using deterministic UUIDs keeps the workflow row idempotent across runs.
# -----------------------------------------------------------------------
_WORKFLOW_ID = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
_PHASE_ID = uuid.UUID("b2c3d4e5-f6a7-8901-bcde-f12345678901")

# Output schema the LLM must satisfy.
_LLM_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["predicted_label", "risk_score", "confidence", "explanation"],
    "properties": {
        "predicted_label": {"type": "string", "enum": ["phishing", "impersonation", "benign"]},
        "risk_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "explanation": {"type": "string"},
    },
}

# Prompt content used for email threat classification.
_PROMPT_CONTENT = (
    "Classify the email evidence bundle below as phishing, impersonation, or benign. "
    "Return a JSON object with predicted_label, risk_score, confidence, and explanation."
)
_PROMPT_VERSION = "email-threat-v1"
_PROMPT_HASH = hashlib.sha256(_PROMPT_CONTENT.encode()).hexdigest()

_DEFAULT_RETRY_POLICY = RetryPolicy(
    max_retries=2,
    rules=[
        RetryRule(
            failure_category=FailureCategory.SCHEMA_VIOLATION,
            retry_strategy="RERUN",
        ),
        RetryRule(
            failure_category=FailureCategory.MISSING_REQUIRED_FIELD,
            retry_strategy="RERUN",
        ),
    ],
)


def _serialize_evidence_bundle(evidence_bundle: Dict[str, Any]) -> str:
    """Return a stable JSON representation for the framework call path."""
    return json.dumps(
        evidence_bundle,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _normalize_success_payload(
    *,
    artifact_json: Dict[str, Any],
    fw_result: Dict[str, Any],
    run_id: uuid.UUID,
    phase_id: uuid.UUID,
    prompt_id: uuid.UUID,
) -> Dict[str, Any]:
    output = {
        "predicted_label": artifact_json["predicted_label"],
        "risk_score": float(artifact_json["risk_score"]),
        "confidence": float(artifact_json["confidence"]),
        "explanation": artifact_json["explanation"],
    }
    call_id = fw_result.get("call_id")
    return {
        "predicted_label": output["predicted_label"],
        "risk_score": output["risk_score"],
        "confidence": output["confidence"],
        "explanation": output["explanation"],
        "output": output,
        "reliability_run_id": str(run_id),
        "reliability_phase_id": str(phase_id),
        "reliability_prompt_id": str(prompt_id),
        "reliability_call_id": call_id,
        "call_id": call_id,
        "provider": fw_result.get("provider"),
        "model": fw_result.get("model"),
        "latency_ms": fw_result.get("latency_ms"),
        "input_tokens": fw_result.get("input_tokens"),
        "output_tokens": fw_result.get("output_tokens"),
        "token_cost_usd": fw_result.get("token_cost_usd"),
    }


class PhaseExecutorAdapter(ReliabilityExecutorProtocol):
    """
    Async adapter that drives PhaseExecutor for a single evidence bundle.

    Manages its own reliability DB session per execute_async() call using
    the reliability-fw session factory — the evaluation runner only handles
    the eval-lab session.

    Usage::

        adapter = PhaseExecutorAdapter(llm_client)
        result = await adapter.execute_async(
            phase_id="email_threat_classification",
            prompt_id="email-threat-v1",
            payload=evidence_bundle,
        )
    """

    def __init__(self, llm_client) -> None:
        self._llm_client = llm_client

    # ------------------------------------------------------------------
    # Setup helpers (all take an explicit repo so they stay pure)
    # ------------------------------------------------------------------

    async def _ensure_workflow(self, repo: ReliabilityRepository) -> None:
        await repo.persist_workflow(
            {
                "workflow_id": _WORKFLOW_ID,
                "name": "email_threat_investigation",
                "version": "1.0",
                "definition_json": {"phases": ["email_threat_classification"]},
            }
        )

    async def _ensure_prompt(self, repo: ReliabilityRepository) -> uuid.UUID:
        prompt_id = await repo.persist_prompt(
            {
                "prompt_id": uuid.uuid5(uuid.NAMESPACE_URL, _PROMPT_HASH),
                "content": _PROMPT_CONTENT,
                "prompt_hash": _PROMPT_HASH,
                "version_tag": _PROMPT_VERSION,
            }
        )
        return prompt_id

    async def _create_run(self, repo: ReliabilityRepository) -> uuid.UUID:
        run_id = uuid.uuid4()
        await repo.persist_run(
            {
                "run_id": run_id,
                "workflow_id": _WORKFLOW_ID,
            }
        )
        return run_id

    # ------------------------------------------------------------------
    # Public async entry point
    # ------------------------------------------------------------------

    async def execute_async(
        self,
        *,
        phase_id: str,
        prompt_id: str,
        payload: Dict[str, Any] | None = None,
        evidence_bundle: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Full async execution path: setup rows → execute → parse output.

        Opens its own reliability DB session via the reliability-fw session
        factory, so the eval runner has no dependency on the reliability
        session layer.

        Returns a dict with:
        {
            "output": {"predicted_label", "risk_score", "confidence", "explanation"},
            "call_id": str | None,
            "model": str | None,
            "latency_ms": int | None,
            "token_cost_usd": float | None,
            "reliability_run_id": str,
            "reliability_phase_id": str,
            "reliability_prompt_id": str,
        }
        """
        # get_db() is the reliability-fw's canonical session factory.
        # It's an async generator that yields exactly one session; we drive
        # it manually since we're outside a FastAPI dependency context.
        structured_evidence = evidence_bundle if evidence_bundle is not None else payload
        if structured_evidence is None:
            raise ValueError("payload or evidence_bundle is required")

        _db_gen = reliability_get_db()
        session = await anext(_db_gen)
        try:
            repo = ReliabilityRepository(session)
            executor = PhaseExecutor(
                repository=repo,
                llm_client=self._llm_client,
                validators=[
                    InputIntegrityValidator(required_fields=["email_text", "signals"]),
                    JsonSchemaValidator(schema=_LLM_OUTPUT_SCHEMA),
                ],
            )

            await self._ensure_workflow(repo)
            resolved_prompt_id = await self._ensure_prompt(repo)
            run_id = await self._create_run(repo)

            # Deterministic serialization of the evidence bundle.
            input_artifact = _serialize_evidence_bundle(structured_evidence)

            fw_result = await executor.execute(
                run_id=run_id,
                phase_id=_PHASE_ID,
                prompt_id=resolved_prompt_id,
                input_artifact=input_artifact,
                retry_policy=_DEFAULT_RETRY_POLICY,
            )
        finally:
            # Close the generator so get_db()'s `async with session` block exits.
            await _db_gen.aclose()

        if fw_result["status"] != "SUCCESS":
            # Raise explicitly so the runner can log and skip the sample
            # rather than silently recording a fabricated "benign" label
            # that would bias evaluation metrics.
            raise RuntimeError(
                f"PhaseExecutor returned non-success status={fw_result['status']!r}"
                f" reason={fw_result.get('reason', '')!r}"
                f" (run_id={run_id}, phase_id={_PHASE_ID})"
            )

        artifact_json = json.loads(fw_result["artifact"])
        return _normalize_success_payload(
            artifact_json=artifact_json,
            fw_result=fw_result,
            run_id=run_id,
            phase_id=_PHASE_ID,
            prompt_id=resolved_prompt_id,
        )

    # ------------------------------------------------------------------
    # Sync shim (satisfies ReliabilityExecutorProtocol for completeness)
    # This project's runner always calls execute_async directly.
    # ------------------------------------------------------------------

    def execute(self, *, phase_id: str, prompt_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError(
            "PhaseExecutorAdapter is async. Call execute_async() or use the evaluation runner."
        )
