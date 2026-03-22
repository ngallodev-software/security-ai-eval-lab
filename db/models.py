"""Eval-lab ORM models.

These tables are owned by security-ai-eval-lab. Reliability-layer
tables (workflow_runs, llm_calls, etc.) are owned by ai-reliability-fw
and are referenced here only by UUID columns where needed.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, synonym


class Base(DeclarativeBase):
    pass


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = {"schema": "security_eval"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    dataset_name = Column(String(512), nullable=False)
    model_label = Column(String(128), nullable=True)
    prompt_version = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Backward-compatible aliases for the current runner task.
    evaluation_run_id = synonym("id")
    dataset_path = synonym("dataset_name")
    model = synonym("model_label")
    created_at = synonym("started_at")


class InvestigationResult(Base):
    __tablename__ = "investigation_results"
    __table_args__ = {"schema": "security_eval"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    evaluation_run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("security_eval.evaluation_runs.id"),
        nullable=False,
    )
    sample_id = Column(String(128), nullable=False)
    actual_label = Column(String(64), nullable=False)
    predicted_label = Column(String(64), nullable=False)
    risk_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    explanation = Column(Text, nullable=True)
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

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    result_id = synonym("id")
