from __future__ import annotations

import os
import pathlib
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from agentic_changescribe.core.models import UserContext
from agentic_changescribe.orchestration.pipeline import ChangePackPipeline
from agentic_changescribe.tools.git_tools import GitTools
from agentic_changescribe.tools.redaction import Redactor
from agentic_changescribe.config import AppConfig, LLMConfig
from agentic_changescribe.llm.openai_compat import OpenAICompatClient
from agentic_changescribe.core.tracing import TraceWriter

app = typer.Typer(add_completion=False, help="AgenticChangeScribe CLI")
console = Console()


def _load_llm_config() -> LLMConfig:
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    if not base_url or not api_key or not model:
        raise typer.BadParameter(
            "Missing LLM env vars. Please set LLM_BASE_URL, LLM_API_KEY, LLM_MODEL."
        )
    return LLMConfig(base_url=base_url, api_key=api_key, model=model)


@app.command()
def generate(
    repo: str = typer.Option(".", help="Path to a git repo."),
    diff: str = typer.Option(
        "auto",
        help="Diff mode: auto|staged|head|worktree",
        show_default=True,
    ),
    title: Optional[str] = typer.Option(None, help="Human-readable change title."),
    summary: Optional[str] = typer.Option(None, help="Short change summary."),
    context_file: Optional[str] = typer.Option(
        None, help="Optional YAML file with extra context (title/summary/env/links)."
    ),
    outdir: str = typer.Option(
        "docs/change-packs",
        help="Output base directory (timestamped subfolder is created).",
    ),
    redact: bool = typer.Option(
        True, help="Redact secrets/internal IPs in prompts and traces."
    ),
) -> None:
    """Generate a CAB-ready change pack using 3 LLM agents (Impact, Risk, Review)."""
    repo_path = pathlib.Path(repo).resolve()
    if not repo_path.exists():
        raise typer.BadParameter(f"Repo path does not exist: {repo_path}")

    llm_cfg = _load_llm_config()
    cfg = AppConfig(llm=llm_cfg)

    git = GitTools(repo_path)
    if not git.is_git_repo():
        raise typer.BadParameter(f"Not a git repo: {repo_path}")

    redactor = Redactor(enabled=redact)
    out_base = pathlib.Path(outdir).resolve()
    out_base.mkdir(parents=True, exist_ok=True)

    # Prepare run folder
    run_dir = ChangePackPipeline.make_run_dir(out_base)
    trace = TraceWriter(run_dir / "agent-trace.jsonl", redactor=redactor)

    console.print(Panel.fit(f"[bold]AgenticChangeScribe[/bold]\nRepo: {repo_path}\nRun: {run_dir}"))

    # Evidence collection
    console.print("[cyan][Observe][/cyan] Collecting changed files & diff...")
    changed_files = git.changed_files(mode=diff)
    diff_text = redactor.redact_text(git.diff_text(mode=diff))

    # Optional context
    user_ctx = UserContext.from_optional_yaml(context_file, title=title, summary=summary)

    # LLM client
    llm = OpenAICompatClient(
        base_url=llm_cfg.base_url,
        api_key=llm_cfg.api_key,
        model=llm_cfg.model,
        timeout_s=llm_cfg.timeout_s,
        temperature=llm_cfg.temperature,
    )

    pipeline = ChangePackPipeline(cfg=cfg, llm=llm, trace=trace)

    console.print("[cyan][Agentic Pipeline][/cyan] Running agents...")
    result = pipeline.run(
        repo_path=repo_path,
        changed_files=changed_files,
        diff_text=diff_text,
        user_ctx=user_ctx,
        out_dir=run_dir,
    )

    console.print(Panel.fit(f"[green]DONE[/green]\n{result.run_dir}\nFiles: {len(result.files_written)}"))
