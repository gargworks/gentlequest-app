#!/usr/bin/env python3
"""Voice Corpus Builder — mine Lokesh's voice from existing signal sources.

Phase 1 §1.4 / DEC-012: voice corpus is MINED + STRATIFIED, not
hand-curated to N=10. Mathematical limits (token budget, diversity
saturation, editorial throughput), not arbitrary caps.

Pipeline:
    1. Inventory signal sources (Claude Code session jsonls, shadow_log,
       preference_pairs, git commits, .brain conversations)
    2. Extract Lokesh-authored text candidates
    3. Filter: drop slashes, commands, errors, image-only, malformed
    4. Embed via sentence-transformers (local, batched, cached)
    5. Cluster (KMeans) on embeddings
    6. Stratify-sample per cluster (top by length-coverage diversity)
    7. Write FULL corpus to .brain/voice/lokesh_corpus.jsonl
    8. Write top-N candidates for editorial review to
       .brain/voice/lokesh_candidates.md
    9. Lokesh promotes approved → .brain/voice/lokesh.md (trusted pool)

Default invocation:
    python3 scripts/voice_corpus_builder.py             # dry-run + report
    python3 scripts/voice_corpus_builder.py --apply     # write corpus + candidates
    python3 scripts/voice_corpus_builder.py --apply --max-sessions 50  # bound

Charter commitments:
    #1 built whole — no MVP, full mining + clustering + editorial gate
    #2 token-budget — runtime selector picks K relevant per turn (env-tunable)
    #5 compounding day-1 — corpus + selector + editorial all wired Phase 1
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
BRAIN = Path(os.environ.get("NUCLEUS_BRAIN_PATH", str(ROOT / ".brain")))
CC_PROJECT = Path.home() / ".claude" / "projects" / "-Users-lokeshgarg-ai-mvp-backend"

# ── Default paths for new sources ───────────────────────────────────
_DEFAULT_WA_SQLITE = (
    Path.home()
    / "Library"
    / "Group Containers"
    / "group.net.whatsapp.WhatsApp.shared"
    / "ChatStorage.sqlite"
)
_DEFAULT_WA_SFT_JSONL = (
    Path.home()
    / "Downloads"
    / ".brain"
    / "training"
    / "inbox"
    / "whatsapp_exports_sft.jsonl"
)
_DEFAULT_IMESSAGE_DB = Path.home() / "Library" / "Messages" / "chat.db"

# Apple Core Data epoch: 2001-01-01 00:00:00 UTC = Unix 978307200
_APPLE_EPOCH_OFFSET = 978307200

VOICE_DIR = BRAIN / "voice"
CORPUS_FILE = VOICE_DIR / "lokesh_corpus.jsonl"
CANDIDATES_FILE = VOICE_DIR / "lokesh_candidates.md"
TRUSTED_FILE = VOICE_DIR / "lokesh.md"
EMBED_CACHE_DIR = VOICE_DIR / ".embed_cache"


# ── Filtering rules ──────────────────────────────────────────────────

# Drop these text patterns — they're system messages, commands, or noise
_DROP_PATTERNS = [
    re.compile(r"^\s*<", re.MULTILINE),               # XML/system tags
    re.compile(r"^\s*\["),                            # bracketed system msgs
    re.compile(r"^\s*$"),                             # empty
    re.compile(r"^/[a-z]"),                           # slash commands
    re.compile(r"^!"),                                # bash escape
    re.compile(r"\[Image:"),                          # image-only paste
    re.compile(r"<command-name>", re.IGNORECASE),     # CLI command output
    re.compile(r"<system-reminder>", re.IGNORECASE),  # CC reminders
    re.compile(r"<task-notification>", re.IGNORECASE),
    re.compile(r"<local-command", re.IGNORECASE),
    re.compile(r"^Continue\.?$"),                     # one-word continuations
    re.compile(r"^continue from where", re.IGNORECASE),
]

# Voice-relevant length window
MIN_CHARS = 30        # too short = "ok", "yes", "thanks"
MAX_CHARS = 1500      # too long = paste-dump, design doc, code

# Voice-relevant content checks (substring matches, case-sensitive)
_NON_VOICE_INDICATORS = [
    "```",                          # code block
    "import ",                       # python code
    "function ",                     # JS code
    "def ",                          # python def
    "class ",                        # python class
    "SELECT ",                       # SQL
    "stdout:",                       # tool output paste
    "Traceback",                     # python stack trace
    "Error:",                        # error class with colon
    "Error (most recent",            # python traceback header
    "Exception:",                    # exception
    "  File \"",                     # traceback file line ('  File "/path"')
    "  at ",                         # JS-style stack trace
    "git log",                       # git output paste
    "$ ",                            # shell prompt paste
    "------",                        # markdown rule (often paste)
    "==========",                    # markdown rule (often paste)
    "warning: ",                     # CLI warnings
    "ERROR ",                        # CLI errors
    "%%capture",                     # jupyter magic
    "!python ",                      # colab cell pastes
    "!pip ",                         # colab pip pastes
    "PyCompileError",                # python compile error
]

# Heuristic: many newlines per character suggests structured paste
def _is_likely_paste(text: str) -> bool:
    """High newline density (lots of short lines) typically means a code
    paste, log paste, or traceback — not voice."""
    n = len(text)
    if n == 0:
        return False
    nl_count = text.count("\n")
    if nl_count >= 5 and (nl_count / n) > 0.04:  # >1 newline per 25 chars on average
        return True
    return False


def is_voice_relevant(text: str) -> bool:
    """Return True if text is plausible Lokesh-voice signal."""
    if not text:
        return False
    n = len(text)
    if n < MIN_CHARS or n > MAX_CHARS:
        return False
    for pat in _DROP_PATTERNS:
        if pat.search(text):
            return False
    # Drop pasted code/output
    for ind in _NON_VOICE_INDICATORS:
        if ind in text:
            return False
    # Drop dense-newline pastes (code/logs/tracebacks)
    if _is_likely_paste(text):
        return False
    # Require minimum word count (not single-shot fragment)
    if len(text.split()) < 5:
        return False
    return True


# ── Source: Claude Code session jsonls (the densest signal) ──────────

def iter_user_turns_from_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    """Extract Lokesh's user turns from one Claude Code session jsonl.

    Yields dicts: {text, ts, source_id (file basename), turn_idx}.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "user":
                    continue
                msg = obj.get("message") or {}
                content = msg.get("content")
                if not content:
                    continue
                # content can be str or list of {type, text}
                texts = []
                if isinstance(content, str):
                    texts.append(content)
                elif isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            t = c.get("text", "")
                            if t:
                                texts.append(t)
                ts = obj.get("timestamp") or obj.get("ts") or ""
                for t in texts:
                    yield {
                        "text": t.strip(),
                        "ts": ts,
                        "source": f"cc_session/{path.stem}",
                        "turn_idx": idx,
                    }
    except OSError:
        return


