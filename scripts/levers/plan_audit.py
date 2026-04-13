"""Lever — plan_audit (accountability lever).

Walks both plan directories, joins against TB's `.brain/audit/results.json`,
and classifies every plan into one of eight buckets so plan rot is visible
on the ledger. The lever observes the accountability loop; it does not
run it. TB's ``--audit-plans`` CLI remains the only place that actually
verifies plans (see feedback_run_the_full_loop memory).

Bucket evaluation order matters (sequential if/elif):

    1. never_audited          — no results entry for this filename
    2. stale                  — plan_mtime on disk > result.plan_mtime + threshold
                                (stale BEATS verdict, including abandoned-but-
                                 modified; touching an abandoned plan signals
                                 reconsideration)
    3. needs_deepen           — verdict=DEEPEN
    4. deepen_exhausted       — verdict=DEEPEN_EXHAUSTED (audit gave up; plan
                                remains unverified — rotting until --audit-force)
    5. failed_audit           — verdict=REJECT
    6. abandoned              — verdict=ABANDONED (NOT counted as rotting)
    7. verified_with_evidence — verdict=ACCEPT, not stale, quality ∈ {strong, weak}
    8. verified_no_evidence   — verdict=ACCEPT, not stale, quality ∈ {none,
                                missing, unknown} — ROTTING: ACCEPT without
                                executed verification commands is a rubber stamp

Rotting = never_audited ∪ stale ∪ needs_deepen ∪ deepen_exhausted ∪
          failed_audit ∪ verified_no_evidence.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Lever, LeverObservation


_ROTTING = frozenset({
    "never_audited",
    "stale",
    "needs_deepen",
    "deepen_exhausted",
    "failed_audit",
    "verified_no_evidence",
})

_EVIDENCE_QUALITIES = frozenset({"strong", "weak"})


class PlanAuditLever(Lever):
    name = "plan_audit"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        plan_dirs_raw = inputs.get("plan_dirs", []) or []
        results_rel = inputs.get("audit_results_path", ".brain/audit/results.json")
        max_report = int(inputs.get("max_report", 10))
        stale_threshold_s = int(inputs.get("stale_threshold_seconds", 60))

        project_root = brain_path.parent
        plan_paths = _enumerate_plans(plan_dirs_raw, project_root)
        if not plan_paths:
            return self.observation_skipped("no_plans_found")

        results_path = _resolve(project_root, results_rel)
        try:
            results = _load_results_with_retry(results_path)
        except json.JSONDecodeError as e:
            return self.observation_error("parse_results", f"invalid json: {e}")
        except OSError as e:
            return self.observation_error("read_results", f"read failed: {e}")

        classified: List[Dict[str, Any]] = []
        by_bucket: Dict[str, int] = {}
        for path in plan_paths:
            info = _classify(path, results, stale_threshold_s)
            if info is None:
                continue
            classified.append(info)
            by_bucket[info["bucket"]] = by_bucket.get(info["bucket"], 0) + 1

        plans_total = len(classified)
        rotting = [p for p in classified if p["bucket"] in _ROTTING]

        if not rotting:
            return self.observation_clean({
                "plans_total": plans_total,
                "plans_audited": sum(
                    n for b, n in by_bucket.items()
                    if b in (
                        "verified_with_evidence",
                        "verified_no_evidence",
                        "abandoned",
                    )
                ),
                "by_bucket": by_bucket,
            })

        rotting_sorted = sorted(rotting, key=lambda p: p["mtime"], reverse=True)
        top_rot = [
            {
                "name": p["name"],
                "bucket": p["bucket"],
                "age_days": p["age_days"],
                "mtime": p["mtime"],
            }
            for p in rotting_sorted[:max_report]
        ]
        return self.observation_found({
            "plans_total": plans_total,
            "plans_rotting": len(rotting),
            "by_bucket": by_bucket,
            "top_rot": top_rot,
        })


def _resolve(root: Path, rel: str) -> Path:
    p = Path(rel).expanduser()
    return p if p.is_absolute() else root / rel


def _enumerate_plans(plan_dirs_raw: List[str], project_root: Path) -> List[Path]:
    paths: List[Path] = []
    for rel in plan_dirs_raw:
        d = _resolve(project_root, rel)
        if not d.exists() or not d.is_dir():
            continue
        paths.extend(sorted(d.glob("*.md")))
    return paths


def _load_results_with_retry(results_path: Path) -> Dict[str, Any]:
    try:
        raw = results_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        time.sleep(0.05)
        raw = results_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    if not isinstance(data, dict):
        raise json.JSONDecodeError("results.json must be an object", raw, 0)
    return data


def _classify(
    path: Path, results: Dict[str, Any], stale_threshold_s: int
) -> Optional[Dict[str, Any]]:
    try:
        st = path.stat()
    except FileNotFoundError:
        return None
    plan_mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
    plan_mtime_iso = plan_mtime.isoformat()

    entry = results.get(path.name)
    if not isinstance(entry, dict):
        bucket = "never_audited"
    else:
        verdict = entry.get("verdict")
        result_mtime = _parse_mtime(entry.get("plan_mtime"))
        is_stale = (
            result_mtime is not None
            and (plan_mtime - result_mtime).total_seconds() > stale_threshold_s
        )
        if is_stale:
            bucket = "stale"
        elif verdict == "DEEPEN":
            bucket = "needs_deepen"
        elif verdict == "DEEPEN_EXHAUSTED":
            bucket = "deepen_exhausted"
        elif verdict == "REJECT":
            bucket = "failed_audit"
        elif verdict == "ABANDONED":
            bucket = "abandoned"
        elif verdict == "ACCEPT":
            quality = entry.get("verification_quality")
            if quality in _EVIDENCE_QUALITIES:
                bucket = "verified_with_evidence"
            else:
                bucket = "verified_no_evidence"
        else:
            bucket = "never_audited"

    now = datetime.now(timezone.utc)
    age_days = int((now - plan_mtime).total_seconds() // 86400)
    return {
        "name": path.name,
        "bucket": bucket,
        "mtime": plan_mtime_iso,
        "age_days": age_days,
    }


def _parse_mtime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
