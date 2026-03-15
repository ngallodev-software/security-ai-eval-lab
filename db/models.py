"""
Eval-lab ORM models.

These tables are owned by security-ai-eval-lab.
Reliability-layer tables (workflow_runs, llm_calls, etc.) are
owned by ai-reliability-fw and are referenced here by UUID FK
without SQLAlchemy relationship objects — cross-project boundaries
stay explicit and loose.
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    evaluation_run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    dataset_path = Column(String(512), nullable=False)
    model = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class InvestigationResult(Base):
    __tablename__ = "investigation_results"

    result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    evaluation_run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_runs.evaluation_run_id"),
        nullable=False,
    )
    sample_id = Column(String(128), nullable=False)
    actual_label = Column(String(64), nullable=False)
    predicted_label = Column(String(64), nullable=False)
    risk_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    explanation = Column(Text, nullable=False)
    signals_json = Column(JSONB, nullable=False)
    timeline_json = Column(JSONB, nullable=False)

    # Cross-project references into ai-reliability-fw tables.
    # No ORM FK constraints — the tables live in a different project.
    # run/phase/prompt are required; call_id is nullable per spec (may be
    # absent if the executor did not reach the LLM call stage).
    reliability_run_id = Column(UUID(as_uuid=True), nullable=False)
    reliability_phase_id = Column(UUID(as_uuid=True), nullable=False)
    reliability_prompt_id = Column(UUID(as_uuid=True), nullable=False)
    reliability_call_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
