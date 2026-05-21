"""Multi-thread storage for TB endpoint (Phase 2).

Per-chat-id namespaced threads with rich metadata. Reuses Phase 1's
AtomicJSONStore primitive — atomic write + rotation + recovery — for the
storage mechanics.

Charter commitment #1 (built whole), #5 (compounding hooks day 1):
    threads carry tunnel_topics + sovereignty_default + person_tags
    fields from day one even though Phase 4 is the consumer. Forward-
    compat hooks live in the schema, not bolted on later.

Schema (per spec phases/phase2_multithread.md §2.1):
    {
      "tg:7575125475": {                # namespace = surface:chat_id
        "active_thread_id": "manju_messaging",
        "threads": {
          "manju_messaging": {
            "id": str,
            "label": str,
            "embedding": [float, ...],   # 1024-dim qwen3-embedding centroid
            "embedding_n_messages": int,
            "last_activity": iso8601 str,
            "status": "active" | "archived",
            "tunnel_topics": list,        # Phase 4 populates
            "sovereignty_default": str,   # public | guarded | sovereign
            "person_tags": list,          # Phase 4 auto-tags
            "turn_count": int,
            "created_at": iso8601 str,
            "session_id": str,            # endpoint session key
            "turns": [(user, tb), ...]    # conversation history (mirrors Phase 1)
          }, ...
        }
      }
    }

Storage:  .brain/tb_personal_ai/threads.json (+ .1, .2 rotation)
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scripts.persist_sessions import AtomicJSONStore, _DEFAULT_DIR

logger = logging.getLogger(__name__)


# ── Defaults + ENV-tunable knobs ─────────────────────────────────────

_DEFAULT_THREADS_FILE = _DEFAULT_DIR / "threads.json"

SOFT_CEILING = int(os.environ.get("TB_THREAD_SOFT_CEILING", "5"))
HARD_CEILING = int(os.environ.get("TB_THREAD_HARD_CEILING", "10"))

# Pre-seeded canonical buckets (§2.4) — every new chat_id starts with
# these so ad-hoc proliferation has a home that already exists.
CANONICAL_BUCKETS = ("inbox", "people", "drafts", "code", "journal")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Schema validation ────────────────────────────────────────────────

def _make_thread(
    thread_id: str,
    chat_id: str,
    label: Optional[str] = None,
    embedding: Optional[List[float]] = None,
    sovereignty_default: str = "public",
) -> Dict[str, Any]:
    """Construct a fresh thread dict with all required fields."""
    now = _now_iso()
    return {
        "id": thread_id,
        "label": label or thread_id,
        "embedding": embedding or [],
        "embedding_n_messages": 0,
        "last_activity": now,
        "status": "active",
        "tunnel_topics": [],
        "sovereignty_default": sovereignty_default,
        "person_tags": [],
        "turn_count": 0,
        "created_at": now,
        "session_id": f"{chat_id}:{thread_id}",
        "turns": [],
    }


_THREAD_REQUIRED = {
    "id": str,
    "label": str,
    "embedding": list,
    "embedding_n_messages": int,
    "last_activity": str,
    "status": str,
    "tunnel_topics": list,
    "sovereignty_default": str,
    "person_tags": list,
    "turn_count": int,
    "created_at": str,
    "session_id": str,
    "turns": list,
}


def _validate_thread(chat_id: str, thread_id: str, data: Any) -> bool:
    if not isinstance(data, dict):
        logger.warning("thread %s/%s: not a dict (%s)",
                       chat_id, thread_id, type(data).__name__)
        return False
    for key, expected in _THREAD_REQUIRED.items():
        if key not in data:
            logger.warning("thread %s/%s: missing key %r",
                           chat_id, thread_id, key)
            return False
        if not isinstance(data[key], expected):
            logger.warning("thread %s/%s: key %r wrong type %s",
                           chat_id, thread_id, key, type(data[key]).__name__)
            return False
    if data["status"] not in ("active", "archived"):
        logger.warning("thread %s/%s: bad status %r",
                       chat_id, thread_id, data["status"])
        return False
    return True


def _normalize_thread(data: Any) -> Dict[str, Any]:
    """Fill in missing fields with defaults; coerce turns to tuples."""
    if not isinstance(data, dict):
        return {}
    out = dict(data)
    if "turns" in out and isinstance(out["turns"], list):
        out["turns"] = [tuple(t) if isinstance(t, list) else t
                        for t in out["turns"]]
    out.setdefault("turns", [])
    out.setdefault("embedding", [])
    out.setdefault("embedding_n_messages", 0)
    out.setdefault("tunnel_topics", [])
    out.setdefault("person_tags", [])
    out.setdefault("turn_count", 0)
    out.setdefault("sovereignty_default", "public")
    out.setdefault("status", "active")
    out.setdefault("last_activity", _now_iso())
    out.setdefault("created_at", _now_iso())
    out.setdefault("tunnel_topics", [])
    return out


# ── Public API ───────────────────────────────────────────────────────

class ThreadStorage:
    """Per-chat-id thread store backed by AtomicJSONStore.

    The endpoint holds an in-memory dict + calls save() after each
    mutation. Same pattern as SessionStore — caller manages state, store
    handles disk.
    """

    def __init__(
        self,
        path: Path = _DEFAULT_THREADS_FILE,
        generations: int = 2,
        soft_ceiling: int = SOFT_CEILING,
        hard_ceiling: int = HARD_CEILING,
    ):
        self._store = AtomicJSONStore(Path(path), generations)
        self.path = self._store.path
        self.soft_ceiling = soft_ceiling
        self.hard_ceiling = hard_ceiling

    # ---- load / save ----

    def load(self) -> Dict[str, Dict[str, Any]]:
        """Restore the full {chat_id: {active_thread_id, threads}} dict."""
        raw = self._store.load_raw()
        if raw is None:
            logger.info("threads: no existing file at %s; starting fresh",
                        self.path)
            return {}

        cleaned: Dict[str, Dict[str, Any]] = {}
        for chat_id, chat_data in raw.items():
            if not isinstance(chat_data, dict):
                logger.warning("threads: chat %s not a dict; skipping", chat_id)
                continue
            threads_raw = chat_data.get("threads", {})
            if not isinstance(threads_raw, dict):
                continue
            cleaned_threads: Dict[str, Dict[str, Any]] = {}
            for tid, tdata in threads_raw.items():
                normalized = _normalize_thread(tdata)
                if _validate_thread(chat_id, tid, normalized):
                    cleaned_threads[tid] = normalized
            if cleaned_threads:
                cleaned[chat_id] = {
                    "active_thread_id": chat_data.get("active_thread_id"),
                    "threads": cleaned_threads,
                }
        logger.info("threads: loaded %d chat namespaces from %s",
                    len(cleaned), self.path)
        return cleaned

    def save(self, data: Dict[str, Dict[str, Any]]) -> bool:
        return self._store.save(data)

    # ---- chat namespace helpers ----

    @staticmethod
    def initialize_chat(
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
    ) -> Dict[str, Any]:
        """Seed canonical buckets (§2.4) for a new chat_id; idempotent."""
        if chat_id not in data:
            threads = {
                bucket: _make_thread(bucket, chat_id, label=bucket)
                for bucket in CANONICAL_BUCKETS
            }
            data[chat_id] = {
                "active_thread_id": "inbox",
                "threads": threads,
            }
        return data[chat_id]

    @staticmethod
    def list_active(
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
    ) -> List[Dict[str, Any]]:
        chat = data.get(chat_id, {})
        threads = chat.get("threads", {})
        return [t for t in threads.values() if t.get("status") == "active"]

    @staticmethod
    def list_all(
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
    ) -> List[Dict[str, Any]]:
        chat = data.get(chat_id, {})
        return list(chat.get("threads", {}).values())

    @staticmethod
    def get_thread(
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
        thread_id: str,
    ) -> Optional[Dict[str, Any]]:
        return data.get(chat_id, {}).get("threads", {}).get(thread_id)

    @staticmethod
    def get_active_thread(
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
    ) -> Optional[Dict[str, Any]]:
        chat = data.get(chat_id)
        if not chat:
            return None
        active_id = chat.get("active_thread_id")
        if not active_id:
            return None
        return chat.get("threads", {}).get(active_id)

    @staticmethod
    def set_active(
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
        thread_id: str,
    ) -> bool:
        chat = data.get(chat_id)
        if not chat or thread_id not in chat.get("threads", {}):
            return False
        # Don't switch to an archived thread silently — caller must
        # un-archive first if intended.
        if chat["threads"][thread_id].get("status") != "active":
            return False
        chat["active_thread_id"] = thread_id
        return True

    # ---- ceiling enforcement (§2.3) ----

    def can_create_thread(
        self,
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
    ) -> Tuple[bool, str]:
        """Returns (allowed, reason). Reason is "" when allowed, or:
            "soft_ceiling" — at soft limit, caller should surface
                             consolidation prompt.
            "hard_ceiling" — at hard limit, refuse.
        """
        active = self.list_active(data, chat_id)
        n = len(active)
        if n >= self.hard_ceiling:
            return False, "hard_ceiling"
        if n >= self.soft_ceiling:
            return True, "soft_ceiling"  # allowed but warn
        return True, ""

    def suggest_consolidation(
        self,
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Suggest a (merge_candidate, archive_candidate) pair when the
        soft ceiling is hit. Cheapest heuristics:
        - merge_candidate: the active thread with the lowest turn_count
          (likely a new ad-hoc thread that didn't take off)
        - archive_candidate: oldest last_activity among active threads
        """
        active = self.list_active(data, chat_id)
        if not active:
            return None, None
        merge_c = min(active, key=lambda t: t.get("turn_count", 0))
        archive_c = min(active, key=lambda t: t.get("last_activity", ""))
        return merge_c, archive_c

    # ---- mutators ----

    def create_thread(
        self,
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
        thread_id: str,
        label: Optional[str] = None,
        embedding: Optional[List[float]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """Create + register a new thread. Returns (thread, reason).
        reason = "" on success, "exists", "hard_ceiling".

        Caller is responsible for surfacing soft-ceiling consolidation
        prompts (use can_create_thread() before calling this).
        """
        self.initialize_chat(data, chat_id)
        chat = data[chat_id]
        if thread_id in chat["threads"]:
            return chat["threads"][thread_id], "exists"
        allowed, reason = self.can_create_thread(data, chat_id)
        if not allowed:
            return None, reason
        thread = _make_thread(thread_id, chat_id, label=label,
                              embedding=embedding)
        chat["threads"][thread_id] = thread
        return thread, ""

    def archive(
        self,
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
        thread_id: str,
    ) -> bool:
        thread = self.get_thread(data, chat_id, thread_id)
        if not thread:
            return False
        thread["status"] = "archived"
        # If it was the active thread, fall back to inbox or first active
        chat = data[chat_id]
        if chat.get("active_thread_id") == thread_id:
            remaining = [t["id"] for t in self.list_active(data, chat_id)]
            chat["active_thread_id"] = remaining[0] if remaining else None
        return True

    def rename(
        self,
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
        thread_id: str,
        new_label: str,
    ) -> bool:
        thread = self.get_thread(data, chat_id, thread_id)
        if not thread or not new_label:
            return False
        thread["label"] = new_label
        return True

    def merge(
        self,
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
        winner_id: str,
        loser_id: str,
    ) -> bool:
        """Merge loser into winner. Loser's turns + tunnel_topics + person_tags
        append onto winner; loser is then archived. Winner's centroid
        becomes a turn-count-weighted blend.
        """
        winner = self.get_thread(data, chat_id, winner_id)
        loser = self.get_thread(data, chat_id, loser_id)
        if not winner or not loser or winner_id == loser_id:
            return False
        winner["turns"] = list(winner.get("turns", [])) + list(loser.get("turns", []))
        winner["turn_count"] = winner.get("turn_count", 0) + loser.get("turn_count", 0)
        # Merge tag fields uniquely
        for key in ("tunnel_topics", "person_tags"):
            seen = set(winner.get(key, []))
            for v in loser.get(key, []):
                if v not in seen:
                    winner[key].append(v)
                    seen.add(v)
        # Centroid: weighted average if both have embeddings
        we = winner.get("embedding")
        le = loser.get("embedding")
        wn = max(1, winner.get("embedding_n_messages", 1))
        ln = max(1, loser.get("embedding_n_messages", 1))
        if we and le and len(we) == len(le):
            total = wn + ln
            winner["embedding"] = [
                (we[i] * wn + le[i] * ln) / total for i in range(len(we))
            ]
            winner["embedding_n_messages"] = total
        winner["last_activity"] = _now_iso()
        # Archive loser; pivot active_thread if needed
        return self.archive(data, chat_id, loser_id)

    # ---- per-turn updates ----

    def record_turn(
        self,
        data: Dict[str, Dict[str, Any]],
        chat_id: str,
        thread_id: str,
        user_msg: str,
        tb_response: str,
    ) -> Optional[Dict[str, Any]]:
        thread = self.get_thread(data, chat_id, thread_id)
        if not thread:
            return None
        thread["turns"] = list(thread.get("turns", []))
        thread["turns"].append((user_msg, tb_response))
        thread["turn_count"] = int(thread.get("turn_count", 0)) + 1
        thread["last_activity"] = _now_iso()
        return thread


# ── Migration from Phase 1 ───────────────────────────────────────────

def migrate_from_sessions(
    sessions: Dict[str, Dict[str, Any]],
    threads_data: Dict[str, Dict[str, Any]],
) -> int:
    """One-shot migration: Phase 1 _sessions[surface:chat_id] dicts →
    Phase 2 threads_data[surface:chat_id]['threads']['default'].

    Idempotent: if a chat_id already has a 'default' thread, skip.
    Returns count of sessions migrated.
    """
    migrated = 0
    for sid, sdata in sessions.items():
        if not isinstance(sdata, dict):
            continue
        # Phase 1 keys are e.g. "tg:7575125475" or REPL "repl-1234567890"
        chat_id = sid
        if chat_id not in threads_data:
            threads_data[chat_id] = {
                "active_thread_id": "default",
                "threads": {},
            }
        chat = threads_data[chat_id]
        chat.setdefault("threads", {})
        if "default" in chat["threads"]:
            continue  # already migrated

        default = _make_thread("default", chat_id, label="default")
        # Carry forward turns + sovereignty + mode metadata
        default["turns"] = list(sdata.get("turns", []))
        default["turn_count"] = len(default["turns"])
        default["sovereignty_default"] = sdata.get("sovereignty", "guarded")
        if sdata.get("created"):
            try:
                ts = float(sdata["created"])
                default["created_at"] = datetime.fromtimestamp(
                    ts, tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
            except (TypeError, ValueError):
                pass
        chat["threads"]["default"] = default
        if not chat.get("active_thread_id"):
            chat["active_thread_id"] = "default"
        migrated += 1
    return migrated
