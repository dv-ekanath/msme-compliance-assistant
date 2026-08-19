from __future__ import annotations

from pydantic import BaseModel, field_validator


class CopilotAskRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("question must not be empty")
        return stripped


class CitationOut(BaseModel):
    source_id: str
    title: str
    authority: str
    section: str | None
    source_url: str
    relevance_score: float
    status: str


class RetrievedSourceOut(BaseModel):
    chunk_id: str
    title: str
    authority: str
    section: str | None
    source_url: str
    relevance_score: float
    status: str


class CopilotAskResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
    retrieved_sources: list[RetrievedSourceOut]
    confidence: str
    grounded: bool
    requires_verification: bool
