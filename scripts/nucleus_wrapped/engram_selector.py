"""Engram pre-load selector for the experimental lane (§2.2).

Deterministic, snapshot-driven selector that produces engram_prefix.<run_id>.md
from a frozen engram snapshot + recording task_tags. Implements the four
predicates and the 12K-token budget policy spelled out in
phase2_experiment_design.md §2.2.

Spec anchors:
- predicate set: phase2_experiment_design.md §2.2 lines 122-126
- budget + overflow: phase2_experiment_design.md §2.2 line 128
- self-review crack #3: BM25 index regenerated from frozen snapshot
  (see cowork relay_20260421_131131_eac569c5 confirming the fix)

This module is pure-data (snapshot in -> rendered text + manifest metadata
out). It does NOT mutate the snapshot or touch the live .brain/engrams/ store;
the launcher pins the snapshot upstream in step_1.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import pathlib
import re
from typing import Iterable

CHARS_PER_TOKEN = 4  # Anthropic rule-of-thumb; replace with tiktoken if a hard
                     # ceiling becomes load-bearing.
DEFAULT_BUDGET_TOKENS = 12_000
TOP_N_HIGH_INTENSITY = 20
TOP_N_BM25 = 10
LAST_N_END_OF_DAY = 3
HIGH_INTENSITY_CONTEXTS = ("Feature", "Architecture", "Decision")
HIGH_INTENSITY_WINDOW_DAYS = 14
END_OF_DAY_KEY_PREFIX = "daily_summary_"
HARD_RULE_SECTION_HEADER = "## ⛔ HARD RULES"
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")


@dataclasses.dataclass
class EngramRecord:
    key: str
    value: str
    context: str
    intensity: int
    timestamp: str  # ISO


@dataclasses.dataclass
class SelectionResult:
    rendered: str
    estimated_tokens: int
    overflow_dropped: list[str]
    sections: dict[str, list[str]]


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def load_snapshot(snapshot_path: pathlib.Path) -> list[EngramRecord]:
    """Load history.jsonl-shaped snapshot.

    Tolerant of the {key, op_type, snapshot:{...}} envelope the live store
    uses, and of the flat {key, value, context, intensity, timestamp} shape
    that snapshot fixtures may use.
    """
    out: list[EngramRecord] = []
    with snapshot_path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = row.get("snapshot", row) if isinstance(row, dict) else None
            if not isinstance(payload, dict):
                continue
            try:
                out.append(
                    EngramRecord(
                        key=str(payload["key"]),
                        value=str(payload.get("value", "")),
                        context=str(payload.get("context", "")),
                        intensity=int(payload.get("intensity", 0)),
                        timestamp=str(payload.get("timestamp", "")),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
    return out


def _extract_md_section(text: str, header_prefix: str) -> str:
    """Return the body of a markdown ## section.

    Matches by header prefix (not exact equality) — MEMORY.md's hard-rule
    header carries an inline annotation (e.g. ``## ⛔ HARD RULES (read before
    any cross-session action)``) that the spec abbreviates. Section ends at
    the next ``## `` heading or EOF.
    """
    out: list[str] = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if not in_section and stripped.startswith(header_prefix):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            out.append(line)
    return "\n".join(out).strip()


def select_hard_rule(memory_index: pathlib.Path) -> tuple[str, list[str]]:
    """Predicate 1. Read MEMORY.md, extract HARD RULES section, inline linked
    .md files verbatim. Returns (rendered_text, list_of_filenames_used)."""
    if not memory_index.exists():
        return ("", [])
    text = memory_index.read_text()
    section = _extract_md_section(text, HARD_RULE_SECTION_HEADER)
    if not section:
        return ("", [])
    md_dir = memory_index.parent
    rendered_parts: list[str] = ["## Hard rules (always loaded, never dropped)\n"]
    keys_used: list[str] = []
    seen: set[str] = set()
    for fname in _MD_LINK_RE.findall(section):
        if fname in seen:
            continue
        seen.add(fname)
        fpath = md_dir / fname
        if not fpath.exists():
            continue
        try:
            body = fpath.read_text()
        except OSError:
            continue
        rendered_parts.append(f"### HARD RULE — {fname}\n\n{body.rstrip()}\n")
        keys_used.append(fname)
    if not keys_used:
        return ("", [])
    return ("\n".join(rendered_parts), keys_used)


def select_top_intensity(
    records: list[EngramRecord],
    *,
    now: dt.datetime,
    n: int = TOP_N_HIGH_INTENSITY,
    contexts: tuple[str, ...] = HIGH_INTENSITY_CONTEXTS,
    window_days: int = HIGH_INTENSITY_WINDOW_DAYS,
) -> list[EngramRecord]:
    """Predicate 2. Top-N highest-intensity Feature/Architecture/Decision engrams from last 14d."""
    cutoff = (now - dt.timedelta(days=window_days)).isoformat()
    in_window = [r for r in records if r.context in contexts and r.timestamp >= cutoff]
    return sorted(in_window, key=lambda r: (-r.intensity, r.timestamp))[:n]


def select_bm25(
    records: list[EngramRecord],
    task_tags: list[str],
    *,
    n: int = TOP_N_BM25,
) -> list[EngramRecord]:
    """Predicate 3. Task-tag BM25 match top-N over the frozen snapshot.

    Crack-3 fix: the BM25 index is built from the ``records`` argument (frozen
    snapshot), not from a cached on-disk index. Running this against the same
    snapshot the prefix renders from is the correctness guarantee.

    Falls back to deterministic token-overlap counting if rank_bm25 isn't
    importable in the launcher environment — the launcher must remain runnable
    without the MCP server's deps.
    """
    if not task_tags or not records:
        return []
    query_tokens = _tokenize(" ".join(task_tags))
    if not query_tokens:
        return []
    try:
        from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]

        corpus = [_tokenize(r.value) for r in records]
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(query_tokens)
    except ImportError:
        scores = []
        query_set = set(query_tokens)
        for r in records:
            doc_tokens = set(_tokenize(r.value))
            scores.append(float(len(query_set & doc_tokens)))
    ranked = sorted(zip(scores, records), key=lambda x: (-x[0], x[1].timestamp))
    return [r for s, r in ranked[:n] if s > 0]


def select_end_of_day(
    records: list[EngramRecord],
    *,
    n: int = LAST_N_END_OF_DAY,
) -> list[EngramRecord]:
    """Predicate 4. Last N daily_summary_* engrams by timestamp.

    Snapshots can carry duplicate {key, value, ...} rows (history.jsonl is
    append-only with re-emits); dedupe by key, keep newest timestamp.
    """
    eod = [r for r in records if r.key.startswith(END_OF_DAY_KEY_PREFIX)]
    by_key: dict[str, EngramRecord] = {}
    for r in eod:
        prev = by_key.get(r.key)
        if prev is None or r.timestamp > prev.timestamp:
            by_key[r.key] = r
    return sorted(by_key.values(), key=lambda r: r.timestamp, reverse=True)[:n]


def _render_records(category: str, records: Iterable[EngramRecord]) -> str:
    parts = [f"## {category}\n"]
    for r in records:
        ts_short = r.timestamp[:10] if r.timestamp else "unknown"
        parts.append(f"- **{r.key}** [{r.context}, intensity={r.intensity}, {ts_short}]")
        body = r.value.strip()
        if body:
            parts.append(f"  {body}")
        parts.append("")
    return "\n".join(parts)


def select_engram_prefix(
    *,
    snapshot_path: pathlib.Path,
    memory_index: pathlib.Path,
    task_tags: list[str],
    now: dt.datetime | None = None,
    budget_tokens: int = DEFAULT_BUDGET_TOKENS,
) -> SelectionResult:
    """Compose engram_prefix.<run_id>.md content + manifest metadata.

    Concatenation order is stable: hard-rule -> top-intensity -> bm25 -> end-of-day.
    Overflow policy: drop bottom of (top-intensity), then (bm25). Never drop
    (hard-rule) or (end-of-day). If after dropping all of (2)+(3) we still
    overflow, mark ``overflow_dropped`` with ``budget_exceeded`` so the caller
    can flag the run via manifest's ``engram_budget_exceeded`` per §2.2.
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    records = load_snapshot(snapshot_path) if snapshot_path.exists() else []
    hard_text, hard_keys = select_hard_rule(memory_index)
    top_intensity = select_top_intensity(records, now=now)
    bm25_hits = select_bm25(records, task_tags)
    top_keys = {r.key for r in top_intensity}
    bm25_hits = [r for r in bm25_hits if r.key not in top_keys]
    eod = select_end_of_day(records)

    sections = {
        "hard_rule": list(hard_keys),
        "top_intensity": [r.key for r in top_intensity],
        "bm25": [r.key for r in bm25_hits],
        "end_of_day": [r.key for r in eod],
    }

    def _render() -> str:
        chunks: list[str] = []
        if hard_text:
            chunks.append(hard_text)
        if top_intensity:
            chunks.append(_render_records("Top-intensity engrams (last 14d)", top_intensity))
        if bm25_hits:
            chunks.append(_render_records("Task-tag BM25 matches", bm25_hits))
        if eod:
            chunks.append(_render_records("End-of-day captures", eod))
        return ("\n\n".join(chunks).rstrip() + "\n") if chunks else ""

    overflow: list[str] = []
    rendered = _render()
    while _estimate_tokens(rendered) > budget_tokens and (top_intensity or bm25_hits):
        if top_intensity:
            dropped = top_intensity.pop()
            overflow.append(f"top_intensity:{dropped.key}")
            sections["top_intensity"] = [r.key for r in top_intensity]
        else:
            dropped = bm25_hits.pop()
            overflow.append(f"bm25:{dropped.key}")
            sections["bm25"] = [r.key for r in bm25_hits]
        rendered = _render()

    if _estimate_tokens(rendered) > budget_tokens:
        overflow.append("budget_exceeded")

    return SelectionResult(
        rendered=rendered,
        estimated_tokens=_estimate_tokens(rendered),
        overflow_dropped=overflow,
        sections=sections,
    )


def write_prefix(result: SelectionResult, out_path: pathlib.Path) -> pathlib.Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result.rendered)
    return out_path
