"""Lever — license_header_check.

Newly-added source files should declare a license/copyright header in
their first ``lines_to_check`` lines. Missing headers are a compliance
gap — finding them at ``pre_commit`` is cheaper than catching them at
open-source release time.

Only files added (``--diff-filter=A``) are checked — modified files are
out of scope since their header state is whatever the original commit
set.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .base import Lever, LeverObservation


class LicenseHeaderCheckLever(Lever):
    name = "license_header_check"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        extensions = list(inputs.get("extensions") or [".py", ".js", ".ts", ".tsx"])
        header_patterns = list(inputs.get("header_patterns") or [])
        lines_to_check = int(inputs.get("lines_to_check", 10))
        project_root = brain_path.parent

        try:
            result = self._run_subprocess(
                ["git", "diff", "--name-only", "--diff-filter=A", diff_spec],
                timeout=10,
                stage="git_diff",
            )
        except FileNotFoundError:
            return self.observation_error("git_diff", "git not installed")
        except subprocess.TimeoutExpired:
            return self.observation_error(
                "git_diff", "timed out", diff_spec=diff_spec
            )

        if result.returncode != 0:
            return self.observation_error(
                "git_diff",
                result.stderr.strip() or f"git exit {result.returncode}",
                returncode=result.returncode,
            )

        compiled = [re.compile(p) for p in header_patterns]
        added_files = [
            p.strip() for p in result.stdout.splitlines()
            if p.strip() and any(p.strip().endswith(ext) for ext in extensions)
        ]

        findings: List[str] = []
        for rel_path in added_files:
            abs_path = project_root / rel_path
            try:
                with abs_path.open("r", encoding="utf-8") as fh:
                    head_lines = [next(fh, "") for _ in range(lines_to_check)]
            except (FileNotFoundError, OSError):
                continue
            head = "".join(head_lines)
            if not any(rx.search(head) for rx in compiled):
                findings.append(rel_path)

        if not findings:
            return self.observation_clean({
                "diff_spec": diff_spec,
                "files_checked": len(added_files),
            })
        return self.observation_found({
            "diff_spec": diff_spec,
            "findings": findings,
        })
