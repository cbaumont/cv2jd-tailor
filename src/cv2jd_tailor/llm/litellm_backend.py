"""LiteLLM backend — supports 100+ LLM providers."""

from __future__ import annotations

import litellm

from .base import LLMBackend


class LiteLLMBackend(LLMBackend):
    """LLM backend using LiteLLM for broad provider support."""

    def __init__(self, model: str, temperature: float = 0.3) -> None:
        self.model = model
        self.temperature = temperature

    def complete(self, system: str, user: str) -> str:
        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=self.temperature,
        )
        return response.choices[0].message.content
