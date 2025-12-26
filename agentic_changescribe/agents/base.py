from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Sequence

from agentic_changescribe.llm.base import LLMClient
from agentic_changescribe.core.models import ChatMessage

T = TypeVar("T")


class Agent(ABC, Generic[T]):
    """Base class for agents producing a structured output type."""

    name: str

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    @abstractmethod
    def build_messages(self, *args, **kwargs) -> Sequence[ChatMessage]:
        raise NotImplementedError

    @abstractmethod
    def parse(self, text: str) -> T:
        raise NotImplementedError

    def run(self, *args, **kwargs) -> T:
        messages = self.build_messages(*args, **kwargs)
        text = self.llm.chat(messages)
        return self.parse(text)
