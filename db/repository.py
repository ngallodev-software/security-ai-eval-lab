"""
Eval-lab persistence layer.

Stores evaluation_runs and investigation_results.
Reliability-layer data (llm_calls, workflow_runs, etc.) is
persisted by ai-reliability-fw — not duplicated here.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EvaluationRun, InvestigationResult


class EvalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_evaluation_run(self, data: dict) -> uuid.UUID:
        stmt = insert(EvaluationRun).values(**data).returning(EvaluationRun.evaluation_run_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def save_investigation_result(self, data: dict) -> uuid.UUID:
        stmt = insert(InvestigationResult).values(**data).returning(InvestigationResult.result_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def get_results_for_run(self, evaluation_run_id: uuid.UUID) -> list[InvestigationResult]:
        result = await self.session.execute(
            select(InvestigationResult)
            .where(InvestigationResult.evaluation_run_id == evaluation_run_id)
            .order_by(InvestigationResult.created_at)
        )
        return list(result.scalars().all())
