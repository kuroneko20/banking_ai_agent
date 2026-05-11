"""
Abstract base class for LLM clients.
Provides a common interface so different backends can be swapped in easily.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract interface for all LLM client implementations."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a completion from the underlying LLM.

        Args:
            prompt: The user prompt / query.
            system_prompt: Optional system instructions.
            temperature: Sampling temperature (0 = deterministic).
            max_tokens: Maximum tokens in the completion.

        Returns:
            The model's text response.

        Raises:
            RuntimeError: On API or network errors.
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the backend is reachable."""