def mine_cc_sessions(max_files: Optional[int] = None,
                    recent_first: bool = True) -> List[Dict[str, Any]]:
    """Mine all Claude Code session jsonls for user turns."""
    if not CC_PROJECT.exists():
        return []
    files = list(CC_PROJECT.glob("*.jsonl"))
    if recent_first:
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    if max_files is not None:
        files = files[:max_files]
    out = []
    for f in files:
        for record in iter_user_turns_from_jsonl(f):
            out.append(record)
    return out


# ── Source: shadow_log (TB endpoint queries — also Lokesh) ───────────

def mine_shadow_log() -> List[Dict[str, Any]]:
    """Mine `query` field from shadow_log entries (Lokesh's prompts to TB)."""
    path = BRAIN / "training" / "shadow_log.jsonl"
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            q = obj.get("query") or ""
            if q:
                out.append({
                    "text": q.strip(),
                    "ts": obj.get("ts") or "",
                    "source": "shadow_log",
                    "turn_idx": idx,
                })
    return out


# ── Source: WhatsApp ChatStorage.sqlite ─────────────────────────────

def mine_whatsapp_sqlite(
    db_path: Path = _DEFAULT_WA_SQLITE,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Read Lokesh's sent WhatsApp messages from ChatStorage.sqlite.

    Opens the DB read-only (mode=ro) to protect the live store.
    ZMESSAGEDATE is Apple Core Data timestamp (seconds since 2001-01-01).
    Joins ZWACHATSESSION on ZCHATSESSION FK to get the partner name.
    """
    if not db_path.exists():
        return []
    uri = f"file:{db_path}?mode=ro"
    out: List[Dict[str, Any]] = []
    try:
        conn = sqlite3.connect(uri, uri=True)
        try:
            cur = conn.cursor()
            sql = """
                SELECT
                    m.ZTEXT,
                    m.ZMESSAGEDATE,
                    s.ZPARTNERNAME,
                    m.Z_PK
                FROM ZWAMESSAGE m
                LEFT JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
                WHERE m.ZISFROMME = 1
                  AND m.ZTEXT IS NOT NULL
                  AND length(m.ZTEXT) > 0
                ORDER BY m.ZMESSAGEDATE DESC
            """
            if limit is not None:
                sql += f" LIMIT {int(limit)}"
            cur.execute(sql)
            rows = cur.fetchall()
        finally:
            conn.close()
    except sqlite3.Error:
        return []

    for idx, (text, msg_date, partner, pk) in enumerate(rows):
        # Convert Apple Core Data timestamp → ISO string
        ts = ""
        if msg_date is not None:
            try:
                unix_ts = float(msg_date) + _APPLE_EPOCH_OFFSET
                ts = datetime.datetime.fromtimestamp(
                    unix_ts, tz=datetime.timezone.utc
                ).isoformat()
            except (ValueError, OSError, OverflowError):
                ts = ""
        contact = (partner or "").strip()
        # person_tag: lowercased first word of partner name
        person_tag = contact.split()[0].lower() if contact else "unknown"
        out.append({
            "text": text.strip(),
            "ts": ts,
            "source": f"whatsapp_sqlite/{contact}" if contact else "whatsapp_sqlite/unknown",
            "person_tag": person_tag,
            "turn_idx": idx,
            "external_id": f"wa_sqlite_{pk}",
        })
    return out


# ── Source: WhatsApp pre-processed SFT JSONL ─────────────────────────

def mine_whatsapp_sft_jsonl(
    path: Path = _DEFAULT_WA_SFT_JSONL,
) -> List[Dict[str, Any]]:
    """Load existing pre-processed WhatsApp SFT JSONL.

    Schema (confirmed by inspection):
        {id, messages: [{role, content}], source, quality, category,
         meta: {chat, window, msgs}}

    Lokesh's messages are those in the assistant turn that contain a line
    starting with "Lokesh:" — extracted verbatim without the prefix.
    The pre-processed records are conversation windows; we pull only
    the Lokesh-authored text segments.
    """
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rec_id = obj.get("id") or f"wa_sft_{idx}"
                meta = obj.get("meta") or {}
                chat_id = meta.get("chat") or ""
                messages = obj.get("messages") or []
                # Extract Lokesh-authored lines from the assistant turn
                # (the conversation window includes "Lokesh: <text>" lines)
                for msg in messages:
                    if msg.get("role") != "assistant":
                        continue
                    content = msg.get("content") or ""
                    for part in content.split("\n"):
                        part = part.strip()
                        if part.startswith("Lokesh:"):
                            text = part[len("Lokesh:"):].strip()
                            if text:
                                out.append({
                                    "text": text,
                                    "ts": "",
                                    "source": "whatsapp_sft_preprocessed",
                                    "person_tag": "lokesh",
                                    "turn_idx": idx,
                                    "external_id": f"{rec_id}_msg_{len(out)}",
                                })
    except OSError:
        pass
    return out


# ── Source: iMessage chat.db ──────────────────────────────────────────

def mine_imessage_chatdb(
    db_path: Path = _DEFAULT_IMESSAGE_DB,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Read Lokesh's sent iMessages from chat.db.

    The 'date' column stores nanoseconds since Apple Core Data epoch
    (2001-01-01). Sent messages have is_from_me=1; handle_id=0 means
    the message was sent from self (no recipient handle row). We join
    via chat_message_join → chat to get the chat_identifier (phone/email).
    """
    if not db_path.exists():
        return []
    uri = f"file:{db_path}?mode=ro"
    out: List[Dict[str, Any]] = []
    try:
        conn = sqlite3.connect(uri, uri=True)
        try:
            cur = conn.cursor()
            sql = """
                SELECT
                    m.text,
                    m.date,
                    c.chat_identifier,
                    m.ROWID
                FROM message m
                JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
                JOIN chat c ON cmj.chat_id = c.ROWID
                WHERE m.is_from_me = 1
                  AND m.text IS NOT NULL
                  AND m.text != ''
                ORDER BY m.date DESC
            """
            if limit is not None:
                sql += f" LIMIT {int(limit)}"
            cur.execute(sql)
            rows = cur.fetchall()
        finally:
            conn.close()
    except sqlite3.Error:
        return []

    for idx, (text, raw_date, chat_identifier, rowid) in enumerate(rows):
        ts = ""
        if raw_date is not None:
            try:
                # Nanoseconds → seconds → Unix
                unix_ts = int(raw_date) / 1_000_000_000 + _APPLE_EPOCH_OFFSET
                ts = datetime.datetime.fromtimestamp(
                    unix_ts, tz=datetime.timezone.utc
                ).isoformat()
            except (ValueError, OSError, OverflowError):
                ts = ""
        handle = (chat_identifier or "").strip()
        # person_tag: first segment of identifier (strip +1, keep number prefix)
        person_tag = re.sub(r"[^a-z0-9]", "", handle.lower())[:20] if handle else "unknown"
        out.append({
            "text": text.strip(),
            "ts": ts,
            "source": f"imessage/{handle}" if handle else "imessage/unknown",
            "person_tag": person_tag,
            "turn_idx": idx,
            "external_id": f"imessage_{rowid}",
        })
    return out


# ── Source: git commit messages authored by Lokesh ───────────────────

def mine_git_commits(repo_root: Path = ROOT, limit: int = 500) -> List[Dict[str, Any]]:
    """Lokesh-authored commit messages (subject + body, but skip Claude-co-authored)."""
    import subprocess
    out = []
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "log",
             "--author=Lokesh", f"-{limit}",
             "--pretty=format:%H%x09%aI%x09%B%x1e"],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            return []
        for record in proc.stdout.split("\x1e"):
            record = record.strip()
            if not record:
                continue
            parts = record.split("\t", 2)
            if len(parts) < 3:
                continue
            sha, ts, body = parts
            # Drop Claude-Code-Plugin-Generated co-authored commits
            if "Co-Authored-By: Claude" in body:
                continue
            # Subject is first line; body is rest
            lines = body.split("\n", 1)
            subject = lines[0].strip() if lines else ""
            if subject:
                out.append({
                    "text": subject,
                    "ts": ts,
                    "source": f"git_commit/{sha[:7]}",
                    "turn_idx": 0,
                })
    except (subprocess.TimeoutExpired, OSError):
        pass
    return out


