#!/usr/bin/env python3
"""Phase 3 §3.7 — one-shot backfill of shadow_log.jsonl into RAG.

Phase 1 wrote `.brain/{training,driver}/shadow_log.jsonl` per turn.
Phase 4 wants those as RAG-searchable conversation chunks (filtered by
thread tunnel_topics). This script reads the jsonl(s) and emits
ChunkDraft per turn with `kind="conversation_turn"`, suitable for
`scripts/cli/ingest.py` insert path.

Idempotent via composite external_id keyed on (ts, session_id, role).

Usage:
    python3 scripts/backfill_conversation_rag.py [--dry-run] [--limit N]
    python3 scripts/backfill_conversation_rag.py --paths PATH1,PATH2,...

Default scans both .brain/training/shadow_log.jsonl and
.brain/driver/shadow_log.jsonl.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterator, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.ingesters import ChunkDraft, slug_for_archive

DEFAULT_PATHS = [
    Path(".brain/training/shadow_log.jsonl"),
    Path(".brain/driver/shadow_log.jsonl"),
]


def _resolve_session_surface(session_id: str) -> str:
    """Map session_id prefix → source_archive name.

    tg:7575125475      → conversation_telegram
    repl-1700000000    → conversation_repl
    tg:7575125475:thread_id → conversation_telegram
    anon-abc123        → conversation_anon       (Phase 1 anon sessions)
    bot:cli-...        → conversation_cli
    Anything else      → conversation_other
    """
    if not session_id:
        return "conversation_other"
    # First, isolate the leading token before any ":" (Phase 2 thread
    # suffix) or "-" (Phase 1 anon-uuid format)
    head = session_id.split(":", 1)[0]
    head = head.split("-", 1)[0].lower()
    if head in ("tg", "telegram"):
        return "conversation_telegram"
    if head == "repl":
        return "conversation_repl"
    if head in ("bot", "cli"):
        return "conversation_cli"
    if head == "anon":
        return "conversation_anon"
    return f"conversation_{head}" if head.isidentifier() else "conversation_other"


def _emit_drafts_from_record(rec: dict, line_no: int) -> Iterator[ChunkDraft]:
    """One shadow_log entry → 1 user chunk + 1 response chunk.

    We split into two chunks (user + response) so retrieval can find
    just the question OR just the answer rather than always coupling.
    Phase 4 may want to pair them; that's a query-time concern.
    """
    ts = rec.get("ts")
    if isinstance(ts, str):
        # iso8601 → unix
        try:
            from datetime import datetime
            ts = int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
        except (TypeError, ValueError):
            ts = None
    if isinstance(ts, float):
        ts = int(ts)

    session_id = rec.get("session_id") or "anon"
    archive_slug = _resolve_session_surface(session_id)

    query = (rec.get("query") or "").strip()
    response = (rec.get("response") or "").strip()

    base_id = f"shadow:{ts or line_no}:{session_id}"

    if query:
        yield ChunkDraft(
            file_path=f"shadow://{archive_slug}/{ts or line_no}/user",
            section="user",
            content=query,
            kind="conversation_turn",
            external_id=f"{base_id}:user",
            source_archive=archive_slug,
            confidentiality="personal",
            external_ts=ts,
            person_tags=["lokesh"],
            sender_raw="lokesh",
            is_outbound=True,
            extra={"role": "user", "session_id": session_id},
        )
    if response:
        yield ChunkDraft(
            file_path=f"shadow://{archive_slug}/{ts or line_no}/response",
            section="response",
            content=response,
            kind="conversation_turn",
            external_id=f"{base_id}:response",
            source_archive=archive_slug,
            confidentiality="personal",
            external_ts=ts,
            person_tags=["tb"],
            sender_raw="tb",
            is_outbound=False,
            extra={
                "role": "tb",
                "session_id": session_id,
                "model": rec.get("model") or rec.get("model_inner"),
            },
        )


def parse_shadow_log(path: Path) -> Iterator[ChunkDraft]:
    """Yield ChunkDraft per shadow_log turn (1 user + 1 response per row).

    Skips malformed lines silently — shadow_log writers are best-effort
    and a single bad line shouldn't poison the backfill.
    """
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            yield from _emit_drafts_from_record(rec, line_no)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paths", default=None,
        help="comma-separated paths to shadow_log.jsonl files. "
             "Default scans both .brain/training and .brain/driver."
    )
    parser.add_argument("--limit", type=int,
                        help="parse only first N drafts (smoke test)")
    parser.add_argument("--dry-run", action="store_true",
                        help="report counts; do not write")
    args = parser.parse_args(argv)

    if args.paths:
        paths = [Path(p) for p in args.paths.split(",") if p.strip()]
    else:
        paths = DEFAULT_PATHS

    drafts: List[ChunkDraft] = []
    by_archive: dict[str, int] = {}
    for path in paths:
        if not path.exists():
            print(f"[backfill] skip (not found): {path}", file=sys.stderr)
            continue
        for d in parse_shadow_log(path):
            drafts.append(d)
            by_archive[d.source_archive] = by_archive.get(d.source_archive, 0) + 1
            if args.limit and len(drafts) >= args.limit:
                break
        if args.limit and len(drafts) >= args.limit:
            break

    print(f"[backfill] parsed {len(drafts)} chunks from "
          f"{sum(1 for p in paths if p.exists())} log file(s)")
    for archive, n in sorted(by_archive.items(), key=lambda x: -x[1]):
        print(f"  {archive}: {n}")

    if args.dry_run:
        print("[backfill] dry-run — no insert performed")
        return 0
    print("[backfill] (insert path implemented in scripts/cli/ingest.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
