#!/usr/bin/env python3
"""Tier 2 digest builder — session-stable context-injection digest.

Per .brain/research/2026-04-28_tier_architecture/08_tier2_design.md v0.2:
  - Component 1: trigger surface (this script invoked from SessionStart hook)
  - Component 2: retrieval engine — naive keyword scan over memory + policies
                 + engrams; SELECT-not-GENERATE pattern (TB ranks chunk IDs,
                 Python assembles real chunks)
  - Component 3: output surface + sub-step 3a strip-anonymize

v0.2 first ship: Stage-1 (Python keyword scan) only. TB ranking gated behind
--use-tb flag, off by default. Prove pipeline works end-to-end first, codify
TB integration after live-fire passes.

Output: ~3-5K-token Markdown digest at the path given by --out.
Token budget enforced softly — if naive selection produces more, truncate to
the top scoring chunks until ≤ budget.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ._strip_local_state import strip_local_state

# ----------------- Config -----------------

DEFAULT_TOKEN_BUDGET = 4500  # below the 5K target, leaves headroom
APPROX_BYTES_PER_TOKEN = 4   # crude but consistent
DEFAULT_MAX_CHUNKS = 30      # max items considered before scoring

MEMORY_DIR = (
    Path.home() / ".claude" / "projects"
    / "-Users-lokeshgarg-ai-mvp-backend" / "memory"
)
REPO_ROOT = Path("/Users/lokeshgarg/ai-mvp-backend")
POLICIES_DIR = REPO_ROOT / ".brain" / "policies"
ENGRAMS_LEDGER = REPO_ROOT / ".brain" / "engrams" / "ledger.jsonl"

_KILLSWITCH_ENV = "NUCLEUS_TIER2_DISABLED"


# ----------------- Data shapes -----------------

@dataclass
class Chunk:
    """One retrievable unit (memory file, policy file, or engram)."""
    source: str                 # 'memory' | 'policy' | 'engram'
    name: str                   # human-readable identifier
    path: Path | None           # source file (None for engram inline content)
    description: str            # short matchable text (frontmatter description / Rule line / engram value)
    body: str                   # full content to include in digest
    score: float = 0.0          # keyword-overlap score


# ----------------- Session-topic extraction -----------------

def extract_session_topic(jsonl_path: Path | None, *, max_recent_user_msgs: int = 5) -> str:
    """Read CC session JSONL (if present) and return concatenated last N user prompts.

    Falls back to empty string if no session JSONL exists yet (cold start);
    caller treats that as "use project-default keywords".
    """
    if not jsonl_path or not jsonl_path.exists():
        return ""
    msgs: list[str] = []
    try:
        with jsonl_path.open() as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") != "user":
                    continue
                msg = rec.get("message", {})
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = " ".join(
                        b.get("text", "") for b in content
                        if isinstance(b, dict) and b.get("type") == "text"
                    )
                if isinstance(content, str) and content.strip():
                    msgs.append(content.strip()[:500])  # cap each msg
    except OSError:
        return ""
    return " | ".join(msgs[-max_recent_user_msgs:])


# ----------------- Stage 1 — Python keyword scan -----------------

_STOPWORDS = frozenset({
    "the", "and", "for", "with", "this", "that", "from", "have", "what",
    "when", "where", "your", "you", "but", "are", "was", "not", "can",
    "any", "all", "some", "into", "out", "to", "of", "in", "on", "at",
    "is", "it", "be", "as", "an", "or", "by",
})


def _tokens(text: str) -> set[str]:
    """Tokenize: lowercase, alphanumeric runs, ≥3 chars, drop stopwords."""
    if not text:
        return set()
    raw = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
    return {t for t in raw if t not in _STOPWORDS}


def _read_frontmatter_description(path: Path) -> tuple[str, str]:
    """Return (description, full_body) from a memory file with YAML-ish frontmatter."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ("", "")
    desc = ""
    m = re.search(r"^description:\s*(.+?)$", text, re.MULTILINE)
    if m:
        desc = m.group(1).strip()
    return (desc, text)