# ── Source: preference_pairs (Lokesh corrections) ────────────────────

def mine_preference_pairs() -> List[Dict[str, Any]]:
    """Lokesh corrections from preference_pairs.jsonl (`chosen` field
    when source=align_correction or explicit_align). These are
    corrections he typed."""
    path = BRAIN / "training" / "preference_pairs.jsonl"
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            src = obj.get("source") or ""
            if src not in ("align_correction", "explicit_align"):
                continue
            chosen = obj.get("chosen") or ""
            if chosen:
                out.append({
                    "text": chosen.strip(),
                    "ts": obj.get("timestamp") or "",
                    "source": "preference_pairs",
                    "turn_idx": idx,
                })
    return out


# ── Voice scorer ─────────────────────────────────────────────────────

# Pre-compiled patterns for score_lokesh_voice
_AI_HEDGES = re.compile(
    r"\b(perhaps|consider|might want to|let me know if|feel free|I should note|"
    r"It'?s worth|please consider|professional help|qualified support)\b",
    re.IGNORECASE,
)
_MD_HEADERS = re.compile(r"^#{1,3}\s", re.MULTILINE)
_EM_DASH_RE = re.compile(r"—")
_LOWERCASE_I = re.compile(r"(?<!\w)i(?!\w)")          # standalone lowercase i
_HINGLISH = re.compile(
    r"\b(kya|bhai|yaar|thoda|matlab|haan|nahi|kahin|abhi)\b", re.IGNORECASE
)
_PERSONAL_REFS = re.compile(
    r"\b(manju|mj|priya|lokesh|weihan|shilpa)\b", re.IGNORECASE
)
_PROJECT_REFS = re.compile(
    r"\b(nucleus|axis|tb|cowork|eidetic)\b", re.IGNORECASE
)
_CASUAL_FILLERS_START = re.compile(
    r"^(yeah|ok|btw|tbh|idk|lol)\b", re.IGNORECASE
)
_TERMINAL_PUNCT = re.compile(r"[.!?:]\s*$")


