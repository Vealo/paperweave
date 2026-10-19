"""API route composition."""

from fastapi import APIRouter

from paperweave.api.auth import router as auth_router
from paperweave.api.health import router as health_router
from paperweave.api.projects import router as projects_router
from paperweave.api.manuscripts import router as manuscripts_router
from paperweave.api.library import router as library_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(manuscripts_router)
api_router.include_router(library_router)
