from __future__ import annotations

import json
from typing import List, Sequence

from agentic_changescribe.agents.base import Agent
from agentic_changescribe.core.models import ChatMessage, Evidence, RiskAssessment, UserContext
from agentic_changescribe.core.prompts import risk_prompt


class RiskAgent(Agent[RiskAssessment]):
    name = "risk"

    def build_messages(self, evidence: List[Evidence], impact_json: str, user_ctx: UserContext) -> Sequence[ChatMessage]:
        return [
            ChatMessage(role="system", content="You are the Risk Agent."),
            ChatMessage(role="user", content=risk_prompt(evidence, impact_json, user_ctx)),
        ]

    def parse(self, text: str) -> RiskAssessment:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        if isinstance(data.get("risk_level"), str):
            data["risk_level"] = data["risk_level"].strip().upper()
        return RiskAssessment.model_validate(data)
