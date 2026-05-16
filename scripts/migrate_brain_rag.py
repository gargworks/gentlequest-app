#!/usr/bin/env python3
"""Phase 3 §3.1 — idempotent migration runner for chunks table extensions.

Adds the 7 archive-related columns (kind, topic_label, confidentiality,
person_tags, external_id, source_archive, external_ts) plus indices.
Backfills sensible defaults onto existing pre-Phase-3 chunks so they
keep working with the new query paths.

Re-running is safe — all column adds are gated by PRAGMA table_info
checks; backfill UPDATEs are scoped with WHERE clauses that no-op on
already-migrated rows.

Usage:
    python3 scripts/migrate_brain_rag.py                       # run on default db
    python3 scripts/migrate_brain_rag.py --db /path/to/db      # custom path
    python3 scripts/migrate_brain_rag.py --dry-run             # report what would change
    python3 scripts/migrate_brain_rag.py --verify              # check schema only
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from typing import Iterable, List, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = Path(os.environ.get(
    "TB_RAG_DB_PATH",
    str(ROOT / ".brain" / "rag_index.db"),
))


# ── Column definitions (column name → ALTER TABLE clause) ────────────

PHASE3_COLUMNS = [
    ("kind",            "ADD COLUMN kind TEXT"),
    ("topic_label",     "ADD COLUMN topic_label TEXT"),
    ("confidentiality", "ADD COLUMN confidentiality TEXT"),
    ("person_tags",     "ADD COLUMN person_tags TEXT"),
    ("external_id",     "ADD COLUMN external_id TEXT"),
    ("source_archive",  "ADD COLUMN source_archive TEXT"),
    ("external_ts",     "ADD COLUMN external_ts INTEGER"),
]

PHASE3_INDICES = [
    ("idx_chunks_topic",           "topic_label"),
    ("idx_chunks_kind",            "kind"),
    ("idx_chunks_external_id",     "external_id"),
    ("idx_chunks_external_ts",     "external_ts"),
    ("idx_chunks_confidentiality", "confidentiality"),
]


# ── Helpers ──────────────────────────────────────────────────────────

def _existing_columns(conn: sqlite3.Connection) -> Set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_info(chunks)").fetchall()}


def _existing_indices(conn: sqlite3.Connection) -> Set[str]:
    return {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()}


def _missing_columns(conn: sqlite3.Connection) -> List[Tuple[str, str]]:
    have = _existing_columns(conn)
    return [(name, alter) for name, alter in PHASE3_COLUMNS if name not in have]


def _missing_indices(conn: sqlite3.Connection) -> List[Tuple[str, str]]:
    have = _existing_indices(conn)
    return [(name, col) for name, col in PHASE3_INDICES if name not in have]


# ── Migration steps ──────────────────────────────────────────────────

def add_columns(conn: sqlite3.Connection, dry_run: bool = False) -> List[str]:
    actions = []
    for name, alter in _missing_columns(conn):
        sql = f"ALTER TABLE chunks {alter}"
        actions.append(sql)
        if not dry_run:
            conn.execute(sql)
    if not dry_run and actions:
        conn.commit()
    return actions


def add_indices(conn: sqlite3.Connection, dry_run: bool = False) -> List[str]:
    actions = []
    for name, col in _missing_indices(conn):
        sql = f"CREATE INDEX {name} ON chunks({col})"
        actions.append(sql)
        if not dry_run:
            conn.execute(sql)
    if not dry_run and actions:
        conn.commit()
    return actions


def backfill_defaults(conn: sqlite3.Connection, dry_run: bool = False) -> List[Tuple[str, int]]:
    """Backfill sensible defaults onto pre-Phase-3 chunks.

    Heuristics:
    - kind='brain' for any chunk with NULL kind (all pre-Phase-3 inserts
      came from .brain/ corpus indexing or related code paths).
    - confidentiality='public' for kind='brain' chunks under code/docs
      paths (mcp-server-nucleus/, providers/, scripts/, docs/, .brain/agi/,
      .brain/config/, etc.) — these are technical/public.
    - confidentiality='personal' for everything else (default safer).
    - person_tags='[]' for NULL person_tags.

    Dry-run + pre-migration db: returns ("(skipped — columns not yet
    added)", 0) since the UPDATE statements reference columns that
    don't exist yet. Run without --dry-run to perform the migration in
    one pass (add_columns + add_indices + backfill_defaults all share
    the same connection and run in the right order).
    """
    actions: List[Tuple[str, int]] = []

    # In dry-run mode, only simulate backfill if the columns already
    # exist (i.e., a partial migration was previously applied). Otherwise
    # the UPDATE statements would error on non-existent columns.
    if dry_run:
        have = _existing_columns(conn)
        needed = {name for name, _ in PHASE3_COLUMNS}
        if not needed.issubset(have):
            return [("(dry-run) backfill skipped — columns not yet added", 0)]

    # 1) kind='brain' for NULL kind
    cur = conn.execute(
        "UPDATE chunks SET kind = 'brain' WHERE kind IS NULL"
    )
    actions.append(("backfill kind='brain' for NULL kind", cur.rowcount))

    # 2) public for code/docs paths under brain
    public_prefixes = (
        "mcp-server-nucleus/",
        "providers/",
        "scripts/",
        "docs/",
        "tests/",
        ".brain/agi/",
        ".brain/config/",
        ".brain/research/",
        ".brain/audits/",
        ".brain/charters/",
        ".brain/dialect/",
        ".brain/guides/",
        ".brain/heuristics/",
        ".brain/rituals/",
        ".brain/specs/",
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
    )
    public_clause = " OR ".join(
        ["file_path LIKE ?"] * len(public_prefixes)
    )
    public_args = tuple(f"{p}%" for p in public_prefixes)
    cur = conn.execute(
        f"UPDATE chunks SET confidentiality = 'public' "
        f"WHERE confidentiality IS NULL AND kind = 'brain' "
        f"AND ({public_clause})",
        public_args,
    )
    actions.append(("backfill confidentiality='public' for code/docs", cur.rowcount))

    # 3) personal for the rest with NULL confidentiality
    cur = conn.execute(
        "UPDATE chunks SET confidentiality = 'personal' "
        "WHERE confidentiality IS NULL"
    )
    actions.append(("backfill confidentiality='personal' for remaining", cur.rowcount))

    # 4) person_tags = '[]' for NULL
    cur = conn.execute(
        "UPDATE chunks SET person_tags = '[]' WHERE person_tags IS NULL"
    )
    actions.append(("backfill person_tags='[]' for NULL", cur.rowcount))

    if dry_run:
        # Roll back the inspection updates so dry-run is truly read-only
        conn.rollback()
    else:
        conn.commit()
    return actions


def verify_schema(conn: sqlite3.Connection) -> Tuple[bool, List[str]]:
    """Return (ok, issues). ok=True iff every Phase 3 column + index present."""
    issues = []
    have_cols = _existing_columns(conn)
    for name, _ in PHASE3_COLUMNS:
        if name not in have_cols:
            issues.append(f"missing column: chunks.{name}")
    have_idx = _existing_indices(conn)
    for name, _ in PHASE3_INDICES:
        if name not in have_idx:
            issues.append(f"missing index: {name}")
    return (not issues), issues


# ── CLI ──────────────────────────────────────────────────────────────

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB),
                        help="path to rag_index.db (default: %(default)s)")
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change; no writes")
    parser.add_argument("--verify", action="store_true",
                        help="check schema only; exit non-zero if missing fields")
    parser.add_argument("--skip-backfill", action="store_true",
                        help="add columns + indices but skip default backfill")
    args = parser.parse_args(argv)

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"[migrate] db not found: {db_path}", file=sys.stderr)
        return 2

    conn = sqlite3.connect(str(db_path))
    try:
        if args.verify:
            ok, issues = verify_schema(conn)
            if ok:
                print(f"[migrate] schema OK at {db_path}")
                return 0
            print(f"[migrate] schema INCOMPLETE at {db_path}")
            for issue in issues:
                print(f"  - {issue}")
            return 1

        col_actions = add_columns(conn, dry_run=args.dry_run)
        idx_actions = add_indices(conn, dry_run=args.dry_run)

        backfill_actions: List[Tuple[str, int]] = []
        if not args.skip_backfill:
            backfill_actions = backfill_defaults(conn, dry_run=args.dry_run)

        # Report
        prefix = "[dry-run] would" if args.dry_run else "[migrate]"
        if not col_actions and not idx_actions:
            print(f"{prefix} no schema changes needed")
        for sql in col_actions:
            print(f"{prefix}: {sql}")
        for sql in idx_actions:
            print(f"{prefix}: {sql}")
        for label, n in backfill_actions:
            print(f"{prefix}: {label}  → {n} rows")

        if not args.dry_run:
            ok, issues = verify_schema(conn)
            if not ok:
                print("[migrate] verify FAILED:", file=sys.stderr)
                for issue in issues:
                    print(f"  - {issue}", file=sys.stderr)
                return 3
            print(f"[migrate] OK — {db_path} ready for Phase 3 ingestion")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
