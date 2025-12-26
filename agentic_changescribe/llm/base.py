from __future__ import annotations

from typing import Protocol, Sequence
from agentic_changescribe.core.models import ChatMessage


class LLMClient(Protocol):
    """Minimal protocol for any chat LLM client."""

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        """Return the assistant text output."""
        raise NotImplementedError
