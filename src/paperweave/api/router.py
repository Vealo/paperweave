"""API route composition."""

from fastapi import APIRouter

from paperweave.api.auth import router as auth_router
from paperweave.api.health import router as health_router
from paperweave.api.projects import router as projects_router
from paperweave.api.manuscripts import router as manuscripts_router
from paperweave.api.library import router as library_router
from paperweave.api.documents import router as documents_router
from paperweave.api.evidence import router as evidence_router
from paperweave.api.ai_proposals import router as ai_proposals_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(manuscripts_router)
api_router.include_router(library_router)
api_router.include_router(documents_router)
api_router.include_router(evidence_router)
api_router.include_router(ai_proposals_router)
