#!/usr/bin/env python3
"""Phase 3 §3.6 — uniform CLI dispatcher for archive ingestion.

Single entry point that routes to the right parser, embeds drafts, and
inserts into rag_index.db with `dedupe_by="external_id"` (idempotency
contract from §3.6).

Usage:
    python -m scripts.cli.ingest telegram --path PATH [--dry-run] [--limit N]
    python -m scripts.cli.ingest whatsapp --path PATH [--confidentiality FLAG]
    python -m scripts.cli.ingest conversation [--paths PATH1,PATH2]
    python -m scripts.cli.ingest --help

The CLI writes to the rag_index.db at NUCLEUS_BRAIN_PATH (default
~/ai-mvp-backend/.brain/rag_index.db). Running against a fresh DB
requires the Phase 3 migration to be applied first:

    python3 scripts/migrate_brain_rag.py

Dry-run skips both embedding (cheap when batch is large) and DB writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import struct
import sys
import time
from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.ingesters import ChunkDraft

# Lazy import each ingester so a missing dependency in one path doesn't
# break the whole CLI surface (e.g., zipfile only needed for whatsapp).
INGESTERS: Dict[str, Tuple[str, str]] = {
    "telegram":     ("scripts.ingest_telegram",      "parse_telegram_export"),
    "whatsapp":     ("scripts.ingest_whatsapp",      "parse_whatsapp_export"),
    "conversation": ("scripts.backfill_conversation_rag", "parse_shadow_log"),
    "perplexity":   ("scripts.ingest_perplexity",    "parse_perplexity_export"),
    "email":        ("scripts.ingest_email",         "parse_email_export"),
    "notes":        ("scripts.ingest_notes",         "parse_notes_export"),
}


DEFAULT_BRAIN = Path(os.environ.get(
    "NUCLEUS_BRAIN_PATH",
    str(ROOT / ".brain"),
))
DEFAULT_DB = DEFAULT_BRAIN / "rag_index.db"


# ── Helpers ──────────────────────────────────────────────────────────

def _content_hash(content: str, external_id: str) -> str:
    """Stable content hash. Phase 1 chunks used sha256(content + path);
    archive chunks use sha256(external_id) so re-export with whitespace
    edits doesn't change the row identity (external_id is the contract,
    not content)."""
    return hashlib.sha256(external_id.encode("utf-8")).hexdigest()


def _existing_external_ids(conn: sqlite3.Connection,
                           external_ids: Iterable[str]) -> set:
    """Return the subset of provided external_ids already in chunks.
    Used for dedupe_by='external_id' before insert."""
    ids = list(external_ids)
    if not ids:
        return set()
    # SQLite bound-param limit is 999 default; chunk the lookup
    out = set()
    for i in range(0, len(ids), 500):
        batch = ids[i:i + 500]
        placeholders = ",".join("?" * len(batch))
        cur = conn.execute(
            f"SELECT external_id FROM chunks WHERE external_id IN ({placeholders})",
            batch,
        )
        for (eid,) in cur.fetchall():
            out.add(eid)
    return out


def _pack_embedding(emb: List[float]) -> bytes:
    """Pack a float embedding into bytes for the BLOB column.
    Matches the Phase 1 schema's expectation: little-endian float32 array."""
    return struct.pack(f"<{len(emb)}f", *emb)


# ── Embed pluggable hook ─────────────────────────────────────────────

# Tests inject a fake embed function; production calls brain_rag._embed.
_EMBED_FN: Optional[Callable[[str], Optional[List[float]]]] = None


def _embed(text: str) -> Optional[List[float]]:
    global _EMBED_FN
    if _EMBED_FN is not None:
        return _EMBED_FN(text)
    from providers import brain_rag
    return brain_rag._embed(text)


