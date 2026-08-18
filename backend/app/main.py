from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import business, compliance, health, obligations, registrations, twin
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="MSME Compliance Assistant API",
    version="0.1.0",
    description="Backend for the AI-Powered MSME Compliance Assistant (SIH 2026).",
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


@app.get("/")
def root() -> dict:
    return {"service": "msme-compliance-assistant-backend", "status": "running"}
