"""rename audit log metadata column"""

from alembic import op

revision = "e681f785a00e"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("audit_logs", "metadata", new_column_name="meta")


def downgrade() -> None:
    op.alter_column("audit_logs", "meta", new_column_name="metadata")
