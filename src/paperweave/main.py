"""FastAPI application factory for the PaperWeave HTTP API."""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from sqlalchemy import create_engine

from paperweave.config import load_config
from paperweave.api.router import api_router
from paperweave.infrastructure.db.connection import build_database_url
from paperweave.infrastructure.db.session import create_session_factory


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
        app.state.config = config
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="PaperWeave", lifespan=lifespan)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