def _embed_batch(texts: List[str]) -> List[Optional[List[float]]]:
    """Batch embed via brain_rag._embed_batch when production embedder is in
    play. Test hook (set_embed_fn) loops single-shot for determinism."""
    global _EMBED_FN
    if _EMBED_FN is not None:
        return [_EMBED_FN(t) for t in texts]
    from providers import brain_rag
    return brain_rag._embed_batch(texts)


def set_embed_fn(fn: Optional[Callable[[str], Optional[List[float]]]]) -> None:
    """Test hook. Pass None to reset to production embedder."""
    global _EMBED_FN
    _EMBED_FN = fn


# Batch size for production embedding. Ollama qwen3-embedding:0.6b on
# M-series tolerates 64-256 well; below that we leave throughput on the
# table, above that we risk timeouts on slow chunks. 64 is the safe
# default; bump via TB_EMBED_BATCH_SIZE if Ollama proves robust at higher.
EMBED_BATCH_SIZE = int(os.environ.get("TB_EMBED_BATCH_SIZE", "64"))


# ── Insert pipeline ──────────────────────────────────────────────────

def insert_drafts(
    drafts: Iterable[ChunkDraft],
    db_path: Path = DEFAULT_DB,
    *,
    batch_size: int = 100,
    skip_embedding: bool = False,
) -> Dict[str, int]:
    """Insert drafts with idempotent external_id dedup.

    Returns counts dict:
        {"received": N, "deduped": N, "embedded": N, "inserted": N,
         "embed_failed": N, "errors": N}

    Embedding happens just-in-time per draft; a single failure logs and
    continues (best-effort, mirrors Phase 1 indexing tolerance).
    """
    counts = {
        "received": 0, "deduped": 0, "embedded": 0,
        "inserted": 0, "embed_failed": 0, "errors": 0,
    }

    drafts = list(drafts)
    counts["received"] = len(drafts)
    if not drafts:
        return counts

    conn = sqlite3.connect(str(db_path))
    try:
        external_ids = [d.external_id for d in drafts]
        existing = _existing_external_ids(conn, external_ids)

        to_insert = [d for d in drafts if d.external_id not in existing]
        counts["deduped"] = len(drafts) - len(to_insert)

        for batch_start in range(0, len(to_insert), batch_size):
            batch = to_insert[batch_start:batch_start + batch_size]
            rows = []
            now = time.time()

            # Phase 3 speed: batch embedding via Ollama N-input API.
            # For 64-chunk batches on M-series we see ~30-100x throughput vs
            # sequential _embed. Falls back to single-shot on shape mismatch.
            embeddings: List[Optional[List[float]]] = []
            if not skip_embedding:
                # Sub-batch by EMBED_BATCH_SIZE so very large `batch_size`
                # values don't blow Ollama's per-request budget.
                for sub_start in range(0, len(batch), EMBED_BATCH_SIZE):
                    sub_texts = [d.content for d in
                                 batch[sub_start:sub_start + EMBED_BATCH_SIZE]]
                    embeddings.extend(_embed_batch(sub_texts))

            for idx, d in enumerate(batch):
                if skip_embedding:
                    emb_blob = b""
                else:
                    emb = embeddings[idx]
                    if emb is None:
                        counts["embed_failed"] += 1
                        continue
                    counts["embedded"] += 1
                    emb_blob = _pack_embedding(emb)
                rows.append((
                    d.file_path,
                    d.section,
                    d.content,
                    _content_hash(d.content, d.external_id),
                    emb_blob,
                    len(d.content.split()),
                    now,
                    d.kind,
                    d.confidentiality,
                    d.person_tags_json(),
                    d.external_id,
                    d.source_archive,
                    d.external_ts,
                    d.topic_label,
                ))
            if not rows:
                continue
            try:
                conn.executemany(
                    "INSERT INTO chunks "
                    "(file_path, section, content, content_hash, embedding, "
                    " word_count, indexed_at, kind, confidentiality, "
                    " person_tags, external_id, source_archive, external_ts, "
                    " topic_label) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    rows,
                )
                counts["inserted"] += len(rows)
            except sqlite3.IntegrityError as e:
                # content_hash collision (rare — same external_id parses to
                # same chunk). Skip those rows; not a real error.
                counts["errors"] += 1
                print(f"[ingest] integrity error on batch: {e}",
                      file=sys.stderr)
        conn.commit()
    finally:
        conn.close()
    return counts


