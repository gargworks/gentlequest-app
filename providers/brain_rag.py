#!/usr/bin/env python3
"""
Brain RAG Engine v2 — Third Brother's Full Knowledge Retrieval System
=====================================================================
SOTA RAG: hybrid search (dense + BM25/FTS5), reciprocal rank fusion,
metadata-boosted scoring, rich multi-source hot context, RAFT-ready
shadow logging.

All local. No API keys. No cloud. Runs on Ollama.

Architecture:
  COLD: Dense embeddings + BM25 keyword search → RRF fusion → metadata boost
  HOT:  Live session + working state + commitments + energy context

Usage:
    python3 providers/brain_rag.py --index           # index .brain knowledge
    python3 providers/brain_rag.py --index --force   # re-embed everything
    python3 providers/brain_rag.py --search "query"  # test hybrid retrieval
    python3 providers/brain_rag.py --stats           # show index stats
    python3 providers/brain_rag.py --live            # show live context snapshot
    python3 providers/brain_rag.py --full "query"    # full hot+cold context
"""

import sqlite3
import hashlib
import json
import re
import time
import subprocess
import sys
import os
import argparse
import urllib.request
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BRAIN_PATH = PROJECT_ROOT / ".brain"
RAG_DB_NAME = "rag_index.db"

# ── Ollama config ────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "qwen3-embedding:0.6b"  # 1024-dim, local, fast
EMBED_DIM = 1024

# ── Session sources ──────────────────────────────────────────
CLAUDE_SESSIONS_DIR = Path.home() / ".claude" / "projects"

# ── Chunking ─────────────────────────────────────────────────
CHUNK_MAX_WORDS = 300
CHUNK_OVERLAP_WORDS = 50   # overlap between adjacent sub-chunks
CHUNK_MIN_CHARS = 30

# ── Retrieval ────────────────────────────────────────────────
DEFAULT_TOP_K = 7
DENSE_CANDIDATES = 20      # fetch more candidates for fusion
BM25_CANDIDATES = 20
SCORE_THRESHOLD = 0.25     # lower threshold — RRF handles quality
RRF_K = 60                 # standard RRF constant

# ── Context budget (words) ───────────────────────────────────
BUDGET_HOT_SESSION = 500
BUDGET_HOT_STATE = 250
BUDGET_HOT_COMMITMENTS = 150
BUDGET_COLD = 1000
BUDGET_TOTAL = 2000

# ── Shadow training ──────────────────────────────────────────
SHADOW_LOG = BRAIN_PATH / "training" / "shadow_log.jsonl"

# ── Index source priorities (lower = higher priority = bigger boost) ──
INDEX_PRIORITY = {
    # Tier 0 — highest signal
    "corrections": 0,
    "memory": 0,
    # Tier 1 — core knowledge
    "vault": 1,
    "knowledge": 1,
    "distill": 1,
    # Tier 2 — strategic
    "artifacts/strategy": 2,
    "artifacts/synthesis": 2,
    "strategy": 2,
    # Tier 3 — execution & missions
    "artifacts/execution": 3,
    "artifacts/architecture": 3,
    "commitments": 3,
    "missions": 3,
    # Tier 4 — research & engrams
    "artifacts/research": 4,
    "artifacts/ideas": 4,
    "engrams": 4,
    # Tier 5 — planning & historical
    "artifacts/planning": 5,
    "artifacts/engineering": 5,
    "archive": 5,
    # Tier 6 — GTM & handoffs
    "artifacts/marketing": 6,
    "artifacts/gtm": 6,
    "handoff": 6,
    "handoffs": 6,
    # Tier 7 — sessions & meta
    "artifacts/sessions": 7,
    "meta": 7,
    # Phase 2 sources — indexed by dedicated functions, not dir-walk
    "conversations": 4,
    "corrections/dpo": 0,
    "perplexity/bulk": 3,
    "perplexity/targeted": 2,
    "code": 5,
}

# Sources indexed by dedicated functions, not the .brain dir-walk loop
_NON_DIR_SOURCES = {"conversations", "corrections/dpo", "perplexity/bulk", "perplexity/targeted", "code"}
INDEX_DIRS = [k for k in INDEX_PRIORITY if k not in _NON_DIR_SOURCES]

# Standalone .brain/ root files worth indexing (not in subdirs)
INDEX_ROOT_FILES = {
    "commandments.md": 0,
    "roadmap.md": 2,
    "strategy.md": 2,
    "risk_registry.md": 3,
    "INDEX_READ_ME_FIRST.md": 1,
    "KNOWLEDGE_BASE_INDEX.md": 1,
}

# Extra files outside .brain/ (absolute paths resolved at index time)
INDEX_EXTRA_FILES = {
    str(PROJECT_ROOT / "CLAUDE.md"): 0,
}

# Training JSONL files — extract instruction/chosen text, not raw pairs
TRAINING_JSONL_INDEX = {
    "training/sparring_log.jsonl": 3,
    "training/preference_pairs.jsonl": 3,
    "training/raft_sft_v1.jsonl": 4,
}

# Priority tier → RRF score multiplier
PRIORITY_BOOST = {
    0: 1.25, 1: 1.15, 2: 1.10, 3: 1.05,
    4: 1.00, 5: 0.95, 6: 0.90, 7: 0.85,
}

# Recency boost: chunks from files modified within N days get a multiplier
RECENCY_BOOST_DAYS = 7
RECENCY_BOOST_FACTOR = 1.15

# ── Search result cache ─────────────────────────────────────
CACHE_MAX_ENTRIES = 128
CACHE_TTL_SECONDS = 300  # 5 minutes
_search_cache: Dict[str, Tuple[float, List[Dict]]] = {}  # key → (timestamp, results)


# ═══════════════════════════════════════════════════════════════
# EMBEDDING (local Ollama — no API key, no cloud)
# ═══════════════════════════════════════════════════════════════

def _embed(text: str) -> Optional[List[float]]:
    """Generate embedding via local Ollama (qwen3-embedding:0.6b)."""
    try:
        if len(text) > 8000:
            text = text[:8000]
        data = json.dumps({"model": EMBED_MODEL, "input": text}).encode()
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/embed", data=data,
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        embs = result.get("embeddings", [[]])
        if embs and len(embs[0]) > 0:
            return embs[0]
        return None
    except Exception as e:
        print(f"  Embed error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# COLD LAYER — Schema (chunks + FTS5)
# ═══════════════════════════════════════════════════════════════

def _db_path(brain_path: Path) -> Path:
    return brain_path / RAG_DB_NAME


def _init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize DB with chunks table + FTS5 virtual table for BM25."""
    conn = sqlite3.connect(str(db_path))

    # Main chunks table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
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
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON chunks(content_hash)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_file ON chunks(file_path)")

    # FTS5 external content table for BM25 keyword search
    # No triggers — we rebuild FTS5 explicitly after indexing and before search.
    # This avoids trigger conflicts during schema migrations.
    try:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                content, file_path, section,
                content='chunks', content_rowid='id',
                tokenize='porter unicode61'
            )
        """)
    except Exception:
        pass  # FTS5 not available — fall back to dense-only

    # Drop any legacy triggers that could interfere with migrations
    for trigger in ("chunks_ai", "chunks_ad", "chunks_au"):
        try:
            conn.execute(f"DROP TRIGGER IF EXISTS {trigger}")
        except Exception:
            pass

    conn.commit()
    return conn


