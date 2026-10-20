"""FastAPI application factory for the PaperWeave HTTP API."""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import AsyncIterator

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
            reconcile_pending_deletes(session, storage)
        try:
            yield
        finally:
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
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if origin not in trusted_origins:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Request origin is not allowed for this local workspace"},
                )
        return await call_next(request)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
