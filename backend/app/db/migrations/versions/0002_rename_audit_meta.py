"""rename audit_logs metadata to meta

Revision ID: 0002_rename_audit_meta
Revises: 0001_initial_schema
Create Date: 2024-10-29

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_rename_audit_meta"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename 'metadata' column to 'meta' to avoid conflict with DeclarativeBase.metadata"""
    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.alter_column("metadata", new_column_name="meta")


def downgrade() -> None:
    """Revert column name back to 'metadata'"""
    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.alter_column("meta", new_column_name="metadata")