def score_lokesh_voice(text: str) -> float:
    """Heuristic 15-feature voice scorer. Returns float in [0.0, 1.0].

    Score starts at 0.5 (neutral). Negative signals pull it down,
    positive signals push it up. Clipped to [0.0, 1.0].

    Negative signals (lower score):
      - AI hedging phrases ("perhaps", "consider", etc.)
      - Markdown headers (##)
      - Em-dash density (> 1)
      - AI qualifier phrases ("I should note", etc.)
      - Mentions professional/qualified help
      - Length > 500 chars (likely paste — each negative weight doubles)

    Positive signals (higher score):
      - Standalone lowercase 'i' pronoun
      - Hinglish words (kya, bhai, yaar, ...)
      - Personal name refs (manju, mj, priya, weihan, shilpa)
      - Project refs (nucleus, axis, tb, cowork, eidetic)
      - Casual fillers at start of message (yeah, ok, btw, tbh, idk, lol)
      - Length < 80 chars (short = typed, not pasted)
      - No terminal punctuation (casual register)
    """
    if not text:
        return 0.0

    score = 0.5
    n = len(text)
    # Weight multiplier: long texts penalise negatives more
    neg_weight = 0.12 if n > 500 else 0.08

    # ── Negative signals ─────────────────────────────────────────────
    # AI hedges (each match counts, up to 3)
    hedge_hits = min(len(_AI_HEDGES.findall(text)), 3)
    score -= hedge_hits * neg_weight

    # Markdown headers (structured content — strong negative regardless of length)
    if _MD_HEADERS.search(text):
        score -= neg_weight * 2.5

    # Em-dash density > 1
    if _EM_DASH_RE.subn("", text)[1] > 1:
        score -= neg_weight

    # ── Positive signals ─────────────────────────────────────────────
    pos_weight = 0.08

    # Standalone lowercase i
    if _LOWERCASE_I.search(text):
        score += pos_weight

    # Hinglish words (each unique match)
    hinglish_hits = min(len(set(_HINGLISH.findall(text.lower()))), 3)
    score += hinglish_hits * pos_weight

    # Personal refs
    if _PERSONAL_REFS.search(text):
        score += pos_weight

    # Project refs
    if _PROJECT_REFS.search(text):
        score += pos_weight

    # Casual fillers at message start
    if _CASUAL_FILLERS_START.search(text.strip()):
        score += pos_weight

    # Short message (likely typed)
    if n < 80:
        score += pos_weight

    # No terminal punctuation (casual)
    if not _TERMINAL_PUNCT.search(text.strip()):
        score += pos_weight * 0.5

    return max(0.0, min(1.0, score))


# ── Dedupe ───────────────────────────────────────────────────────────

