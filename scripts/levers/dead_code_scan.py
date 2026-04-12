"""Lever — dead_code_scan.

Detect newly-added top-level Python functions or classes that never appear
anywhere else in the tracked repo — a cheap dead-code signal. For each
changed ``.py`` file in the diff, parse it with ``ast``, extract top-level
``def`` / ``class`` names, and run ``git grep -lwE <name>`` across the
tree. If the only file matching the symbol is the file that defines it,
the symbol has no callers and gets flagged.

Conservative by design:
  - only top-level defs (inner / nested defs often *look* unused)
  - skip underscore-prefixed names (``_foo``), dunders (``__init__``),
    and ``test_*`` (pytest discovers those by convention, not by import)
  - skip files whose path matches an ``ignore_patterns`` entry
"""

from __future__ import annotations

import ast
import fnmatch
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .base import Lever, LeverObservation


class DeadCodeScanLever(Lever):
    name = "dead_code_scan"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        ignore_patterns = list(inputs.get("ignore_patterns") or [])
        max_findings = int(inputs.get("max_findings", 25))
        project_root = brain_path.parent

        try:
            result = self._run_subprocess(
                ["git", "diff", "--name-only", diff_spec, "--", "*.py"],
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

        changed = [
            p.strip() for p in result.stdout.splitlines()
            if p.strip() and p.strip().endswith(".py")
            and not any(fnmatch.fnmatch(p.strip(), pat) for pat in ignore_patterns)
        ]

        findings: List[str] = []
        for rel_path in changed:
            if len(findings) >= max_findings:
                break
            abs_path = project_root / rel_path
            try:
                src = abs_path.read_text(encoding="utf-8")
            except (FileNotFoundError, OSError):
                continue
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for node in tree.body:
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                name = node.name
                if name.startswith("_") or name.startswith("test_"):
                    continue
                if _only_defined_here(name, rel_path):
                    findings.append(f"{rel_path}:{name}")
                    if len(findings) >= max_findings:
                        break

        base = {
            "diff_spec": diff_spec,
            "files_checked": len(changed),
        }
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)


def _only_defined_here(name: str, defining_file: str) -> bool:
    try:
        result = Lever._run_subprocess(
            ["git", "grep", "-lwE", rf"\b{name}\b"],
            timeout=10,
            stage="git_grep",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    if result.returncode not in (0, 1):
        return False
    files = {p.strip() for p in result.stdout.splitlines() if p.strip()}
    return files == {defining_file}
