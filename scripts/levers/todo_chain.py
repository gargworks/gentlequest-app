"""Lever — todo_chain.

Scans the diff for newly-added TODO/FIXME/XXX/HACK markers. These are
half-finished signals in a repo: a commit adding a TODO is a commit
that knowingly ships partial work. The lever makes that visible to
the substrate so the review gate can catch it before ACCEPT.

Zero external dependencies beyond git. Uses the shared ``_diff``
added-line iterator so every diff-walking lever reuses one parser.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Dict

from ._diff import iter_added_lines
from .base import Lever, LeverObservation, SubprocessFailure

MARKER_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b[:\s]")


class TodoChainLever(Lever):
    name = "todo_chain"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        max_findings = int(inputs.get("max_findings", 50))

        findings = []
        try:
            for added in iter_added_lines(diff_spec):
                if MARKER_RE.search(added.content):
                    findings.append(f"{added.path}: {added.content.strip()[:200]}")
                    if len(findings) >= max_findings:
                        break
        except FileNotFoundError:
            return self.observation_error("git_diff", "git not installed")
        except subprocess.TimeoutExpired:
            return self.observation_error("git_diff", "timed out", diff_spec=diff_spec)
        except SubprocessFailure as e:
            return self.observation_error(
                "git_diff", e.stderr.strip() or f"git exit {e.returncode}",
                returncode=e.returncode,
            )

        if not findings:
            return self.observation_clean({"diff_spec": diff_spec})

        return self.observation_found({
            "diff_spec": diff_spec,
            "findings": findings,
        })
