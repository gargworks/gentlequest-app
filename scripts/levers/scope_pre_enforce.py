"""Lever — scope_pre_enforce.

Enforces that the executor only touched files matching the active task's
``scope`` glob list. Complements TB's post-review scope gate by catching
drift at observation time — findings land on the ledger before TB even
reads the commit, so ACCEPT is gated by the earliest possible signal.

Skipped when ``NUCLEUS_TASK_ID`` is unset (manual session) or when the
task has no declared scope (bootstrap / unrestricted task).
"""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


from .base import Lever, LeverObservation


class ScopePreEnforceLever(Lever):
    name = "scope_pre_enforce"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        tasks_path_str = inputs.get("tasks_path", ".brain/driver/tasks.json")
        task_id_env = inputs.get("task_id_env", "NUCLEUS_TASK_ID")
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")

        task_id = os.environ.get(task_id_env)
        if not task_id:
            return self.observation_skipped("no_task_context", env_var=task_id_env)

        tasks_path = Path(tasks_path_str)
        if not tasks_path.is_absolute():
            tasks_path = brain_path.parent / tasks_path_str

        try:
            raw = tasks_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return self.observation_error(
                "task_load", f"tasks file missing: {tasks_path}"
            )
        except OSError as e:
            return self.observation_error("task_load", f"read failed: {e}")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            return self.observation_error("task_load", f"invalid json: {e}")

        task = _find_task(data, task_id)
        if task is None:
            return self.observation_error(
                "task_load", f"task {task_id} not found", task_id=task_id
            )

        scope = task.get("scope") or []
        if not isinstance(scope, list) or not scope:
            return self.observation_skipped(
                "empty_scope", task_id=task_id
            )

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

        changed = [p.strip() for p in result.stdout.splitlines() if p.strip()]
        findings: List[str] = []
        for f in changed:
            if not any(fnmatch.fnmatch(f, g) for g in scope):
                findings.append(f"OUT_OF_SCOPE: {f}")

        base = {
            "task_id": task_id,
            "files_checked": len(changed),
            "scope": list(scope),
        }
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)


def _find_task(data: Any, task_id: str) -> Optional[Dict[str, Any]]:
    if isinstance(data, dict):
        inner = data.get("tasks", data)
    else:
        inner = data
    if isinstance(inner, list):
        for t in inner:
            if isinstance(t, dict) and t.get("id") == task_id:
                return t
        return None
    if isinstance(inner, dict):
        candidate = inner.get(task_id)
        if isinstance(candidate, dict):
            return candidate
    return None
