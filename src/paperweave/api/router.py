"""API route composition."""

from fastapi import APIRouter

from paperweave.api.auth import router as auth_router
from paperweave.api.health import router as health_router
from paperweave.api.projects import router as projects_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(projects_router)
