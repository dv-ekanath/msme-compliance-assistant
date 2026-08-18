from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.llm.factory import get_llm_provider

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "environment": settings.app_env}


@router.get("/health/db")
def health_db(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    except Exception as exc:  # surfaced to caller for local debugging only
        return {"status": "error", "database": "unreachable", "detail": str(exc)}


@router.get("/health/llm")
async def health_llm() -> dict:
    """Confirms the LLM provider abstraction is wired up correctly.

    Does not exercise any real feature -- just proves the configured
    provider (mock by default) resolves and responds.
    """
    provider = get_llm_provider()
    healthy = await provider.health_check()
    return {"status": "ok" if healthy else "error", "provider": provider.name}
