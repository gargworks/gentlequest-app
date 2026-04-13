"""Lever — plan_audit (accountability lever).

Walks both plan directories, joins against TB's `.brain/audit/results.json`,
and classifies every plan into one of 11 buckets so plan rot is visible
on the ledger. The lever observes the accountability loop; it does not
run it. TB's ``--audit-plans`` CLI remains the only place that actually
verifies plans (see feedback_run_the_full_loop memory).

Bucket evaluation order matters (sequential if/elif):

    1. unverifiable           — plan has no parseable `## Files Modified`
                                AND no `## Verification` section. Lever
                                can never auto-grade this plan; structural
                                fix is cheap (add sections). Highest
                                priority — beats audit state.
    2. never_audited          — no results entry for this filename
    3. stale                  — plan_mtime on disk > result.plan_mtime +
                                threshold (stale BEATS verdict)
    4. drift_detected         — verdict ∈ {ACCEPT, DEEPEN, REJECT} AND
                                max(referenced_file.mtime) > audited_at.
                                Strictly stronger than stale: catches
                                code drift independent of plan edits.
    5. needs_deepen           — verdict=DEEPEN
    6. deepen_exhausted       — verdict=DEEPEN_EXHAUSTED (audit gave up)
    7. failed_audit           — verdict=REJECT
    8. abandoned              — verdict=ABANDONED (NOT counted as rotting)
    9. verified_with_evidence — verdict=ACCEPT, not stale/drift,
                                quality ∈ {strong, weak}
   10. verified_no_evidence   — verdict=ACCEPT, not stale/drift,
                                quality ∈ {none, missing, unknown}
                                — ROTTING: rubber-stamp accept
   11. parse_error            — per-plan classification raised (R3
                                isolation). NOT rotting; reported via
                                skip_reasons for bull_audit to observe.

Rotting = unverifiable ∪ never_audited ∪ stale ∪ drift_detected ∪
          needs_deepen ∪ deepen_exhausted ∪ failed_audit ∪
          verified_no_evidence.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ._plan_parser import extract_modified_files, has_verification_section
from .base import Lever, LeverObservation


_ROTTING = frozenset({
    "unverifiable",
    "never_audited",
    "stale",
    "drift_detected",
    "needs_deepen",
    "deepen_exhausted",
    "failed_audit",
    "verified_no_evidence",
})

_EVIDENCE_QUALITIES = frozenset({"strong", "weak"})

_DRIFT_VERDICTS = frozenset({"ACCEPT", "DEEPEN", "REJECT"})


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
        skip_reasons: Dict[str, str] = {}
        for path in plan_paths:
            try:
                info = _classify(path, results, stale_threshold_s, project_root)
            except Exception as e:  # R3 — per-plan error isolation
                by_bucket["parse_error"] = by_bucket.get("parse_error", 0) + 1
                skip_reasons[path.name] = f"{type(e).__name__}: {e}"
                continue
            if info is None:
                continue
            classified.append(info)
            by_bucket[info["bucket"]] = by_bucket.get(info["bucket"], 0) + 1

        plans_total = len(classified)
        rotting = [p for p in classified if p["bucket"] in _ROTTING]

        if not rotting and not skip_reasons:
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
        detail: Dict[str, Any] = {
            "plans_total": plans_total,
            "plans_rotting": len(rotting),
            "by_bucket": by_bucket,
            "top_rot": top_rot,
        }
        if skip_reasons:
            detail["skip_reasons"] = skip_reasons
        return self.observation_found(detail)


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
    path: Path,
    results: Dict[str, Any],
    stale_threshold_s: int,
    project_root: Path,
) -> Optional[Dict[str, Any]]:
    try:
        st = path.stat()
    except FileNotFoundError:
        return None
    plan_mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
    plan_mtime_iso = plan_mtime.isoformat()

    try:
        plan_text = path.read_text(encoding="utf-8")
    except OSError:
        plan_text = ""
    modified_files = extract_modified_files(plan_text)
    has_verify = has_verification_section(plan_text)

    entry = results.get(path.name)
    entry_valid = isinstance(entry, dict)

    # Priority 1: unverifiable — lever can never auto-grade (R2: empty
    # or missing section both qualify, since parser returns [] for both).
    if not modified_files and not has_verify:
        bucket = "unverifiable"
    elif not entry_valid:
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
        elif _has_drift(modified_files, entry, project_root):
            bucket = "drift_detected"
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


def _has_drift(
    modified_files: List[str],
    entry: Dict[str, Any],
    project_root: Path,
) -> bool:
    """Return True iff a referenced file was modified after audit."""
    if not modified_files:
        return False
    verdict = entry.get("verdict")
    if verdict not in _DRIFT_VERDICTS:
        return False
    audited_epoch = _to_epoch(entry.get("audited_at"))
    if audited_epoch is None:
        return False
    for rel in modified_files:
        fp = _resolve(project_root, rel)
        try:
            mtime = fp.stat().st_mtime
        except (FileNotFoundError, OSError):
            continue
        if mtime > audited_epoch:
            return True
    return False


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


def _to_epoch(value: Any) -> Optional[float]:
    """R4 — normalize ISO-8601 string or numeric epoch to UTC epoch seconds.

    Writer behavior: results.json stores `audited_at` as ISO-8601.
    st_mtime is POSIX float. Drift comparison must be in one unit.
    Naive ISO timestamps are treated as UTC (matches writer default).
    """
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()
