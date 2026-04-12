"""Lever dispatcher.

Usage:
    python -m scripts.levers.run_lever <lever_name>
    python -m scripts.levers.run_lever --trigger <trigger_name>

Reads ``scripts/levers/manifests/<name>.yaml``, loads
``scripts/levers/<name>.py``, runs the ``Lever`` subclass, and appends a
typed observation to ``.brain/ledger/events.jsonl``. That ledger IS the
compounding substrate — any other lever or feature reading the ledger
sees this observation.

Substrate posture (fail-closed):
  - appends acquire a process-wide advisory flock on ``.brain/ledger.lock``
  - events are validated against ``LedgerEvent`` before write
  - writes are fsync'd before the lock releases
  - dispatcher failures emit ``lever.dispatcher.failure`` events
  - manifest-load errors emit ``lever.manifest.error`` events
"""

from __future__ import annotations

import argparse
import fcntl
import importlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BRAIN_PATH = PROJECT_ROOT / ".brain"
LEDGER_PATH = BRAIN_PATH / "ledger" / "events.jsonl"
LEDGER_LOCK_PATH = BRAIN_PATH / "ledger.lock"
MANIFESTS_DIR = Path(__file__).resolve().parent / "manifests"

from .base import LedgerEvent, LedgerSchemaError, Lever


