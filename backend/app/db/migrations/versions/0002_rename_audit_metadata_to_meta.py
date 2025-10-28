"""Rename audit log metadata column to meta."""

from __future__ import annotations

from alembic import op

revision = "0002_rename_audit_metadata_to_meta"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("audit_logs", "metadata", new_column_name="meta")


def downgrade() -> None:
    op.alter_column("audit_logs", "meta", new_column_name="metadata")
