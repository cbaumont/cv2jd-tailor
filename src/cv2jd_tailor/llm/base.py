"""Abstract LLM interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMBackend(ABC):
    """Base class for LLM backends."""

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Send a prompt and return the completion text."""
        ...
