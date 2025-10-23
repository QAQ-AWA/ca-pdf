"""SQLAlchemy base metadata and model imports for Alembic."""

from app.db.base_class import Base

# Import models so that metadata is correctly configured for migrations
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.ca_artifact import CAArtifact  # noqa: F401
from app.models.certificate import Certificate  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.seal import Seal  # noqa: F401
from app.models.storage import EncryptedSecret, FileMetadata  # noqa: F401
from app.models.user import TokenBlocklist, User  # noqa: F401
