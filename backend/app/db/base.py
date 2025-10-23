"""SQLAlchemy base metadata and model imports for Alembic."""

from app.db.base_class import Base

# Import models so that metadata is correctly configured for migrations
from app.models.user import TokenBlocklist, User  # noqa: F401
