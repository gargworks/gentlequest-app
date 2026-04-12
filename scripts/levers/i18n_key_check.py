"""Lever — i18n_key_check.

Hardcoded user-facing text escapes translation. This lever walks the
added lines in the diff for JSX/TSX files and flags any visible text
node that isn't wrapped in an i18n call (``t(...)`` / ``i18n.t(...)``).

Intentionally conservative:
  - JSX text node detected only via ``>Hello World<`` shape
  - only flags text ≥ ``min_length`` characters (short strings like
    ``>X<`` are usually markup, not prose)
  - line already containing ``t(`` or ``i18n.t(`` is assumed i18n-aware,
    even if the specific text isn't wrapped (cheap false-negative to
    avoid the expensive AST walk)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from ._diff import iter_added_lines
from .base import Lever, LeverObservation, SubprocessFailure


class I18nKeyCheckLever(Lever):
    name = "i18n_key_check"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        extensions = tuple(inputs.get("source_extensions") or [".tsx", ".jsx"])
        min_length = int(inputs.get("min_length", 3))
        max_findings = int(inputs.get("max_findings", 25))
        i18n_guard = re.compile(
            inputs.get("i18n_call_regex", r"(?:\bt|\bi18n\.t)\(")
        )
        jsx_text = re.compile(
            inputs.get(
                "jsx_text_regex",
                r">([A-Za-z][A-Za-z0-9 ,.!?'\-]{2,})<",
            )
        )

        try:
            added_iter = list(iter_added_lines(diff_spec))
        except FileNotFoundError:
            return self.observation_error("git_diff", "git not installed")
        except subprocess.TimeoutExpired:
            return self.observation_error("git_diff", "timed out", diff_spec=diff_spec)
        except SubprocessFailure as e:
            return self.observation_error(
                "git_diff", e.stderr.strip() or f"git exit {e.returncode}",
                returncode=e.returncode,
            )

        findings: List[str] = []
        for added in added_iter:
            if not added.path.endswith(extensions):
                continue
            if i18n_guard.search(added.content):
                continue
            for match in jsx_text.finditer(added.content):
                text = match.group(1).strip()
                if len(text) < min_length:
                    continue
                findings.append(f"{added.path}: \"{text}\"")
                if len(findings) >= max_findings:
                    break
            if len(findings) >= max_findings:
                break

        base = {
            "diff_spec": diff_spec,
            "lines_scanned": sum(1 for a in added_iter if a.path.endswith(extensions)),
        }
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)
