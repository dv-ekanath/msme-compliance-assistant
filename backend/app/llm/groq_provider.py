from __future__ import annotations

from typing import Any

from app.llm.base import LLMMessage, LLMProvider, LLMResponse

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqLLMProvider(LLMProvider):
    """Groq API provider (OpenAI-compatible chat completions endpoint).

    Uses `httpx` directly rather than a dedicated Groq SDK -- httpx is
    already a project dependency, so no extra install is needed. Only
    this module talks to Groq; the rest of the app depends on the
    LLMProvider interface, same as the Anthropic/mock providers.

    Enable by setting LLM_PROVIDER=groq and GROQ_API_KEY in backend/.env.
    """

    name = "groq"

    def __init__(self, api_key: str | None, model: str = "llama-3.3-70b-versatile") -> None:
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Use LLM_PROVIDER=mock for local "
                "development, or set an API key to use the Groq provider."
            )

        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError(
                "The 'httpx' package is not installed. Run `pip install httpx` "
                "to use LLM_PROVIDER=groq."
            ) from exc

        self._httpx = httpx
        self._api_key = api_key
        self._model = model

    async def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            # 350 was too tight in practice: the model sometimes explains
            # at length before it reaches the closing [S1]-style citation
            # tag, so the completion got cut off mid-sentence before ever
            # emitting a citation -- which then made the guardrail (which
            # parses citation tags out of the finished text) report zero
            # citations and grounded=false even though retrieval found
            # good evidence. Verified live: raising this fixed it.
            "max_tokens": kwargs.get("max_tokens", 700),
            "temperature": kwargs.get("temperature", 0.2),
        }
        async with self._httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                GROQ_API_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        text = data["choices"][0]["message"]["content"]
        return LLMResponse(content=text, provider=self.name, model=self._model, raw=data)

    async def health_check(self) -> bool:
        try:
            await self.complete([LLMMessage(role="user", content="ping")], max_tokens=1)
            return True
        except Exception:
            return False
