from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant"]


@dataclass
class LLMMessage:
    role: Role
    content: str


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    citations: list[str] = field(default_factory=list)
    raw: dict[str, Any] | None = None


class LLMProvider(ABC):
    """Interface every LLM backend must implement.

    The rest of the application (orchestrator, RAG layer, future chat
    endpoints) must depend only on this interface -- never on a specific
    vendor SDK -- so the model backing it can be swapped via the
    LLM_PROVIDER env var without touching business logic. See
    `app.llm.factory.get_llm_provider`.
    """

    name: str = "base"

    @abstractmethod
    async def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
