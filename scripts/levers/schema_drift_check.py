"""Lever — schema_drift_check.

Schema files (JSON Schema, OpenAPI) are contracts — a field removed or
a type changed is a breaking change for every downstream consumer. This
lever walks every schema file in the diff, compares its top-level key
set + JSON types to the previous version (``git show HEAD~1:<path>``),
and flags removed keys or changed types.

Additive-only changes are clean. A schema that didn't exist at HEAD~1
(``git show`` exits non-zero) is skipped for that file — it's a new
schema with no contract to break.
"""

from __future__ import annotations

import fnmatch
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .base import Lever, LeverObservation


class SchemaDriftCheckLever(Lever):
    name = "schema_drift_check"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        schema_patterns = list(inputs.get("schema_patterns") or [])
        max_findings = int(inputs.get("max_findings", 25))
        project_root = brain_path.parent

        try:
            result = self._run_subprocess(
                ["git", "diff", "--name-only", diff_spec],
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
            if p.strip() and any(_glob_match(p.strip(), g) for g in schema_patterns)
        ]

        findings: List[str] = []
        prev_ref = _prev_ref_from(diff_spec)
        for rel_path in changed:
            if len(findings) >= max_findings:
                break
            current = _load_schema(project_root / rel_path)
            if current is None:
                return self.observation_error(
                    "parse_schema", f"{rel_path}: current unreadable or invalid"
                )
            previous = _load_schema_at_ref(prev_ref, rel_path)
            if previous is None:
                continue
            for msg in _drift_findings(previous, current):
                findings.append(f"{rel_path}: {msg}")
                if len(findings) >= max_findings:
                    break

        base = {
            "diff_spec": diff_spec,
            "schemas_checked": len(changed),
        }
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)


def _glob_match(path: str, pattern: str) -> bool:
    """``**/`` prefix means 'any depth (including zero)'. fnmatch doesn't
    implement that by default, so we try both the full pattern and the
    pattern with the leading ``**/`` stripped."""
    if fnmatch.fnmatch(path, pattern):
        return True
    if pattern.startswith("**/"):
        return fnmatch.fnmatch(path, pattern[3:])
    return False


def _prev_ref_from(diff_spec: str) -> str:
    if ".." in diff_spec:
        return diff_spec.split("..", 1)[0] or "HEAD~1"
    return "HEAD~1"


def _load_schema(path: Path) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _load_schema_at_ref(ref: str, rel_path: str) -> Any:
    try:
        result = Lever._run_subprocess(
            ["git", "show", f"{ref}:{rel_path}"],
            timeout=10,
            stage="git_show",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _drift_findings(prev: Any, cur: Any) -> List[str]:
    out: List[str] = []
    if not isinstance(prev, dict) or not isinstance(cur, dict):
        return out
    for key, prev_val in prev.items():
        if key not in cur:
            out.append(f"removed '{key}'")
            continue
        p_type = type(prev_val).__name__
        c_type = type(cur[key]).__name__
        if p_type != c_type:
            out.append(f"type '{key}' {p_type}->{c_type}")
    return out
