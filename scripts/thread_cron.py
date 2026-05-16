"""Background maintenance for thread storage (Phase 2 §2.5, §2.6).

Two operations exposed as plain functions plus a CLI entrypoint:

  archive_stale_threads(now=None) — flip status=archived on threads with
    last_activity older than TB_THREAD_ARCHIVE_DAYS (default 14d). Runs
    daily via launchd (or invoked at endpoint warmup).

  find_merge_candidates(chat_id, ...) — surface pairs of active threads
    whose centroid cosine similarity > MERGE_COSINE_THRESHOLD (default
    0.7). Returns ranked list; caller chooses to surface or auto-act.

Pre-seeded canonical buckets (inbox/people/drafts/code/journal) are
carved out from auto-archive — they exist as homes for ad-hoc traffic
even before they accumulate activity.

CLI:
    python -m scripts.thread_cron archive
    python -m scripts.thread_cron suggest-merges --chat-id tg:7575125475
    python -m scripts.thread_cron summary
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scripts.thread_router import cosine
from scripts.thread_storage import (
    CANONICAL_BUCKETS,
    ThreadStorage,
    _DEFAULT_THREADS_FILE,
)

logger = logging.getLogger(__name__)


ARCHIVE_DAYS = int(os.environ.get("TB_THREAD_ARCHIVE_DAYS", "14"))
MERGE_COSINE_THRESHOLD = float(
    os.environ.get("TB_THREAD_MERGE_THRESHOLD", "0.7")
)


def _parse_iso(ts: str) -> Optional[datetime]:
    if not ts:
        return None
    try:
        # The store writes Z-suffixed UTC iso8601
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None


# ── §2.5 — 14-day inactivity auto-archive ────────────────────────────

def archive_stale_threads(
    threads_data: Dict[str, Dict[str, Any]],
    archive_days: int = ARCHIVE_DAYS,
    now: Optional[datetime] = None,
    skip_canonical_when_unused: bool = True,
) -> List[Tuple[str, str]]:
    """Flip status=archived on threads inactive > archive_days.

    Returns list of (chat_id, thread_id) pairs that were archived. The
    caller is responsible for persisting threads_data.

    skip_canonical_when_unused: when True (default), pre-seeded canonical
    buckets (inbox, people, etc.) with turn_count == 0 are NOT archived.
    They exist as homes for future traffic; archiving them would force
    reseeding on the next message.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    cutoff = now - timedelta(days=archive_days)
    archived: List[Tuple[str, str]] = []

    for chat_id, chat in threads_data.items():
        threads = chat.get("threads", {})
        for tid, thread in threads.items():
            if thread.get("status") != "active":
                continue
            if (skip_canonical_when_unused
                    and tid in CANONICAL_BUCKETS
                    and thread.get("turn_count", 0) == 0):
                continue
            last = _parse_iso(thread.get("last_activity", ""))
            if last is None:
                continue
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if last < cutoff:
                thread["status"] = "archived"
                # Pivot active_thread_id off if needed
                if chat.get("active_thread_id") == tid:
                    remaining = [
                        t["id"] for t in threads.values()
                        if t.get("status") == "active" and t["id"] != tid
                    ]
                    chat["active_thread_id"] = remaining[0] if remaining else None
                archived.append((chat_id, tid))

    if archived:
        logger.info("thread_cron: archived %d stale threads (cutoff=%s)",
                    len(archived), cutoff.isoformat())
    return archived


# ── §2.6 — Auto-merge candidate detection ────────────────────────────

def find_merge_candidates(
    threads_data: Dict[str, Dict[str, Any]],
    chat_id: str,
    threshold: float = MERGE_COSINE_THRESHOLD,
    skip_canonical: bool = True,
) -> List[Tuple[Dict[str, Any], Dict[str, Any], float]]:
    """Find pairs of active threads with centroid similarity > threshold.

    Returns list of (thread_a, thread_b, similarity) sorted descending
    by similarity. Skips canonical buckets by default (these exist as
    catch-alls and aren't meaningful to merge into each other).

    Pure pairwise comparison: O(n^2). Phase 2 hard ceiling = 10 active
    threads, so worst-case 45 pair comparisons. No clustering needed.
    """
    chat = threads_data.get(chat_id, {})
    active = [
        t for t in chat.get("threads", {}).values()
        if t.get("status") == "active" and t.get("embedding")
    ]
    if skip_canonical:
        active = [t for t in active if t["id"] not in CANONICAL_BUCKETS]
    if len(active) < 2:
        return []

    pairs: List[Tuple[Dict[str, Any], Dict[str, Any], float]] = []
    for i in range(len(active)):
        for j in range(i + 1, len(active)):
            a = active[i]
            b = active[j]
            sim = cosine(a["embedding"], b["embedding"])
            if sim >= threshold:
                pairs.append((a, b, sim))

    pairs.sort(key=lambda p: p[2], reverse=True)
    return pairs


# ── Summary helper ───────────────────────────────────────────────────

