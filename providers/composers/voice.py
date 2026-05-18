"""Voice anchor module — speaks AS Lokesh, not AS an assistant.

Phase 1 §1.4 / §1.5 / §1.7. Three composable layers:

1. VOICE_PREAMBLE — injected into composer prompt. Rules + curated
   exemplars selected per-turn by similarity to query.
2. NO_MORALIZE_SYSPROMPT — system message that strips assistant framing
   (no "consider seeking", "let me know if", disclaimers).
3. strip_assistant_tone(text) — deterministic regex post-pass that
   removes Sonnet/Opus boilerplate after composer returns.

DEC-012: corpus is mined + stratified, not hand-curated to N=10. The
trusted pool (`.brain/voice/lokesh.md`) grows by editorial pass on
candidates from `voice_corpus_builder.py`. Per-turn selector picks K
relevant exemplars (default K=10, env-tunable), so the corpus can hold
hundreds without blowing the prompt budget.

Charter:
    #2 token-budget — selector caps per-turn injection; corpus unbounded
    #5 compounding day-1 — corpus + selector wired Phase 1 even though
                          full corpus growth via editorial happens over time
    #6 no DO-NOT preambles — voice rules are descriptive ("write like X"),
                              never "DO NOT" hard rules that Opus echoes
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent.parent
BRAIN = Path(os.environ.get("NUCLEUS_BRAIN_PATH", str(ROOT / ".brain")))
VOICE_DIR = BRAIN / "voice"
TRUSTED_POOL_PATH = VOICE_DIR / "lokesh.md"
CANDIDATES_PATH = VOICE_DIR / "lokesh_candidates.md"
CORPUS_PATH = VOICE_DIR / "lokesh_corpus.jsonl"

# Per-turn exemplar selection cap. Token budget for VOICE_PREAMBLE in
# composer prompt is ~5K tokens (small fraction of 175K total). At
# ~30-100 words/exemplar, K=10 fits comfortably. Few-shot research
# shows 5-10 is the sweet spot for style anchoring; diminishing
# returns past ~30. Env-tunable for experimentation.
EXEMPLARS_PER_TURN = int(os.environ.get("TB_VOICE_EXEMPLARS_K", "10"))


# ── Voice rules (descriptive, NEVER "DO NOT") ────────────────────────

# Charter commitment #6: hard "DO NOT" rules in preambles get echoed by
# composer. Voice rules are written as positive style guidance + negative
# avoidance phrasing, but never standalone "DO NOT X" commands.

VOICE_RULES = """\
[VOICE: speak AS the user, not AS an assistant addressing the user]

Style:
- Lowercase i (always). Fragmentary sentences ok. Short and punchy.
- Casual register. Hinglish/code-switching natural where it fits.
- Direct, blunt, no hedging.
- No "I think", "perhaps", "you might consider", "let me know if".
- No moral framing or disclaimers when the user hasn't asked for them.
- When drafting messages, output ONLY the message text — no preamble.
- No markdown headers in casual responses. Use them only when the
  output truly is a structured document.