def _read_policy_rule(path: Path) -> tuple[str, str]:
    """Return (rule_first_line, full_body) from a .brain/policies file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ("", "")
    m = re.search(r"\*\*Rule:\*\*\s*([^\n]+)", text)
    return (m.group(1).strip() if m else "", text)


def scan_memories(topic_tokens: set[str]) -> list[Chunk]:
    out: list[Chunk] = []
    if not MEMORY_DIR.exists():
        return out
    for p in MEMORY_DIR.glob("*.md"):
        if p.name == "MEMORY.md":
            continue
        desc, body = _read_frontmatter_description(p)
        if not desc:
            continue
        score = len(_tokens(desc) & topic_tokens)
        if score > 0:
            out.append(Chunk(
                source="memory", name=p.stem, path=p,
                description=desc, body=body, score=float(score),
            ))
    return out


def scan_policies(topic_tokens: set[str]) -> list[Chunk]:
    out: list[Chunk] = []
    if not POLICIES_DIR.exists():
        return out
    for p in POLICIES_DIR.glob("*.md"):
        if p.name == "README.md":
            continue
        rule, body = _read_policy_rule(p)
        if not rule:
            continue
        score = len(_tokens(rule) & topic_tokens)
        if score > 0:
            out.append(Chunk(
                source="policy", name=p.stem, path=p,
                description=rule, body=body, score=float(score),
            ))
    return out


def scan_engrams(topic_tokens: set[str], *, min_intensity: int = 7, max_emit: int = 10) -> list[Chunk]:
    """Fallback only — scan high-intensity engrams for keyword overlap."""
    out: list[Chunk] = []
    if not ENGRAMS_LEDGER.exists():
        return out
    try:
        with ENGRAMS_LEDGER.open() as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("intensity", 0) < min_intensity:
                    continue
                if rec.get("deleted"):
                    continue
                key = rec.get("key", "")
                value = rec.get("value", "")
                desc = f"{key}: {value[:200]}"
                score = len(_tokens(desc) & topic_tokens)
                if score > 0:
                    out.append(Chunk(
                        source="engram", name=key, path=None,
                        description=desc, body=f"{key}\n\n{value}",
                        score=float(score),
                    ))
    except OSError:
        return out
    out.sort(key=lambda c: -c.score)
    return out[:max_emit]


# ----------------- Stage 3 — assemble digest -----------------

def _approx_tokens(text: str) -> int:
    return max(1, len(text.encode("utf-8")) // APPROX_BYTES_PER_TOKEN)


def assemble_digest(chunks: Iterable[Chunk], token_budget: int) -> str:
    """Concatenate top-scoring chunks until budget exhausted, with section headers.

    Caller has already strip-anonymized the chunk bodies; assemble preserves
    that property by NOT re-introducing local state via section headers
    (uses chunk.name only, not chunk.path).
    """
    sorted_chunks = sorted(chunks, key=lambda c: -c.score)
    parts: list[str] = []
    parts.append("# Tier 2 session digest\n")
    parts.append(
        "Session-stable context per .brain/research/2026-04-28_tier_architecture/"
        "08_tier2_design.md. Selected chunks ranked by keyword overlap with "
        "session topic. Strip-anonymize pass applied per Component 3 sub-step 3a.\n"
    )
    used_tokens = _approx_tokens("\n".join(parts))
    n_included = 0
    for c in sorted_chunks:
        section = f"\n## {c.source}: {c.name} (score={c.score:.1f})\n\n{c.body.strip()}\n"
        section_tokens = _approx_tokens(section)
        if used_tokens + section_tokens > token_budget:
            break
        parts.append(section)
        used_tokens += section_tokens
        n_included += 1
    parts.append(
        f"\n---\n"
        f"Digest stats: {n_included} chunk(s), ~{used_tokens} approx tokens."
    )
    return "".join(parts)


# ----------------- Main entry point -----------------

def build_digest(
    out_path: Path,
    *,
    session_jsonl: Path | None = None,
    project_default_keywords: list[str] | None = None,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
) -> dict:
    """Build a session digest and write to out_path. Returns stats dict."""
    if os.environ.get(_KILLSWITCH_ENV):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("# Tier 2 disabled via NUCLEUS_TIER2_DISABLED\n")
        return {"ok": True, "disabled": True, "n_chunks": 0}

    topic = extract_session_topic(session_jsonl)
    if not topic and project_default_keywords:
        topic = " ".join(project_default_keywords)
    topic_tokens = _tokens(topic) if topic else set()
    # If still empty, use a baseline of project-relevant terms so we always
    # produce *something* useful.
    if not topic_tokens:
        topic_tokens = {"nucleus", "claude", "substrate", "policy", "feedback", "engram"}

    candidates = (
        scan_memories(topic_tokens)
        + scan_policies(topic_tokens)
    )
    if len(candidates) < 3:
        candidates += scan_engrams(topic_tokens)

    # Sub-step 3a: strip-anonymize each chunk body BEFORE assembly.
    for c in candidates:
        c.body = strip_local_state(c.body)
        c.description = strip_local_state(c.description)

    digest = assemble_digest(candidates, token_budget=token_budget)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text(digest, encoding="utf-8")
    tmp.replace(out_path)  # atomic rename

    return {
        "ok": True,
        "disabled": False,
        "n_candidates": len(candidates),
        "n_topic_tokens": len(topic_tokens),
        "approx_token_count": _approx_tokens(digest),
        "out_path": str(out_path),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path,
                    help="Output digest path (will be atomically renamed from .tmp)")
    ap.add_argument("--session-jsonl", type=Path, default=None,
                    help="CC session JSONL to extract recent user prompts from")
    ap.add_argument("--token-budget", type=int, default=DEFAULT_TOKEN_BUDGET)
    args = ap.parse_args(argv)

    stats = build_digest(
        out_path=args.out,
        session_jsonl=args.session_jsonl,
        token_budget=args.token_budget,
    )
    print(json.dumps(stats, indent=2))
    return 0 if stats.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