# ── CLI ──────────────────────────────────────────────────────────────

def _dispatch(source: str, **kwargs) -> Iterator[ChunkDraft]:
    """Lazy-load the parser for a given source + invoke it."""
    if source not in INGESTERS:
        raise ValueError(f"unknown source: {source!r}. "
                         f"Available: {', '.join(sorted(INGESTERS))}")
    module_name, fn_name = INGESTERS[source]
    import importlib
    mod = importlib.import_module(module_name)
    fn = getattr(mod, fn_name)
    yield from fn(**kwargs)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=sorted(INGESTERS),
                        help="archive type to ingest")
    parser.add_argument("--path", help="path to archive (Telegram JSON, "
                                       "WhatsApp _chat.txt or .zip)")
    parser.add_argument("--paths", help="comma-separated paths (used by "
                                        "conversation source)")
    parser.add_argument("--db", default=str(DEFAULT_DB),
                        help="rag_index.db path (default: %(default)s)")
    parser.add_argument("--confidentiality",
                        choices=("public", "personal", "sealed"),
                        default="personal")
    parser.add_argument("--limit", type=int,
                        help="cap parsed drafts (smoke testing)")
    parser.add_argument("--dry-run", action="store_true",
                        help="report counts; skip embedding + DB writes")
    parser.add_argument("--skip-embedding", action="store_true",
                        help="insert with empty embedding (e.g., when "
                             "embedding will be backfilled later)")
    args = parser.parse_args(argv)

    # Verify migration applied before any insert
    if not args.dry_run:
        from scripts.migrate_brain_rag import verify_schema
        conn = sqlite3.connect(args.db)
        try:
            ok, issues = verify_schema(conn)
        finally:
            conn.close()
        if not ok:
            print(f"[ingest] schema NOT migrated at {args.db}",
                  file=sys.stderr)
            for issue in issues[:5]:
                print(f"  - {issue}", file=sys.stderr)
            print("[ingest] run scripts/migrate_brain_rag.py first",
                  file=sys.stderr)
            return 2

    # Build kwargs for the parser
    parser_kwargs: Dict = {"confidentiality": args.confidentiality}
    if args.source == "conversation":
        if args.paths:
            parser_kwargs = {}  # paths handled inline below
            paths_iter = [Path(p) for p in args.paths.split(",")]
        else:
            from scripts.backfill_conversation_rag import DEFAULT_PATHS
            paths_iter = list(DEFAULT_PATHS)
        # conversation backfill takes path per call
        drafts: List[ChunkDraft] = []
        for p in paths_iter:
            if not p.exists():
                continue
            for d in _dispatch("conversation", path=p):
                drafts.append(d)
                if args.limit and len(drafts) >= args.limit:
                    break
            if args.limit and len(drafts) >= args.limit:
                break
    else:
        if not args.path:
            print(f"[ingest] --path required for source={args.source}",
                  file=sys.stderr)
            return 2
        parser_kwargs["path"] = Path(args.path)
        drafts = []
        for d in _dispatch(args.source, **parser_kwargs):
            drafts.append(d)
            if args.limit and len(drafts) >= args.limit:
                break

    print(f"[ingest] {args.source}: {len(drafts)} drafts ready")
    if args.dry_run:
        print(f"[ingest] dry-run — no embed, no DB write")
        return 0

    counts = insert_drafts(
        drafts, db_path=Path(args.db),
        skip_embedding=args.skip_embedding,
    )
    print(f"[ingest] result: {json.dumps(counts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
