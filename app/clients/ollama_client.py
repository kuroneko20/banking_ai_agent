"""
Async Ollama client — wraps the Ollama /api/generate endpoint.
"""

from __future__ import annotations

import logging

import httpx

from app.clients.base import BaseLLMClient
from app.core.settings import settings

logger = logging.getLogger(__name__)


class OllamaClient(BaseLLMClient):
    """Async HTTP client for the local Ollama server."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.model_name
        self.timeout = timeout or settings.ollama_timeout

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        """Call the Ollama /api/generate endpoint and return the full response."""
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        logger.debug("Ollama request → model=%s prompt_len=%d", self.model, len(prompt))

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                text: str = data.get("response", "").strip()
                logger.debug("Ollama response len=%d", len(text))
                return text
            except httpx.TimeoutException as exc:
                logger.error("Ollama request timed out: %s", exc)
                raise RuntimeError(f"Ollama request timed out after {self.timeout}s") from exc
            except httpx.HTTPStatusError as exc:
                logger.error("Ollama HTTP error %s: %s", exc.response.status_code, exc.response.text)
                raise RuntimeError(f"Ollama returned HTTP {exc.response.status_code}") from exc
            except Exception as exc:
                logger.error("Ollama unexpected error: %s", exc)
                raise RuntimeError(f"Ollama client error: {exc}") from exc

    async def health_check(self) -> bool:
        """Return True if Ollama server responds at /api/tags."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
            except Exception:
                return False


# ---------------------------------------------------------------------------
# Module-level singleton — import this in nodes
# ---------------------------------------------------------------------------

ollama_client = OllamaClient()
