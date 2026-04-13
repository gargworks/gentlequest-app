"""Lever — diff_size_check.

Large diffs get rubber-stamped. This lever reads ``git diff --numstat``
for the active diff spec and flags when either the file count or the
added-line count exceeds the manifest thresholds. Binary entries (numstat
shows ``-`` instead of a line count) are counted as 0 added lines — they
still contribute to the file count.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .base import Lever, LeverObservation


class DiffSizeCheckLever(Lever):
    name = "diff_size_check"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        max_files = int(inputs.get("max_files", 20))
        max_added_lines = int(inputs.get("max_added_lines", 500))

        try:
            result = self._run_subprocess(
                ["git", "diff", "--numstat", diff_spec],
                timeout=10,
                stage="git_numstat",
            )
        except FileNotFoundError:
            return self.observation_error("git_numstat", "git not installed")
        except subprocess.TimeoutExpired:
            return self.observation_error(
                "git_numstat", "timed out", diff_spec=diff_spec
            )

        if result.returncode != 0:
            return self.observation_error(
                "git_numstat",
                result.stderr.strip() or f"git exit {result.returncode}",
                returncode=result.returncode,
            )

        files, added = _parse_numstat(result.stdout)

        findings: List[str] = []
        if files > max_files:
            findings.append(f"files={files} > {max_files}")
        if added > max_added_lines:
            findings.append(f"added={added} > {max_added_lines}")

        base = {
            "diff_spec": diff_spec,
            "files": files,
            "added_lines": added,
        }
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)


def _parse_numstat(stdout: str) -> Tuple[int, int]:
    files = 0
    added = 0
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        files += 1
        added_str = parts[0]
        if added_str == "-":
            continue
        try:
            added += int(added_str)
        except ValueError:
            continue
    return files, added
