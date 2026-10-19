"""Liveness and database readiness endpoints."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def liveness() -> dict[str, str]:
    return {"status": "ok", "service": "paperweave-api"}


@router.get("/ready")
def readiness(request: Request) -> JSONResponse:
    try:
        with request.app.state.engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "unavailable"},
        )
    return JSONResponse(status_code=200, content={"status": "ok", "database": "available"})
