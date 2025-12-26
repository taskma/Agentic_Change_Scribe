from __future__ import annotations

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
import pathlib
import yaml


class ChatMessage(BaseModel):
    role: str
    content: str


class Evidence(BaseModel):
    type: str = Field(..., description="changed_files|diff_snippet|user_context|review_feedback")
    value: str
    note: Optional[str] = None


class UserContext(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    environment: Optional[str] = None
    service_hints: List[str] = Field(default_factory=list)
    links: Dict[str, str] = Field(default_factory=dict)

    @staticmethod
    def from_optional_yaml(path: Optional[str], title: Optional[str], summary: Optional[str]) -> "UserContext":
        ctx = UserContext(title=title, summary=summary)
        if not path:
            return ctx
        p = pathlib.Path(path)
        if not p.exists():
            return ctx
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if title:
            data["title"] = title
        if summary:
            data["summary"] = summary
        return UserContext.model_validate(data)


class ImpactAnalysis(BaseModel):
    summary: str
    scope: List[str] = Field(default_factory=list)
    change_types: List[str] = Field(default_factory=list)
    key_files: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    risk_level: str = Field(..., description="LOW|MEDIUM|HIGH")
    reasons: List[str] = Field(default_factory=list)
    mitigations: List[str] = Field(default_factory=list)
    monitoring: List[str] = Field(default_factory=list)
    rollback: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)


class TestPlan(BaseModel):
    recommended_commands: List[str] = Field(default_factory=list)
    evidence_available: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)


class ReviewIssue(BaseModel):
    severity: str = Field(..., description="INFO|WARN|ERROR")
    field: str
    message: str
    suggested_fix: Optional[str] = None
    route_to: str = Field(..., description="impact|risk")


class ReviewResult(BaseModel):
    status: str = Field(..., description="PASS|NEEDS_FIX")
    issues: List[ReviewIssue] = Field(default_factory=list)


class ChangePackResult(BaseModel):
    run_dir: str
    files_written: List[str] = Field(default_factory=list)