def _migrate_existing_db(conn: sqlite3.Connection):
    """Migrate existing DB: add missing columns, rebuild FTS5 from existing data."""
    cols = [row[1] for row in conn.execute("PRAGMA table_info(chunks)").fetchall()]

    if "priority_tier" not in cols:
        conn.execute("ALTER TABLE chunks ADD COLUMN priority_tier INTEGER NOT NULL DEFAULT 5")
        for tier_dir, priority in INDEX_PRIORITY.items():
            conn.execute(
                "UPDATE chunks SET priority_tier = ? WHERE file_path LIKE ?",
                (priority, f"{tier_dir}/%")
            )
        conn.commit()

    if "file_mtime" not in cols:
        conn.execute("ALTER TABLE chunks ADD COLUMN file_mtime REAL NOT NULL DEFAULT 0")
        conn.commit()

    # Create indexes on new columns (safe to run repeatedly)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON chunks(priority_tier)")

    # Rebuild FTS5 index from chunks table
    _rebuild_fts(conn)


def _rebuild_fts(conn: sqlite3.Connection):
    """Rebuild FTS5 index from current chunks data. Safe to call repeatedly."""
    try:
        conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
        conn.commit()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# COLD LAYER — Chunking (overlapping windows)
# ═══════════════════════════════════════════════════════════════

def chunk_markdown(content: str, max_words: int = CHUNK_MAX_WORDS,
                   overlap: int = CHUNK_OVERLAP_WORDS) -> List[Tuple[str, str]]:
    """Split markdown into overlapping (section_title, chunk_text) pairs.

    Splits on # and ## headings first, then sub-chunks long sections
    with `overlap` words shared between adjacent pieces so boundary
    context is never lost.
    """
    # Phase 1: split by headings
    sections = []
    current_title = "intro"
    current_lines = []

    for line in content.split('\n'):
        if line.startswith('## ') or line.startswith('# '):
            if current_lines:
                text = '\n'.join(current_lines).strip()
                if len(text) >= CHUNK_MIN_CHARS:
                    sections.append((current_title, text))
            current_title = line.lstrip('#').strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        text = '\n'.join(current_lines).strip()
        if len(text) >= CHUNK_MIN_CHARS:
            sections.append((current_title, text))

    # Phase 2: sub-chunk with overlap
    result = []
    for title, text in sections:
        words = text.split()
        if len(words) <= max_words:
            result.append((title, text))
        else:
            step = max(max_words - overlap, 1)
            part_num = 0
            i = 0
            while i < len(words):
                chunk_words = words[i:i + max_words]
                chunk = ' '.join(chunk_words)
                part_num += 1
                label = f"{title} (part {part_num})"
                result.append((label, chunk))
                i += step

    return result


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]


def _chunk_plain_text(text: str, max_words: int = CHUNK_MAX_WORDS,
                      overlap: int = CHUNK_OVERLAP_WORDS) -> List[str]:
    """Split plain text into overlapping word-window chunks.

    Unlike chunk_markdown(), this doesn't split on headings — suitable for
    JSONL conversation content and other non-markdown sources.
    """
    words = text.split()
    if len(words) <= max_words:
        return [text] if len(text) >= CHUNK_MIN_CHARS else []

    chunks = []
    step = max(max_words - overlap, 1)
    i = 0
    while i < len(words):
        chunk = ' '.join(words[i:i + max_words])
        if len(chunk) >= CHUNK_MIN_CHARS:
            chunks.append(chunk)
        i += step
    return chunks


def _get_priority_tier(file_path: str) -> int:
    """Determine priority tier from file path."""
    for dir_prefix, priority in INDEX_PRIORITY.items():
        if file_path.startswith(dir_prefix):
            return priority
    return 7


# ═══════════════════════════════════════════════════════════════
# COLD LAYER — Indexing
# ═══════════════════════════════════════════════════════════════