def summarize(threads_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """One-shot count summary across all chats. Used by CLI + bot."""
    total_chats = len(threads_data)
    total_threads = 0
    active = 0
    archived = 0
    by_chat: Dict[str, Dict[str, int]] = {}
    for chat_id, chat in threads_data.items():
        n_active = 0
        n_archived = 0
        for thread in chat.get("threads", {}).values():
            total_threads += 1
            if thread.get("status") == "active":
                active += 1
                n_active += 1
            elif thread.get("status") == "archived":
                archived += 1
                n_archived += 1
        by_chat[chat_id] = {"active": n_active, "archived": n_archived}
    return {
        "total_chats": total_chats,
        "total_threads": total_threads,
        "active": active,
        "archived": archived,
        "by_chat": by_chat,
    }


# ── CLI entrypoint ───────────────────────────────────────────────────

def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="thread_cron",
        description="Background maintenance for TB thread storage.",
    )
    parser.add_argument("--threads-file", default=str(_DEFAULT_THREADS_FILE),
                        help="path to threads.json (default: %(default)s)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_archive = sub.add_parser(
        "archive", help="archive threads inactive > N days"
    )
    p_archive.add_argument("--days", type=int, default=ARCHIVE_DAYS)
    p_archive.add_argument("--dry-run", action="store_true")

    p_merge = sub.add_parser(
        "suggest-merges", help="surface high-similarity pairs"
    )
    p_merge.add_argument("--chat-id", required=True)
    p_merge.add_argument("--threshold", type=float,
                         default=MERGE_COSINE_THRESHOLD)

    sub.add_parser("summary", help="count by chat + status")

    # Phase 3 §3.12 — populate thread.tunnel_topics from cluster centroids
    p_topics = sub.add_parser(
        "resolve-topics",
        help="populate thread.tunnel_topics from approved cluster centroids "
             "(Phase 3 §3.12 bridge)",
    )
    p_topics.add_argument("--centroids-file",
                          help="cluster_centroids.json path (default: env "
                               "TB_CLUSTER_CENTROIDS_PATH or "
                               ".brain/tb_personal_ai/cluster_centroids.json)")
    p_topics.add_argument("--top-k", type=int, default=3)
    p_topics.add_argument("--threshold", type=float, default=0.6)
    p_topics.add_argument("--dry-run", action="store_true")
    return parser


def _cli_archive(args: argparse.Namespace) -> int:
    storage = ThreadStorage(path=Path(args.threads_file))
    data = storage.load()
    archived = archive_stale_threads(data, archive_days=args.days)
    if args.dry_run:
        print(json.dumps({"would_archive": archived, "count": len(archived)},
                         indent=2))
        return 0
    if archived and not storage.save(data):
        print("ERROR: archive succeeded in memory but save failed",
              file=sys.stderr)
        return 2
    print(json.dumps({"archived": archived, "count": len(archived)},
                     indent=2))
    return 0


def _cli_merge(args: argparse.Namespace) -> int:
    storage = ThreadStorage(path=Path(args.threads_file))
    data = storage.load()
    pairs = find_merge_candidates(
        data, chat_id=args.chat_id, threshold=args.threshold
    )
    out = [
        {"a": p[0]["id"], "b": p[1]["id"], "similarity": round(p[2], 4)}
        for p in pairs
    ]
    print(json.dumps({"chat_id": args.chat_id, "pairs": out}, indent=2))
    return 0


def _cli_summary(args: argparse.Namespace) -> int:
    storage = ThreadStorage(path=Path(args.threads_file))
    data = storage.load()
    print(json.dumps(summarize(data), indent=2))
    return 0


def _cli_resolve_topics(args: argparse.Namespace) -> int:
    """Walk every active thread, resolve tunnel_topics from approved
    cluster centroids. Phase 3 §3.12 bridge.
    """
    from scripts.thread_topic_resolver import (
        load_centroids, resolve_all_threads, DEFAULT_CENTROIDS_PATH,
    )
    storage = ThreadStorage(path=Path(args.threads_file))
    data = storage.load()

    centroids_path = (Path(args.centroids_file) if args.centroids_file
                      else DEFAULT_CENTROIDS_PATH)
    centroids = load_centroids(centroids_path)
    if not centroids:
        print(json.dumps({
            "ok": False,
            "reason": f"no approved centroids at {centroids_path}; "
                      f"run scripts/cluster_topics + scripts/label_clusters first",
        }, indent=2))
        return 1

    changes = resolve_all_threads(
        data, centroids, top_k=args.top_k, threshold=args.threshold,
    )
    summary = {
        "centroids_path": str(centroids_path),
        "approved_clusters": len(centroids),
        "threads_changed": len(changes),
        "changes": [
            {"chat_id": c, "thread_id": t, "tunnel_topics": tt}
            for c, t, tt in changes
        ],
    }
    if args.dry_run:
        summary["dry_run"] = True
        print(json.dumps(summary, indent=2))
        return 0

    if changes and not storage.save(data):
        print("ERROR: resolve-topics succeeded in memory but save failed",
              file=sys.stderr)
        return 2

    print(json.dumps(summary, indent=2))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(
        level=os.environ.get("TB_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    parser = _build_argparser()
    args = parser.parse_args(argv)
    if args.cmd == "archive":
        return _cli_archive(args)
    if args.cmd == "suggest-merges":
        return _cli_merge(args)
    if args.cmd == "summary":
        return _cli_summary(args)
    if args.cmd == "resolve-topics":
        return _cli_resolve_topics(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
