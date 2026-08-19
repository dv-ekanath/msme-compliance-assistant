from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    alerts,
    auth,
    business,
    compliance,
    copilot,
    documents,
    filings,
    health,
    obligations,
    registrations,
    twin,
    watchdog,
)
from app.core.config import get_settings
from app.watchdog.scheduler import start_scheduler, stop_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Disabled in tests (WATCHDOG_SCHEDULER_ENABLED=false, set in
    # tests/conftest.py) -- the FastAPI TestClient triggers this lifespan
    # on every test, and a background job has no business running there.
    if settings.watchdog_scheduler_enabled:
        start_scheduler()
    try:
        yield
    finally:
        if settings.watchdog_scheduler_enabled:
            stop_scheduler()


app = FastAPI(
    title="MSME Compliance Assistant API",
    version="0.1.0",
    description="Backend for the AI-Powered MSME Compliance Assistant (SIH 2026).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(business.router, prefix="/api/v1")
app.include_router(registrations.router, prefix="/api/v1")
app.include_router(twin.router, prefix="/api/v1")
app.include_router(obligations.router, prefix="/api/v1")
app.include_router(compliance.router, prefix="/api/v1")
app.include_router(copilot.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(watchdog.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(filings.router, prefix="/api/v1")


@app.get("/")
def root() -> dict:
    return {"service": "msme-compliance-assistant-backend", "status": "running"}