def index_brain(brain_path: Path = BRAIN_PATH, force: bool = False) -> int:
    """Index all .brain/**/*.md with embeddings + FTS5. Returns new chunk count."""
    import numpy as np

    brain_path = Path(brain_path)
    db = _db_path(brain_path)
    conn = _init_db(db)
    _migrate_existing_db(conn)

    indexed = 0
    skipped = 0
    errors = 0

    for rel_dir in INDEX_DIRS:
        src = brain_path / rel_dir
        if not src.exists():
            continue
        md_files = sorted(src.rglob("*.md"))
        if not md_files:
            continue

        priority = INDEX_PRIORITY.get(rel_dir, 5)
        print(f"\n  [{rel_dir}] {len(md_files)} files (priority={priority})", flush=True)

        for md_file in md_files:
            try:
                content = md_file.read_text(errors='ignore')
                if len(content) < 50:
                    continue

                rel_path = str(md_file.relative_to(brain_path))
                file_mtime = md_file.stat().st_mtime
                chunks = chunk_markdown(content)

                for section, chunk_text in chunks:
                    c_hash = _content_hash(chunk_text)

                    existing = conn.execute(
                        "SELECT id FROM chunks WHERE content_hash=?", (c_hash,)
                    ).fetchone()
                    if existing and not force:
                        skipped += 1
                        continue

                    emb = _embed(chunk_text)
                    if not emb:
                        errors += 1
                        continue

                    # Semantic dedup: skip if near-identical chunk already exists
                    if not force and not existing:
                        sim_hits = _dense_search(emb, conn, topk=1)
                        if sim_hits and sim_hits[0][1] > 0.95:
                            skipped += 1
                            continue

                    emb_blob = np.array(emb, dtype=np.float32).tobytes()
                    wc = len(chunk_text.split())

                    if existing:
                        conn.execute(
                            "UPDATE chunks SET embedding=?, word_count=?, priority_tier=?, "
                            "file_mtime=?, indexed_at=? WHERE content_hash=?",
                            (emb_blob, wc, priority, file_mtime, time.time(), c_hash)
                        )
                    else:
                        conn.execute(
                            "INSERT INTO chunks (file_path, section, content, content_hash, "
                            "embedding, word_count, priority_tier, file_mtime, indexed_at) "
                            "VALUES (?,?,?,?,?,?,?,?,?)",
                            (rel_path, section, chunk_text, c_hash, emb_blob, wc,
                             priority, file_mtime, time.time())
                        )
                    indexed += 1

                    if indexed % 50 == 0:
                        conn.commit()
                        print(f"    +{indexed} chunks (skip={skipped} err={errors})", flush=True)

            except Exception as e:
                print(f"    Skip {md_file.name}: {e}")
                errors += 1

    conn.commit()

    # ── Index standalone .brain/ root files ──
    for filename, priority in INDEX_ROOT_FILES.items():
        root_file = brain_path / filename
        if not root_file.exists():
            continue
        try:
            content = root_file.read_text(errors='ignore')
            if len(content) < 50:
                continue
            file_mtime = root_file.stat().st_mtime
            for section, chunk_text in chunk_markdown(content):
                c_hash = _content_hash(chunk_text)
                existing = conn.execute("SELECT id FROM chunks WHERE content_hash=?", (c_hash,)).fetchone()
                if existing and not force:
                    skipped += 1
                    continue
                emb = _embed(chunk_text)
                if not emb:
                    errors += 1
                    continue
                if not force and not existing:
                    sim_hits = _dense_search(emb, conn, topk=1)
                    if sim_hits and sim_hits[0][1] > 0.95:
                        skipped += 1
                        continue
                emb_blob = np.array(emb, dtype=np.float32).tobytes()
                wc = len(chunk_text.split())
                if existing:
                    conn.execute(
                        "UPDATE chunks SET embedding=?, word_count=?, priority_tier=?, "
                        "file_mtime=?, indexed_at=? WHERE content_hash=?",
                        (emb_blob, wc, priority, file_mtime, time.time(), c_hash))
                else:
                    conn.execute(
                        "INSERT INTO chunks (file_path, section, content, content_hash, "
                        "embedding, word_count, priority_tier, file_mtime, indexed_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (filename, section, chunk_text, c_hash, emb_blob, wc,
                         priority, file_mtime, time.time()))
                indexed += 1
        except Exception as e:
            print(f"    Skip {filename}: {e}")
            errors += 1
    if INDEX_ROOT_FILES:
        print(f"  [root-files] scanned {len(INDEX_ROOT_FILES)} files", flush=True)

    # ── Index extra files (CLAUDE.md etc.) ──
    for abs_path_str, priority in INDEX_EXTRA_FILES.items():
        extra_file = Path(abs_path_str)
        if not extra_file.exists():
            continue
        try:
            content = extra_file.read_text(errors='ignore')
            if len(content) < 50:
                continue
            rel_label = extra_file.name
            file_mtime = extra_file.stat().st_mtime
            for section, chunk_text in chunk_markdown(content):
                c_hash = _content_hash(chunk_text)
                existing = conn.execute("SELECT id FROM chunks WHERE content_hash=?", (c_hash,)).fetchone()
                if existing and not force:
                    skipped += 1
                    continue
                emb = _embed(chunk_text)
                if not emb:
                    errors += 1
                    continue
                if not force and not existing:
                    sim_hits = _dense_search(emb, conn, topk=1)
                    if sim_hits and sim_hits[0][1] > 0.95:
                        skipped += 1
                        continue
                emb_blob = np.array(emb, dtype=np.float32).tobytes()
                wc = len(chunk_text.split())
                if existing:
                    conn.execute(
                        "UPDATE chunks SET embedding=?, word_count=?, priority_tier=?, "
                        "file_mtime=?, indexed_at=? WHERE content_hash=?",
                        (emb_blob, wc, priority, file_mtime, time.time(), c_hash))
                else:
                    conn.execute(
                        "INSERT INTO chunks (file_path, section, content, content_hash, "
                        "embedding, word_count, priority_tier, file_mtime, indexed_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (rel_label, section, chunk_text, c_hash, emb_blob, wc,
                         priority, file_mtime, time.time()))
                indexed += 1
        except Exception as e:
            print(f"    Skip {abs_path_str}: {e}")
            errors += 1
    if INDEX_EXTRA_FILES:
        print(f"  [extra-files] scanned {len(INDEX_EXTRA_FILES)} files", flush=True)

    conn.commit()

    # ── Index Claude memory (external, curated) ──
    claude_mem_dirs = list(Path.home().glob(".claude/projects/*/memory"))
    claude_mem_count = 0
    for mem_dir in claude_mem_dirs:
        md_files = sorted(mem_dir.rglob("*.md"))
        if not md_files:
            continue
        priority = 0  # Tier 0 — curated founder knowledge
        project_name = mem_dir.parent.name
        print(f"\n  [claude-memory/{project_name}] {len(md_files)} files (priority={priority})", flush=True)
        for md_file in md_files:
            try:
                content = md_file.read_text(errors='ignore')
                if len(content) < 50:
                    continue
                rel_label = f"claude-memory/{project_name}/{md_file.name}"
                file_mtime = md_file.stat().st_mtime
                for section, chunk_text in chunk_markdown(content):
                    c_hash = _content_hash(chunk_text)
                    existing = conn.execute("SELECT id FROM chunks WHERE content_hash=?", (c_hash,)).fetchone()
                    if existing and not force:
                        skipped += 1
                        continue
                    emb = _embed(chunk_text)
                    if not emb:
                        errors += 1
                        continue
                    if not force and not existing:
                        sim_hits = _dense_search(emb, conn, topk=1)
                        if sim_hits and sim_hits[0][1] > 0.95:
                            skipped += 1
                            continue
                    emb_blob = np.array(emb, dtype=np.float32).tobytes()
                    wc = len(chunk_text.split())
                    if existing:
                        conn.execute(
                            "UPDATE chunks SET embedding=?, word_count=?, priority_tier=?, "
                            "file_mtime=?, indexed_at=? WHERE content_hash=?",
                            (emb_blob, wc, priority, file_mtime, time.time(), c_hash))
                    else:
                        conn.execute(
                            "INSERT INTO chunks (file_path, section, content, content_hash, "
                            "embedding, word_count, priority_tier, file_mtime, indexed_at) "
                            "VALUES (?,?,?,?,?,?,?,?,?)",
                            (rel_label, section, chunk_text, c_hash, emb_blob, wc,
                             priority, file_mtime, time.time()))
                    indexed += 1
                    claude_mem_count += 1
            except Exception as e:
                print(f"    Skip {md_file.name}: {e}")
                errors += 1
    if claude_mem_count:
        conn.commit()
        print(f"  [claude-memory] {claude_mem_count} chunks indexed", flush=True)

    # ── Index git commit history (weekly chunks) ──
    try:
        git_result = subprocess.run(
            ["git", "log", "--all", "--format=%ai|%s", "--since=2025-06-01"],
            capture_output=True, text=True, cwd=str(brain_path.parent), timeout=30)
        if git_result.returncode == 0 and git_result.stdout.strip():
            from collections import defaultdict
            weekly = defaultdict(list)
            for line in git_result.stdout.strip().split('\n'):
                if '|' not in line:
                    continue
                date_str, msg = line.split('|', 1)
                # Group by ISO week
                week_key = date_str[:10][:8]  # YYYY-MM- prefix → group by ~week
                try:
                    from datetime import datetime as _dt
                    d = _dt.strptime(date_str[:10], "%Y-%m-%d")
                    week_key = f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"
                except Exception:
                    pass
                weekly[week_key].append(msg.strip())

            priority = 6
            git_chunks_count = 0
            print(f"\n  [git-history] {len(weekly)} weeks of commits", flush=True)
            for week, msgs in sorted(weekly.items()):
                chunk_text = f"Git commits — week {week}:\n" + "\n".join(f"- {m}" for m in msgs)
                if len(chunk_text) < 50:
                    continue
                c_hash = _content_hash(chunk_text)
                existing = conn.execute("SELECT id FROM chunks WHERE content_hash=?", (c_hash,)).fetchone()
                if existing and not force:
                    skipped += 1
                    continue
                emb = _embed(chunk_text)
                if not emb:
                    errors += 1
                    continue
                emb_blob = np.array(emb, dtype=np.float32).tobytes()
                wc = len(chunk_text.split())
                if existing:
                    conn.execute(
                        "UPDATE chunks SET embedding=?, word_count=?, priority_tier=?, "
                        "file_mtime=?, indexed_at=? WHERE content_hash=?",
                        (emb_blob, wc, priority, time.time(), time.time(), c_hash))
                else:
                    conn.execute(
                        "INSERT INTO chunks (file_path, section, content, content_hash, "
                        "embedding, word_count, priority_tier, file_mtime, indexed_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (f"git-history/{week}", week, chunk_text, c_hash, emb_blob, wc,
                         priority, time.time(), time.time()))
                indexed += 1
                git_chunks_count += 1
            if git_chunks_count:
                conn.commit()
                print(f"  [git-history] {git_chunks_count} weekly chunks indexed", flush=True)
    except Exception as e:
        print(f"  [git-history] Skipped: {e}")

    # ── Index training JSONL metadata ──
    for rel_path, priority in TRAINING_JSONL_INDEX.items():
        jsonl_path = brain_path / rel_path
        if not jsonl_path.exists():
            continue
        try:
            jsonl_count = 0
            texts = []
            with open(jsonl_path, 'r', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    # Extract text based on file type
                    text_parts = []
                    for key in ("task_description", "instruction", "chosen", "output", "question",
                                "task", "correction", "reason", "tb_output"):
                        if key in obj and isinstance(obj[key], str):
                            text_parts.append(obj[key])
                    # Handle messages-format (RAFT SFT): extract user+assistant content
                    if "messages" in obj and isinstance(obj["messages"], list):
                        for msg in obj["messages"]:
                            if isinstance(msg, dict) and msg.get("role") in ("user", "assistant"):
                                content = msg.get("content", "")
                                if isinstance(content, str) and len(content) > 20:
                                    text_parts.append(content[:500])  # cap per message
                    if text_parts:
                        texts.append(" ".join(text_parts))

            # Batch texts into chunks of ~300 words
            if texts:
                batch = []
                batch_words = 0
                batch_num = 0
                source_name = Path(rel_path).stem
                print(f"\n  [training/{source_name}] {len(texts)} entries", flush=True)
                for t in texts:
                    wc = len(t.split())
                    if batch_words + wc > CHUNK_MAX_WORDS and batch:
                        chunk_text = "\n".join(batch)
                        c_hash = _content_hash(chunk_text)
                        existing = conn.execute("SELECT id FROM chunks WHERE content_hash=?", (c_hash,)).fetchone()
                        if existing and not force:
                            skipped += 1
                        else:
                            emb = _embed(chunk_text)
                            if emb:
                                if not force and not existing:
                                    sim_hits = _dense_search(emb, conn, topk=1)
                                    if sim_hits and sim_hits[0][1] > 0.95:
                                        skipped += 1
                                        batch = [t]
                                        batch_words = wc
                                        continue
                                emb_blob = np.array(emb, dtype=np.float32).tobytes()
                                if existing:
                                    conn.execute(
                                        "UPDATE chunks SET embedding=?, word_count=?, priority_tier=?, "
                                        "file_mtime=?, indexed_at=? WHERE content_hash=?",
                                        (emb_blob, batch_words, priority, time.time(), time.time(), c_hash))
                                else:
                                    conn.execute(
                                        "INSERT INTO chunks (file_path, section, content, content_hash, "
                                        "embedding, word_count, priority_tier, file_mtime, indexed_at) "
                                        "VALUES (?,?,?,?,?,?,?,?,?)",
                                        (rel_path, f"batch-{batch_num}", chunk_text, c_hash, emb_blob,
                                         batch_words, priority, time.time(), time.time()))
                                indexed += 1
                                jsonl_count += 1
                            else:
                                errors += 1
                        batch = [t]
                        batch_words = wc
                        batch_num += 1
                    else:
                        batch.append(t)
                        batch_words += wc
                # Flush remaining batch
                if batch:
                    chunk_text = "\n".join(batch)
                    c_hash = _content_hash(chunk_text)
                    existing = conn.execute("SELECT id FROM chunks WHERE content_hash=?", (c_hash,)).fetchone()
                    if not existing or force:
                        emb = _embed(chunk_text)
                        if emb:
                            emb_blob = np.array(emb, dtype=np.float32).tobytes()
                            if existing:
                                conn.execute(
                                    "UPDATE chunks SET embedding=?, word_count=?, priority_tier=?, "
                                    "file_mtime=?, indexed_at=? WHERE content_hash=?",
                                    (emb_blob, batch_words, priority, time.time(), time.time(), c_hash))
                            else:
                                conn.execute(
                                    "INSERT INTO chunks (file_path, section, content, content_hash, "
                                    "embedding, word_count, priority_tier, file_mtime, indexed_at) "
                                    "VALUES (?,?,?,?,?,?,?,?,?)",
                                    (rel_path, f"batch-{batch_num}", chunk_text, c_hash, emb_blob,
                                     batch_words, priority, time.time(), time.time()))
                            indexed += 1
                            jsonl_count += 1
                conn.commit()
                print(f"  [training/{source_name}] {jsonl_count} chunks indexed", flush=True)
        except Exception as e:
            print(f"  [training/{rel_path}] Skipped: {e}")
            errors += 1

    # --- Phase 2 sources (non-directory indexers) ---
    for source_name, indexer in [
        ("conversations", lambda: _index_conversations(conn, brain_path, force)),
        ("perplexity", lambda: _index_perplexity(conn, brain_path, force)),
        ("codebase", lambda: _index_codebase_docstrings(conn, force)),
    ]:
        try:
            n = indexer()
            indexed += n
            print(f"\n  [{source_name}] +{n} chunks", flush=True)
        except Exception as e:
            print(f"\n  [{source_name}] skipped: {e}", flush=True)

    conn.commit()
    # Rebuild FTS5 index after all inserts
    print("\n  Rebuilding FTS5 index...", flush=True)
    _rebuild_fts(conn)
    conn.close()
    print(f"\n  Done: +{indexed} new, {skipped} cached, {errors} errors")
    return indexed


# ═══════════════════════════════════════════════════════════════
# PHASE 2 INDEXERS — Conversations, Perplexity, Codebase
# ═══════════════════════════════════════════════════════════════

def _insert_chunk(conn, file_path: str, section: str, text: str,
                  priority: int, file_mtime: float, force: bool) -> bool:
    """Embed and insert a single chunk. Returns True if inserted, False if skipped/error."""
    import numpy as np

    c_hash = _content_hash(text)
    existing = conn.execute("SELECT id FROM chunks WHERE content_hash=?", (c_hash,)).fetchone()
    if existing and not force:
        return False

    emb = _embed(text)
    if not emb:
        return False

    emb_blob = np.array(emb, dtype=np.float32).tobytes()
    wc = len(text.split())

    if existing:
        conn.execute(
            "UPDATE chunks SET embedding=?, word_count=?, priority_tier=?, "
            "file_mtime=?, indexed_at=? WHERE content_hash=?",
            (emb_blob, wc, priority, file_mtime, time.time(), c_hash)
        )
    else:
        conn.execute(
            "INSERT INTO chunks (file_path, section, content, content_hash, "
            "embedding, word_count, priority_tier, file_mtime, indexed_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (file_path, section, text, c_hash, emb_blob, wc,
             priority, file_mtime, time.time())
        )
    return True


