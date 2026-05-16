"""Persistent session storage for TB endpoint.

Replaces the in-memory-only `_sessions` dict in tb_endpoint.py with an
atomic JSON file persisted on every turn. Survives:
- Endpoint daemon restart (launchd kickstart)
- `git pull && launchctl kickstart` compounding flow
- Mac reboot
- Brief power loss (atomic write protects against mid-write corruption)

Charter commitment #1: built whole, not MVP scaffolding.
Charter commitment #9: migration paths real — existing in-memory state
                       at startup snapshots cleanly into the persistent
                       store on first save.

Phase 1 Subsystem 1.1.

Storage layout:
    .brain/tb_personal_ai/sessions.json    (live)
    .brain/tb_personal_ai/sessions.json.1  (rotation -1)
    .brain/tb_personal_ai/sessions.json.2  (rotation -2)

Atomicity: write to .tmp, fsync, rename onto target. POSIX rename is
atomic so a crash mid-write either leaves the prior version intact or
the new one — never a partially-written file.

Rotation: on each save, the prior version moves to .1 (and .1 → .2,
old .2 deleted). Recovery: on load, if .json fails to parse, try .1,
then .2, then start fresh. Worst case: lose 1-2 turns of history, not
the whole session log.

Schema validation: each session entry validated against expected shape
on load. Malformed entries dropped with a warning logged to status.md
(not the noisy stderr).
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Storage paths ────────────────────────────────────────────────────

_DEFAULT_BRAIN = Path(os.environ.get(
    "NUCLEUS_BRAIN_PATH",
    str(Path(__file__).resolve().parent.parent / ".brain"),
))
_DEFAULT_DIR = _DEFAULT_BRAIN / "tb_personal_ai"
_DEFAULT_FILE = _DEFAULT_DIR / "sessions.json"


def _rotation_paths(target: Path, generations: int = 2) -> List[Path]:
    """Returns paths for rotation: [target, target.1, target.2, ...]."""
    return [target] + [target.with_suffix(f"{target.suffix}.{i}")
                       for i in range(1, generations + 1)]


# ── Generic atomic JSON store ────────────────────────────────────────

class AtomicJSONStore:
    """Generic atomic-write + rotate-on-save JSON dict store.

    Phase 1 introduced this pattern for SessionStore. Phase 2 extracts the
    primitive so ThreadStorage (and future stores) reuse it without
    duplication. Charter commitment #1: built whole, no MVP scaffolding.

    This base class handles only the storage mechanics:
    - atomic write (tmp → fsync → POSIX rename)
    - 2-generation rotation on save (target → .1 → .2; oldest dropped)
    - load with fallback (target → .1 → .2 if newer corrupt)

    Schema validation lives in subclasses — load_raw returns the parsed
    dict as-is; subclasses override load() to apply per-entry validation.
    """

    def __init__(self, path: Path, generations: int = 2):
        self.path = Path(path)
        self.generations = generations
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load_raw(self) -> Optional[Dict[str, Any]]:
        """Load raw dict from disk. Falls back through rotation generations
        on parse failure. Returns None if no recoverable file exists."""
        for candidate in _rotation_paths(self.path, self.generations):
            if not candidate.exists():
                continue
            try:
                with candidate.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("%s: %s parse failed (%s); trying older",
                               type(self).__name__, candidate, e)
                continue
            if not isinstance(raw, dict):
                logger.warning("%s: %s root not a dict; trying older",
                               type(self).__name__, candidate)
                continue
            return raw
        return None

    def save(self, data: Dict[str, Any]) -> bool:
        """Atomically write data to disk + rotate prior version."""
        with self._lock:
            try:
                self._rotate()
                tmp = self.path.with_suffix(self.path.suffix + ".tmp")
                with tmp.open("w", encoding="utf-8") as f:
                    json.dump(data, f, default=_json_default,
                              ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                tmp.replace(self.path)  # POSIX atomic rename
                return True
            except OSError as e:
                logger.error("%s: save failed (%s)",
                             type(self).__name__, e)
                return False

    def _rotate(self) -> None:
        """Shift old generations: target → .1, .1 → .2, drop .2."""
        if not self.path.exists():
            return
        paths = _rotation_paths(self.path, self.generations)
        oldest = paths[-1]
        if oldest.exists():
            try:
                oldest.unlink()
            except OSError:
                pass
        for i in range(len(paths) - 1, 0, -1):
            src = paths[i - 1]
            dst = paths[i]
            if src.exists():
                try:
                    src.replace(dst)
                except OSError as e:
                    logger.warning("%s: rotation %s → %s failed: %s",
                                   type(self).__name__,
                                   src.name, dst.name, e)


# ── Schema validation ────────────────────────────────────────────────

# Sessions are dicts with the shape produced by tb_endpoint._get_session.
# Required keys + their expected types. Extras tolerated forward-compat.
_REQUIRED_KEYS: Dict[str, Any] = {
    "turns": list,           # [(user_msg, tb_response), ...]
    "last_verdict_id": (type(None), str),
    "created": (int, float),
    "mode": str,
    "sovereignty": str,
}


def _validate_session(session_id: str, data: Any) -> bool:
    """True if data has the required shape. Logs reason if not."""
    if not isinstance(data, dict):
        logger.warning("session %s: not a dict (%s)", session_id, type(data).__name__)
        return False
    for key, expected in _REQUIRED_KEYS.items():
        if key not in data:
            logger.warning("session %s: missing key %r", session_id, key)
            return False
        if not isinstance(data[key], expected):
            logger.warning("session %s: key %r wrong type %s (expected %s)",
                           session_id, key, type(data[key]).__name__, expected)
            return False
    # Validate turns shape: list of [str, str] pairs
    for i, turn in enumerate(data["turns"]):
        if not (isinstance(turn, (list, tuple)) and len(turn) == 2
                and all(isinstance(x, str) for x in turn)):
            logger.warning("session %s: turn %d malformed: %r",
                           session_id, i, turn)
            return False
    return True


# ── Public API ───────────────────────────────────────────────────────

class SessionStore(AtomicJSONStore):
    """Thread-safe persistent session store.

    Wraps AtomicJSONStore with session-specific schema validation +
    legacy-format normalization. Public API unchanged from Phase 1:

        store = SessionStore()
        sessions = store.load()    # validates + normalizes
        store.save(sessions)       # atomic write + rotate
    """

    def __init__(self, path: Path = _DEFAULT_FILE, generations: int = 2):
        super().__init__(path, generations)

    def load(self) -> Dict[str, Dict[str, Any]]:
        """Restore sessions dict from disk; validate + normalize each entry."""
        raw = self.load_raw()
        if raw is None:
            logger.info("sessions: no existing file at %s; starting fresh",
                        self.path)
            return {}
        cleaned: Dict[str, Dict[str, Any]] = {}
        dropped: List[str] = []
        for sid, sdata in raw.items():
            normalized = _normalize_session(sdata)
            if _validate_session(sid, normalized):
                cleaned[sid] = normalized
            else:
                dropped.append(sid)
        if dropped:
            logger.warning("sessions: dropped %d malformed entries: %s",
                           len(dropped), dropped[:5])
        logger.info("sessions: loaded %d from %s", len(cleaned), self.path)
        return cleaned


# ── JSON helpers ─────────────────────────────────────────────────────

def _json_default(obj: Any) -> Any:
    """JSON encoder fallback: tuples → lists (for `turns` field)."""
    if isinstance(obj, tuple):
        return list(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"not JSON-serializable: {type(obj).__name__}")


def _normalize_session(sdata: Any) -> Dict[str, Any]:
    """Normalize a session dict on load. Turns become tuples, missing
    keys filled with defaults, type coercions applied. Returns the
    normalized dict (does not mutate input)."""
    if not isinstance(sdata, dict):
        return {}
    out = dict(sdata)
    # Normalize turns: list-of-list → list-of-tuple (downstream code
    # uses tuple destructuring `for u, a in turns`)
    if "turns" in out and isinstance(out["turns"], list):
        out["turns"] = [tuple(t) if isinstance(t, list) else t
                        for t in out["turns"]]
    # Fill missing keys with defaults (forward-compat with future fields,
    # backward-compat with legacy in-memory shape)
    out.setdefault("turns", [])
    out.setdefault("last_verdict_id", None)
    out.setdefault("created", time.time())
    out.setdefault("mode", "code")
    out.setdefault("sovereignty", "guarded")
    return out


# ── Migration helper ─────────────────────────────────────────────────

def migrate_in_memory(in_memory: Dict[str, Dict[str, Any]],
                      store: SessionStore) -> int:
    """One-shot migration: existing in-memory sessions → persisted store.

    Called by tb_endpoint at startup if the persistent file doesn't exist
    yet. Charter commitment #9: migration paths real, no data loss.

    Returns number of sessions migrated.
    """
    if not in_memory:
        return 0
    if store.path.exists():
        # Already migrated — don't overwrite persistent state with
        # in-memory copy (might be stale)
        return 0
    ok = store.save(in_memory)
    if ok:
        logger.info("sessions: migrated %d in-memory sessions to %s",
                    len(in_memory), store.path)
        return len(in_memory)
    return 0
