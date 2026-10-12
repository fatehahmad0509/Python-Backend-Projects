"""add user plan/is_blocked and daily_token_usage table

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-03 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PLAN_CHOICES = ("free", "plus", "pro", "developer")


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("plan", sa.String(length=20), nullable=False, server_default="free"),
    )
    op.create_check_constraint(
        "ck_users_plan_valid",
        "users",
        f"plan IN {_PLAN_CHOICES}",
    )

    op.create_table(
        "daily_token_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "date", name="uq_daily_token_usage_user_date"),
    )
    op.create_index("ix_daily_token_usage_user_id", "daily_token_usage", ["user_id"])
    op.create_index("ix_daily_token_usage_date", "daily_token_usage", ["date"])


def downgrade() -> None:
    op.drop_index("ix_daily_token_usage_date", table_name="daily_token_usage")
    op.drop_index("ix_daily_token_usage_user_id", table_name="daily_token_usage")
    op.drop_table("daily_token_usage")

    op.drop_constraint("ck_users_plan_valid", "users", type_="check")
    op.drop_column("users", "plan")
    op.drop_column("users", "is_blocked")
