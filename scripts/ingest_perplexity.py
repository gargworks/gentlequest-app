#!/usr/bin/env python3
"""Phase 3 §3.4 — Perplexity ingester stub.

Deferred per Q5 (resolved 2026-05-09 in `10_open_questions.md` —
recommendation: skip for Phase 3, revisit if a usage gap emerges).

This stub locks the interface contract so future implementation slots
in cleanly:

    from scripts.ingesters import ChunkDraft
    def parse_perplexity_export(path, *, confidentiality="personal") \
            -> Iterator[ChunkDraft]:
        ...

If Lokesh reverses Q5 during Phase 3, the implementation paths are:
  (a) Chrome extension scraper → JSON dump → this parser
  (b) Manual URL list → fetch + parse
  (c) Official export when Perplexity ships one
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator, Optional

from scripts.ingesters import ChunkDraft


def parse_perplexity_export(
    path: Path,
    *,
    confidentiality: str = "personal",
) -> Iterator[ChunkDraft]:
    """Stub — raises NotImplementedError until Q5 reversed.

    Contract (locked):
    - external_id format: 'perplexity:<thread_id>:<message_id>'
    - source_archive: 'perplexity_<thread_slug>'
    - kind: 'perplexity'
    - person_tags: ['perplexity'] for AI responses, ['lokesh'] for prompts
    """
    raise NotImplementedError(
        "Perplexity ingester deferred per Q5 "
        "(see docs/tb_personal_ai/10_open_questions.md). "
        "Reverse Q5 first to unlock implementation."
    )


def main(argv: Optional[list] = None) -> int:
    print(
        "[ingest_perplexity] DEFERRED per Q5. To activate: \n"
        "  1) reverse Q5 in docs/tb_personal_ai/10_open_questions.md\n"
        "  2) implement parse_perplexity_export() per the locked contract\n"
        "  3) wire into scripts/cli/ingest.py",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
