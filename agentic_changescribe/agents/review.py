from __future__ import annotations

import json
from typing import List, Sequence

from agentic_changescribe.agents.base import Agent
from agentic_changescribe.core.models import ChatMessage, Evidence, ReviewResult, UserContext
from agentic_changescribe.core.prompts import review_prompt


class ReviewerAgent(Agent[ReviewResult]):
    name = "review"

    def build_messages(self, evidence: List[Evidence], impact_json: str, risk_json: str, user_ctx: UserContext) -> Sequence[ChatMessage]:
        return [
            ChatMessage(role="system", content="You are the Reviewer Agent."),
            ChatMessage(role="user", content=review_prompt(evidence, impact_json, risk_json, user_ctx)),
        ]

    def parse(self, text: str) -> ReviewResult:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        if isinstance(data.get("status"), str):
            data["status"] = data["status"].strip().upper()
        return ReviewResult.model_validate(data)
