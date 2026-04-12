"""Lever — dead_link_check.

Markdown rots. A renamed file or a deleted doc leaves dangling
``[text](path/that/no/longer/exists.md)`` references that never trip
CI. This lever walks every changed ``.md`` in the diff, extracts
relative-path markdown links (``[…](…)``), and flags any whose
target file doesn't exist.

External URLs (``http://``, ``https://``, ``mailto:``, ``ftp:``,
``tel:``) and pure-anchor links (``#section``) are deferred — fully
validating external links would require network and is out of scope
for a smoke lever.

Anchor suffixes on relative paths (``docs/foo.md#bar``) are stripped
before the existence check.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .base import Lever, LeverObservation

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "ftp:", "tel:", "data:")


class DeadLinkCheckLever(Lever):
    name = "dead_link_check"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        max_findings = int(inputs.get("max_findings", 25))
        project_root = brain_path.parent

        try:
            result = self._run_subprocess(
                ["git", "diff", "--name-only", diff_spec, "--", "*.md"],
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

        changed = [p.strip() for p in result.stdout.splitlines() if p.strip().endswith(".md")]

        findings: List[str] = []
        for rel_path in changed:
            abs_md = project_root / rel_path
            try:
                src = abs_md.read_text(encoding="utf-8")
            except (FileNotFoundError, OSError):
                continue
            md_dir = abs_md.parent
            for match in _LINK_RE.finditer(src):
                target = match.group(1).strip()
                if not target or target.startswith("#"):
                    continue
                if target.lower().startswith(_EXTERNAL_PREFIXES):
                    continue
                path_part = target.split("#", 1)[0].split("?", 1)[0]
                if not path_part:
                    continue
                if path_part.startswith("/"):
                    candidate = project_root / path_part.lstrip("/")
                else:
                    candidate = md_dir / path_part
                if not candidate.exists():
                    findings.append(f"{rel_path}: dead link -> {target}")
                    if len(findings) >= max_findings:
                        break
            if len(findings) >= max_findings:
                break

        base = {"diff_spec": diff_spec, "markdowns_checked": len(changed)}
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)
