"""Add username field to users table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_add_username_to_users"
down_revision = "0002_rename_audit_meta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("username", sa.String(length=100), nullable=True),
    )
    op.create_index(
        op.f("ix_users_username"),
        "users",
        ["username"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_users_username"),
        table_name="users",
    )
    op.drop_column("users", "username")
