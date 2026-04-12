"""Lever — config_schema_check.

Lightweight JSON-config validator: the manifest declares a mapping of
``{path: {key: type_name}}`` and the lever checks, for every config
file whose path appears in the current diff, that each required key is
present and its JSON type matches. Only fires on configs touched in
the diff (no diff match → clean-no-op, keeps noise low).

Type names mirror ``type(value).__name__`` — i.e. ``str``, ``int``,
``float``, ``bool``, ``list``, ``dict``, ``NoneType``. Use ``int|float``
to allow either numeric type.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .base import Lever, LeverObservation


class ConfigSchemaCheckLever(Lever):
    name = "config_schema_check"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        schemas = inputs.get("schemas") or {}
        max_findings = int(inputs.get("max_findings", 25))
        project_root = brain_path.parent

        if not isinstance(schemas, dict) or not schemas:
            return self.observation_skipped("no_schemas_configured")

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

        changed = {p.strip() for p in result.stdout.splitlines() if p.strip()}
        touched = [p for p in schemas if p in changed]

        findings: List[str] = []
        for rel_path in touched:
            expected = schemas[rel_path]
            if not isinstance(expected, dict):
                continue
            abs_path = project_root / rel_path
            try:
                raw = abs_path.read_text(encoding="utf-8")
            except FileNotFoundError:
                findings.append(f"{rel_path}: file missing")
                if len(findings) >= max_findings:
                    break
                continue
            except OSError as e:
                return self.observation_error(
                    "read_config", f"{rel_path}: {e}"
                )
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as e:
                return self.observation_error(
                    "parse_config", f"{rel_path}: invalid json: {e}"
                )
            if not isinstance(payload, dict):
                findings.append(f"{rel_path}: root is not an object")
                if len(findings) >= max_findings:
                    break
                continue
            for key, type_spec in expected.items():
                if key not in payload:
                    findings.append(f"{rel_path}: missing '{key}'")
                    if len(findings) >= max_findings:
                        break
                    continue
                actual_type = type(payload[key]).__name__
                allowed = {t.strip() for t in str(type_spec).split("|") if t.strip()}
                if actual_type not in allowed:
                    findings.append(
                        f"{rel_path}: '{key}' is {actual_type}, expected {type_spec}"
                    )
                    if len(findings) >= max_findings:
                        break
            if len(findings) >= max_findings:
                break

        base = {"diff_spec": diff_spec, "configs_checked": len(touched)}
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)
