#!/usr/bin/env python3
"""Phase 3 §3.5 — Apple Notes ingester stub (deferred this phase).

Stub locks the interface contract for Phase 5+ activation.

Implementation path when activated:
  - Apple Notes SQLite at ~/Library/Group Containers/group.com.apple.notes/
    NoteStore.sqlite — gzip-compressed body fields + zfolder + ZNOTE schema
  - One ChunkDraft per note (chunk by paragraph or section if note is long)

Contract (locked):
  external_id: 'notes:<note_uuid>:<chunk_idx>'
  source_archive: 'notes_<folder_slug>'
  kind: 'notes'
  external_ts: ZCREATIONDATE1 from NoteStore (Apple epoch + 978307200)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator, Optional

from scripts.ingesters import ChunkDraft


def parse_notes_export(
    path: Path,
    *,
    confidentiality: str = "personal",
) -> Iterator[ChunkDraft]:
    raise NotImplementedError(
        "Apple Notes ingester deferred this phase. Activate when a usage "
        "gap emerges. Contract locked in this stub's docstring."
    )


def main(argv: Optional[list] = None) -> int:
    print("[ingest_notes] DEFERRED. See contract in stub docstring.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
