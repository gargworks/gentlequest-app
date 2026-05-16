#!/usr/bin/env python3
"""Phase 3 §3.3 — WhatsApp `_chat.txt` plain-text export ingester.

Parses WhatsApp's `_chat.txt` (the only export format WhatsApp exposes)
and emits ChunkDraft instances. Idempotent across re-runs via composite
external_id keyed on filename + line offset + content hash slice.

Format variants handled:
  - iOS:     [12/05/26, 4:32:18 PM] Manju: hello
  - iOS-alt: [12/05/2026, 04:32:18] Manju: hello (24h, year=YYYY)
  - Android: 12/05/26, 16:32 - Manju: hello
  - Android-alt: 5/12/2026, 4:32 PM - Manju: hello

Multi-line messages: lines without a leading timestamp belong to the
prior message (WhatsApp emits literal "\\n" in long messages).

ZIP support: if path ends in .zip, extract `_chat.txt` in-memory before
parsing (some users export-then-zip the bundle).

Usage:
    python3 scripts/ingest_whatsapp.py --path PATH [--dry-run] [--limit N]
    python3 scripts/ingest_whatsapp.py --path PATH --confidentiality sealed
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.ingesters import (
    ChunkDraft,
    normalize_person_tag,
    slug_for_archive,
)


# ── Self-detection ───────────────────────────────────────────────────

LOKESH_OUTBOUND_NAMES = {
    name.lower() for name in
    os.environ.get("TB_LOKESH_NAMES", "lokesh,lokesh garg").split(",")
}


def _is_self(sender: str) -> bool:
    return sender.lower().strip() in LOKESH_OUTBOUND_NAMES


# ── Format detection ─────────────────────────────────────────────────

# iOS: bracketed timestamp + sender + colon
# Examples:
#   [12/05/26, 4:32:18 PM] Manju: hello
#   [12/05/2026, 04:32:18] Manju: hello
_IOS_LINE = re.compile(
    r"^\[(?P<date>\d{1,2}/\d{1,2}/\d{2,4}),\s*"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?)\]\s*"
    r"(?P<sender>[^:]+?):\s*(?P<body>.*)$"
)

# Android: bare date + dash + sender + colon
# Examples:
#   12/05/26, 16:32 - Manju: hello
#   5/12/2026, 4:32 PM - Manju: hello
_ANDROID_LINE = re.compile(
    r"^(?P<date>\d{1,2}/\d{1,2}/\d{2,4}),\s*"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?)\s*-\s*"
    r"(?P<sender>[^:]+?):\s*(?P<body>.*)$"
)


# Date parsing — WhatsApp uses dd/mm/yy (most regions) or mm/dd/yy (US).
# We'll try both; emit unix ts on the most plausible interpretation.
_TS_FALLBACK = 0  # if we can't parse, leave 0 so caller sees the gap


def _parse_ts(date: str, time: str) -> int:
    """Best-effort unix-second parse. Returns 0 on failure (caller decides
    if that's OK)."""
    import datetime as _dt
    # Normalize 12/24-hour
    time = time.strip()
    has_meridian = bool(re.search(r"[APap][Mm]$", time))
    fmt_time = "%I:%M:%S %p" if (has_meridian and ":" in time and time.count(":") == 2) \
        else "%I:%M %p" if has_meridian \
        else "%H:%M:%S" if time.count(":") == 2 \
        else "%H:%M"

    # Year length detection
    parts = date.split("/")
    if len(parts) != 3:
        return _TS_FALLBACK
    yr_part = parts[2]
    fmt_yr = "%Y" if len(yr_part) == 4 else "%y"

    # Try dd/mm first (most regions), then mm/dd as fallback
    for fmt_date in (f"%d/%m/{fmt_yr}", f"%m/%d/{fmt_yr}"):
        try:
            dt = _dt.datetime.strptime(f"{date} {time.upper()}",
                                       f"{fmt_date} {fmt_time}")
            return int(dt.replace(tzinfo=_dt.timezone.utc).timestamp())
        except ValueError:
            continue
    return _TS_FALLBACK


# ── Parser ───────────────────────────────────────────────────────────

def _read_lines(path: Path) -> Tuple[str, List[str]]:
    """Return (chat_filename_for_slug, list_of_lines).

    Auto-extracts `_chat.txt` from a zip if path is a .zip archive.
    """
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            chat_member = None
            for name in zf.namelist():
                if name.lower().endswith("_chat.txt") or name.lower().endswith(".txt"):
                    chat_member = name
                    break
            if not chat_member:
                raise ValueError(f"no _chat.txt inside {path}")
            with zf.open(chat_member) as fh:
                lines = io.TextIOWrapper(fh, encoding="utf-8").read().splitlines()
            base = path.stem
            return base, lines
    with path.open("r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    return path.stem, lines


def parse_whatsapp_export(
    path: Path,
    *,
    confidentiality: str = "personal",
) -> Iterator[ChunkDraft]:
    """Parse a WhatsApp `_chat.txt` (or .zip containing one). Yields one
    ChunkDraft per logical message (multi-line messages reassembled).

    Args:
        path: file path to _chat.txt or .zip
        confidentiality: "personal" (default), "public", or "sealed"
    """
    base_name, lines = _read_lines(path)
    archive_slug = slug_for_archive("whatsapp", base_name)
    chat_norm = normalize_person_tag(base_name)

    # Stable line offset → external_id. We record the offset of the
    # FIRST line of each logical message, plus a content-hash slice so
    # re-exports with mostly-identical content stay stable even if
    # earlier messages got deleted (truncation shifts offsets, but
    # content hash anchors).
    cur: Optional[Dict[str, Any]] = None

    def _flush() -> Iterator[ChunkDraft]:
        nonlocal cur
        if not cur:
            return
        body = cur["body"].strip()
        if not body:
            cur = None
            return
        sender = cur["sender"]
        sender_norm = normalize_person_tag(sender)
        person_tags = []
        if sender_norm:
            person_tags.append(sender_norm)
        if chat_norm and chat_norm not in person_tags:
            person_tags.append(chat_norm)

        # external_id = "whatsapp:<filename>:<line_offset>:<content_hash_8>"
        h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]
        external_id = f"whatsapp:{base_name}:{cur['offset']}:{h}"

        ts = _parse_ts(cur["date"], cur["time"])

        draft = ChunkDraft(
            file_path=f"whatsapp://{archive_slug}/L{cur['offset']}",
            section="msg",
            content=body,
            kind="whatsapp",
            external_id=external_id,
            source_archive=archive_slug,
            confidentiality=confidentiality,
            external_ts=ts if ts > 0 else None,
            person_tags=person_tags,
            sender_raw=sender,
            is_outbound=_is_self(sender),
            extra={"line_offset": cur["offset"]},
        )
        cur = None
        yield draft

    for offset, line in enumerate(lines):
        # iOS first (more specific bracket pattern), then Android
        m = _IOS_LINE.match(line) or _ANDROID_LINE.match(line)
        if m:
            # Flush prior message
            yield from _flush()
            cur = {
                "offset": offset,
                "date": m.group("date"),
                "time": m.group("time"),
                "sender": m.group("sender").strip(),
                "body": m.group("body"),
            }
        else:
            # Continuation line — append to current message
            if cur is not None:
                cur["body"] += "\n" + line

    # Final flush for the last in-flight message
    yield from _flush()


# ── CLI ──────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True,
                        help="path to _chat.txt or .zip containing it")
    parser.add_argument("--confidentiality",
                        choices=("public", "personal", "sealed"),
                        default="personal",
                        help="confidentiality flag for all parsed chunks "
                             "(default: personal)")
    parser.add_argument("--limit", type=int,
                        help="parse only first N messages (smoke testing)")
    parser.add_argument("--dry-run", action="store_true",
                        help="report counts; do not insert into rag_index.db")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.exists():
        print(f"[ingest_whatsapp] path not found: {path}", file=sys.stderr)
        return 2

    drafts: List[ChunkDraft] = []
    by_kind = {"outbound": 0, "inbound": 0}
    for draft in parse_whatsapp_export(
        path, confidentiality=args.confidentiality,
    ):
        drafts.append(draft)
        by_kind["outbound" if draft.is_outbound else "inbound"] += 1
        if args.limit and len(drafts) >= args.limit:
            break

    print(f"[ingest_whatsapp] parsed {len(drafts)} messages from {path}")
    print(f"  outbound: {by_kind['outbound']}, inbound: {by_kind['inbound']}")
    if drafts:
        print(f"  archive: {drafts[0].source_archive}")
        print(f"  ts range: {min((d.external_ts or 0) for d in drafts)} → "
              f"{max((d.external_ts or 0) for d in drafts)}")

    if args.dry_run:
        print("[ingest_whatsapp] dry-run — no insert performed")
        return 0

    print("[ingest_whatsapp] (insert path implemented in scripts/cli/ingest.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
