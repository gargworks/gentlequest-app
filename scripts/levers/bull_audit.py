"""Lever — bull_audit (Brazen Bull meta-lever skeleton).

The Brazen Bull audits its own upgrades: the creator goes in first.
This lever replays the tail window of the ledger and checks five
frozen invariants that together describe "the substrate is
structurally sound right now." A finding means a lever is rotting
the substrate — runaway duration, repeated errors, schema drift — and
that pattern should be visible on the ledger like any other lever
finding.

Why skeleton: the 5 invariants cover RUNTIME integrity (schema, outcome
space, duration bound, CSR floor, repeated-error spiking). Structural
drift (manifests edited by hand, lever count dropping silently) is
ongoing discovery — tracked in TODOS.md.

Design notes
============

Data flow:

    cron_daily
        │
        ▼
    iter events.jsonl  ──▶  tail last `window_events` rows
        │
        ▼
    read .brain/flywheel/csr.json  ──▶  ratio float
        │
        ▼
    five invariants (each pure: events + csr -> Optional[str])
        │
        ▼
    findings list → observation(clean|found|skipped)

Adding an invariant: write a top-level function
``_inv_<name>(events, csr) -> Optional[str]`` that returns a finding
string or None, then append its callable to ``_INVARIANTS``. Each
invariant must be independently testable.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .base import Lever, LedgerEvent, LedgerSchemaError, LeverObservation, OUTCOMES


class BullAuditLever(Lever):
    name = "bull_audit"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        ledger_rel = inputs.get("ledger_path", ".brain/ledger/events.jsonl")
        csr_rel = inputs.get("csr_path", ".brain/flywheel/csr.json")
        window_events = int(inputs.get("window_events", 1000))
        duration_threshold_ms = int(inputs.get("duration_threshold_ms", 30_000))
        csr_floor = float(inputs.get("csr_floor", 0.5))
        repeated_error_threshold = int(inputs.get("repeated_error_threshold", 3))

        project_root = brain_path.parent
        ledger_path = _resolve(project_root, ledger_rel)
        csr_path = _resolve(project_root, csr_rel)

        if not ledger_path.exists():
            return self.observation_skipped(
                "no_ledger", path=str(ledger_path)
            )

        events, schema_errors = _read_window(ledger_path, window_events)
        if not events and not schema_errors:
            return self.observation_skipped("empty_ledger")

        csr = _read_csr(csr_path)

        ctx = _InvariantContext(
            events=events,
            schema_errors=schema_errors,
            csr=csr,
            duration_threshold_ms=duration_threshold_ms,
            csr_floor=csr_floor,
            repeated_error_threshold=repeated_error_threshold,
        )

        findings: List[str] = []
        for name, fn in _INVARIANTS:
            finding = fn(ctx)
            if finding is not None:
                findings.append(f"{name}: {finding}")

        base = {
            "window_events": window_events,
            "events_read": len(events),
            "schema_errors": schema_errors,
            "csr": csr if csr is not None else "unavailable",
            "invariants_checked": len(_INVARIANTS),
        }
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)


class _InvariantContext:
    __slots__ = (
        "events", "schema_errors", "csr",
        "duration_threshold_ms", "csr_floor", "repeated_error_threshold",
    )

    def __init__(self, *, events, schema_errors, csr,
                 duration_threshold_ms, csr_floor, repeated_error_threshold):
        self.events = events
        self.schema_errors = schema_errors
        self.csr = csr
        self.duration_threshold_ms = duration_threshold_ms
        self.csr_floor = csr_floor
        self.repeated_error_threshold = repeated_error_threshold


def _resolve(root: Path, rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else root / rel


def _read_window(ledger_path: Path, window: int) -> Tuple[List[LedgerEvent], int]:
    """Return (last-N successfully parsed events, count of schema-invalid lines in window).

    We read raw lines so we can count schema failures in the window itself.
    iter_events would silently skip them — for bull_audit, they ARE the signal.
    """
    try:
        lines = ledger_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ([], 0)
    tail = [ln for ln in lines[-window:] if ln.strip()]
    events: List[LedgerEvent] = []
    errors = 0
    for ln in tail:
        try:
            events.append(LedgerEvent.from_jsonl(ln))
        except LedgerSchemaError:
            errors += 1
    return (events, errors)


def _read_csr(csr_path: Path) -> Optional[float]:
    try:
        raw = csr_path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    ratio = data.get("ratio") if isinstance(data, dict) else None
    try:
        return float(ratio) if ratio is not None else None
    except (TypeError, ValueError):
        return None


def _inv_schema_valid(ctx: _InvariantContext) -> Optional[str]:
    if ctx.schema_errors > 0:
        return f"{ctx.schema_errors} ledger line(s) failed schema parse"
    return None


def _inv_outcome_in_set(ctx: _InvariantContext) -> Optional[str]:
    bad: List[str] = []
    for ev in ctx.events:
        if ev.outcome is None:
            continue
        if ev.outcome not in OUTCOMES:
            bad.append(f"{ev.lever or ev.type}={ev.outcome}")
    if bad:
        return f"{len(bad)} observation(s) with outcome outside OUTCOMES: {bad[:3]}"
    return None


def _inv_duration_bounded(ctx: _InvariantContext) -> Optional[str]:
    offenders: List[str] = []
    for ev in ctx.events:
        dur = ev.extra.get("duration_ms")
        if not isinstance(dur, int):
            continue
        if dur > ctx.duration_threshold_ms:
            offenders.append(f"{ev.lever or ev.type}={dur}ms")
    if offenders:
        return (
            f"{len(offenders)} observation(s) above {ctx.duration_threshold_ms}ms: "
            f"{offenders[:3]}"
        )
    return None


def _inv_csr_not_collapsed(ctx: _InvariantContext) -> Optional[str]:
    if ctx.csr is None:
        return "CSR unavailable (file missing or malformed)"
    if ctx.csr < ctx.csr_floor:
        return f"CSR {ctx.csr:.3f} < floor {ctx.csr_floor}"
    return None


def _inv_no_repeated_lever_errors(ctx: _InvariantContext) -> Optional[str]:
    counts: Counter = Counter()
    for ev in ctx.events:
        if ev.outcome != "error":
            continue
        lever = ev.lever
        stage = (ev.detail or {}).get("stage") if isinstance(ev.detail, dict) else None
        if lever and stage:
            counts[(lever, stage)] += 1
    offenders = [
        f"{lever}:{stage}={n}"
        for (lever, stage), n in counts.items()
        if n > ctx.repeated_error_threshold
    ]
    if offenders:
        return (
            f"lever errors repeating > {ctx.repeated_error_threshold} in window: "
            f"{offenders[:3]}"
        )
    return None


_INVARIANTS: List[tuple] = [
    ("schema_valid", _inv_schema_valid),
    ("outcome_in_set", _inv_outcome_in_set),
    ("duration_bounded", _inv_duration_bounded),
    ("csr_not_collapsed", _inv_csr_not_collapsed),
    ("no_repeated_lever_errors", _inv_no_repeated_lever_errors),
]
