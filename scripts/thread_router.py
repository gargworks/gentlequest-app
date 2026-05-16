"""Auto-routing for multi-thread infrastructure (Phase 2 §2.2).

When a user sends a message, embed it and find the closest active thread
by cosine similarity to thread centroids. Route per threshold bands:

    sim >= 0.75  →  route silently
    0.5 <= sim < 0.75  →  prompt user to confirm
    sim < 0.5  →  create new thread (auto-named)

After each turn, the routed thread's centroid updates as an EMA blend:
    new_centroid = old_centroid * 0.85 + new_emb * 0.15

Embedding source: providers.brain_rag exposes _embed_query (qwen3-
embedding 0.6b via Ollama, 1024-dim). Same model used for RAG, so
thread centroids and RAG document embeddings live in the same space.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Thresholds (spec §2.2) ───────────────────────────────────────────

THRESHOLD_ROUTE = 0.75   # >= → silent route
THRESHOLD_PROMPT = 0.5   # >= → prompt user to confirm; below → new thread

EMA_ALPHA = 0.85         # weight on prior centroid; (1-alpha) on new emb


# ── Cosine + EMA ─────────────────────────────────────────────────────

def cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity in [-1, 1]. Returns 0.0 if either vector empty
    or zero-norm (treated as 'no signal' rather than mathematical NaN)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    dot = sum(a[i] * b[i] for i in range(len(a)))
    return dot / (na * nb)


def update_centroid(
    centroid: List[float],
    new_emb: List[float],
    alpha: float = EMA_ALPHA,
) -> List[float]:
    """EMA blend: alpha * centroid + (1 - alpha) * new_emb.

    Cold start (centroid empty): first message becomes the centroid
    outright. After that, EMA dampens drift.
    """
    if not new_emb:
        return list(centroid)
    if not centroid:
        return list(new_emb)
    if len(centroid) != len(new_emb):
        logger.warning("centroid dim mismatch: %d vs %d; using new_emb",
                       len(centroid), len(new_emb))
        return list(new_emb)
    beta = 1.0 - alpha
    return [centroid[i] * alpha + new_emb[i] * beta for i in range(len(centroid))]


# ── Auto-naming for new threads ──────────────────────────────────────

_NON_SLUG = re.compile(r"[^a-z0-9]+")


def auto_name(text: str, max_chars: int = 30) -> str:
    """Slugify the first message into a thread id. Returns 'untitled' if
    nothing usable remains."""
    if not text:
        return "untitled"
    # Take first sentence-ish chunk
    head = re.split(r"[.\n!?]", text, maxsplit=1)[0][:max_chars * 3]
    slug = _NON_SLUG.sub("_", head.lower()).strip("_")
    slug = slug[:max_chars].rstrip("_")
    return slug or "untitled"


# ── Routing decision ─────────────────────────────────────────────────

class RouteDecision:
    __slots__ = ("action", "thread_id", "candidate_label",
                 "candidate_score", "candidate_id")

    def __init__(
        self,
        action: str,
        thread_id: Optional[str] = None,
        candidate_label: Optional[str] = None,
        candidate_score: float = 0.0,
        candidate_id: Optional[str] = None,
    ):
        # action ∈ {"routed", "prompt_user", "confirmed_new",
        #           "cold_start", "hard_ceiling"}
        self.action = action
        self.thread_id = thread_id
        self.candidate_label = candidate_label
        self.candidate_score = candidate_score
        self.candidate_id = candidate_id

    def __repr__(self) -> str:
        return (f"RouteDecision(action={self.action!r}, "
                f"thread_id={self.thread_id!r}, "
                f"candidate={self.candidate_label!r}@{self.candidate_score:.3f})")


def route_message(
    chat_id: str,
    text: str,
    query_embedding: List[float],
    threads_data: Dict[str, Dict[str, Any]],
    storage,  # ThreadStorage; typed loosely to avoid cyclic import
    threshold_route: float = THRESHOLD_ROUTE,
    threshold_prompt: float = THRESHOLD_PROMPT,
) -> RouteDecision:
    """Pick a thread for this message. Caller is responsible for actually
    switching active_thread_id and persisting — this only decides.

    Returns RouteDecision with one of:
    - action="cold_start", thread_id="inbox": no embeddings yet, fall to inbox
    - action="routed", thread_id=<id>: similarity >= 0.75, route silent
    - action="prompt_user", candidate_id/label/score set: 0.5–0.75, surface to user
    - action="confirmed_new", thread_id=<auto-name>: < 0.5, create new
    - action="hard_ceiling": at hard limit; cannot create new (caller refuses)
    """
    storage.initialize_chat(threads_data, chat_id)
    active = storage.list_active(threads_data, chat_id)

    # Find best-scoring thread among those with non-empty embeddings.
    best: Optional[Tuple[Dict[str, Any], float]] = None
    for thread in active:
        emb = thread.get("embedding") or []
        if not emb:
            continue
        sim = cosine(query_embedding, emb)
        if best is None or sim > best[1]:
            best = (thread, sim)

    # Cold start: no thread has an embedding yet → drop into "inbox"
    if best is None:
        return RouteDecision(action="cold_start", thread_id="inbox")

    thread, sim = best

    if sim >= threshold_route:
        return RouteDecision(
            action="routed",
            thread_id=thread["id"],
            candidate_label=thread.get("label"),
            candidate_score=sim,
            candidate_id=thread["id"],
        )

    if sim >= threshold_prompt:
        return RouteDecision(
            action="prompt_user",
            candidate_label=thread.get("label"),
            candidate_score=sim,
            candidate_id=thread["id"],
        )

    # sim < threshold_prompt → propose new thread (subject to ceiling)
    proposed = auto_name(text)
    # Avoid collision with existing thread id
    existing_ids = set(threads_data.get(chat_id, {}).get("threads", {}).keys())
    base_proposed = proposed
    counter = 2
    while proposed in existing_ids:
        proposed = f"{base_proposed}_{counter}"
        counter += 1

    allowed, reason = storage.can_create_thread(threads_data, chat_id)
    if not allowed and reason == "hard_ceiling":
        return RouteDecision(action="hard_ceiling")
    return RouteDecision(
        action="confirmed_new",
        thread_id=proposed,
        candidate_score=sim,
    )


# ── Embedding helper (thin wrapper around brain_rag's qwen3 model) ───

def embed_text(text: str) -> List[float]:
    """Embed text via providers.brain_rag (qwen3-embedding 0.6b).

    Imported lazily so test envs without Ollama don't blow up at import.
    Returns [] on any failure — caller decides cold-start fallback.
    """
    try:
        from providers import brain_rag  # type: ignore
        emb = brain_rag._embed_query(text)
        if emb is None:
            return []
        return list(emb)
    except Exception as e:
        logger.warning("embed_text failed (%s); returning []", e)
        return []