def dedupe(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Drop duplicate texts. Keep first occurrence."""
    seen = set()
    out = []
    for r in records:
        h = hashlib.sha1(r["text"].encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        out.append(r)
    return out


# ── Embedding ────────────────────────────────────────────────────────

def _embed_batch(texts: List[str]) -> List[List[float]]:
    """Batch embed via local Ollama (qwen3-embedding:0.6b). Reuses the
    same embedding infra brain_rag.py uses for RAG — no new dependencies.

    Falls back to deterministic hash-based embeddings if Ollama isn't
    reachable (lets the pipeline run in CI/test environments without
    a live model).
    """
    sys.path.insert(0, str(ROOT))
    try:
        from providers.brain_rag import _embed as ollama_embed
    except ImportError:
        return [_hash_embedding(t) for t in texts]
    out = []
    fail_count = 0
    for i, text in enumerate(texts):
        if i % 200 == 0 and i > 0:
            print(f"  [{i}/{len(texts)}] embedded ({fail_count} fallbacks so far)")
        emb = ollama_embed(text[:8192])  # cap length for embedder
        if emb is None or not emb:
            emb = _hash_embedding(text)
            fail_count += 1
        out.append(emb)
    if fail_count:
        print(f"  ⚠ {fail_count} embedding failures fell back to hash-embed")
    return out


def _hash_embedding(text: str, dim: int = 384) -> List[float]:
    """Deterministic pseudo-embedding for fallback."""
    import struct
    h = hashlib.sha256(text.encode()).digest()
    # Repeat hash to fill dim, normalize
    vec = []
    while len(vec) < dim:
        for i in range(0, len(h) - 4, 4):
            vec.append(struct.unpack("f", h[i:i+4])[0] / 1e30)
            if len(vec) >= dim:
                break
    # Normalize
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def embed_with_cache(records: List[Dict[str, Any]],
                    cache_dir: Path = EMBED_CACHE_DIR) -> List[List[float]]:
    """Embed records' text, caching by content hash so re-runs are fast."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "embeddings.jsonl"
    cache: Dict[str, List[float]] = {}
    if cache_path.exists():
        try:
            with cache_path.open() as f:
                for line in f:
                    obj = json.loads(line)
                    cache[obj["h"]] = obj["v"]
        except (json.JSONDecodeError, OSError):
            cache = {}
    # Identify uncached
    to_embed: List[Tuple[int, str, str]] = []  # (idx, text, hash)
    embeddings: List[Optional[List[float]]] = [None] * len(records)
    for i, r in enumerate(records):
        h = hashlib.sha1(r["text"].encode()).hexdigest()
        r["_hash"] = h
        if h in cache:
            embeddings[i] = cache[h]
        else:
            to_embed.append((i, r["text"], h))
    if to_embed:
        print(f"[voice] embedding {len(to_embed)} new texts "
              f"({len(records) - len(to_embed)} cache hits)...")
        new_vecs = _embed_batch([t for _, t, _ in to_embed])
        # Append to cache
        with cache_path.open("a") as f:
            for (i, _, h), v in zip(to_embed, new_vecs):
                embeddings[i] = v
                f.write(json.dumps({"h": h, "v": v}) + "\n")
    return [e for e in embeddings if e is not None]


# ── Clustering ───────────────────────────────────────────────────────

def cluster_kmeans(embeddings: List[List[float]],
                  n_clusters: int = 30) -> List[int]:
    """KMeans cluster assignment per record. Returns list of cluster ids.

    Tries sklearn first (faster, more robust). Falls back to a pure-Python
    Lloyd's algorithm implementation that uses numpy if available, else
    pure-Python (slower but no dependency).
    """
    if len(embeddings) <= n_clusters:
        return list(range(len(embeddings)))

    try:
        import numpy as np
        from sklearn.cluster import KMeans
        arr = np.array(embeddings, dtype="float32")
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=5)
        return km.fit_predict(arr).tolist()
    except ImportError:
        pass

    try:
        import numpy as np
        return _kmeans_numpy(embeddings, n_clusters)
    except ImportError:
        pass

    # Pure-Python fallback (slow but works)
    return _kmeans_pure_python(embeddings, n_clusters)


def _kmeans_numpy(embeddings: List[List[float]], k: int,
                  max_iter: int = 50, seed: int = 42) -> List[int]:
    """Pure-numpy KMeans (Lloyd's algorithm). No sklearn needed."""
    import numpy as np
    rng = np.random.RandomState(seed)
    X = np.array(embeddings, dtype="float32")
    n = len(X)
    # k-means++ init
    indices = [int(rng.randint(n))]
    for _ in range(k - 1):
        d2 = np.full(n, np.inf, dtype="float32")
        for ci in indices:
            diff = X - X[ci]
            d = (diff * diff).sum(axis=1)
            d2 = np.minimum(d2, d)
        probs = d2 / d2.sum()
        indices.append(int(rng.choice(n, p=probs)))
    centroids = X[indices].copy()
    labels = np.zeros(n, dtype="int32")
    for _iter in range(max_iter):
        # Assign
        # cosine on normalized → 1 - dot
        dists = np.zeros((n, k), dtype="float32")
        for ci in range(k):
            diff = X - centroids[ci]
            dists[:, ci] = (diff * diff).sum(axis=1)
        new_labels = dists.argmin(axis=1).astype("int32")
        if (new_labels == labels).all() and _iter > 0:
            break
        labels = new_labels
        # Update centroids
        for ci in range(k):
            mask = labels == ci
            if mask.any():
                centroids[ci] = X[mask].mean(axis=0)
    return labels.tolist()


