"""FastAPI application factory and initial liveness endpoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI

from paperweave.config import AppConfig, load_config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    config_path = Path(os.getenv("PAPERWEAVE_CONFIG_FILE", "/app/config.toml"))
    app.state.config = load_config(config_path)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="PaperWeave", lifespan=lifespan)

    @app.get("/api/v1/health/live", tags=["health"])
    async def liveness() -> dict[str, str]:
        return {"status": "ok", "service": "paperweave-api"}

    return app


app = create_app()
