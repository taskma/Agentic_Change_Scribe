from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import List

from agentic_changescribe.config import AppConfig
from agentic_changescribe.core.models import Evidence, UserContext, ImpactAnalysis, RiskAssessment, TestPlan, ChangePackResult
from agentic_changescribe.core.renderer import MarkdownRenderer
from agentic_changescribe.core.tracing import TraceWriter
from agentic_changescribe.llm.base import LLMClient
from agentic_changescribe.agents.impact import ImpactAgent
from agentic_changescribe.agents.risk import RiskAgent
from agentic_changescribe.agents.review import ReviewerAgent


class ChangePackPipeline:
    def __init__(self, cfg: AppConfig, llm: LLMClient, trace: TraceWriter) -> None:
        self.cfg = cfg
        self.llm = llm
        self.trace = trace
        self.impact_agent = ImpactAgent(llm)
        self.risk_agent = RiskAgent(llm)
        self.reviewer_agent = ReviewerAgent(llm)

    @staticmethod
    def make_run_dir(base_out: Path) -> Path:
        ts = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        run_dir = base_out / ts
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def run(
        self,
        repo_path: Path,
        changed_files: List[str],
        diff_text: str,
        user_ctx: UserContext,
        out_dir: Path,
    ) -> ChangePackResult:
        evidence = self._build_evidence(changed_files, diff_text, user_ctx)

        impact = self._call_impact(evidence, user_ctx)
        impact_json = impact.model_dump_json(indent=2, ensure_ascii=False)

        risk = self._call_risk(evidence, impact_json, user_ctx)
        risk_json = risk.model_dump_json(indent=2, ensure_ascii=False)

        review = self._call_review(evidence, impact_json, risk_json, user_ctx)

        revision_passes = 0
        while review.status == "NEEDS_FIX" and revision_passes < self.cfg.max_revision_passes:
            revision_passes += 1
            rerun_impact = any(i.route_to == "impact" for i in review.issues)
            rerun_risk = any(i.route_to == "risk" for i in review.issues)

            if rerun_impact:
                impact = self._call_impact(evidence, user_ctx, review_feedback=review.model_dump())
                impact_json = impact.model_dump_json(indent=2, ensure_ascii=False)

            if rerun_risk:
                risk = self._call_risk(evidence, impact_json, user_ctx, review_feedback=review.model_dump())
                risk_json = risk.model_dump_json(indent=2, ensure_ascii=False)

            review = self._call_review(evidence, impact_json, risk_json, user_ctx)

        test_plan = self._make_test_plan(repo_path)

        files = MarkdownRenderer.write_all(
            out_dir=out_dir,
            user_ctx=user_ctx,
            changed_files=changed_files,
            impact=impact,
            risk=risk,
            test_plan=test_plan,
        )
        return ChangePackResult(run_dir=str(out_dir), files_written=files)

    def _build_evidence(self, changed_files: List[str], diff_text: str, user_ctx: UserContext) -> List[Evidence]:
        evidence: List[Evidence] = []
        if changed_files:
            evidence.append(Evidence(type="changed_files", value="; ".join(changed_files[:50]), note="up to 50 files"))
        if diff_text:
            snippet = diff_text[: self.cfg.max_llm_chars]
            evidence.append(Evidence(type="diff_snippet", value=snippet, note=f"first {len(snippet)} chars"))
        if user_ctx.title or user_ctx.summary or user_ctx.environment or user_ctx.service_hints or user_ctx.links:
            evidence.append(Evidence(type="user_context", value=user_ctx.model_dump_json(ensure_ascii=False)))
        return evidence

    def _call_impact(self, evidence: List[Evidence], user_ctx: UserContext, review_feedback: dict | None = None) -> ImpactAnalysis:
        if review_feedback:
            evidence = list(evidence) + [Evidence(type="review_feedback", value=str(review_feedback), note="Reviewer notes")]
        self.trace.write({"agent": "impact", "event": "call"})
        out = self.impact_agent.run(evidence=evidence, user_ctx=user_ctx)
        self.trace.write({"agent": "impact", "event": "result", "response": out.model_dump_json(ensure_ascii=False)})
        return out

    def _call_risk(self, evidence: List[Evidence], impact_json: str, user_ctx: UserContext, review_feedback: dict | None = None) -> RiskAssessment:
        if review_feedback:
            evidence = list(evidence) + [Evidence(type="review_feedback", value=str(review_feedback), note="Reviewer notes")]
        self.trace.write({"agent": "risk", "event": "call"})
        out = self.risk_agent.run(evidence=evidence, impact_json=impact_json, user_ctx=user_ctx)
        self.trace.write({"agent": "risk", "event": "result", "response": out.model_dump_json(ensure_ascii=False)})
        return out

    def _call_review(self, evidence: List[Evidence], impact_json: str, risk_json: str, user_ctx: UserContext):
        self.trace.write({"agent": "review", "event": "call"})
        out = self.reviewer_agent.run(evidence=evidence, impact_json=impact_json, risk_json=risk_json, user_ctx=user_ctx)
        self.trace.write({"agent": "review", "event": "result", "response": out.model_dump_json(ensure_ascii=False)})
        return out

    def _make_test_plan(self, repo_path: Path) -> TestPlan:
        cmds: List[str] = []
        if (repo_path / "pyproject.toml").exists() or (repo_path / "requirements.txt").exists():
            cmds.append("pytest -q")
        if (repo_path / "package.json").exists():
            cmds.append("npm test")
        if (repo_path / "pom.xml").exists():
            cmds.append("mvn test")
        if (repo_path / "gradlew").exists():
            cmds.append("./gradlew test")
        if not cmds:
            cmds = ["TODO: add project-specific test command"]
        return TestPlan(
            recommended_commands=cmds,
            evidence_available=["UNKNOWN (MVP does not execute CI/tests)"],
            missing_evidence=["TODO: attach CI link or paste test output"],
        )
