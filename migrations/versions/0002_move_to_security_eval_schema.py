"""Move eval-lab tables to security_eval schema

Revision ID: 0002_security_eval_schema
Revises: 0001_eval_lab_tables
Create Date: 2026-03-22

Moves evaluation_runs and investigation_results from the public schema
into the dedicated security_eval schema.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_security_eval_schema"
down_revision: Union[str, Sequence[str], None] = "0001_eval_lab_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS security_eval")
    op.execute("ALTER TABLE investigation_results SET SCHEMA security_eval")
    op.execute("ALTER TABLE evaluation_runs SET SCHEMA security_eval")


def downgrade() -> None:
    op.execute("ALTER TABLE security_eval.investigation_results SET SCHEMA public")
    op.execute("ALTER TABLE security_eval.evaluation_runs SET SCHEMA public")
