from __future__ import annotations

from typing import Any

from app.llm.base import LLMMessage, LLMProvider, LLMResponse


class AnthropicLLMProvider(LLMProvider):
    """Claude API provider.

    This is the ONLY module in the codebase allowed to import the
    `anthropic` SDK, and it does so lazily inside __init__ -- not at
    module import time -- so that:
      - the app can start with LLM_PROVIDER=mock even if `anthropic`
        is not installed at all
      - importing `app.llm.anthropic_provider` itself is always safe;
        only *instantiating* this class requires the package + a key

    Enable by setting LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY in
    backend/.env, and `pip install anthropic` (not a default dependency,
    see backend/requirements.txt).
    """

    name = "anthropic"

    def __init__(self, api_key: str | None, model: str = "claude-sonnet-5") -> None:
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Use LLM_PROVIDER=mock for local "
                "development, or set an API key to use the Anthropic provider."
            )

        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError(
                "The 'anthropic' package is not installed. Run "
                "`pip install anthropic` to use LLM_PROVIDER=anthropic."
            ) from exc

        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        system = "\n".join(m.content for m in messages if m.role == "system") or None
        turns = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=kwargs.get("max_tokens", 1024),
            system=system,
            messages=turns,
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMResponse(content=text, provider=self.name, model=self._model)

    async def health_check(self) -> bool:
        try:
            await self._client.models.list(limit=1)
            return True
        except Exception:
            return False
