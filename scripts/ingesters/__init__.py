"""Phase 3 §3.2-3.5 — shared types + helpers for archive ingesters.

Every ingester emits ChunkDraft instances. The CLI dispatcher
(scripts/cli/ingest.py) collects drafts, embeds, and inserts via
brain_rag with `dedupe_by="external_id"` for idempotency.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


# ── ChunkDraft — pre-embedding shape produced by ingesters ───────────

@dataclass
class ChunkDraft:
    """Minimal shape every ingester produces. Embedding + DB insertion
    happen later in the pipeline; ingesters stay LLM-call-free.

    Fields map 1:1 to chunks table columns post-Phase-3 migration plus
    the legacy `file_path`/`section`/`content_hash` triple needed for
    insert. The CLI dispatcher computes content_hash + embedding before
    insert.
    """
    # Legacy required fields (from pre-Phase-3 schema)
    file_path: str             # e.g., "telegram://chat42/msg17"
    section: str               # e.g., "msg" or "thread"
    content: str               # the actual message text (post-cleanup)

    # Phase 3 required fields
    kind: str                  # "telegram" | "whatsapp" | "perplexity" | "conversation_turn"
    external_id: str           # source-stable: "<source>:<chat>:<msg_or_offset>"
    source_archive: str        # e.g., "telegram_manju"

    # Phase 3 optional fields (defaults applied at insert time if unset)
    confidentiality: str = "personal"   # "public" | "personal" | "sealed"
    external_ts: Optional[int] = None    # unix seconds
    person_tags: List[str] = field(default_factory=list)
    topic_label: Optional[str] = None    # set by clustering, NULL on first insert

    # Metadata that doesn't go to chunks but useful for ingester logs
    sender_raw: Optional[str] = None     # original sender string before tag normalization
    is_outbound: bool = False             # True iff message was sent by Lokesh (vs received)
    extra: Dict[str, Any] = field(default_factory=dict)  # parser-specific debugging metadata

    def person_tags_json(self) -> str:
        """JSON-encode person_tags for SQLite TEXT column."""
        return json.dumps(self.person_tags, ensure_ascii=False)

    def __post_init__(self) -> None:
        # Invariants enforced at construction so ingesters can't ship malformed
        if not self.kind:
            raise ValueError("ChunkDraft.kind is required")
        if not self.external_id:
            raise ValueError("ChunkDraft.external_id is required (idempotency contract)")
        if self.confidentiality not in ("public", "personal", "sealed"):
            raise ValueError(
                f"ChunkDraft.confidentiality must be public|personal|sealed, "
                f"got {self.confidentiality!r}"
            )


# ── Person-tag normalization ─────────────────────────────────────────

_NON_ALPHANUM = re.compile(r"[^a-z0-9_]+")
_EMOJI = re.compile(
    "["
    "\U0001F600-\U0001F64F"   # emoticons
    "\U0001F300-\U0001F5FF"   # symbols & pictographs
    "\U0001F680-\U0001F6FF"   # transport & map symbols
    "\U0001F1E0-\U0001F1FF"   # flags
    "\U00002600-\U000027BF"   # misc symbols / dingbats
    "‍"                   # ZWJ
    "️"                   # variation selector
    "]+", flags=re.UNICODE,
)


def normalize_person_tag(raw: str) -> str:
    """Reduce a sender label to a stable cross-source person identifier.

    Examples:
        "Manju 💕" → "manju"
        "MJ" → "mj"
        "Lokesh Garg" → "lokesh_garg"
        "+91 98765 43210" → "91_98765_43210"
        "" → ""
    """
    if not raw:
        return ""
    s = _EMOJI.sub("", raw)
    s = s.lower().strip()
    s = _NON_ALPHANUM.sub("_", s).strip("_")
    return s


def normalize_person_tags(raws: Iterable[str]) -> List[str]:
    """Normalize a list of sender labels, dedupe, drop empties.
    Order-preserving."""
    seen = set()
    out: List[str] = []
    for r in raws:
        norm = normalize_person_tag(r)
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out


# ── Slug helper for source_archive ──────────────────────────────────

def slug_for_archive(prefix: str, source: str) -> str:
    """Produce a stable source_archive identifier.

    Examples:
        slug_for_archive("telegram", "Manju 💕") → "telegram_manju"
        slug_for_archive("whatsapp", "Family Group") → "whatsapp_family_group"
    """
    norm = normalize_person_tag(source)
    return f"{prefix}_{norm}" if norm else prefix
