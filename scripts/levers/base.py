"""Lever contract: modular operator over the .brain/ substrate.

A Lever is a small, self-contained unit that:
  1. reads a declarative manifest (YAML)
  2. observes current state via the .brain/ ledger
  3. takes one well-defined action
  4. returns an observation dict that the dispatcher appends to the ledger

Levers must not keep private state outside .brain/. Compounding happens
through the shared substrate, never through inter-lever coupling.

Contract rules (enforced by this module + linted by the Wave 0 audit):
  - never use subprocess with shell=True; use Lever._run_subprocess
  - never bare `except Exception`; raise named exceptions instead
  - every observation must conform to LeverObservation (outcome is one of
    OUTCOMES; detail is a mapping)
  - every ledger append goes through LedgerEvent, never ad-hoc dicts
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Tuple, TypedDict


OUTCOMES = frozenset({"clean", "found", "error", "skipped", "unknown"})


class LeverObservation(TypedDict, total=False):
    outcome: str
    detail: Dict[str, Any]
    duration_ms: int


class LeverError(Exception):
    """Base class for all lever-substrate errors."""


class LedgerSchemaError(LeverError):
    """Raised when an event does not satisfy the LedgerEvent schema."""


class SubprocessFailure(LeverError):
    """Raised when a subprocess invoked via Lever._run_subprocess fails.

    Carries stage/returncode/stdout/stderr so downstream can record a
    structured error observation without parsing exception text.
    """

    def __init__(
        self,
        stage: str,
        returncode: int,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        super().__init__(f"{stage}: exit {returncode}")
        self.stage = stage
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _strip_control_chars(value: Any) -> Any:
    if isinstance(value, str):
        return _CONTROL_CHARS.sub("", value)
    if isinstance(value, dict):
        return {k: _strip_control_chars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_strip_control_chars(v) for v in value]
    return value


@dataclass(frozen=True)
class LedgerEvent:
    """One typed row in .brain/ledger/events.jsonl.

    Frozen by design — events are immutable once constructed. Use
    ``from_jsonl`` to parse incoming lines (raises LedgerSchemaError on
    malformed input) and ``to_jsonl`` to emit. Free-form module-specific
    fields live in ``extra`` so the required schema stays small.
    """

    ts: str
    type: str
    lever: Optional[str] = None
    outcome: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"ts": self.ts, "type": self.type}
        if self.lever is not None:
            out["lever"] = self.lever
        if self.outcome is not None:
            out["outcome"] = self.outcome
        if self.detail is not None:
            out["detail"] = self.detail
        for k, v in self.extra.items():
            if k not in out:
                out[k] = v
        return out

    def to_jsonl(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_jsonl(cls, line: str) -> "LedgerEvent":
        line = line.strip()
        if not line:
            raise LedgerSchemaError("empty ledger line")
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as e:
            raise LedgerSchemaError(f"invalid JSON: {e}") from e
        if not isinstance(raw, dict):
            raise LedgerSchemaError(f"event must be an object, got {type(raw).__name__}")
        ts = raw.get("ts")
        etype = raw.get("type")
        if not isinstance(ts, str) or not ts:
            raise LedgerSchemaError("event missing required field 'ts'")
        if not isinstance(etype, str) or not etype:
            raise LedgerSchemaError("event missing required field 'type'")
        lever = raw.get("lever")
        if lever is not None and not isinstance(lever, str):
            raise LedgerSchemaError("'lever' must be a string if present")
        outcome = raw.get("outcome")
        if outcome is not None:
            if not isinstance(outcome, str):
                raise LedgerSchemaError("'outcome' must be a string if present")
            if outcome not in OUTCOMES:
                raise LedgerSchemaError(
                    f"outcome '{outcome}' not in allowed set {sorted(OUTCOMES)}"
                )
        detail = raw.get("detail")
        if detail is not None and not isinstance(detail, dict):
            raise LedgerSchemaError("'detail' must be an object if present")
        reserved = {"ts", "type", "lever", "outcome", "detail"}
        extra = {k: v for k, v in raw.items() if k not in reserved}
        return cls(
            ts=ts,
            type=etype,
            lever=lever,
            outcome=outcome,
            detail=detail,
            extra=extra,
        )

    @classmethod
    def for_lever_observation(
        cls,
        lever_name: str,
        observation: Mapping[str, Any],
        *,
        ts: Optional[str] = None,
    ) -> "LedgerEvent":
        if not lever_name or not isinstance(lever_name, str):
            raise LedgerSchemaError("lever name must be a non-empty string")
        outcome = observation.get("outcome")
        if outcome not in OUTCOMES:
            raise LedgerSchemaError(
                f"observation outcome '{outcome}' not in allowed set {sorted(OUTCOMES)}"
            )
        detail = observation.get("detail", {})
        if not isinstance(detail, dict):
            raise LedgerSchemaError("observation 'detail' must be a dict")
        extra: Dict[str, Any] = {}
        duration = observation.get("duration_ms")
        if duration is not None:
            if not isinstance(duration, int) or duration < 0:
                raise LedgerSchemaError("duration_ms must be a non-negative int")
            extra["duration_ms"] = duration
        return cls(
            ts=ts or datetime.now(timezone.utc).isoformat(),
            type=f"lever.{lever_name}.observation",
            lever=lever_name,
            outcome=outcome,
            detail=_strip_control_chars(detail),
            extra=extra,
        )


class Lever(ABC):
    """Base class every concrete lever subclasses.

    Subclasses MUST:
      - set ``name`` to match the manifest stem
      - implement ``run(manifest, brain_path) -> LeverObservation``
      - use ``_run_subprocess`` for any shell-out (never subprocess.run
        with shell=True directly)
      - return a dict that fits ``LeverObservation`` — outcome ∈ OUTCOMES,
        detail is a dict
    """

    name: str = ""

    @abstractmethod
    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        ...

    @staticmethod
    def _run_subprocess(
        argv: List[str],
        *,
        timeout: float,
        stage: str,
        check: bool = False,
        cwd: Optional[Path] = None,
    ) -> subprocess.CompletedProcess:
        """Run a subprocess with argv-only invocation. Raises named errors.

        - argv MUST be list[str]; anything else is a contract violation.
        - shell=True is never allowed (argv list is invoked directly).
        - FileNotFoundError propagates so callers can tag missing-tool
          errors distinct from process failures.
        - TimeoutExpired propagates so callers can tag stuck processes.
        - When ``check=True``, non-zero exit raises SubprocessFailure
          (instead of CalledProcessError, so the stage name is carried).
        """
        if not isinstance(argv, list) or not all(isinstance(a, str) for a in argv):
            raise TypeError(f"{stage}: argv must be list[str]")
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd else None,
        )
        if check and result.returncode != 0:
            raise SubprocessFailure(
                stage=stage,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        return result

    @staticmethod
    def _timed(fn: Callable[[], Any]) -> Tuple[Any, int]:
        start = time.monotonic()
        result = fn()
        return result, int((time.monotonic() - start) * 1000)

    @staticmethod
    def observation_clean(detail: Optional[Dict[str, Any]] = None) -> LeverObservation:
        return {"outcome": "clean", "detail": detail or {}}

    @staticmethod
    def observation_found(detail: Dict[str, Any]) -> LeverObservation:
        return {"outcome": "found", "detail": detail}

    @staticmethod
    def observation_error(stage: str, error: str, **extra: Any) -> LeverObservation:
        detail: Dict[str, Any] = {"stage": stage, "error": error}
        detail.update(extra)
        return {"outcome": "error", "detail": detail}

    @staticmethod
    def observation_skipped(reason: str, **extra: Any) -> LeverObservation:
        detail: Dict[str, Any] = {"reason": reason}
        detail.update(extra)
        return {"outcome": "skipped", "detail": detail}


def iter_events(
    ledger_path: Path,
    *,
    skip_invalid: bool = True,
) -> Iterator[LedgerEvent]:
    """Yield typed LedgerEvent rows from a JSONL ledger.

    Used by readers (the TB lever gate, bull_audit, MCP resources). When
    ``skip_invalid`` is False, a corrupt line raises LedgerSchemaError;
    otherwise corrupt lines are silently skipped (the fail-closed callers
    check counts against manifest to detect truncation/corruption).
    """
    if not ledger_path.exists():
        return
    with ledger_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                yield LedgerEvent.from_jsonl(line)
            except LedgerSchemaError:
                if not skip_invalid:
                    raise
                continue
