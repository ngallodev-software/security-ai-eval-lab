"""eval_lab_tables

Revision ID: 0001_eval_lab_tables
Revises:
Create Date: 2026-03-15 00:00:00

Adds evaluation_runs and investigation_results tables.
These are owned by security-ai-eval-lab. References to
ai-reliability-fw tables (workflow_runs, llm_calls, prompts)
are UUID columns without DB-level FK constraints, keeping the
two projects loosely coupled at the schema boundary.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_eval_lab_tables"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluation_runs",
        sa.Column("evaluation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("dataset_path", sa.String(512), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("evaluation_run_id"),
    )

    op.create_table(
        "investigation_results",
        sa.Column("result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evaluation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sample_id", sa.String(128), nullable=False),
        sa.Column("actual_label", sa.String(64), nullable=False),
        sa.Column("predicted_label", sa.String(64), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("signals_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("timeline_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        # Cross-project UUID references (no DB FK — different project boundary).
        # run/phase/prompt are required; call_id is nullable per spec.
        sa.Column("reliability_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reliability_phase_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reliability_prompt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reliability_call_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["evaluation_run_id"],
            ["evaluation_runs.evaluation_run_id"],
        ),
        sa.PrimaryKeyConstraint("result_id"),
    )


def downgrade() -> None:
    op.drop_table("investigation_results")
    op.drop_table("evaluation_runs")