def _index_conversations(conn: sqlite3.Connection, brain_path: Path,
                         force: bool = False) -> int:
    """Index distilled conversation turns from Layer 0 archive + DPO corrections.

    Reads loop_turns.jsonl (distilled by conversation_ops.py) and
    preference_pairs.jsonl (DPO correction pairs).
    """
    indexed = 0

    # --- Distilled conversation turns ---
    turns_file = brain_path / "training" / "loop_turns.jsonl"
    if turns_file.exists():
        mtime = turns_file.stat().st_mtime
        priority = _get_priority_tier("conversations")
        print(f"\n  [conversations] indexing {turns_file.name}...", flush=True)

        with open(turns_file) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    turn = json.loads(line)
                    parts = []
                    for msg in turn.get("conversation", []):
                        content = msg.get("content", "")
                        if isinstance(content, str) and content.strip():
                            parts.append(content.strip())
                    text = "\n".join(parts)
                    if len(text) < 50:
                        continue

                    session_id = turn.get("session_id", f"batch")
                    turn_idx = turn.get("turn_index", line_num)
                    fp = f"conversations/{session_id}/turn_{turn_idx}"

                    for i, chunk in enumerate(_chunk_plain_text(text)):
                        section = f"turn_{turn_idx}" if i == 0 else f"turn_{turn_idx} (part {i+1})"
                        if _insert_chunk(conn, fp, section, chunk, priority, mtime, force):
                            indexed += 1

                    if indexed % 50 == 0 and indexed > 0:
                        conn.commit()
                        print(f"    +{indexed} chunks", flush=True)
                except (json.JSONDecodeError, KeyError):
                    continue

        conn.commit()

    # --- DPO preference pairs (correction signal) ---
    pairs_file = brain_path / "training" / "preference_pairs.jsonl"
    if pairs_file.exists():
        mtime = pairs_file.stat().st_mtime
        priority = _get_priority_tier("corrections/dpo")
        print(f"\n  [corrections/dpo] indexing {pairs_file.name}...", flush=True)

        with open(pairs_file) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    pair = json.loads(line)
                    prompt = pair.get("prompt", "")
                    chosen = pair.get("chosen", "")
                    rejected = pair.get("rejected", "")
                    if not (prompt and chosen):
                        continue

                    text = f"Correction:\nPrompt: {prompt}\nWrong: {rejected}\nRight: {chosen}"
                    fp = f"corrections/dpo/{line_num}"

                    if _insert_chunk(conn, fp, f"dpo_pair_{line_num}", text,
                                     priority, mtime, force):
                        indexed += 1
                except (json.JSONDecodeError, KeyError):
                    continue

        conn.commit()

    return indexed


# ── Perplexity quality tier cache ────────────────────────────
_perplexity_quality_cache: Optional[Dict[str, str]] = None

def _load_perplexity_quality(brain_path: Path) -> Dict[str, str]:
    """Load thread_classification.json → {filename_stem: quality_tier}."""
    global _perplexity_quality_cache
    if _perplexity_quality_cache is not None:
        return _perplexity_quality_cache

    _perplexity_quality_cache = {}
    cls_file = brain_path / "training" / "inbox" / "perplexity" / "thread_classification.json"
    if cls_file.exists():
        try:
            data = json.loads(cls_file.read_text())
            for thread in data if isinstance(data, list) else data.get("threads", []):
                name = thread.get("filename", thread.get("name", ""))
                tier = thread.get("quality_tier", thread.get("tier", ""))
                if name and tier:
                    stem = Path(name).stem
                    _perplexity_quality_cache[stem] = tier.lower()
        except Exception:
            pass
    return _perplexity_quality_cache


def _get_perplexity_quality(file_path: str, brain_path: Path = BRAIN_PATH) -> str:
    """Look up Perplexity quality tier (gold/silver/copper) for a file_path."""
    quality_map = _load_perplexity_quality(brain_path)
    stem = Path(file_path).stem
    return quality_map.get(stem, "")


def _index_perplexity(conn: sqlite3.Connection, brain_path: Path,
                      force: bool = False) -> int:
    """Index Perplexity research threads (bulk + targeted)."""
    indexed = 0

    dirs = [
        (brain_path / "training" / "inbox" / "perplexity" / "bulk", "perplexity/bulk"),
        (brain_path / "training" / "inbox" / "perplexity" / "targeted", "perplexity/targeted"),
    ]

    for src_dir, path_prefix in dirs:
        if not src_dir.exists():
            continue

        md_files = sorted(src_dir.rglob("*.md"))
        if not md_files:
            continue

        priority = _get_priority_tier(path_prefix)
        quality_map = _load_perplexity_quality(brain_path)
        print(f"\n  [{path_prefix}] {len(md_files)} files (priority={priority})", flush=True)

        for md_file in md_files:
            try:
                content = md_file.read_text(errors='ignore')
                if len(content) < 50:
                    continue

                fname = md_file.stem
                fp = f"{path_prefix}/{md_file.name}"
                mtime = md_file.stat().st_mtime
                quality = quality_map.get(fname, "")
                chunks = chunk_markdown(content)

                for section, chunk_text in chunks:
                    sec = f"{section} [{quality}]" if quality else section
                    if _insert_chunk(conn, fp, sec, chunk_text, priority, mtime, force):
                        indexed += 1

                if indexed % 50 == 0 and indexed > 0:
                    conn.commit()
                    print(f"    +{indexed} chunks", flush=True)
            except Exception as e:
                print(f"    Skip {md_file.name}: {e}")

        conn.commit()

    return indexed


def _index_codebase_docstrings(conn: sqlite3.Connection,
                               force: bool = False) -> int:
    """Extract and index function/class docstrings from Python source files.

    Uses ast.parse() to walk AST nodes. Zero external dependencies.
    """
    import ast

    CODE_ROOTS = [
        PROJECT_ROOT / "providers",
        PROJECT_ROOT / "mcp-server-nucleus" / "src" / "mcp_server_nucleus",
        PROJECT_ROOT / "scripts",
    ]

    indexed = 0
    priority = _get_priority_tier("code")

    for root in CODE_ROOTS:
        if not root.exists():
            continue

        py_files = sorted(root.rglob("*.py"))
        if not py_files:
            continue

        print(f"\n  [code/{root.name}] {len(py_files)} .py files (priority={priority})", flush=True)

        for py_file in py_files:
            if py_file.name.startswith("test_") or "__pycache__" in str(py_file):
                continue

            try:
                source = py_file.read_text(errors='ignore')
                tree = ast.parse(source, filename=str(py_file))
            except (SyntaxError, UnicodeDecodeError):
                continue

            rel_path = str(py_file.relative_to(PROJECT_ROOT))
            mtime = py_file.stat().st_mtime

            for node in ast.walk(tree):
                if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                docstring = ast.get_docstring(node)
                if not docstring:
                    continue

                name = node.name
                if name.startswith('_') and not name.startswith('__'):
                    continue  # skip private helpers — low retrieval value

                # Build signature for functions
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    try:
                        args = []
                        for arg in node.args.args:
                            ann = ""
                            if arg.annotation:
                                ann = f": {ast.unparse(arg.annotation)}"
                            args.append(f"{arg.arg}{ann}")
                        sig = ", ".join(args)
                        text = f"{name}({sig})\n\n{docstring}"
                    except Exception:
                        text = f"{name}()\n\n{docstring}"
                else:
                    text = f"class {name}\n\n{docstring}"

                fp = f"code/{rel_path}:{name}"

                # Most docstrings fit in one chunk; sub-chunk if long
                for i, chunk in enumerate(_chunk_plain_text(text)):
                    section = name if i == 0 else f"{name} (part {i+1})"
                    if _insert_chunk(conn, fp, section, chunk, priority, mtime, force):
                        indexed += 1

            if indexed % 50 == 0 and indexed > 0:
                conn.commit()
                print(f"    +{indexed} chunks", flush=True)

    conn.commit()
    return indexed


# ═══════════════════════════════════════════════════════════════
# COLD LAYER — Hybrid Retrieval (dense + BM25 → RRF → boost)
# ═══════════════════════════════════════════════════════════════

def _dense_search(query_emb, conn: sqlite3.Connection,
                  topk: int = DENSE_CANDIDATES) -> List[Tuple[int, float]]:
    """Cosine similarity search, vectorized. Returns (chunk_id, score) ranked."""
    import numpy as np

    query_vec = np.array(query_emb, dtype=np.float32)
    qnorm = np.linalg.norm(query_vec)
    if qnorm == 0:
        return []
    query_vec = query_vec / qnorm

    rows = conn.execute("SELECT id, embedding FROM chunks").fetchall()
    if not rows:
        return []

    ids = [r[0] for r in rows]
    matrix = np.empty((len(rows), len(query_emb)), dtype=np.float32)
    for i, (_, emb_blob) in enumerate(rows):
        matrix[i] = np.frombuffer(emb_blob, dtype=np.float32)

    # Batch cosine similarity via normalized dot product
    norms = np.linalg.norm(matrix, axis=1)
    norms[norms == 0] = 1
    matrix = matrix / norms[:, np.newaxis]
    scores = matrix @ query_vec

    top_idx = np.argsort(scores)[-topk:][::-1]
    return [(ids[i], float(scores[i])) for i in top_idx if scores[i] >= SCORE_THRESHOLD]


def _bm25_search(query: str, conn: sqlite3.Connection,
                 topk: int = BM25_CANDIDATES) -> List[Tuple[int, float]]:
    """BM25 keyword search via FTS5. Returns (chunk_id, normalized_score) ranked."""
    terms = re.findall(r'\w{3,}', query.lower())
    if not terms:
        return []

    fts_query = ' OR '.join(f'"{t}"' for t in terms[:10])
    try:
        rows = conn.execute(
            "SELECT rowid, rank FROM chunks_fts WHERE chunks_fts MATCH ? "
            "ORDER BY rank LIMIT ?",
            (fts_query, topk)
        ).fetchall()
        if not rows:
            return []
        # FTS5 rank is negative (lower = better match)
        # Normalize to [0.5, 1.0] range for display — RRF only uses rank order
        ranks = [abs(r[1]) for r in rows]
        max_rank = max(ranks) if ranks else 1
        return [(r[0], 1.0 - (abs(r[1]) / max_rank) * 0.5) for r in rows]
    except Exception:
        return []  # FTS5 not available


def _rrf_fuse(*rankings: List[Tuple[int, float]], k: int = RRF_K) -> List[Tuple[int, float]]:
    """Reciprocal Rank Fusion: combine multiple ranked lists into one.

    RRF score = sum over rankings of 1/(k + rank_position)
    Items that appear in multiple rankings get boosted.
    k=60 is the standard value from the original RRF paper.
    """
    scores = {}
    for ranking in rankings:
        for rank, (chunk_id, _) in enumerate(ranking):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _apply_metadata_boost(fused: List[Tuple[int, float]],
                          conn: sqlite3.Connection) -> List[Tuple[int, float]]:
    """Apply priority tier + recency + Perplexity quality boost to fused RRF scores."""
    if not fused:
        return fused

    chunk_ids = [cid for cid, _ in fused]
    placeholders = ','.join('?' * len(chunk_ids))
    meta = conn.execute(
        f"SELECT id, priority_tier, file_mtime, file_path FROM chunks WHERE id IN ({placeholders})",
        chunk_ids
    ).fetchall()
    meta_map = {row[0]: (row[1], row[2], row[3]) for row in meta}

    now = time.time()
    recency_cutoff = now - (RECENCY_BOOST_DAYS * 86400)
    perplexity_quality_boost = {"gold": 1.20, "silver": 1.10}

    boosted = []
    for chunk_id, score in fused:
        tier, mtime, file_path = meta_map.get(chunk_id, (5, 0, ""))
        boost = PRIORITY_BOOST.get(tier, 1.0)
        if mtime > recency_cutoff:
            boost *= RECENCY_BOOST_FACTOR
        # Perplexity quality tier boost
        if file_path.startswith("perplexity/"):
            quality = _get_perplexity_quality(file_path)
            boost *= perplexity_quality_boost.get(quality, 1.0)
        boosted.append((chunk_id, score * boost))

    boosted.sort(key=lambda x: x[1], reverse=True)
    return boosted


def _cache_key(query: str, brain_path: Path, topk: int) -> str:
    """Build a stable cache key from search parameters."""
    return f"{query}|{brain_path}|{topk}"


def _cache_get(key: str) -> Optional[List[Dict]]:
    """Return cached results if present and not expired, else None."""
    entry = _search_cache.get(key)
    if entry is None:
        return None
    ts, results = entry
    if time.time() - ts > CACHE_TTL_SECONDS:
        del _search_cache[key]
        return None
    return results


def _cache_put(key: str, results: List[Dict]) -> None:
    """Store results in cache, evicting oldest entries if over limit."""
    # Evict oldest entries when at capacity
    if len(_search_cache) >= CACHE_MAX_ENTRIES:
        oldest_key = min(_search_cache, key=lambda k: _search_cache[k][0])
        del _search_cache[oldest_key]
    _search_cache[key] = (time.time(), results)


def search_brain(
    query: str,
    brain_path: Path = BRAIN_PATH,
    topk: int = DEFAULT_TOP_K,
) -> List[Dict]:
    """Full hybrid search: dense + BM25 → RRF fusion → metadata boost → top-K."""
    import numpy as np

    brain_path = Path(brain_path)
    db = _db_path(brain_path)
    if not db.exists():
        return []

    # Check cache before embedding
    ck = _cache_key(query, brain_path, topk)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    query_emb = _embed(query)
    if not query_emb:
        return []

    conn = sqlite3.connect(str(db))
    _migrate_existing_db(conn)

    # Two-lane retrieval
    dense_results = _dense_search(query_emb, conn, DENSE_CANDIDATES)
    bm25_results = _bm25_search(query, conn, BM25_CANDIDATES)

    # Fuse rankings (falls back to dense-only if BM25 unavailable)
    if bm25_results:
        fused = _rrf_fuse(dense_results, bm25_results)
    else:
        fused = [(cid, score) for cid, score in dense_results]

    # Metadata boost (priority tier + recency)
    fused = _apply_metadata_boost(fused, conn)

    # Fetch full chunk data for top-K
    top_ids = [cid for cid, _ in fused[:topk]]
    if not top_ids:
        conn.close()
        return []

    placeholders = ','.join('?' * len(top_ids))
    rows = conn.execute(
        f"SELECT id, file_path, section, content, word_count, priority_tier FROM chunks "
        f"WHERE id IN ({placeholders})",
        top_ids
    ).fetchall()
    conn.close()

    chunk_map = {r[0]: r for r in rows}
    score_map = {cid: score for cid, score in fused[:topk]}

    results = []
    for cid in top_ids:
        if cid not in chunk_map:
            continue
        _, fp, sec, content, wc, tier = chunk_map[cid]
        results.append({
            "id": cid,
            "source": fp,
            "section": sec,
            "content": content,
            "score": score_map.get(cid, 0),
            "word_count": wc,
            "priority_tier": tier,
        })

    _cache_put(ck, results)
    return results


def format_rag_context(results: List[Dict], max_words: int = BUDGET_COLD) -> str:
    """Format retrieved chunks for prompt injection with source attribution."""
    if not results:
        return ""

    lines = ["[BRAIN KNOWLEDGE — ground your answer in these facts]"]
    total_words = 0

    for r in results:
        wc = r.get("word_count", len(r["content"].split()))
        if total_words + wc > max_words:
            remaining = max_words - total_words
            if remaining > 30:
                words = r["content"].split()[:remaining]
                truncated = ' '.join(words) + '...'
                source = r["source"].replace(".md", "").split("/")[-1]
                lines.append(f"\n[{source} > {r['section']}]")
                lines.append(truncated)
            break
        source = r["source"].replace(".md", "").split("/")[-1]
        lines.append(f"\n[{source} > {r['section']}]")
        lines.append(r["content"])
        total_words += wc

    if len(lines) <= 1:
        return ""
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════
# HOT LAYER — Live Session Context
# ═══════════════════════════════════════════════════════════════

def _tail_file(path: Path, max_bytes: int = 50000) -> str:
    """Read last N bytes of a file efficiently."""
    if not path.exists():
        return ""
    size = path.stat().st_size
    with open(path, 'rb') as f:
        if size > max_bytes:
            f.seek(size - max_bytes)
            f.readline()  # skip partial line
        return f.read().decode('utf-8', errors='ignore')


def _find_active_session() -> Optional[Path]:
    """Find the most recently modified Claude Code session JSONL."""
    project_dir = CLAUDE_SESSIONS_DIR / "-Users-lokeshgarg-ai-mvp-backend"
    if not project_dir.exists():
        return None
    jsonl_files = sorted(project_dir.glob("*.jsonl"),
                         key=lambda f: f.stat().st_mtime, reverse=True)
    return jsonl_files[0] if jsonl_files else None


def _parse_session_events(path: Path, max_bytes: int = 150000) -> List[Dict]:
    """Parse Claude Code session into structured events.

    Extracts not just text messages but also file operations and commands,
    giving Third Brother full situational awareness of what's happening.
    """
    raw = _tail_file(path, max_bytes)
    events = []

    for line in raw.strip().split('\n'):
        try:
            obj = json.loads(line)
            msg = obj.get("message", {})
            role = msg.get("role", "")
            content = msg.get("content")

            if role == "user" and isinstance(content, str) and len(content) > 5:
                if not content.startswith("<") and not content.startswith("{"):
                    events.append({"type": "user_msg", "text": content[:500]})

            elif role == "assistant" and isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    ptype = part.get("type", "")

                    if ptype == "text":
                        text = part.get("text", "").strip()
                        if len(text) > 20:
                            events.append({"type": "assistant_msg", "text": text[:500]})

                    elif ptype == "tool_use":
                        tool = part.get("name", "")
                        inp = part.get("input", {})
                        if tool in ("Read", "Edit", "Write"):
                            fp = inp.get("file_path", "")
                            if fp:
                                # Strip project root for compact display
                                short = fp.replace(str(PROJECT_ROOT) + "/", "")
                                events.append({
                                    "type": "file_op", "tool": tool.lower(),
                                    "path": short
                                })
                        elif tool == "Bash":
                            cmd = inp.get("command", "")[:200]
                            if cmd:
                                events.append({"type": "command", "cmd": cmd})
                        elif tool == "Grep":
                            pat = inp.get("pattern", "")
                            events.append({"type": "search", "pattern": pat})

        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    return events


def get_live_session_context(max_words: int = BUDGET_HOT_SESSION) -> str:
    """Build rich live session context from Claude Code conversation.

    Includes: active files, recent commands, conversation turns.
    This is what Third Brother sees to understand 'what Father is doing right now'.
    """
    session = _find_active_session()
    if not session:
        return ""

    events = _parse_session_events(session)
    if not events:
        return ""

    # Active files (deduped, most recent last)
    active_files = []
    seen_files = set()
    for e in reversed(events):
        if e["type"] == "file_op" and e["path"] not in seen_files:
            active_files.append(f"{e['tool']}:{e['path']}")
            seen_files.add(e["path"])
    active_files = list(reversed(active_files[-8:]))

    # Recent commands (deduped)
    recent_cmds = []
    seen_cmds = set()
    for e in reversed(events):
        if e["type"] == "command" and e["cmd"] not in seen_cmds:
            recent_cmds.append(e["cmd"])
            seen_cmds.add(e["cmd"])
            if len(recent_cmds) >= 4:
                break
    recent_cmds.reverse()

    # Recent searches
    searches = [e["pattern"] for e in events if e["type"] == "search"][-3:]

    # Build context
    lines = ["[LIVE SESSION — what Father and McKinsey are working on right now]"]

    if active_files:
        lines.append(f"Files touched: {', '.join(active_files[-6:])}")
    if recent_cmds:
        lines.append(f"Commands: {' | '.join(recent_cmds[-3:])}")
    if searches:
        lines.append(f"Searching for: {', '.join(searches)}")

    # Last N conversation turns
    conv_events = [e for e in events if e["type"] in ("user_msg", "assistant_msg")]
    recent_turns = conv_events[-12:]

    if recent_turns:
        lines.append("")
        total_words = sum(len(l.split()) for l in lines)
        for e in recent_turns:
            text = e["text"]
            words = len(text.split())
            if total_words + words > max_words:
                remaining = max_words - total_words
                if remaining > 10:
                    text = ' '.join(text.split()[:remaining]) + '...'
                else:
                    break
            role = "Father" if e["type"] == "user_msg" else "McKinsey"
            lines.append(f"{role}: {text}")
            total_words += len(text.split())

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════
# HOT LAYER — Working State (git, sprint, energy)
# ═══════════════════════════════════════════════════════════════

def get_working_state(max_words: int = BUDGET_HOT_STATE) -> str:
    """Git state + uncommitted changes + sprint + time/energy context."""
    lines = ["[WORKING STATE]"]

    # Current branch
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=str(PROJECT_ROOT)
        ).stdout.strip()
        if branch:
            lines.append(f"Branch: {branch}")
    except Exception:
        pass

    # Uncommitted changes
    try:
        diff_stat = subprocess.run(
            ["git", "diff", "--stat", "--no-color", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=str(PROJECT_ROOT)
        ).stdout.strip()
        if diff_stat:
            summary_line = diff_stat.split('\n')[-1]
            lines.append(f"Uncommitted: {summary_line}")
            changed = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True, text=True, timeout=5, cwd=str(PROJECT_ROOT)
            ).stdout.strip().split('\n')[:6]
            if changed and changed[0]:
                lines.append(f"Changed: {', '.join(changed)}")
    except Exception:
        pass

    # Recent commits
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-5", "--no-decorate"],
            capture_output=True, text=True, timeout=5, cwd=str(PROJECT_ROOT)
        )
        if result.returncode == 0 and result.stdout.strip():
            lines.append(f"\nRecent commits:")
            lines.append(result.stdout.strip())
    except Exception:
        pass

    # Sprint/phase from brain state
    state_file = BRAIN_PATH / "ledger" / "state.json"
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            sprint = state.get("current_sprint", {})
            if sprint:
                lines.append(f"\nSprint: {sprint.get('name', '?')} ({sprint.get('status', '?')})")
        except Exception:
            pass

    # Time + energy context
    now = datetime.now()
    hour = now.hour
    if hour < 6:
        energy = "deep night — high focus, low energy"
    elif hour < 9:
        energy = "early morning — building momentum"
    elif hour < 12:
        energy = "morning — peak energy"
    elif hour < 14:
        energy = "midday"
    elif hour < 17:
        energy = "afternoon — steady"
    elif hour < 20:
        energy = "evening — winding down"
    elif hour < 23:
        energy = "night — second wind"
    else:
        energy = "late night — deep focus mode"

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    lines.append(f"\nTime: {now.strftime('%Y-%m-%d %H:%M')} ({day_names[now.weekday()]}, {energy})")

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════
# HOT LAYER — Commitments & Tasks
# ═══════════════════════════════════════════════════════════════

def get_commitments_context(max_words: int = BUDGET_HOT_COMMITMENTS) -> str:
    """Active commitments, tasks, priorities from ledgers."""
    lines = []

    # Commitments ledger
    ledger = PROJECT_ROOT / "commitments" / "ledger.json"
    if ledger.exists():
        try:
            data = json.loads(ledger.read_text())
            active = [c for c in data.get("commitments", [])
                      if c.get("status") in ("active", "in_progress", "pending")]
            if active:
                lines.append("[ACTIVE COMMITMENTS]")
                for c in active[:5]:
                    title = c.get("title", c.get("description", "?"))
                    lines.append(f"• {title} [{c.get('status', '?')}]")
        except Exception:
            pass

    # Recent events from brain ledger
    events_file = BRAIN_PATH / "ledger" / "events.jsonl"
    if events_file.exists():
        try:
            raw = _tail_file(events_file, max_bytes=5000)
            recent = []
            for line in raw.strip().split('\n')[-5:]:
                try:
                    evt = json.loads(line)
                    etype = evt.get("type", evt.get("event", ""))
                    if etype:
                        recent.append(etype)
                except json.JSONDecodeError:
                    continue
            if recent:
                lines.append(f"Recent events: {', '.join(recent)}")
        except Exception:
            pass

    if not lines:
        return ""
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════
# CONTEXT ASSEMBLY — Priority-ordered token budget management
# ═══════════════════════════════════════════════════════════════

def build_full_context(query: str, brain_path: Path = BRAIN_PATH,
                       max_words: int = BUDGET_TOTAL) -> Tuple[str, List[Dict]]:
    """Assemble complete context: HOT (always) + COLD (query-dependent).

    Returns (context_string, search_results) so callers can access
    raw results for shadow logging / RAFT data.

    Priority order if budget is tight:
      1. Working state (compact, always relevant)
      2. Live session (what's happening now)
      3. Cold knowledge (query-dependent brain search)
      4. Commitments (if room)
    """
    brain_path = Path(brain_path)
    sections = []
    used_words = 0
    search_results = []

    # 1. Working state (compact, high signal)
    state = get_working_state()
    if state:
        wc = len(state.split())
        sections.append(state)
        used_words += wc

    # 2. Live session (what Father and McKinsey are doing)
    remaining = max_words - used_words
    session = get_live_session_context(max_words=min(BUDGET_HOT_SESSION, remaining))
    if session:
        wc = len(session.split())
        sections.append(session)
        used_words += wc

    # 3. Cold knowledge (hybrid semantic + keyword search)
    remaining = max_words - used_words
    if remaining > 100:
        search_results = search_brain(query, brain_path)
        cold = format_rag_context(search_results, max_words=min(BUDGET_COLD, remaining))
        if cold:
            wc = len(cold.split())
            sections.append(cold)
            used_words += wc

    # 4. Commitments (if room)
    remaining = max_words - used_words
    if remaining > 50:
        commitments = get_commitments_context(max_words=min(BUDGET_HOT_COMMITMENTS, remaining))
        if commitments:
            sections.append(commitments)

    return '\n\n'.join(sections), search_results


# ═══════════════════════════════════════════════════════════════
# SHADOW TRAINING LOG — RAFT-ready
# ═══════════════════════════════════════════════════════════════

def log_shadow_turn(query: str, response: str, model: str,
                    rag_results: Optional[List[Dict]] = None,
                    rag_context: str = "",
                    session_id: str = "",
                    latency_ms: int = 0):
    """Log a turn for future RAFT/DPO training.

    Stores oracle chunks (top-3 used in context) and distractor
    chunks (remaining results) so RAFT training data can be
    generated automatically from real conversations.
    """
    try:
        SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)

        oracle = []
        distractors = []
        if rag_results:
            for i, r in enumerate(rag_results):
                chunk = {
                    "source": r.get("source", ""),
                    "section": r.get("section", ""),
                    "score": round(r.get("score", 0), 4),
                    "content": r.get("content", "")[:500],
                }
                if i < 3:
                    oracle.append(chunk)
                else:
                    distractors.append(chunk)

        entry = {
            "ts": datetime.now().isoformat(),
            "session_id": session_id,
            "query": query,
            "response": response,
            "model": model,
            "oracle_chunks": oracle,
            "distractor_chunks": distractors,
            "rag_context_words": len(rag_context.split()) if rag_context else 0,
            "latency_ms": latency_ms,
            "format": "raft_v1",
        }

        with open(SHADOW_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # never interrupt chat for logging


# ═══════════════════════════════════════════════════════════════
# STATS + CLI
# ═══════════════════════════════════════════════════════════════

def show_stats(brain_path: Path = BRAIN_PATH):
    db = _db_path(brain_path)
    if not db.exists():
        print("No index found. Run --index first.")
        return

    conn = _init_db(db)
    _migrate_existing_db(conn)
    total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    files = conn.execute("SELECT COUNT(DISTINCT file_path) FROM chunks").fetchone()[0]
    words = conn.execute("SELECT SUM(word_count) FROM chunks").fetchone()[0] or 0
    size_mb = db.stat().st_size / (1024 * 1024)

    # FTS5 status
    try:
        fts_count = conn.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]
        fts_status = f"{fts_count} rows"
    except Exception:
        fts_status = "not available"

    # By priority tier
    tiers = conn.execute(
        "SELECT priority_tier, COUNT(*) FROM chunks GROUP BY priority_tier ORDER BY priority_tier"
    ).fetchall()

    # By source dir
    dirs = conn.execute(
        "SELECT SUBSTR(file_path, 1, INSTR(file_path, '/') - 1) as dir, COUNT(*) "
        "FROM chunks GROUP BY dir ORDER BY COUNT(*) DESC"
    ).fetchall()
    conn.close()

    # Shadow log stats
    shadow_turns = 0
    if SHADOW_LOG.exists():
        shadow_turns = sum(1 for _ in open(SHADOW_LOG))

    tier_names = {
        0: "memory/corrections", 1: "vault", 2: "strategy/synth/perplexity-deep",
        3: "execution/arch/perplexity", 4: "research/ideas/conversations",
        5: "planning/eng/code", 6: "marketing/gtm", 7: "sessions/meta",
    }

    print(f"\n  Brain RAG Index (v2 — hybrid search)")
    print(f"  {'='*45}")
    print(f"  Chunks:      {total:,}")
    print(f"  Files:       {files:,}")
    print(f"  Words:       {words:,}")
    print(f"  DB size:     {size_mb:.1f} MB")
    print(f"  FTS5 index:  {fts_status}")
    print(f"  Shadow log:  {shadow_turns} turns")
    print(f"\n  By priority tier:")
    for tier, count in tiers:
        print(f"    T{tier} ({tier_names.get(tier, '?'):20s}) {count:5d}")
    print(f"\n  By source:")
    for d, c in dirs:
        print(f"    {d:30s} {c:5d}")


def main():
    parser = argparse.ArgumentParser(description="Brain RAG Engine v2 — Hybrid Search")
    parser.add_argument("--index", action="store_true", help="Index .brain knowledge")
    parser.add_argument("--force", action="store_true", help="Re-embed all chunks")
    parser.add_argument("--search", type=str, help="Hybrid search query")
    parser.add_argument("--topk", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--live", action="store_true", help="Show live context snapshot")
    parser.add_argument("--full", type=str, help="Full context for a query (hot+cold)")
    parser.add_argument("--brain", type=str, default=str(BRAIN_PATH))
    args = parser.parse_args()

    brain = Path(args.brain)

    if args.stats:
        show_stats(brain)
    elif args.index:
        print(f"=== Brain RAG Indexer v2 ===")
        print(f"Brain: {brain}")
        print(f"Embedding: {EMBED_MODEL} ({EMBED_DIM}d, local)")
        print(f"Search: hybrid (dense + BM25/FTS5 + RRF)")
        print(f"Force: {args.force}")
        n = index_brain(brain, force=args.force)
        show_stats(brain)
    elif args.search:
        results = search_brain(args.search, brain, topk=args.topk)
        if not results:
            print("No results found.")
            return
        for i, r in enumerate(results):
            tier = f"T{r['priority_tier']}" if 'priority_tier' in r else ""
            print(f"\n{'─'*50}")
            print(f"  #{i+1} [{r['source']} > {r['section']}]  score={r['score']:.4f} {tier}")
            print(f"  {r['content'][:300]}...")
    elif args.live:
        print("=== Live Context Snapshot ===\n")
        print(get_live_session_context())
        print()
        print(get_working_state())
        print()
        print(get_commitments_context())
    elif args.full:
        ctx, results = build_full_context(args.full, brain)
        wc = len(ctx.split())
        print(f"=== Full Context ({wc} words, {len(results)} chunks) ===\n")
        print(ctx)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