def _kmeans_pure_python(embeddings: List[List[float]], k: int,
                        max_iter: int = 30) -> List[int]:
    """Pure-Python KMeans fallback. Slow but dependency-free.

    Used only when both sklearn and numpy are unavailable. For large
    corpora this is too slow — install numpy+sklearn for production.
    """
    import random
    random.seed(42)
    n = len(embeddings)
    dim = len(embeddings[0])
    # Random init from data
    centroid_idxs = random.sample(range(n), k)
    centroids = [list(embeddings[i]) for i in centroid_idxs]
    labels = [0] * n

    def sq_dist(a, b):
        return sum((x - y) ** 2 for x, y in zip(a, b))

    for _ in range(max_iter):
        new_labels = [
            min(range(k), key=lambda c: sq_dist(embeddings[i], centroids[c]))
            for i in range(n)
        ]
        if new_labels == labels:
            break
        labels = new_labels
        # Update
        sums = [[0.0] * dim for _ in range(k)]
        counts = [0] * k
        for i, c in enumerate(labels):
            counts[c] += 1
            for d in range(dim):
                sums[c][d] += embeddings[i][d]
        for c in range(k):
            if counts[c]:
                centroids[c] = [s / counts[c] for s in sums[c]]
    return labels


# ── Stratification ───────────────────────────────────────────────────

def stratify_sample(records: List[Dict[str, Any]],
                   clusters: List[int],
                   per_cluster: int = 3,
                   length_diverse: bool = True) -> List[Dict[str, Any]]:
    """Pick top-N from each cluster, biased toward length diversity.

    For each cluster, pick `per_cluster` records that span the length
    distribution within that cluster (short, medium, long). This avoids
    "all clusters dominated by short fragments" or vice versa.
    """
    by_cluster: Dict[int, List[int]] = defaultdict(list)
    for i, c in enumerate(clusters):
        by_cluster[c].append(i)

    selected_indices: List[int] = []
    for c, idxs in by_cluster.items():
        if not length_diverse or len(idxs) <= per_cluster:
            selected_indices.extend(idxs[:per_cluster])
            continue
        # Sort by length, pick from short/mid/long buckets
        idxs_by_length = sorted(idxs, key=lambda i: len(records[i]["text"]))
        n = len(idxs_by_length)
        # Pick evenly spaced indices across the sorted-by-length list
        picks = []
        for k in range(per_cluster):
            pos = k * (n - 1) // max(per_cluster - 1, 1) if per_cluster > 1 else n // 2
            picks.append(idxs_by_length[pos])
        selected_indices.extend(picks)

    # Dedupe (length-diverse picks could overlap on small clusters)
    seen = set()
    out = []
    for i in selected_indices:
        if i in seen:
            continue
        seen.add(i)
        rec = dict(records[i])
        rec["cluster"] = clusters[i]
        out.append(rec)
    return out


# ── Output ───────────────────────────────────────────────────────────

def write_corpus(records: List[Dict[str, Any]], path: Path = CORPUS_FILE) -> None:
    """Write full mined corpus to JSONL (one record per line)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            r_clean = {k: v for k, v in r.items() if not k.startswith("_")}
            f.write(json.dumps(r_clean, ensure_ascii=False) + "\n")


def write_candidates(samples: List[Dict[str, Any]],
                     path: Path = CANDIDATES_FILE) -> None:
    """Write top-N candidates as a markdown file for Lokesh editorial pass.

    Each candidate has metadata + the text. Lokesh promotes approved ones
    to .brain/voice/lokesh.md (the trusted pool) by hand or via a
    promotion script.

    Candidates are grouped first by score band (HIGH >= 0.7, MEDIUM 0.5–0.7),
    then by cluster within each band so editorial focus lands on highest-signal
    records first.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    def _band(s: Dict[str, Any]) -> str:
        v = s.get("voice_score", 0.5)
        return "HIGH" if v >= 0.7 else "MEDIUM"

    high = [s for s in samples if _band(s) == "HIGH"]
    medium = [s for s in samples if _band(s) == "MEDIUM"]

    lines = [
        "# Voice Candidates — Editorial Pass",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Count: {len(samples)} candidates (HIGH={len(high)}, MEDIUM={len(medium)})",
        "",
        "Process: review each, promote approved → `.brain/voice/lokesh.md`",
        "(the trusted pool). Drop ones that don't sound like you. The corpus",
        "below is stratified for diversity, so a good editorial pass keeps the",
        "spread, not just your favorite tone.",
        "",
        "Format: each candidate has source + cluster + score + text. Promote by",
        "copying the text block (with leading >) into `lokesh.md` exemplars.",
        "",
        "---",
        "",
    ]

    for band_label, band_items in [("HIGH (score >= 0.7)", high),
                                   ("MEDIUM (score 0.5–0.7)", medium)]:
        if not band_items:
            continue
        lines.append(f"# Score Band: {band_label}  ({len(band_items)} candidates)")
        lines.append("")
        by_cluster: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for s in band_items:
            by_cluster[s.get("cluster", 0)].append(s)
        for cluster_id in sorted(by_cluster):
            items = by_cluster[cluster_id]
            lines.append(
                f"## Cluster {cluster_id} "
                f"({len(items)} candidate{'s' if len(items) != 1 else ''})"
            )
            lines.append("")
            for s in items:
                score_str = f"{s.get('voice_score', 0.0):.2f}"
                lines.append(
                    f"**source**: `{s['source']}` | "
                    f"**score**: {score_str} | "
                    f"**chars**: {len(s['text'])} | "
                    f"**ts**: {s.get('ts', '?')[:19]}"
                )
                lines.append("")
                # Quote the candidate
                for line in s["text"].split("\n"):
                    lines.append(f"> {line}")
                lines.append("")
                lines.append("---")
                lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