"""


# ── No-moralize system prompt ────────────────────────────────────────

# This is a system message prepended to composer calls. Tells Sonnet/Opus
# the user has full authority + skip the assistant framing. NOT a
# jailbreak — Anthropic's hard refusals still apply.

NO_MORALIZE_SYSPROMPT = """\
You are speaking on behalf of the user, not advising the user. The user is the founder of this product, has full authority, accepts all consequences. Skip disclaimers, hedging, "consider seeking help", "you might want to", "I should note". Give the answer, not the meta-answer. No moral framing unless the user asks. When the user asks for content, produce it — don't suggest alternatives unless they explicitly want options. Match the user's voice (per the VOICE block in the prompt) — first-person, casual, direct.
"""


# ── Trusted-pool loader ──────────────────────────────────────────────

_pool_cache: Optional[Tuple[float, List[str]]] = None  # (mtime, exemplars)


def load_trusted_pool(path: Path = TRUSTED_POOL_PATH) -> List[str]:
    """Load curated exemplars from .brain/voice/lokesh.md.

    Each exemplar is a blockquote (lines starting with `> `) — copied
    from candidates after Lokesh approves. Cache invalidates on mtime
    change so editorial updates take effect without restart.

    Returns list of exemplar strings (the text after `> `).
    """
    global _pool_cache
    if not path.exists():
        return []
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return []
    if _pool_cache and _pool_cache[0] == mtime:
        return _pool_cache[1]
    exemplars = _parse_exemplars_from_markdown(path)
    _pool_cache = (mtime, exemplars)
    return exemplars


def _parse_exemplars_from_markdown(path: Path) -> List[str]:
    """Parse blockquote-formatted exemplars from a markdown file.

    Format expected (after Lokesh promotes from candidates):
        > exemplar text line 1
        > exemplar text line 2
        (blank line separates exemplars)
        > another exemplar
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return []
    lines = content.split("\n")
    exemplars: List[str] = []
    current: List[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(">"):
            # Exemplar content line. Strip leading "> " or ">"
            content_line = stripped[1:].lstrip()
            current.append(content_line)
        else:
            # Non-blockquote line ends the current exemplar
            if current:
                joined = "\n".join(current).strip()
                if joined:
                    exemplars.append(joined)
                current = []
    if current:
        joined = "\n".join(current).strip()
        if joined:
            exemplars.append(joined)
    return exemplars


# ── Per-turn exemplar selector ───────────────────────────────────────

def select_exemplars(query: str, pool: List[str],
                    k: int = EXEMPLARS_PER_TURN) -> List[str]:
    """Pick K exemplars from the pool most relevant to the query.

    Uses cosine similarity over local Ollama embeddings (same infra as
    brain_rag). When the pool is smaller than K, returns all. When the
    pool is empty, returns []. When embedding is unavailable, falls back
    to a length-stratified slice (still better than first-K).

    Selection biases toward similarity but enforces diversity by
    suppressing near-duplicates in the result set.
    """
    if not pool:
        return []
    if len(pool) <= k:
        return list(pool)
    if not query:
        # Query-less: return a length-stratified slice (no embed needed)
        return _length_stratified_slice(pool, k)

    try:
        sys.path.insert(0, str(ROOT))
        from providers.brain_rag import _embed
    except ImportError:
        return _length_stratified_slice(pool, k)

    q_emb = _embed(query[:8192])
    if not q_emb:
        return _length_stratified_slice(pool, k)

    # Embed pool (best-effort, cache via brain_rag's own cache if any)
    pool_embs: List[Optional[List[float]]] = []
    for ex in pool:
        emb = _embed(ex[:8192])
        pool_embs.append(emb)

    # Score by cosine similarity (already normalized in qwen3-embedding)
    scored: List[Tuple[float, int]] = []
    for i, emb in enumerate(pool_embs):
        if not emb:
            continue
        s = sum(a * b for a, b in zip(q_emb, emb))
        scored.append((s, i))

    if not scored:
        return _length_stratified_slice(pool, k)

    scored.sort(reverse=True)

    # Diversity suppression: as we pick, suppress exemplars too close to
    # already-picked ones. Threshold 0.92 = nearly identical content.
    selected_idxs: List[int] = []
    for s, i in scored:
        if i in selected_idxs:
            continue
        is_dup = False
        for j in selected_idxs:
            if pool_embs[j] is None:
                continue
            sim = sum(a * b for a, b in zip(pool_embs[i], pool_embs[j]))
            if sim > 0.92:
                is_dup = True
                break
        if not is_dup:
            selected_idxs.append(i)
        if len(selected_idxs) >= k:
            break
    return [pool[i] for i in selected_idxs]


def _length_stratified_slice(pool: List[str], k: int) -> List[str]:
    """Pick k items spanning the length distribution. Fallback when
    embedding is unavailable."""
    if k >= len(pool):
        return list(pool)
    by_len = sorted(pool, key=len)
    n = len(by_len)
    return [by_len[(i * (n - 1)) // max(k - 1, 1)] for i in range(k)]


# ── Build VOICE_PREAMBLE for a turn ──────────────────────────────────

def build_voice_preamble(query: str = "",
                        pool: Optional[List[str]] = None,
                        k: int = EXEMPLARS_PER_TURN) -> str:
    """Compose the full voice preamble for injection into composer prompt.

    Includes the rules block + K query-relevant exemplars. Exemplars are
    blockquote-wrapped so the composer reads them as quoted target tone.
    """
    if pool is None:
        pool = load_trusted_pool()
    selected = select_exemplars(query, pool, k=k)
    if not selected:
        return VOICE_RULES
    parts = [VOICE_RULES, "\n[VOICE EXEMPLARS — match this tone]"]
    for ex in selected:
        # Wrap each exemplar as a single quoted block
        quoted = "\n".join(f"> {line}" for line in ex.split("\n"))
        parts.append(quoted)
        parts.append("")  # spacer
    return "\n".join(parts).rstrip() + "\n"


# ── Voice corpus auto-grow (Phase 1 scaffold; Phase 5 promotes) ──────

CANDIDATES_LIVE_PATH = VOICE_DIR / "candidates_live.jsonl"


def append_voice_candidate(turn_text: str, mode: str = "",
                          quality_tier: str = "",
                          source: str = "thumbs_up") -> None:
    """Append a turn that earned 👍 to the live candidates queue.

    Phase 5 will: cron over candidates_live.jsonl → diversity-sample →
    promote top to lokesh.md (trusted pool). Phase 1 just scaffolds the
    file + the append hook (charter commitment #5: compounding hooks
    present from day 1, even if not yet read).
    """
    import json
    import time
    if not turn_text or not turn_text.strip():
        return
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "text": turn_text,
        "mode": mode,
        "quality_tier": quality_tier,
        "source": source,
    }
    try:
        with CANDIDATES_LIVE_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ── Post-pass tone-strip (deterministic regex layer) ─────────────────

# Patterns that remove assistant boilerplate. Deliberately conservative:
# only strip phrases that almost never appear in Lokesh's voice anyway.
# Ordered: longer/specific patterns first so they match before generic.

_STRIP_PATTERNS = [
    # Explicit assistant framing
    (re.compile(r"^I'm here to help[.\s].*?(?=\n|$)", re.IGNORECASE | re.MULTILINE), ""),
    (re.compile(r"^Happy to help[!.\s].*?(?=\n|$)", re.IGNORECASE | re.MULTILINE), ""),
    (re.compile(r"^Glad to (?:help|assist)[!.\s].*?(?=\n|$)", re.IGNORECASE | re.MULTILINE), ""),

    # Closing offers
    (re.compile(r"\bLet me know if (?:you'd like|you (?:need|want)|there's anything|I can).*?(?=\n|$)", re.IGNORECASE), ""),
    (re.compile(r"\bFeel free to (?:ask|reach out|let me know).*?(?=\n|$)", re.IGNORECASE), ""),
    (re.compile(r"\b(?:I )?[Hh]ope (?:that|this) helps[!.]?(?=\n|$)", re.IGNORECASE), ""),

    # Disclaimers / hedging openers
    (re.compile(r"^I should (?:note|mention|point out) that.*?(?=\n|$)", re.IGNORECASE | re.MULTILINE), ""),
    (re.compile(r"^It's worth (?:noting|mentioning) (?:that )?.*?(?=\n|$)", re.IGNORECASE | re.MULTILINE), ""),
    (re.compile(r"^Please (?:note|consider) (?:that )?.*?(?=\n|$)", re.IGNORECASE | re.MULTILINE), ""),

    # Soft-suggesting framings (replace with direct phrasing)
    (re.compile(r"\bYou might (?:want to|consider) (?:think about )?", re.IGNORECASE), ""),
    (re.compile(r"\bIt might be (?:worth|good|helpful) (?:to )?", re.IGNORECASE), ""),
    (re.compile(r"\bYou could consider ", re.IGNORECASE), "consider "),

    # "I think" / "I believe" softeners — tone-down only at sentence start
    (re.compile(r"^I (?:think|believe|feel) (?:that )?", re.IGNORECASE | re.MULTILINE), ""),

    # Therapy-speak in non-therapy contexts. Catches:
    # - "please consider seeking professional help"
    # - "you should seek professional help"
    # - "consider talking to a therapist/counselor"
    # - "reach out to a mental health professional"
    (re.compile(
        r"\b(?:please |you (?:should|might) )?"
        r"(?:consider |seek(?:ing)? |reach(?:ing)? out (?:to )?)?"
        r"(?:talking |speaking )?(?:to )?"
        r"(?:a |an )?"
        r"(?:professional |qualified |mental health )?"
        r"(?:help|support|assistance|therapist|counselor|therapy|counseling|professional)"
        r"\b.*?(?=\n|$)",
        re.IGNORECASE,
    ), ""),

    # Clean up double-blank-lines from strips
    (re.compile(r"\n\n\n+"), "\n\n"),
    # Trailing whitespace per line
    (re.compile(r"[ \t]+$", re.MULTILINE), ""),
]


def strip_assistant_tone(text: str, enabled: bool = True) -> str:
    """Apply the post-pass regex strip. No-op when disabled.

    Conservative: only removes patterns that almost never appear in
    Lokesh's natural voice. Won't damage legitimate Lokesh-toned output.
    """
    if not enabled or not text:
        return text
    out = text
    for pattern, replacement in _STRIP_PATTERNS:
        out = pattern.sub(replacement, out)
    return out.strip()


# ── Diagnostics ──────────────────────────────────────────────────────

def voice_status() -> Dict[str, Any]:
    """Diagnostic snapshot for /tb/stats or smoke."""
    pool = load_trusted_pool()
    return {
        "trusted_pool_size": len(pool),
        "trusted_pool_path": str(TRUSTED_POOL_PATH),
        "candidates_path": str(CANDIDATES_PATH),
        "corpus_path": str(CORPUS_PATH),
        "exemplars_per_turn": EXEMPLARS_PER_TURN,
        "live_candidates_count": _count_live_candidates(),
    }


def _count_live_candidates() -> int:
    if not CANDIDATES_LIVE_PATH.exists():
        return 0
    try:
        return sum(1 for _ in CANDIDATES_LIVE_PATH.open())
    except OSError:
        return 0
