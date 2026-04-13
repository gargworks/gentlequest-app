"""Lever — narrow_task_filter.

Broad task scope is the #1 predictor of Phase-D ACCEPT failures in the
driver. This lever reads the active task (via NUCLEUS_TASK_ID) from
``.brain/driver/tasks.json`` and surfaces findings whenever scope size,
description length, or title length breaches the manifest thresholds
— so the session_start trigger can catch over-broad tasks before the
executor spends Claude Code context trying to finish them.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .base import Lever, LeverObservation


class NarrowTaskFilterLever(Lever):
    name = "narrow_task_filter"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        tasks_path_str = inputs.get("tasks_path", ".brain/driver/tasks.json")
        task_id_env = inputs.get("task_id_env", "NUCLEUS_TASK_ID")
        max_scope_items = int(inputs.get("max_scope_items", 5))
        max_description_chars = int(inputs.get("max_description_chars", 500))
        max_title_chars = int(inputs.get("max_title_chars", 120))

        task_id = os.environ.get(task_id_env)
        if not task_id:
            return self.observation_skipped("no_task_id", env_var=task_id_env)

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
        description = task.get("description") or ""
        title = task.get("title") or ""

        scope_len = len(scope) if isinstance(scope, list) else 0
        description_len = len(description) if isinstance(description, str) else 0
        title_len = len(title) if isinstance(title, str) else 0

        findings = []
        if scope_len > max_scope_items:
            findings.append(f"scope={scope_len} > {max_scope_items}")
        if description_len > max_description_chars:
            findings.append(f"description={description_len} > {max_description_chars}")
        if title_len > max_title_chars:
            findings.append(f"title={title_len} > {max_title_chars}")

        base = {
            "task_id": task_id,
            "scope_items": scope_len,
            "description_chars": description_len,
            "title_chars": title_len,
        }

        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)


def _find_task(data: Any, task_id: str) -> Optional[Dict[str, Any]]:
    """Locate a task by id in either a list or dict shape."""
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
