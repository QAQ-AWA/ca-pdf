from fastapi import APIRouter

from app.api.endpoints import audit, auth, ca, health, pdf_signing
from app.core.config import settings

router = APIRouter()
api_router = APIRouter(prefix=settings.api_v1_prefix)

api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(audit.router)
api_router.include_router(ca.router)
api_router.include_router(pdf_signing.router)
router.include_router(api_router)
router.include_router(health.router)
