"""FastAPI application factory for the PaperWeave HTTP API."""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from time import perf_counter
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine

from paperweave.config import load_config
from paperweave.api.router import api_router
from paperweave.infrastructure.db.connection import build_database_url
from paperweave.infrastructure.db.session import create_session_factory
from paperweave.infrastructure.db.artifact_lifecycle import reconcile_pending_deletes
from paperweave.infrastructure.storage.factory import create_storage
from paperweave.infrastructure.logging import configure_logging, log_context, log_event


configure_logging(service="api")
logger = logging.getLogger(__name__)


def create_app(
    config_path: Path | None = None,
    *,
    database_url: str | None = None,
    engine_factory=create_engine,
) -> FastAPI:
    """Create the API app; database_url is an explicit isolated-test seam."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        selected_config = config_path or Path(
            os.getenv("PAPERWEAVE_CONFIG_FILE", "/app/config.toml")
        )
        config = load_config(selected_config)
        engine = engine_factory(database_url or build_database_url(config))
        storage = create_storage(config)
        app.state.config = config
        app.state.storage = storage
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        with app.state.session_factory() as session:
            cleaned, cleanup_failed = reconcile_pending_deletes(session, storage)
        if cleaned or cleanup_failed:
            log_event(logger, logging.INFO, "storage.cleanup.reconciled", "Очередь удаления объектов обработана", completed=cleaned, failed=cleanup_failed)
        log_event(logger, logging.INFO, "app.started", "API запущен")
        try:
            yield
        finally:
            log_event(logger, logging.INFO, "app.stopping", "API останавливается")
            engine.dispose()

    app = FastAPI(title="PaperWeave", lifespan=lifespan)
    bind_host = os.getenv("PW_BIND_HOST", "127.0.0.1")
    if ":" in bind_host:
        bind_host = f"[{bind_host}]"
    ui_port = os.getenv("PW_UI_PORT", "18742")
    trusted_origins = {f"http://{bind_host}:{ui_port}", f"http://localhost:{ui_port}"}
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(trusted_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )

    @app.middleware("http")
    async def enforce_local_browser_origin(request, call_next):
        request_id = uuid4().hex
        started_at = perf_counter()
        with log_context(request_id=request_id):
            if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
                origin = request.headers.get("origin")
                if origin not in trusted_origins:
                    response = JSONResponse(
                        status_code=403,
                        content={"detail": "Request origin is not allowed for this local workspace"},
                    )
                else:
                    response = await call_next(request)
            else:
                response = await call_next(request)

            response.headers["X-Request-ID"] = request_id
            route = request.scope.get("route")
            route_path = getattr(route, "path", "<unmatched>")
            if not route_path.startswith("/api/v1/health/"):
                elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
                event_level = logging.ERROR if response.status_code >= 500 else logging.INFO
                log_event(
                    logger,
                    event_level,
                    "http.request.completed",
                    "HTTP-запрос завершён",
                    method=request.method,
                    route=route_path,
                    status_code=response.status_code,
                    duration_ms=elapsed_ms,
                )
        return response
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
