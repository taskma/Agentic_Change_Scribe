from __future__ import annotations

from pathlib import Path
from typing import List

from agentic_changescribe.core.models import ImpactAnalysis, RiskAssessment, TestPlan, UserContext


class MarkdownRenderer:
    """Renders CAB-friendly Markdown artifacts."""

    @staticmethod
    def write_all(
        out_dir: Path,
        user_ctx: UserContext,
        changed_files: List[str],
        impact: ImpactAnalysis,
        risk: RiskAssessment,
        test_plan: TestPlan,
    ) -> List[str]:
        out_dir.mkdir(parents=True, exist_ok=True)
        files: List[str] = []
        files.append(MarkdownRenderer._write(out_dir / "change-brief.md", MarkdownRenderer.change_brief(user_ctx, impact, risk, test_plan)))
        files.append(MarkdownRenderer._write(out_dir / "impact-analysis.md", MarkdownRenderer.impact_doc(changed_files, impact)))
        files.append(MarkdownRenderer._write(out_dir / "risk-assessment.md", MarkdownRenderer.risk_doc(risk)))
        files.append(MarkdownRenderer._write(out_dir / "test-plan.md", MarkdownRenderer.test_doc(test_plan)))
        files.append(MarkdownRenderer._write(out_dir / "rollback-plan.md", MarkdownRenderer.rollback_doc(risk)))
        return files

    @staticmethod
    def _write(path: Path, content: str) -> str:
        path.write_text(content, encoding="utf-8")
        return str(path)

    @staticmethod
    def change_brief(user_ctx: UserContext, impact: ImpactAnalysis, risk: RiskAssessment, test_plan: TestPlan) -> str:
        title = user_ctx.title or "Change Brief"
        summary = user_ctx.summary or impact.summary
        env = user_ctx.environment or "UNKNOWN"

        return "\n".join([
            f"# {title}",
            "",
            "## Summary",
            summary.strip(),
            "",
            "## Scope",
            "\n".join([f"- {s}" for s in (impact.scope or ["UNKNOWN"])]),
            "",
            "## Change Types",
            ", ".join(impact.change_types) if impact.change_types else "UNKNOWN",
            "",
            "## Risk",
            f"**{risk.risk_level}**",
            "",
            "### Reasons",
            "\n".join([f"- {r}" for r in (risk.reasons or ["UNKNOWN"])]),
            "",
            "### Mitigations",
            "\n".join([f"- {m}" for m in (risk.mitigations or ["TODO: add mitigations"])]),
            "",
            "## Test Plan",
            "\n".join([f"- `{c}`" for c in (test_plan.recommended_commands or ["TODO: add test commands"])]),
            "",
            "## Rollback (high level)",
            "\n".join([f"- {rb}" for rb in (risk.rollback or ["TODO: define rollback"])]),
            "",
            "## Monitoring (suggested)",
            "\n".join([f"- {m}" for m in (risk.monitoring or ["TODO: add monitoring metrics"])]),
            "",
            f"**Environment:** {env}",
            "",
        ])

    @staticmethod
    def impact_doc(changed_files: List[str], impact: ImpactAnalysis) -> str:
        return "\n".join([
            "# Impact Analysis",
            "",
            "## Summary",
            impact.summary.strip(),
            "",
            "## Changed Files (evidence)",
            "\n".join([f"- `{f}`" for f in changed_files]) if changed_files else "- (none detected)",
            "",
            "## Impacted Scope",
            "\n".join([f"- {s}" for s in (impact.scope or ["UNKNOWN"])]),
            "",
            "## Assumptions",
            "\n".join([f"- {a}" for a in (impact.assumptions or ["(none)"])]),
            "",
        ])

    @staticmethod
    def risk_doc(risk: RiskAssessment) -> str:
        return "\n".join([
            "# Risk Assessment",
            "",
            f"## Risk Level: {risk.risk_level}",
            "",
            "## Reasons",
            "\n".join([f"- {r}" for r in (risk.reasons or ["UNKNOWN"])]),
            "",
            "## Mitigations",
            "\n".join([f"- {m}" for m in (risk.mitigations or ["TODO"])]),
            "",
            "## Monitoring Suggestions",
            "\n".join([f"- {m}" for m in (risk.monitoring or ["TODO"])]),
            "",
        ])

    @staticmethod
    def test_doc(test_plan: TestPlan) -> str:
        return "\n".join([
            "# Test Plan",
            "",
            "## Recommended Commands",
            "\n".join([f"- `{c}`" for c in (test_plan.recommended_commands or ["TODO"])]),
            "",
            "## Evidence Available",
            "\n".join([f"- {e}" for e in (test_plan.evidence_available or ["UNKNOWN"])]),
            "",
            "## Missing Evidence / TODO",
            "\n".join([f"- {m}" for m in (test_plan.missing_evidence or ["TODO"])]),
            "",
        ])

    @staticmethod
    def rollback_doc(risk: RiskAssessment) -> str:
        return "\n".join([
            "# Rollback Plan",
            "",
            "## Steps",
            "\n".join([f"- {rb}" for rb in (risk.rollback or ["TODO: define rollback steps"])]),
            "",
            "## Notes",
            "- Prefer disabling via feature flags (if available) before reverting.",
            "- Validate health checks and critical workflows after rollback.",
            "",
        ])
