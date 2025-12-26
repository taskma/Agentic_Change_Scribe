from __future__ import annotations

import pathlib
import subprocess
from typing import List


class GitTools:
    """Thin wrapper around git commands with safe defaults."""

    def __init__(self, repo_path: pathlib.Path) -> None:
        self.repo_path = repo_path

    def is_git_repo(self) -> bool:
        try:
            self._run(["git", "rev-parse", "--is-inside-work-tree"])
            return True
        except Exception:
            return False

    def changed_files(self, mode: str = "auto") -> List[str]:
        out = self._run(self._diff_name_only_cmd(mode)).strip()
        return [line.strip() for line in out.splitlines() if line.strip()] if out else []

    def diff_text(self, mode: str = "auto") -> str:
        return self._run(self._diff_cmd(mode))

    def _diff_name_only_cmd(self, mode: str) -> List[str]:
        mode = (mode or "auto").lower()
        if mode == "staged":
            return ["git", "diff", "--name-only", "--staged"]
        if mode == "worktree":
            return ["git", "diff", "--name-only"]
        if mode == "head":
            return ["git", "diff", "--name-only", "HEAD"]
        staged = self._run(["git", "diff", "--name-only", "--staged"]).strip()
        return ["git", "diff", "--name-only", "--staged"] if staged else ["git", "diff", "--name-only", "HEAD"]

    def _diff_cmd(self, mode: str) -> List[str]:
        mode = (mode or "auto").lower()
        if mode == "staged":
            return ["git", "diff", "--staged"]
        if mode == "worktree":
            return ["git", "diff"]
        if mode == "head":
            return ["git", "diff", "HEAD"]
        staged = self._run(["git", "diff", "--staged"]).strip()
        return ["git", "diff", "--staged"] if staged else ["git", "diff", "HEAD"]

    def _run(self, cmd: List[str]) -> str:
        proc = subprocess.run(
            cmd,
            cwd=str(self.repo_path),
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout
