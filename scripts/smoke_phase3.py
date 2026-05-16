#!/usr/bin/env python3
"""Phase 3 smoke runner — end-to-end archive ingest + clustering + thread bridge.

Each scenario asserts a specific subsystem invariant from the Phase 3
spec. Runs entirely against a temp DB + synthetic data; no Ollama
calls, no Lokesh archives needed. This is the unit-equivalent ship gate
that doesn't require external setup.

Live-fire smoke against real archives + real Ollama embeddings is a
separate manual run after Lokesh's exports land.

Scenarios (per spec §3 acceptance criteria):
  1. schema-live              — migration applies cleanly to fresh db
  2. telegram-roundtrip       — synthetic export → ingest → query
  3. whatsapp-formats         — iOS + Android both parse + dedup
  4. idempotent-reingest      — run telegram ingest 2x → row count unchanged
  5. clustering-coherence     — synthetic 3-topic → 3 clusters, silhouette ≥ 0.5
  6. auto-route               — assign_topic picks correct cluster
  7. thread-bridge            — resolve_thread_topics → expected top-3
  8. confidentiality-default  — archive insert defaults to 'personal'

Usage:
    python3 scripts/smoke_phase3.py
    python3 scripts/smoke_phase3.py --scenarios telegram_roundtrip,clustering_coherence

Exit code: 0 = all pass, non-zero = N failures.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ── Scenario harness ─────────────────────────────────────────────────

class Scenario:
    def __init__(self, name: str):
        self.name = name
        self.passed: List[str] = []
        self.failed: List[str] = []

    def check(self, label: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed.append(label)
            print(f"  ✓ {label}")
        else:
            self.failed.append(f"{label} — {detail}" if detail else label)
            print(f"  ✗ {label}  {detail}")

    @property
    def ok(self) -> bool:
        return not self.failed


# ── Helpers ──────────────────────────────────────────────────────────

def _make_legacy_db(path: Path) -> None:
    """Create a fresh chunks table matching pre-Phase-3 shape."""
    conn = sqlite3.connect(str(path))
    conn.execute("""
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            section TEXT NOT NULL,
            content TEXT NOT NULL,
            content_hash TEXT NOT NULL UNIQUE,
            embedding BLOB NOT NULL,
            word_count INTEGER NOT NULL,
            priority_tier INTEGER NOT NULL DEFAULT 5,
            file_mtime REAL NOT NULL DEFAULT 0,
            indexed_at REAL NOT NULL
        )
    """)
    conn.execute("CREATE INDEX idx_hash ON chunks(content_hash)")
    conn.commit()
    conn.close()


def _migrate(path: Path) -> None:
    from scripts.migrate_brain_rag import (
        add_columns, add_indices, backfill_defaults,
    )
    conn = sqlite3.connect(str(path))
    add_columns(conn)
    add_indices(conn)
    backfill_defaults(conn)
    conn.close()


def _stub_embed(text: str) -> List[float]:
    """Deterministic test embedder — first letter → one-hot in 8 dims."""
    if not text:
        return [0.0] * 8
    ch = text.lower()[0]
    slots = "abcdefghijklmnopqrstuvwxyz"
    idx = slots.find(ch) % 8 if ch in slots else 0
    v = [0.0] * 8
    v[idx] = 1.0
    return v


# ── Scenarios ────────────────────────────────────────────────────────

def scenario_schema_live() -> Scenario:
    s = Scenario("schema-live")
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "rag_index.db"
        _make_legacy_db(db)
        _migrate(db)

        from scripts.migrate_brain_rag import verify_schema
        conn = sqlite3.connect(str(db))
        try:
            ok, issues = verify_schema(conn)
            s.check("verify_schema passes", ok, f"issues: {issues}")

            # Each Phase 3 column is queryable
            for col in ("kind", "topic_label", "confidentiality",
                        "person_tags", "external_id", "source_archive",
                        "external_ts"):
                try:
                    conn.execute(f"SELECT {col} FROM chunks LIMIT 1").fetchall()
                    s.check(f"column {col} queryable", True)
                except sqlite3.OperationalError as e:
                    s.check(f"column {col} queryable", False, str(e))
        finally:
            conn.close()
    return s


def scenario_telegram_roundtrip() -> Scenario:
    s = Scenario("telegram-roundtrip")
    from scripts.cli.ingest import insert_drafts, set_embed_fn
    from scripts.ingest_telegram import parse_telegram_export

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "rag_index.db"
        _make_legacy_db(db)
        _migrate(db)

        # Synthetic export with 3 messages across 2 chats
        export_path = Path(tmp) / "result.json"
        export_path.write_text(json.dumps({
            "chats": [
                {"id": 1, "name": "Manju 💕", "messages": [
                    {"id": 1, "type": "message", "date_unixtime": 1700000000,
                     "from": "Manju", "text": "hi"},
                    {"id": 2, "type": "message", "date_unixtime": 1700000010,
                     "from": "Lokesh", "text": "hello back"},
                ]},
                {"id": 2, "name": "Work", "messages": [
                    {"id": 100, "type": "message", "date_unixtime": 1700001000,
                     "from": "Alice", "text": "agenda?"},
                ]},
            ],
        }), encoding="utf-8")

        drafts = list(parse_telegram_export(export_path))
        s.check("3 messages parsed", len(drafts) == 3,
                f"got {len(drafts)}")

        set_embed_fn(_stub_embed)
        try:
            counts = insert_drafts(drafts, db_path=db)
            s.check("3 drafts inserted", counts["inserted"] == 3,
                    f"counts={counts}")

            conn = sqlite3.connect(str(db))
            try:
                rows = conn.execute(
                    "SELECT count(*) FROM chunks WHERE kind = 'telegram'"
                ).fetchone()
                s.check("kind=telegram queryable", rows[0] == 3,
                        f"got {rows[0]}")
                rows = conn.execute(
                    "SELECT count(DISTINCT source_archive) "
                    "FROM chunks WHERE kind = 'telegram'"
                ).fetchone()
                s.check("2 distinct archives", rows[0] == 2, f"got {rows[0]}")
            finally:
                conn.close()
        finally:
            set_embed_fn(None)
    return s


def scenario_whatsapp_formats() -> Scenario:
    s = Scenario("whatsapp-formats")
    from scripts.cli.ingest import insert_drafts, set_embed_fn
    from scripts.ingest_whatsapp import parse_whatsapp_export

    ios = ("[12/05/26, 4:32:18 PM] Manju: hi there\n"
           "[12/05/26, 4:32:25 PM] Lokesh: hey\n"
           "multi-line\n"
           "[12/05/26, 4:33:00 PM] Manju: oh nice\n")
    android = ("12/05/26, 16:32 - Manju: hi there\n"
               "12/05/26, 16:32 - Lokesh: hey\n"
               "multi-line\n"
               "12/05/26, 16:33 - Manju: oh nice\n")

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "rag_index.db"
        _make_legacy_db(db)
        _migrate(db)

        ios_path = Path(tmp) / "manju_chat.txt"
        ios_path.write_text(ios, encoding="utf-8")
        android_path = Path(tmp) / "android_chat.txt"
        android_path.write_text(android, encoding="utf-8")

        ios_drafts = list(parse_whatsapp_export(ios_path))
        and_drafts = list(parse_whatsapp_export(android_path))
        s.check("iOS parses 3 messages", len(ios_drafts) == 3,
                f"got {len(ios_drafts)}")
        s.check("Android parses 3 messages", len(and_drafts) == 3,
                f"got {len(and_drafts)}")

        set_embed_fn(_stub_embed)
        try:
            counts1 = insert_drafts(ios_drafts, db_path=db)
            counts2 = insert_drafts(and_drafts, db_path=db)
            s.check("iOS + Android 6 distinct rows",
                    counts1["inserted"] == 3 and counts2["inserted"] == 3,
                    f"counts: ios={counts1}, android={counts2}")
        finally:
            set_embed_fn(None)
    return s


def scenario_idempotent_reingest() -> Scenario:
    s = Scenario("idempotent-reingest")
    from scripts.cli.ingest import insert_drafts, set_embed_fn
    from scripts.ingest_telegram import parse_telegram_export

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "rag_index.db"
        _make_legacy_db(db)
        _migrate(db)

        export_path = Path(tmp) / "result.json"
        export_path.write_text(json.dumps({
            "chats": [{"id": 1, "name": "Manju", "messages": [
                {"id": 1, "type": "message", "date_unixtime": 1700000000,
                 "from": "Manju", "text": "hi"},
                {"id": 2, "type": "message", "date_unixtime": 1700000010,
                 "from": "Lokesh", "text": "hello"},
            ]}],
        }), encoding="utf-8")

        set_embed_fn(_stub_embed)
        try:
            drafts1 = list(parse_telegram_export(export_path))
            counts1 = insert_drafts(drafts1, db_path=db)
            drafts2 = list(parse_telegram_export(export_path))
            counts2 = insert_drafts(drafts2, db_path=db)
            s.check("first run inserts 2", counts1["inserted"] == 2,
                    f"got {counts1}")
            s.check("second run dedups 2", counts2["deduped"] == 2,
                    f"got {counts2}")
            s.check("second run inserts 0", counts2["inserted"] == 0,
                    f"got {counts2}")
        finally:
            set_embed_fn(None)
    return s


def scenario_clustering_coherence() -> Scenario:
    s = Scenario("clustering-coherence")
    from scripts.cluster_topics import cluster

    random.seed(42)
    embeddings, docs, eids = [], [], []
    # 3 well-separated topics × 50 chunks
    for cid in range(3):
        for i in range(50):
            v = [random.gauss(0, 0.05) for _ in range(8)]
            v[cid * 2] += 1.0
            embeddings.append(v)
            docs.append(f"topic-{cid} discussion {i}")
            eids.append(f"t{cid}:{i}")

    run = cluster(embeddings, docs, eids,
                  min_size=20, prefer_bertopic=False)
    s.check("3 clusters found", run.n_clusters == 3,
            f"got {run.n_clusters}")
    s.check("silhouette ≥ 0.5",
            run.silhouette is not None and run.silhouette >= 0.5,
            f"got {run.silhouette}")
    s.check("each cluster has ≥30 chunks",
            all(c.n_chunks >= 30 for c in run.clusters),
            f"sizes={[c.n_chunks for c in run.clusters]}")
    s.check("each cluster has keywords + samples",
            all(c.keywords and c.top_chunks for c in run.clusters),
            "")
    return s


def scenario_auto_route() -> Scenario:
    s = Scenario("auto-route")
    from scripts.cluster_topics import assign_topic

    centroids = {
        "manju":  {"embedding": [1.0, 0.0, 0.0], "label_status": "approved"},
        "code":   {"embedding": [0.0, 1.0, 0.0], "label_status": "approved"},
        "career": {"embedding": [0.0, 0.0, 1.0], "label_status": "approved"},
    }

    s.check("near-manju → manju",
            assign_topic([0.95, 0.1, 0.0], centroids, threshold=0.5) == "manju",
            "")
    s.check("near-code → code",
            assign_topic([0.1, 0.9, 0.0], centroids, threshold=0.5) == "code",
            "")
    s.check("orthogonal → None",
            assign_topic([0.0, 0.0, 0.0], centroids, threshold=0.5) is None,
            "")
    return s


def scenario_thread_bridge() -> Scenario:
    s = Scenario("thread-bridge")
    from scripts.thread_topic_resolver import resolve_thread_topics

    thread = {
        "id": "t1", "embedding": [0.95, 0.1, 0.05],
        "tunnel_topics": [], "status": "active",
    }
    # Thread emb [0.95, 0.1, 0.05] cosine with centroids:
    #   manju  [1.0, 0.0, 0.0]   ≈ 0.989  → above threshold
    #   code   [0.0, 1.0, 0.0]   ≈ 0.103  → below threshold (orthogonal)
    #   career [0.6, 0.4, 0.0]   ≈ 0.642  → above threshold
    centroids = {
        "manju":  {"embedding": [1.0, 0.0, 0.0], "label_status": "approved"},
        "code":   {"embedding": [0.0, 1.0, 0.0], "label_status": "approved"},
        "career": {"embedding": [0.6, 0.4, 0.0], "label_status": "approved"},
    }
    topics = resolve_thread_topics(
        thread, centroids, top_k=3, threshold=0.5,
    )
    s.check("manju ranked first", topics and topics[0] == "manju",
            f"got {topics}")
    s.check("2 topics cross threshold (manju + career; code orthogonal)",
            topics == ["manju", "career"], f"got {topics}")
    s.check("orthogonal centroid (code) excluded",
            "code" not in topics, f"got {topics}")
    return s


def scenario_confidentiality_default() -> Scenario:
    s = Scenario("confidentiality-default")
    from scripts.cli.ingest import insert_drafts, set_embed_fn
    from scripts.ingest_telegram import parse_telegram_export

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "rag_index.db"
        _make_legacy_db(db)
        _migrate(db)

        export_path = Path(tmp) / "result.json"
        export_path.write_text(json.dumps({
            "chats": [{"id": 1, "name": "Manju", "messages": [
                {"id": 1, "type": "message", "date_unixtime": 1700000000,
                 "from": "Manju", "text": "hi"},
            ]}],
        }), encoding="utf-8")

        # NOTE: parse_telegram_export defaults confidentiality='personal'
        # — this is the spec invariant under test.
        drafts = list(parse_telegram_export(export_path))
        s.check("draft default = personal",
                all(d.confidentiality == "personal" for d in drafts),
                f"got {[d.confidentiality for d in drafts]}")

        set_embed_fn(_stub_embed)
        try:
            insert_drafts(drafts, db_path=db)

            conn = sqlite3.connect(str(db))
            try:
                rows = conn.execute(
                    "SELECT confidentiality FROM chunks WHERE kind = 'telegram'"
                ).fetchall()
                s.check("DB row confidentiality = personal",
                        all(r[0] == "personal" for r in rows),
                        f"got {[r[0] for r in rows]}")
            finally:
                conn.close()
        finally:
            set_embed_fn(None)
    return s


SCENARIOS: List[Tuple[str, Callable[[], Scenario]]] = [
    ("schema_live",              scenario_schema_live),
    ("telegram_roundtrip",       scenario_telegram_roundtrip),
    ("whatsapp_formats",         scenario_whatsapp_formats),
    ("idempotent_reingest",      scenario_idempotent_reingest),
    ("clustering_coherence",     scenario_clustering_coherence),
    ("auto_route",               scenario_auto_route),
    ("thread_bridge",            scenario_thread_bridge),
    ("confidentiality_default",  scenario_confidentiality_default),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 smoke runner")
    parser.add_argument("--scenarios", default="all",
                        help="comma-separated names or 'all'")
    args = parser.parse_args()

    if args.scenarios == "all":
        runners = SCENARIOS
    else:
        wanted = set(args.scenarios.split(","))
        runners = [(n, fn) for n, fn in SCENARIOS if n in wanted]

    print(f"Phase 3 smoke runner — {len(runners)} scenarios\n")

    results: List[Scenario] = []
    for name, fn in runners:
        print(f"[scenario] {name}")
        try:
            sc = fn()
        except Exception as e:
            sc = Scenario(name)
            sc.failed.append(f"crashed: {type(e).__name__}: {e}")
            print(f"  ✗ crashed: {e}")
        results.append(sc)
        print()

    total_pass = sum(len(r.passed) for r in results)
    total_fail = sum(len(r.failed) for r in results)
    print("=" * 60)
    print(f"summary: {total_pass} pass / {total_fail} fail "
          f"across {len(results)} scenarios")
    if total_fail:
        for r in results:
            for f in r.failed:
                print(f"  FAIL {r.name}: {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
