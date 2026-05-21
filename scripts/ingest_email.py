#!/usr/bin/env python3
"""Phase 3 §3.5 — Email ingester stub (deferred this phase).

Stub locks the interface contract for Phase 5+ activation. Not blocking
Phase 3 ship.

Implementation paths when activated:
  - Gmail API via existing creds in .brain/config/gmail_creds.json
    (assuming they're still valid)
  - mbox file ingestion (Apple Mail, Thunderbird, Outlook export)

Contract (locked):
  external_id: 'email:<message_id>' (RFC 5322 Message-ID is globally unique)
  source_archive: 'email_<from_normalized>' or 'email_inbox' for incoming
  kind: 'email'
  person_tags: [normalized(from), normalized(to)...]
  external_ts: parsed Date header
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator, Optional

from scripts.ingesters import ChunkDraft


def parse_email_export(
    path: Path,
    *,
    confidentiality: str = "personal",
) -> Iterator[ChunkDraft]:
    raise NotImplementedError(
        "Email ingester deferred this phase. Activate when a usage gap "
        "emerges. Contract locked in this stub's docstring."
    )


def main(argv: Optional[list] = None) -> int:
    print("[ingest_email] DEFERRED. See contract in stub docstring.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
