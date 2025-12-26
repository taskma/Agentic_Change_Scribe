from __future__ import annotations

from typing import List
from agentic_changescribe.core.models import Evidence, UserContext

SYSTEM_GUARDRAILS = """You are a meticulous staff-level engineer writing CAB-ready change documents.
Hard rules:
- Do NOT invent systems, services, metrics, or tests you cannot justify.
- If evidence is insufficient, write UNKNOWN and add a TODO.
- When making a claim, cite evidence using short quoted snippets from the EVIDENCE section.
- Keep outputs concise and enterprise-friendly.
"""

def _evidence_block(evidence: List[Evidence]) -> str:
    lines = []
    for e in evidence:
        note = f" ({e.note})" if e.note else ""
        lines.append(f"- [{e.type}]{note}: {e.value}")
    return "\n".join(lines)

def impact_prompt(evidence: List[Evidence], user_ctx: UserContext) -> str:
    return f"""{SYSTEM_GUARDRAILS}

TASK (Impact Agent):
Analyze the change and produce:
- a 3-6 sentence summary
- impacted scope (services/modules) (avoid guessing; use UNKNOWN if unsure)
- change types from: code, config, db, infra, contract, docs
- key files (top 5)
- assumptions (if any)

Return as JSON matching this schema:
{{
  \"summary\": \"string\",
  \"scope\": [\"string\"],
  \"change_types\": [\"string\"],
  \"key_files\": [\"string\"],
  \"assumptions\": [\"string\"],
  \"evidence\": [{{\"type\":\"changed_files|diff_snippet|user_context\",\"value\":\"string\",\"note\":\"string?\"}}]
}}

USER CONTEXT:
title={user_ctx.title}
summary={user_ctx.summary}
environment={user_ctx.environment}
service_hints={user_ctx.service_hints}
links={user_ctx.links}

EVIDENCE:
{_evidence_block(evidence)}
"""

def risk_prompt(evidence: List[Evidence], impact_json: str, user_ctx: UserContext) -> str:
    return f"""{SYSTEM_GUARDRAILS}

TASK (Risk Agent):
Given the Impact Analysis JSON and evidence, produce:
- risk_level: LOW|MEDIUM|HIGH
- 3-7 reasons (each must cite evidence)
- mitigations
- monitoring metrics/checks (if unknown, propose generic but label as suggestion)
- rollback steps (specific if possible; else TODO)

Return as JSON matching this schema:
{{
  \"risk_level\": \"LOW|MEDIUM|HIGH\",
  \"reasons\": [\"string\"],
  \"mitigations\": [\"string\"],
  \"monitoring\": [\"string\"],
  \"rollback\": [\"string\"],
  \"evidence\": [{{\"type\":\"changed_files|diff_snippet|user_context\",\"value\":\"string\",\"note\":\"string?\"}}]
}}

USER CONTEXT:
title={user_ctx.title}
summary={user_ctx.summary}
environment={user_ctx.environment}
service_hints={user_ctx.service_hints}
links={user_ctx.links}

IMPACT JSON:
{impact_json}

EVIDENCE:
{_evidence_block(evidence)}
"""

def review_prompt(evidence: List[Evidence], impact_json: str, risk_json: str, user_ctx: UserContext) -> str:
    return f"""{SYSTEM_GUARDRAILS}

TASK (Reviewer Agent):
Review the Impact and Risk outputs for:
- Missing required sections
- Contradictions (e.g., says no config change but config files changed)
- Generic statements without evidence
- Missing TODO/UNKNOWN where evidence is lacking

If issues exist, set status=NEEDS_FIX and return issues routed to 'impact' or 'risk'.
Otherwise status=PASS.

Return JSON with schema:
{{
  \"status\": \"PASS|NEEDS_FIX\",
  \"issues\": [
    {{
      \"severity\": \"INFO|WARN|ERROR\",
      \"field\": \"string\",
      \"message\": \"string\",
      \"suggested_fix\": \"string?\",
      \"route_to\": \"impact|risk\"
    }}
  ]
}}

USER CONTEXT:
title={user_ctx.title}
summary={user_ctx.summary}
environment={user_ctx.environment}
service_hints={user_ctx.service_hints}
links={user_ctx.links}

IMPACT JSON:
{impact_json}

RISK JSON:
{risk_json}

EVIDENCE:
{_evidence_block(evidence)}
"""
