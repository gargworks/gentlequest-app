"""Phase 3 §3.12 — Phase 2 thread → Phase 3 cluster bridge.

Populates `thread.tunnel_topics` (the field Phase 2 schema already
carries — charter #5 compounding hook firing) from cluster centroids
produced by M2.

When a Phase 2 thread accumulates traffic, its centroid drifts toward
its topical home. We compute cosine similarity to every cluster
centroid and assign the top-K labels above threshold as tunnel_topics.
Phase 4 retrieval then filters chunks by those topic labels.

Usage as library (called from scripts/thread_cron.py resolve-topics
subcommand):

    from scripts.thread_topic_resolver import resolve_thread_topics

    topics = resolve_thread_topics(
        thread=thread_dict,
        clusters=cluster_centroids,   # {label: [embedding, n_chunks]}
        top_k=3,
        threshold=0.6,
    )
    thread["tunnel_topics"] = topics
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scripts.thread_router import cosine

logger = logging.getLogger(__name__)


# ── Defaults (env-tunable for dogfood) ───────────────────────────────

DEFAULT_TOP_K = int(os.environ.get("TB_TUNNEL_TOPIC_TOP_K", "3"))
DEFAULT_THRESHOLD = float(os.environ.get("TB_TUNNEL_TOPIC_THRESHOLD", "0.6"))


# ── Cluster centroid file format ─────────────────────────────────────

# Phase 3 §3.8 stores centroids per topic label. File path:
#   .brain/tb_personal_ai/cluster_centroids.json
# Shape:
#   {
#     "manju_messaging": {
#       "embedding": [float, ...],         # 1024-dim qwen3-embedding
#       "n_chunks": int,                   # how many chunks contributed
#       "label_status": "approved" | "proposed",  # only "approved" used here
#     },
#     ...
#   }
# Only "approved" labels are eligible for tunnel routing — proposed
# labels still pending Lokesh sign-off don't shape thread retrieval.

DEFAULT_CENTROIDS_PATH = Path(os.environ.get(
    "TB_CLUSTER_CENTROIDS_PATH",
    str(Path(__file__).resolve().parent.parent
        / ".brain" / "tb_personal_ai" / "cluster_centroids.json"),
))


def load_centroids(
    path: Path = DEFAULT_CENTROIDS_PATH,
    *,
    approved_only: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """Load cluster centroids from disk. Returns empty dict on missing file
    (Phase 3 M2 hasn't run yet — silent no-op so pre-M2 callers can ship)."""
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("centroids: %s parse failed (%s)", path, e)
        return {}
    if not isinstance(raw, dict):
        return {}
    if approved_only:
        return {
            label: data for label, data in raw.items()
            if isinstance(data, dict)
            and data.get("label_status") == "approved"
            and isinstance(data.get("embedding"), list)
            and data["embedding"]
        }
    return {
        label: data for label, data in raw.items()
        if isinstance(data, dict)
        and isinstance(data.get("embedding"), list)
        and data["embedding"]
    }


# ── Public API ───────────────────────────────────────────────────────

def resolve_thread_topics(
    thread: Dict[str, Any],
    clusters: Dict[str, Dict[str, Any]],
    *,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = DEFAULT_THRESHOLD,
) -> List[str]:
    """Compute tunnel_topics for a single thread.

    Returns ordered list (descending similarity) of cluster labels with
    cosine ≥ threshold, capped at top_k. Empty list if thread has no
    centroid yet OR no clusters cross the threshold.

    Pure function — caller mutates thread.tunnel_topics + persists.
    """
    thread_emb = thread.get("embedding") or []
    if not thread_emb:
        return []
    if not clusters:
        return []

    scored: List[Tuple[float, str]] = []
    for label, data in clusters.items():
        cluster_emb = data.get("embedding") or []
        if not cluster_emb:
            continue
        sim = cosine(thread_emb, cluster_emb)
        if sim >= threshold:
            scored.append((sim, label))

    scored.sort(reverse=True)
    return [label for _, label in scored[:top_k]]


def resolve_all_threads(
    threads_data: Dict[str, Dict[str, Any]],
    clusters: Dict[str, Dict[str, Any]],
    *,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = DEFAULT_THRESHOLD,
    only_active: bool = True,
) -> List[Tuple[str, str, List[str]]]:
    """Walk every chat namespace + thread, resolve tunnel_topics for each.

    Returns list of (chat_id, thread_id, new_topics) tuples for threads
    where tunnel_topics changed. Caller persists threads_data.

    only_active: when True (default), skip archived threads — they're
    rarely retrieved against and reclustering shouldn't mutate them.
    """
    changes: List[Tuple[str, str, List[str]]] = []
    for chat_id, chat in threads_data.items():
        threads = chat.get("threads", {}) if isinstance(chat, dict) else {}
        for tid, thread in threads.items():
            if not isinstance(thread, dict):
                continue
            if only_active and thread.get("status") != "active":
                continue
            new_topics = resolve_thread_topics(
                thread, clusters, top_k=top_k, threshold=threshold,
            )
            if new_topics != list(thread.get("tunnel_topics") or []):
                thread["tunnel_topics"] = new_topics
                changes.append((chat_id, tid, new_topics))
    return changes


# ── Centroid persistence helper (used by M2) ─────────────────────────

def write_centroids(
    centroids: Dict[str, Dict[str, Any]],
    path: Path = DEFAULT_CENTROIDS_PATH,
) -> bool:
    """Atomic write of centroid file. Used by clustering pipeline (M2)
    + label CLI (M2). Mirrors AtomicJSONStore pattern from Phase 1
    without taking the dependency (centroids are a different shape +
    aren't keyed/rotated like sessions/threads)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(centroids, f, indent=2, ensure_ascii=False)
        tmp.replace(path)
        return True
    except OSError as e:
        logger.error("centroids: write failed (%s)", e)
        return False
