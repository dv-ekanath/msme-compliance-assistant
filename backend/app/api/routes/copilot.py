from __future__ import annotations

import uuid
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.embeddings.base import EmbeddingProvider
from app.embeddings.factory import get_embedding_provider
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.models.business import Business
from app.rag.copilot import ComplianceCopilotService
from app.schemas.copilot import CitationOut, CopilotAskRequest, CopilotAskResponse, RetrievedSourceOut

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/ask/{business_id}", response_model=CopilotAskResponse)
async def ask_copilot(
    business_id: uuid.UUID,
    payload: CopilotAskRequest,
    db: Session = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
) -> CopilotAskResponse:
    """Citation-grounded compliance Q&A for one business.

    The LLM never decides applicability -- it only explains, grounded in
    retrieved regulatory evidence + this business's Digital Twin (built by
    the deterministic Rules Engine). See app/rag/copilot.py.

    Providers are taken as FastAPI dependencies (not called directly) so
    tests can override them (see backend/tests/conftest.py) without
    loading the real embedding model or touching LLM_PROVIDER=anthropic.
    """
    business = db.get(Business, business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")

    service = ComplianceCopilotService(db, llm_provider, embedding_provider)
    result = await service.ask(business, payload.question)

    return CopilotAskResponse(
        answer=result.answer,
        citations=[CitationOut(**asdict(c)) for c in result.citations],
        retrieved_sources=[RetrievedSourceOut(**asdict(s)) for s in result.retrieved_sources],
        confidence=result.confidence,
        grounded=result.grounded,
        requires_verification=result.requires_verification,
    )
