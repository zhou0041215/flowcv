"""add role column to ai_model_configs

Revision ID: 0028_ai_model_role
Revises: 0027_starter_tpl_backfill
Create Date: 2026-07-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0028_ai_model_role"
down_revision = "0027_starter_tpl_backfill"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ai_model_configs",
        sa.Column("role", sa.String(20), nullable=False, server_default="main"),
    )


def downgrade() -> None:
    op.drop_column("ai_model_configs", "role")
