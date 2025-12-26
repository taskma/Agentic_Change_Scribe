from __future__ import annotations

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration for any OpenAI-compatible LLM gateway."""

    base_url: str = Field(..., description="Base URL (e.g. https://api.openai.com)")
    api_key: str = Field(..., description="API key/token")
    model: str = Field(..., description="Model name")
    timeout_s: float = Field(60.0, description="HTTP timeout (seconds)")
    temperature: float = Field(0.2, description="Default temperature")


class AppConfig(BaseModel):
    llm: LLMConfig
    max_llm_chars: int = Field(
        12000,
        description="Max diff chars passed into a single agent prompt to control token usage.",
    )
    max_revision_passes: int = Field(
        1,
        description="Max additional revision passes triggered by the Reviewer (MVP default: 1).",
    )
