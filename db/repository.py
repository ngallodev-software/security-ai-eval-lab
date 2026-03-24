"""
Eval-lab persistence layer.

Stores evaluation_runs and investigation_results.
Reliability-layer data (llm_calls, workflow_runs, etc.) is
persisted by ai-reliability-fw — not duplicated here.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Mapping


def _naive_utc(dt: datetime | None) -> datetime | None:
    """Strip timezone info so asyncpg accepts a TIMESTAMP WITHOUT TIME ZONE column."""
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt

from sqlalchemy import select, update, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EvaluationRun, InvestigationResult


class EvalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _normalize_evaluation_run_data(self, data: Mapping[str, Any]) -> dict[str, Any]:
        record = {
            "name": data["name"],
            "dataset_name": data.get("dataset_name") or data.get("dataset_path"),
            "model_label": data.get("model_label") or data.get("model"),
            "prompt_version": data.get("prompt_version"),
            "status": data.get("status") or "running",
            "started_at": _naive_utc(data.get("started_at") or data.get("created_at")) or datetime.utcnow(),
            "completed_at": _naive_utc(data.get("completed_at")),
        }
        run_id = data.get("id") or data.get("evaluation_run_id")
        record["id"] = run_id or uuid.uuid4()
        return record

    def _normalize_investigation_result_data(self, data: Mapping[str, Any]) -> dict[str, Any]:
        record = {
            "evaluation_run_id": data["evaluation_run_id"],
            "sample_id": data["sample_id"],
            "actual_label": data["actual_label"],
            "predicted_label": data["predicted_label"],
            "risk_score": data["risk_score"],
            "confidence": data["confidence"],
            "explanation": data.get("explanation"),
            "signals_json": data["signals_json"],
            "timeline_json": data["timeline_json"],
            "reliability_run_id": data["reliability_run_id"],
            "reliability_phase_id": data["reliability_phase_id"],
            "reliability_prompt_id": data["reliability_prompt_id"],
            "reliability_call_id": data.get("reliability_call_id"),
            "created_at": _naive_utc(data.get("created_at")) or datetime.utcnow(),
        }
        result_id = data.get("id") or data.get("result_id")
        record["id"] = result_id or uuid.uuid4()
        return record

    async def create_evaluation_run(self, data: Mapping[str, Any]) -> uuid.UUID:
        record = self._normalize_evaluation_run_data(data)
        stmt = insert(EvaluationRun).values(**record).returning(EvaluationRun.id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def mark_evaluation_run_complete(
        self,
        evaluation_run_id: uuid.UUID,
        completed_at: datetime | None = None,
        status: str = "completed",
    ) -> uuid.UUID:
        stmt = (
            update(EvaluationRun)
            .where(EvaluationRun.id == evaluation_run_id)
            .values(status=status, completed_at=_naive_utc(completed_at) or datetime.utcnow())
            .returning(EvaluationRun.id)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def insert_investigation_result(self, data: Mapping[str, Any]) -> uuid.UUID:
        record = self._normalize_investigation_result_data(data)
        stmt = insert(InvestigationResult).values(**record).returning(InvestigationResult.id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def list_investigation_results_by_evaluation_run_id(
        self, evaluation_run_id: uuid.UUID
    ) -> list[InvestigationResult]:
        result = await self.session.execute(
            select(InvestigationResult)
            .where(InvestigationResult.evaluation_run_id == evaluation_run_id)
            .order_by(InvestigationResult.created_at, InvestigationResult.id)
        )
        return list(result.scalars().all())

    async def get_evaluation_run(self, evaluation_run_id: uuid.UUID) -> EvaluationRun | None:
        result = await self.session.execute(
            select(EvaluationRun).where(EvaluationRun.id == evaluation_run_id)
        )
        return result.scalar_one_or_none()

    async def get_evaluation_run_by_name(self, name: str) -> EvaluationRun | None:
        result = await self.session.execute(
            select(EvaluationRun)
            .where(EvaluationRun.name == name)
            .order_by(EvaluationRun.started_at.desc())
        )
        return result.scalars().first()

    async def get_llm_call_metadata(
        self, call_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, dict[str, Any]]:
        if not call_ids:
            return {}
        result = await self.session.execute(
            text(
                """
                SELECT
                    call_id,
                    provider,
                    model,
                    latency_ms,
                    input_tokens,
                    output_tokens,
                    token_cost_usd,
                    retry_attempt_num
                FROM reliability.llm_calls
                WHERE call_id = ANY(:call_ids)
                """
            ),
            {"call_ids": call_ids},
        )
        rows = result.fetchall()
        return {
            row.call_id: {
                "provider": row.provider,
                "model": row.model,
                "latency_ms": row.latency_ms,
                "input_tokens": row.input_tokens,
                "output_tokens": row.output_tokens,
                "token_cost_usd": row.token_cost_usd,
                "retry_attempt_num": row.retry_attempt_num,
            }
            for row in rows
        }

    # Backward-compatible aliases for the current runner task.
    save_investigation_result = insert_investigation_result
    get_results_for_run = list_investigation_results_by_evaluation_run_id
