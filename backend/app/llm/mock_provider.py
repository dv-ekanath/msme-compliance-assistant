from __future__ import annotations

import re
from typing import Any

from app.llm.base import LLMMessage, LLMProvider, LLMResponse

_EVIDENCE_TAG_RE = re.compile(r"\[S(\d+)\]")


class MockLLMProvider(LLMProvider):
    """Deterministic, fully offline provider for local development and tests.

    Returns a clearly-labeled canned response so the rest of the app --
    and demos -- can be built and run end-to-end with zero external API
    keys. This is the default provider (LLM_PROVIDER=mock).

    Recognizes one documented convention: if the prompt contains an
    "EVIDENCE:" section listing numbered [S1], [S2], ... items (the
    format app.rag.prompts.build_copilot_messages uses), it deterministically
    cites 1-2 of them instead of just echoing -- so citation-grounded
    features (the Compliance Copilot) are fully testable/demoable without
    a real LLM. Any other prompt gets the original generic echo.
    """

    name = "mock"

    async def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")

        if "EVIDENCE:" in last_user:
            content = self._grounded_mock_answer(last_user)
        else:
            content = (
                "[MOCK LLM RESPONSE] No external LLM was called. "
                f"Prompt received ({len(last_user)} chars): {last_user[:200]!r}"
            )
        return LLMResponse(content=content, provider=self.name, model="mock-echo-1")

    @staticmethod
    def _grounded_mock_answer(user_content: str) -> str:
        tags = sorted({int(n) for n in _EVIDENCE_TAG_RE.findall(user_content)})
        if not tags:
            return (
                "[MOCK LLM RESPONSE] The available regulatory evidence is insufficient to "
                "answer this confidently. Please verify with the source material directly."
            )
        cited = tags[: min(2, len(tags))]
        cite_str = "".join(f"[S{n}]" for n in cited)
        return (
            f"[MOCK LLM RESPONSE] Based on the retrieved regulatory evidence {cite_str}, "
            "this appears relevant to your question. This is a deterministic mock answer "
            "for local development (LLM_PROVIDER=mock) -- it is not legal advice, and the "
            "cited source(s) should be verified before you rely on it."
        )

    async def health_check(self) -> bool:
        return True
