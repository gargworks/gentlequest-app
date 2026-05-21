#!/usr/bin/env python3
"""Phase 3 §3.2 — Telegram Desktop JSON export ingester.

Parses Telegram Desktop's `result.json` export (Settings → Advanced →
Export Telegram data → JSON) and emits ChunkDraft instances. Idempotent
across re-runs via composite external_id.

Schema variants handled:
  - Telegram Desktop v1.x export: top-level {chats: {list: [...]}}
  - Telegram Desktop v2.x export: top-level {chats: [...]}
  - Single-chat export: top-level chat object directly

Skipped:
  - System messages (e.g., "joined the group", "called you") — type=service
  - Media-only messages with no caption (kind != "message" or empty text)

Preserved:
  - Reply chains (reply_to_message_id stored in extra metadata)
  - Outbound vs inbound classification (Lokesh's user_id = self_id arg)
  - Sender → person_tags normalization

Usage:
    python3 scripts/ingest_telegram.py --path PATH [--dry-run] [--limit N]
    python3 scripts/ingest_telegram.py --path PATH --confidentiality sealed
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.ingesters import (
    ChunkDraft,
    normalize_person_tag,
    slug_for_archive,
)


# ── Self-id heuristics ───────────────────────────────────────────────

# Lokesh's outbound message detection. Telegram exports include
# `from_id` for each message; if it equals the export's owner id (which
# isn't always recorded), we know it's outbound. Fallback: name match.
LOKESH_OUTBOUND_NAMES = {
    name.lower() for name in
    os.environ.get("TB_LOKESH_NAMES", "lokesh,lokesh garg").split(",")
}


def _is_self(from_name: Optional[str], from_id: Optional[str],
             self_id: Optional[str]) -> bool:
    """True if the message was sent by Lokesh (outbound)."""
    if self_id and from_id and str(from_id) == str(self_id):
        return True
    if from_name and from_name.lower().strip() in LOKESH_OUTBOUND_NAMES:
        return True
    return False


# ── Text extraction ──────────────────────────────────────────────────

def _extract_text(msg: Dict[str, Any]) -> str:
    """Telegram messages may have `text` as a string OR a list of
    {type, text} segments (when entities like @mention or bold are
    present). Coalesce to plain text."""
    raw = msg.get("text", "")
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, list):
        parts = []
        for seg in raw:
            if isinstance(seg, str):
                parts.append(seg)
            elif isinstance(seg, dict) and "text" in seg:
                parts.append(seg["text"])
        return "".join(parts).strip()
    return ""


# ── Chat-list normalization (handle schema variants) ─────────────────

def _iter_chats(export: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    """Yield chat dicts regardless of v1 / v2 / single-chat schema."""
    chats = export.get("chats")
    if isinstance(chats, dict):
        # v1.x: chats is {list: [...]}
        sub = chats.get("list") or []
        if isinstance(sub, list):
            yield from sub
            return
    if isinstance(chats, list):
        # v2.x: chats is [...]
        yield from chats
        return
    # Single-chat export (top-level IS a chat)
    if "messages" in export and "name" in export:
        yield export


# ── Main parser ──────────────────────────────────────────────────────

def parse_telegram_export(
    path: Path,
    *,
    self_id: Optional[str] = None,
    confidentiality: str = "personal",
    skip_service: bool = True,
) -> Iterator[ChunkDraft]:
    """Parse a Telegram Desktop JSON export. Yields ChunkDraft per message.

    Args:
        path: result.json or single-chat .json
        self_id: Lokesh's Telegram numeric user_id (if known); enables
                 reliable outbound classification
        confidentiality: "personal" (default), "public", or "sealed"
        skip_service: drop non-message events (default True)
    """
    with path.open("r", encoding="utf-8") as f:
        export = json.load(f)

    for chat in _iter_chats(export):
        chat_id = chat.get("id") or chat.get("chat_id")
        if chat_id is None:
            # Fallback: hash the chat name for stability
            chat_id = abs(hash(chat.get("name", "unknown"))) % (10 ** 12)
        chat_name = chat.get("name") or f"chat_{chat_id}"
        archive_slug = slug_for_archive("telegram", chat_name)

        for msg in chat.get("messages") or []:
            if not isinstance(msg, dict):
                continue
            msg_type = msg.get("type", "message")
            if skip_service and msg_type != "message":
                continue

            text = _extract_text(msg)
            if not text:
                # Media-only with no caption → skip (Phase 3 §3.2 anti-corner trap
                # says preserve media-with-caption; pure media is dropped to keep
                # the archive signal-dense)
                continue

            msg_id = msg.get("id")
            if msg_id is None:
                continue
            external_id = f"telegram:{chat_id}:{msg_id}"

            from_name = msg.get("from") or msg.get("actor")
            from_id = msg.get("from_id") or msg.get("actor_id")
            sender_raw = from_name or "unknown"
            person_tags = []
            sender_norm = normalize_person_tag(sender_raw)
            if sender_norm:
                person_tags.append(sender_norm)
            # Always tag chat-level person too (e.g., 1-1 chat with Manju
            # adds 'manju' even on Lokesh's outbound messages)
            chat_norm = normalize_person_tag(chat_name)
            if chat_norm and chat_norm not in person_tags:
                person_tags.append(chat_norm)

            ts = msg.get("date_unixtime") or msg.get("date_unix") or 0
            try:
                ts = int(ts)
            except (TypeError, ValueError):
                ts = 0

            extra: Dict[str, Any] = {}
            if "reply_to_message_id" in msg:
                extra["reply_to"] = f"telegram:{chat_id}:{msg['reply_to_message_id']}"
            if "forwarded_from" in msg:
                extra["forwarded_from"] = msg["forwarded_from"]

            yield ChunkDraft(
                file_path=f"telegram://{archive_slug}/{msg_id}",
                section="msg",
                content=text,
                kind="telegram",
                external_id=external_id,
                source_archive=archive_slug,
                confidentiality=confidentiality,
                external_ts=ts,
                person_tags=person_tags,
                sender_raw=sender_raw,
                is_outbound=_is_self(from_name, from_id, self_id),
                extra=extra,
            )


# ── CLI ──────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True,
                        help="path to Telegram export (result.json)")
    parser.add_argument("--self-id",
                        help="Lokesh's Telegram numeric user_id (optional, "
                             "improves outbound classification)")
    parser.add_argument("--confidentiality",
                        choices=("public", "personal", "sealed"),
                        default="personal",
                        help="confidentiality flag for all parsed chunks "
                             "(default: personal)")
    parser.add_argument("--limit", type=int,
                        help="parse only first N messages (for smoke testing)")
    parser.add_argument("--dry-run", action="store_true",
                        help="report counts; do not insert into rag_index.db")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.exists():
        print(f"[ingest_telegram] path not found: {path}", file=sys.stderr)
        return 2

    drafts: List[ChunkDraft] = []
    by_archive: Dict[str, int] = {}
    by_kind: Dict[str, int] = {"outbound": 0, "inbound": 0}
    for draft in parse_telegram_export(
        path, self_id=args.self_id,
        confidentiality=args.confidentiality,
    ):
        drafts.append(draft)
        by_archive[draft.source_archive] = by_archive.get(draft.source_archive, 0) + 1
        by_kind["outbound" if draft.is_outbound else "inbound"] += 1
        if args.limit and len(drafts) >= args.limit:
            break

    print(f"[ingest_telegram] parsed {len(drafts)} messages from {path}")
    print(f"  outbound: {by_kind['outbound']}, inbound: {by_kind['inbound']}")
    print(f"  archives: {len(by_archive)}")
    for archive, n in sorted(by_archive.items(), key=lambda x: -x[1])[:10]:
        print(f"    {archive}: {n}")

    if args.dry_run:
        print("[ingest_telegram] dry-run — no insert performed")
        return 0

    # Real insert path lives in scripts/cli/ingest.py (M1.6) — for now,
    # standalone CLI just reports what it found.
    print("[ingest_telegram] (insert path implemented in scripts/cli/ingest.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