TRIGGERS = frozenset({
    "post_executor",
    "pre_commit",
    "post_commit",
    "session_start",
    "cron_15m",
    "cron_hourly",
    "cron_daily",
    "manual",
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_manifest(name: str, manifests_dir: Path = MANIFESTS_DIR) -> Dict[str, Any]:
    path = manifests_dir / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No manifest at {path}")
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_lever(name: str) -> Lever:
    if not name.isidentifier():
        raise ValueError(f"Invalid lever name {name!r} — must be a Python identifier")
    module = importlib.import_module(f"scripts.levers.{name}")
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (isinstance(attr, type) and attr is not Lever
                and issubclass(attr, Lever)
                and getattr(attr, "name", "") == name):
            return attr()
    raise ValueError(f"No Lever subclass with name={name!r} in scripts.levers.{name}")


def _append_event(event: LedgerEvent, ledger_path: Path) -> Dict[str, Any]:
    """Validated, fsync'd, lock-protected append of a single LedgerEvent.

    The lock is advisory (flock) on a dedicated lock file so concurrent
    dispatchers serialize without blocking readers.
    """
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = ledger_path.parent.parent / "ledger.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    line = event.to_jsonl()
    with open(lock_path, "a+") as lock_f:
        fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
        try:
            with open(ledger_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())
        finally:
            fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
    return event.to_dict()


def _append_meta_event(
    event_type: str,
    detail: Dict[str, Any],
    ledger_path: Path,
) -> None:
    """Best-effort meta-event append. Never raises; meta-events cannot
    themselves crash the dispatcher, or we'd loop on failures."""
    try:
        meta = LedgerEvent(ts=_now_iso(), type=event_type, detail=detail)
        _append_event(meta, ledger_path)
    except Exception:
        pass


def append_observation(
    lever_name: str,
    observation: Dict[str, Any],
    ledger_path: Path = LEDGER_PATH,
) -> Dict[str, Any]:
    """Append a typed lever observation to the ledger.

    Validates the observation shape via ``LedgerEvent.for_lever_observation``.
    A malformed observation raises ``LedgerSchemaError`` AND writes a
    ``lever.schema.violation`` event so the substrate records the bug.
    """
    try:
        event = LedgerEvent.for_lever_observation(lever_name, observation)
    except LedgerSchemaError as e:
        _append_meta_event(
            "lever.schema.violation",
            {
                "lever": lever_name,
                "error": str(e),
                "observation_outcome": observation.get("outcome") if isinstance(observation, dict) else None,
            },
            ledger_path,
        )
        raise
    return _append_event(event, ledger_path)


def publish_event(
    event_type: str,
    *,
    outcome: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
    ledger_path: Optional[Path] = None,
    **extra: Any,
) -> bool:
    """Best-effort module-level event publisher.

    For non-lever events that still belong on the shared substrate —
    ``tb.review.decided``, ``chat.request.received``,
    ``ground.tier0.passed``. Unlike ``append_observation`` this never
    raises into the caller; publishing failure must not break the
    request path it's observing.

    ``outcome`` (if passed) is validated against OUTCOMES — an
    adversarial caller slipping a bogus outcome through here would
    break bull_audit's schema_valid invariant on the next read. Failed
    validation emits a ``lever.schema.violation`` event and returns False.

    ``ledger_path`` resolves at call time (not at def time) so tests
    can patch ``LEDGER_PATH`` and have it apply to all downstream calls.
    """
    effective_ledger = ledger_path or LEDGER_PATH
    try:
        if outcome is not None:
            from .base import OUTCOMES
            if outcome not in OUTCOMES:
                _append_meta_event(
                    "lever.schema.violation",
                    {
                        "source": "publish_event",
                        "event_type": event_type,
                        "bad_outcome": outcome,
                    },
                    effective_ledger,
                )
                return False
        event = LedgerEvent(
            ts=_now_iso(),
            type=event_type,
            outcome=outcome,
            detail=detail,
            extra={k: v for k, v in extra.items() if v is not None},
        )
        _append_event(event, effective_ledger)
        return True
    except Exception:
        return False


def run(
    name: str,
    manifests_dir: Optional[Path] = None,
    ledger_path: Optional[Path] = None,
) -> Dict[str, Any]:
    manifest = load_manifest(name, manifests_dir or MANIFESTS_DIR)
    effective_ledger = ledger_path or LEDGER_PATH
    if not manifest.get("enabled", True):
        observation = {"outcome": "skipped", "detail": {"reason": "disabled in manifest"}}
        append_observation(name, observation, effective_ledger)
        return observation
    lever = load_lever(name)
    start = datetime.now(timezone.utc)
    observation = lever.run(manifest, BRAIN_PATH)
    duration_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    if isinstance(observation, dict) and "duration_ms" not in observation:
        observation = dict(observation)
        observation["duration_ms"] = duration_ms
    append_observation(name, observation, effective_ledger)
    return observation


def run_trigger(
    trigger: str,
    manifests_dir: Optional[Path] = None,
    ledger_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Fire every enabled lever whose manifest lists the given trigger.

    Lever failures are caught AND emit ``lever.dispatcher.failure`` events
    so the substrate surfaces broken levers. The caller (TB driver,
    pre-commit hook) never breaks — lever auto-fire is supporting, not
    precondition.

    Returns ``[{"lever": name, "observation": obs}, ...]``.
    """
    mdir = manifests_dir or MANIFESTS_DIR
    effective_ledger = ledger_path or LEDGER_PATH
    if not mdir.exists():
        return []

    results: List[Dict[str, Any]] = []
    for manifest_file in sorted(mdir.glob("*.yaml")):
        name = manifest_file.stem
        try:
            manifest = load_manifest(name, mdir)
        except (yaml.YAMLError, OSError) as e:
            _append_meta_event(
                "lever.manifest.error",
                {"lever": name, "error": str(e), "trigger": trigger},
                effective_ledger,
            )
            continue
        if not manifest.get("enabled", True):
            continue
        triggers = manifest.get("triggers", []) or []
        trigger_names = set()
        for t in triggers:
            if isinstance(t, str):
                trigger_names.add(t)
            elif isinstance(t, dict):
                val = t.get("trigger") or t.get("name")
                if val:
                    trigger_names.add(val)
        if trigger not in trigger_names:
            continue
        try:
            obs = run(name, mdir, effective_ledger)
            results.append({"lever": name, "observation": obs})
        except (LedgerSchemaError, ValueError, FileNotFoundError, ImportError,
                TimeoutError, OSError, RuntimeError) as e:
            _append_meta_event(
                "lever.dispatcher.failure",
                {
                    "lever": name,
                    "trigger": trigger,
                    "error": str(e),
                    "error_class": type(e).__name__,
                },
                effective_ledger,
            )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a lever by name, or a trigger.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("name", nargs="?", help="Lever name (matches manifest filename)")
    group.add_argument(
        "--trigger",
        help=f"Fire all levers matching this trigger. Known: {sorted(TRIGGERS)}",
    )
    args = parser.parse_args()

    if args.trigger:
        results = run_trigger(args.trigger)
        print(f"[LEVER] trigger={args.trigger} fired {len(results)} lever(s)")
        for r in results:
            print(f"  - {r['lever']}: {r['observation'].get('outcome')}")
        return 0

    obs = run(args.name)
    outcome = obs.get("outcome", "unknown")
    print(f"[LEVER] {args.name}: {outcome}")
    detail = obs.get("detail", {})
    if outcome == "found":
        for finding in detail.get("findings", [])[:5]:
            print(f"  - {finding}")
    elif outcome == "error":
        print(f"  error: {detail.get('error', detail)}")

    return 0 if outcome in ("clean", "skipped") else 1


if __name__ == "__main__":
    sys.exit(main())
