"""Lever — migration_lint.

DB migrations get rubber-stamped until prod locks up. This lever
scans every newly-added migration file (``--diff-filter=A``) for a
short list of known-dangerous SQL patterns:

  - ``NOT NULL`` added without a ``DEFAULT`` on the same line
  - ``DROP COLUMN`` / ``DROP TABLE`` (consider deprecation first)
  - ``RENAME COLUMN`` / ``RENAME TABLE`` (breaks every live reader)

Only added files are checked — modifying a migration after it's merged
is its own kind of sin but out of scope here.
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .base import Lever, LeverObservation


def _glob_match(path: str, pattern: str) -> bool:
    """``**/`` prefix means 'any depth (including zero)'. fnmatch doesn't
    implement that by default, so we try both the full pattern and the
    pattern with the leading ``**/`` stripped."""
    if fnmatch.fnmatch(path, pattern):
        return True
    if pattern.startswith("**/"):
        return fnmatch.fnmatch(path, pattern[3:])
    return False


_DANGER_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"DROP\s+COLUMN", re.IGNORECASE), "DROP COLUMN — consider deprecation window"),
    (re.compile(r"DROP\s+TABLE", re.IGNORECASE), "DROP TABLE — breaks every live reader"),
    (re.compile(r"RENAME\s+COLUMN", re.IGNORECASE), "RENAME COLUMN — stage via add+backfill+remove"),
    (re.compile(r"RENAME\s+TABLE", re.IGNORECASE), "RENAME TABLE — stage via view-alias first"),
]
_NOT_NULL_RE = re.compile(r"\bNOT\s+NULL\b", re.IGNORECASE)
_DEFAULT_RE = re.compile(r"\bDEFAULT\b", re.IGNORECASE)


class MigrationLintLever(Lever):
    name = "migration_lint"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        migration_globs = list(inputs.get("migration_globs") or [])
        max_findings = int(inputs.get("max_findings", 25))
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

        added = [
            p.strip() for p in result.stdout.splitlines()
            if p.strip() and any(_glob_match(p.strip(), g) for g in migration_globs)
        ]

        findings: List[str] = []
        for rel_path in added:
            if len(findings) >= max_findings:
                break
            try:
                src = (project_root / rel_path).read_text(encoding="utf-8")
            except (FileNotFoundError, OSError):
                continue
            for line_no, line in enumerate(src.splitlines(), start=1):
                for pattern, message in _DANGER_PATTERNS:
                    if pattern.search(line):
                        findings.append(f"{rel_path}:{line_no}: {message}")
                        if len(findings) >= max_findings:
                            break
                if len(findings) >= max_findings:
                    break
                if _NOT_NULL_RE.search(line) and not _DEFAULT_RE.search(line):
                    findings.append(
                        f"{rel_path}:{line_no}: NOT NULL without DEFAULT — add DEFAULT to avoid backfill lock"
                    )
                    if len(findings) >= max_findings:
                        break

        base = {
            "diff_spec": diff_spec,
            "migrations_added": len(added),
        }
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)
