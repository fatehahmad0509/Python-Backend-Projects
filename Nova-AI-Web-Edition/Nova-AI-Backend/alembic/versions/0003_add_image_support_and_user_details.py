"""add message image fields and user details field

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-04 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("image_base64", sa.Text(), nullable=True))
    op.add_column("messages", sa.Column("image_mime_type", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("details", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "details")
    op.drop_column("messages", "image_mime_type")
    op.drop_column("messages", "image_base64")
