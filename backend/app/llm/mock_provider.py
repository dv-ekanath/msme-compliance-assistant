from __future__ import annotations

from typing import Any

from app.llm.base import LLMMessage, LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Deterministic, fully offline provider for local development and tests.

    Returns a clearly-labeled canned response so the rest of the app --
    and demos -- can be built and run end-to-end with zero external API
    keys. This is the default provider (LLM_PROVIDER=mock).
    """

    name = "mock"

    async def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        content = (
            "[MOCK LLM RESPONSE] No external LLM was called. "
            f"Prompt received ({len(last_user)} chars): {last_user[:200]!r}"
        )
        return LLMResponse(content=content, provider=self.name, model="mock-echo-1")

    async def health_check(self) -> bool:
        return True