# ── Trusted-pool helpers (used by composer) ──────────────────────────

def initialize_trusted_pool_if_missing(path: Path = TRUSTED_FILE) -> None:
    """Create lokesh.md template if missing. Lokesh fills in by promoting
    approved candidates from lokesh_candidates.md."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    template = """# Lokesh Voice Anchor

Style rules + curated exemplars. Composer (Sonnet/Opus) gets these as a
preamble so it speaks AS Lokesh, not AS an assistant addressing him.

## Rules

- Lowercase i (always)
- Fragmentary sentences ok; short and punchy
- No markdown headers in casual messages
- Casual hinglish/code-switching natural
- Direct, blunt, no hedging
- Avoid: "I think", "perhaps", "you might consider", "let me know if"
- No moral framing or disclaimers
- When drafting messages, output ONLY the message text

## Exemplars (curated)

Promote here from `.brain/voice/lokesh_candidates.md` after editorial pass.
Each exemplar wrapped in a blockquote so the composer sees it as quoted
target tone.

<!-- example shape:
> what's the call here. i don't want to wait
-->

"""
    path.write_text(template, encoding="utf-8")


# ── Main ─────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="write corpus + candidates (default: dry-run report only)")
    ap.add_argument("--max-sessions", type=int, default=100,
                    help="max recent CC session files to scan (default 100)")
    ap.add_argument("--clusters", type=int, default=30,
                    help="number of clusters for stratification (default 30)")
    ap.add_argument("--per-cluster", type=int, default=3,
                    help="candidates picked per cluster (default 3)")
    ap.add_argument("--no-cc", action="store_true",
                    help="skip Claude Code session mining (use only other sources)")
    # ── New enrichment sources ─────────────────────────────────────
    ap.add_argument(
        "--whatsapp-sqlite",
        metavar="PATH",
        nargs="?",
        const="auto",
        default=None,
        help="mine WhatsApp ChatStorage.sqlite; omit value to use default path",
    )
    ap.add_argument(
        "--whatsapp-sft",
        metavar="PATH",
        nargs="?",
        const="auto",
        default=None,
        help="mine pre-processed WhatsApp SFT JSONL; omit value to use default path",
    )
    ap.add_argument(
        "--imessage",
        metavar="PATH",
        nargs="?",
        const="auto",
        default=None,
        help="mine iMessage chat.db; omit value to use default path",
    )
    ap.add_argument(
        "--score-threshold",
        type=float,
        default=0.5,
        help="drop records below this voice score (default 0.5; 0 = keep all)",
    )
    args = ap.parse_args()

    print("=== Voice Corpus Builder ===")
    sources_summary: List[str] = []

    all_records: List[Dict[str, Any]] = []

    # Mine existing sources
    if not args.no_cc:
        cc_records = mine_cc_sessions(max_files=args.max_sessions)
        sources_summary.append(f"  cc_sessions: {len(cc_records)} raw user turns "
                               f"(from up to {args.max_sessions} files)")
        all_records.extend(cc_records)

    shadow_records = mine_shadow_log()
    sources_summary.append(f"  shadow_log: {len(shadow_records)} queries")
    all_records.extend(shadow_records)

    git_records = mine_git_commits()
    sources_summary.append(f"  git_commits: {len(git_records)} subjects")
    all_records.extend(git_records)

    pref_records = mine_preference_pairs()
    sources_summary.append(f"  preference_pairs: {len(pref_records)} corrections")
    all_records.extend(pref_records)

    # ── New enrichment sources ─────────────────────────────────────
    if args.whatsapp_sqlite is not None:
        wa_path = (
            _DEFAULT_WA_SQLITE
            if args.whatsapp_sqlite == "auto"
            else Path(args.whatsapp_sqlite)
        )
        wa_records = mine_whatsapp_sqlite(wa_path)
        sources_summary.append(
            f"  whatsapp_sqlite: {len(wa_records)} sent messages (from {wa_path.name})"
        )
        all_records.extend(wa_records)

    if args.whatsapp_sft is not None:
        sft_path = (
            _DEFAULT_WA_SFT_JSONL
            if args.whatsapp_sft == "auto"
            else Path(args.whatsapp_sft)
        )
        sft_records = mine_whatsapp_sft_jsonl(sft_path)
        sources_summary.append(
            f"  whatsapp_sft_jsonl: {len(sft_records)} Lokesh turns (from {sft_path.name})"
        )
        all_records.extend(sft_records)

    if args.imessage is not None:
        imsg_path = (
            _DEFAULT_IMESSAGE_DB
            if args.imessage == "auto"
            else Path(args.imessage)
        )
        imsg_records = mine_imessage_chatdb(imsg_path)
        sources_summary.append(
            f"  imessage: {len(imsg_records)} sent messages (from {imsg_path.name})"
        )
        all_records.extend(imsg_records)

    print("\nSources scanned:")
    for s in sources_summary:
        print(s)
    raw_total = len(all_records)
    print(f"  TOTAL raw: {raw_total}")

    # Filter
    filtered = [r for r in all_records if is_voice_relevant(r["text"])]
    print(f"\nAfter voice-relevance filter: {len(filtered)} records "
          f"({100 * len(filtered) // max(raw_total, 1)}% pass rate)")

    # Dedupe (by text hash; respects external_id for idempotency across runs)
    deduped = dedupe(filtered)
    print(f"After dedupe: {len(deduped)} unique records")

    # ── Voice score every record ───────────────────────────────────
    for r in deduped:
        r["voice_score"] = score_lokesh_voice(r["text"])

    before_score = len(deduped)
    if args.score_threshold > 0:
        deduped = [r for r in deduped if r["voice_score"] >= args.score_threshold]
    after_score = len(deduped)
    print(
        f"After voice-score filter (threshold={args.score_threshold:.2f}): "
        f"{after_score} records "
        f"({before_score - after_score} dropped)"
    )

    # Score band distribution
    high = sum(1 for r in deduped if r["voice_score"] >= 0.7)
    medium = after_score - high
    print(f"  Score bands: HIGH(>=0.7)={high}, MEDIUM(0.5-0.7)={medium}")

    if len(deduped) < args.clusters:
        print(f"  fewer records ({len(deduped)}) than clusters ({args.clusters}); "
              f"reducing clusters to {max(len(deduped) // 2, 1)}")
        args.clusters = max(len(deduped) // 2, 1)

    # Length distribution
    lengths = [len(r["text"]) for r in deduped]
    if lengths:
        print(f"\nLength stats:")
        print(f"  min={min(lengths)} max={max(lengths)} "
              f"avg={sum(lengths)//len(lengths)} "
              f"median={sorted(lengths)[len(lengths)//2]}")

    # Source distribution
    by_source: Counter = Counter(r["source"].split("/")[0] for r in deduped)
    print(f"\nDistribution by source:")
    for src, n in by_source.most_common():
        print(f"  {src}: {n}")

    if not args.apply:
        print("\n[dry-run] Re-run with --apply to embed + cluster + write corpus + candidates")
        return 0

    # Embed
    print(f"\nEmbedding {len(deduped)} records...")
    t0 = time.time()
    embeddings = embed_with_cache(deduped)
    print(f"  done in {time.time() - t0:.1f}s")

    # Cluster
    print(f"\nClustering into {args.clusters} clusters...")
    clusters = cluster_kmeans(embeddings, n_clusters=args.clusters)
    cluster_sizes = Counter(clusters)
    print(f"  cluster size range: {min(cluster_sizes.values())} - {max(cluster_sizes.values())}")
    print(f"  cluster distribution: "
          + ", ".join(f"{c}:{cluster_sizes[c]}" for c in sorted(cluster_sizes)[:10])
          + ("..." if len(cluster_sizes) > 10 else ""))

    # Stratify-sample
    samples = stratify_sample(deduped, clusters,
                              per_cluster=args.per_cluster, length_diverse=True)
    print(f"\nStratified sample: {len(samples)} candidates "
          f"(target: {args.clusters} x {args.per_cluster} = {args.clusters * args.per_cluster}, "
          f"actual reduced by overlap on small clusters)")

    # Write corpus + candidates
    write_corpus(deduped, CORPUS_FILE)
    write_candidates(samples, CANDIDATES_FILE)
    initialize_trusted_pool_if_missing(TRUSTED_FILE)

    high_cands = sum(1 for s in samples if s.get("voice_score", 0) >= 0.7)
    med_cands = len(samples) - high_cands
    print(f"\n[RESULT] raw={raw_total} | after_filter={len(filtered)} | "
          f"after_score={after_score} | candidates={len(samples)} "
          f"(HIGH={high_cands}, MEDIUM={med_cands})")
    print(f"  Wrote corpus  -> {CORPUS_FILE}")
    print(f"  Wrote candidates -> {CANDIDATES_FILE}")
    print(f"  Trusted pool template -> {TRUSTED_FILE}")
    print(f"\nEditorial focus: {'HIGH band' if high_cands >= med_cands else 'MEDIUM band'} "
          f"has more volume")
    return 0


if __name__ == "__main__":
    sys.exit(main())
