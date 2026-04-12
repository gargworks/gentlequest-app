"""Lever — secret_scan.

Scans added diff lines for known secret-key patterns (Google/Perplexity/
Stripe/GitHub/AWS). Findings carry the file path + the *pattern prefix*
only — never the matched secret body — so the lever observation itself
never leaks a credential into the ledger.

Alphabetical manifest iteration puts this lever before ``todo_chain`` on
shared triggers, so a secret buried inside a TODO comment is caught here
before todo_chain would echo it into its finding.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from ._diff import iter_added_lines
from .base import Lever, LeverObservation, SubprocessFailure

_PREFIX_RE = re.compile(r"^[A-Za-z0-9_-]+")


class SecretScanLever(Lever):
    name = "secret_scan"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        max_findings = int(inputs.get("max_findings", 25))
        patterns: List[str] = inputs.get("patterns") or []

        compiled = [(p, re.compile(p), _pattern_prefix(p)) for p in patterns]
        findings: List[str] = []

        try:
            for added in iter_added_lines(diff_spec):
                for _raw, rx, prefix in compiled:
                    if rx.search(added.content):
                        findings.append(f"{added.path}: pattern={prefix}")
                        if len(findings) >= max_findings:
                            break
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
            return self.observation_clean({
                "diff_spec": diff_spec,
                "patterns_checked": len(compiled),
            })
        return self.observation_found({
            "diff_spec": diff_spec,
            "findings": findings,
        })


def _pattern_prefix(pattern: str) -> str:
    m = _PREFIX_RE.match(pattern)
    return m.group(0) if m else pattern[:8]
