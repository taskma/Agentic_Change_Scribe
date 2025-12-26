from __future__ import annotations

import json
from typing import List, Sequence

from agentic_changescribe.agents.base import Agent
from agentic_changescribe.core.models import ChatMessage, Evidence, ImpactAnalysis, UserContext
from agentic_changescribe.core.prompts import impact_prompt


class ImpactAgent(Agent[ImpactAnalysis]):
    name = "impact"

    def build_messages(self, evidence: List[Evidence], user_ctx: UserContext) -> Sequence[ChatMessage]:
        return [
            ChatMessage(role="system", content="You are the Impact Agent."),
            ChatMessage(role="user", content=impact_prompt(evidence, user_ctx)),
        ]

    def parse(self, text: str) -> ImpactAnalysis:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        return ImpactAnalysis.model_validate(data)
