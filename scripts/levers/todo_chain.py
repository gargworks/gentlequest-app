"""Lever — todo_chain.

Scans the diff for newly-added TODO/FIXME/XXX/HACK markers. These are
half-finished signals in a repo: a commit adding a TODO is a commit
that knowingly ships partial work. The lever makes that visible to
the substrate so the review gate can catch it before ACCEPT.

Zero external dependencies — pattern match on git-diff output only.
"""

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .base import Lever

MARKER_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b[:\s]")


class TodoChainLever(Lever):
    name = "todo_chain"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> Dict[str, Any]:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        max_findings = int(inputs.get("max_findings", 50))

        try:
            diff_result = subprocess.run(
                ["git", "diff", "--unified=0", diff_spec],
                capture_output=True, text=True, timeout=10,
            )
        except Exception as e:
            return {"outcome": "error", "detail": {"stage": "git_diff", "error": str(e)}}

        findings: List[str] = []
        current_file = ""
        for line in diff_result.stdout.splitlines():
            if line.startswith("+++ b/"):
                current_file = line[6:].strip()
                continue
            if not line.startswith("+") or line.startswith("+++"):
                continue
            content = line[1:]
            if MARKER_RE.search(content):
                findings.append(f"{current_file}: {content.strip()[:200]}")
                if len(findings) >= max_findings:
                    break

        if not findings:
            return {"outcome": "clean", "detail": {"diff_spec": diff_spec}}

        return {
            "outcome": "found",
            "detail": {
                "diff_spec": diff_spec,
                "findings": findings,
            },
        }
