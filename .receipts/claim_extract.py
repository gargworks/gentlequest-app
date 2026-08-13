#!/usr/bin/env python3
"""
lib/claim_extract.py -- offline extraction of citation-bearing claims from a
pasted AI answer, plus parsing of pasted source text into an offline corpus.

This is the NEW glue code this tool needed (freeform paste -> structured
claims); the actual PROVEN / REFUTED / INSUFFICIENT judgment on each
extracted claim is delegated to ../../build/citation_verifier.py's
verify_claim() (loaded unchanged via importlib by entrypoint.py) -- this
file only turns freeform pasted text into the (subject, expected_value)
shape that function already knows how to judge. It renders zero verdicts
itself.

Stdlib only. Zero network. Zero filesystem writes -- pure text -> data
transforms; the caller decides what, if anything, to persist.

CITATION SYNTAX this tool expects the pasted AI answer to use (also
documented in ../README.md's "input format" section):

    A claim earns a CHECKABLE citation by containing a bracket of the form

        [source_id: "exact or near-exact supporting phrase from the source"]

    e.g.
        Johnson and Lee identify three primary deployment patterns
        [johnson2021: "identify three primary deployment patterns"].

    A bracket with no quoted phrase -- [source_id] alone -- is still
    detected as a citation, but is not enough to verify: this tool requires
    the exact phrase because that is the only thing that can be looked up
    in the pasted source text without guessing. Guessing would mean either
    (a) inventing a fuzzy paraphrase-match threshold, which produces FALSE
    REFUTED verdicts on claims that are actually fine but just worded
    differently, or (b) softening REFUTED into a shrug when the match is
    ambiguous -- both are exactly the "coerce to green" (or "coerce to an
    unjustified negative") failure this tool exists to refuse. A quote-less
    citation is reported INSUFFICIENT, with a reason that names exactly
    what is missing, never silently dropped.

    A factual-sounding sentence with NO bracket at all is extracted too --
    and reported INSUFFICIENT ("no source cited for this claim") -- because
    catching *that* is this tool's whole reason to exist (research_goal.md:
    "the AI generates a confident-sounding paragraph... no Smith et al.
    paper in that year with that title").

SOURCE CORPUS FORMAT the pasted sources text may use (either works, and the
parser auto-detects which one it was handed):

    (a) JSON object:      {"source_id": "full pasted text", ...}
    (b) plain delimited blocks:
            === SOURCE: source_id ===
            <full pasted text of that source>
            === SOURCE: another_id ===
            <full pasted text of that source>
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Sentence + citation parsing -- deliberately simple, deterministic regexes
# (same discipline citation_verifier.py and research_receipt.py already
# used: no NLP dependency, no network, behavior fully readable from source).
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WHITESPACE_RE = re.compile(r"\s+")

# [source_id]  OR  [source_id: "quoted supporting phrase"]
#
# source_id may itself legitimately contain punctuation, including a colon
# (e.g. `paper:martinez-singh-2022`, the id style demo_dataset.md's own
# Source headings use) -- so the id capture group only excludes `]` (the
# bracket delimiter), not `:`. It stays non-greedy (`+?`), which is what
# makes this safe: the engine expands the id char-by-char and only accepts
# a stopping point where the REST of the bracket parses as either a bare
# `]` or a real `: "quote"]` separator (colon immediately followed by a
# quote character). A colon that's part of the id itself (like the one
# after "paper" above) is never followed by a quote character, so that
# candidate split fails to match and the id keeps expanding past it --
# only the genuine id/quote separator colon (if any) can end the match.
#
# The quoted-phrase group uses PAIRED alternation -- `"([^"]*)"` OR
# `'([^']*)'` -- rather than a single shared `["\']` class for both the
# delimiter and the body. A shared class (the old `["\']([^"\']*)["\']`
# shape) treats BOTH quote characters as forbidden inside the body no
# matter which one opened the quote, so a double-quoted phrase containing
# an apostrophe (e.g. `[src: "FIFO's 71%"]`) truncates at the apostrophe
# and the group fails to close cleanly -- the citation then silently
# degrades to the bare `[source_id]` alternative (quote=None), which is
# fail-closed (INSUFFICIENT, never a false PROVEN) but under-checks a
# citation that was actually fine. Pairing each delimiter with a body
# class that excludes only THAT delimiter lets a `"..."` quote contain
# apostrophes and a `'...'` quote contain double-quotes, while still
# requiring the two delimiters of a given quote to match. Because `re`
# (stdlib) has no branch-reset group, the two alternatives capture into
# separate groups (2 and 3); callers must read whichever one is not None
# (see extract_claims below) -- at most one of the two ever matches, since
# the alternation is mutually exclusive per attempt.
#
# Trailing `(?!\()` -- a zero-width negative lookahead right after the
# closing `]` -- excludes markdown links. `[text](url)` is legitimate
# prose (a hyperlink), not a citation bracket, but the bare `[id]` form
# above matches it anyway: without this guard, `[claude-code issue
# 82914](https://...)` gets id="claude-code issue 82914" and cited=True,
# which the receipt gate then wrongly demands a RESEARCH RECEIPT for
# (false block, live 2026-08-09: flywheel fw-1786281886-1-653f). The
# CLASS is "a bracket group immediately followed by `(`", not any
# specific link text, so this excludes the whole class rather than
# special-casing observed examples. The lookahead consumes nothing, so
# it changes zero capture-group offsets and cannot affect `_CITATION_RE.sub`
# (used to strip citations from a sentence) on any bracket that still
# matches. A real citation is never immediately followed by `(` in normal
# prose, so this costs nothing on the must-still-match side.
_CITATION_RE = re.compile(r'\[\s*([^\]]+?)\s*(?::\s*(?:"([^"]*)"|\'([^\']*)\')\s*)?\](?!\()')

_SOURCE_BLOCK_RE = re.compile(r"^===\s*SOURCE:\s*(.+?)\s*===\s*$", re.MULTILINE)

# A sentence "looks like a claim" (a factual assertion worth checking) if it
# is not a question, not hedged, and contains at least one assertion verb.
# Deliberately permissive/inclusive: this tool's whole job is to catch
# uncited claims, so it is designed to OVER-flag rather than under-flag --
# a sentence that slips through this filter as "not a claim" never gets
# checked at all, which is the one failure mode worse than a false flag.
_HEDGE_WORDS = ("might", "could", "may ", "perhaps", "possibly", "suggests that", "appears to", "seems to")
_CLAIM_VERBS = (
    " is ", " are ", " was ", " were ", " has ", " have ", " had ",
    " shows ", " show ", " showed ", " demonstrates ", " demonstrate ",
    " found ", " finds ", " reports ", " report ", " identifies ", " identify ",
    " achieves ", " achieve ", " reduces ", " reduce ", " increases ", " increase ",
    " enables ", " enable ", " requires ", " require ", " causes ", " cause ",
    " proves ", " prove ", " confirms ", " confirm ", " indicates ", " indicate ",
)


def _looks_like_claim(sentence: str) -> bool:
    s = sentence.strip()
    if not s or s.endswith("?"):
        return False
    low = f" {s.lower()} "
    if any(h in low for h in _HEDGE_WORDS):
        return False
    return any(v in low for v in _CLAIM_VERBS)


def _subject_from_quote(quote: str, n: int = 3) -> str:
    """A short anchor phrase (the FIRST n words of the quote) used only to
    locate whether the source addresses this topic at all. Deliberately
    shorter than the full quote so the anchor doesn't itself include the
    specific detail a hallucinated citation is most likely to get wrong --
    the same subject/expected_value split citation_verifier.py's own
    REFUTED self-test fixture uses (subject="precision on", expected_value=
    "89% precision on edge-case detection")."""
    words = quote.strip().split()
    if not words:
        return ""
    return " ".join(words[: max(1, min(n, len(words)))])


@dataclass(frozen=True)
class ExtractedClaim:
    claim_id: str
    statement: str            # the sentence, citation brackets stripped
    source_id: Optional[str]  # None if no citation at all was present
    quote: Optional[str]      # the quoted supporting phrase, if the citation carried one
    subject: Optional[str]    # anchor phrase derived from `quote`; None if quote is None
    cited: bool                # True if a bracket citation was present at all (quote or not)


def parse_sources(sources_text: str) -> Dict[str, str]:
    """Parse the offline source corpus the researcher pasted in. Never
    fetches anything -- the text handed in IS the corpus; a source_id not
    present here is, by construction, a source this tool cannot check
    (citation_verifier.verify_claim's own Rule 1 turns that into
    INSUFFICIENT, never a silent skip)."""
    text = sources_text.strip()
    if not text:
        return {}
    if text.startswith("{"):
        obj = json.loads(text)
        if not isinstance(obj, dict):
            raise ValueError("sources JSON must be an object of {source_id: text}")
        return {str(k): str(v) for k, v in obj.items()}

    matches = list(_SOURCE_BLOCK_RE.finditer(sources_text))
    if not matches:
        raise ValueError(
            "sources text has no '=== SOURCE: <id> ===' blocks and does not start "
            "with '{' (JSON); cannot parse an offline corpus from it -- see "
            "README.md's 'input format' section for the two accepted shapes"
        )
    sources: Dict[str, str] = {}
    for i, m in enumerate(matches):
        source_id = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(sources_text)
        sources[source_id] = sources_text[start:end].strip()
    return sources


def extract_claims(answer_text: str) -> List[ExtractedClaim]:
    """Split the pasted AI answer into sentences and turn each one into zero
    or more ExtractedClaim records:
      - a sentence with N bracket citations produces N records (one per
        citation -- each is checked against its own source independently);
      - a sentence with NO citation, that still looks like a factual claim,
        produces exactly ONE record with source_id=None (destined for
        INSUFFICIENT: "no source cited");
      - a sentence with no citation that does not look like a claim (a
        question, a hedge, a transition sentence) produces nothing -- it
        was never asserted as fact, so there is nothing to check.
    """
    claims: List[ExtractedClaim] = []
    sentences = [s for s in _SENTENCE_SPLIT_RE.split(answer_text.strip()) if s.strip()]

    for sentence in sentences:
        citations = list(_CITATION_RE.finditer(sentence))
        clean = _WHITESPACE_RE.sub(" ", _CITATION_RE.sub("", sentence)).strip()
        if not clean:
            continue

        if not citations:
            if _looks_like_claim(sentence):
                claims.append(ExtractedClaim(
                    claim_id=f"claim_{len(claims) + 1}",
                    statement=clean,
                    source_id=None,
                    quote=None,
                    subject=None,
                    cited=False,
                ))
            continue

        for m in citations:
            source_id = m.group(1).strip()
            # group(2) = double-quoted body, group(3) = single-quoted body;
            # the paired-alternation regex above matches at most one of the
            # two per citation, so whichever is not None is the real quote.
            raw_quote = m.group(2) if m.group(2) is not None else m.group(3)
            quote = raw_quote.strip() if raw_quote else None
            subject = _subject_from_quote(quote) if quote else None
            claims.append(ExtractedClaim(
                claim_id=f"claim_{len(claims) + 1}",
                statement=clean,
                source_id=source_id or None,
                quote=quote,
                subject=subject,
                cited=True,
            ))

    return claims


# ===========================================================================
# Self-test: extraction mechanics only (NOT verdicts -- that instrument is
# citation_verifier.py and is tested there and in entrypoint.py's opposed
# pair). This file's job is purely "does the pasted text turn into the right
# shape", checked directly.
# ===========================================================================

def _self_test() -> bool:
    ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        status = "PASS" if cond else "FAIL"
        if not cond:
            ok = False
        print(f"  [{status}] {label}" + (f" -- {detail}" if detail and not cond else ""))

    print("=== claim_extract.py opposed-pair self-test ===\n")

    answer = (
        'Johnson and Lee identify three primary deployment patterns '
        '[johnson2021: "identify three primary deployment patterns"]. '
        'Smith et al. report 89% precision on edge-case detection '
        '[smith2019: "achieves 89% precision on edge-case detection"]. '
        'Verification gates are widely adopted in production ML pipelines. '
        'This claim cites a source with no quote attached [johnson2021]. '
        'Is this approach always reliable? '
        'This might work in some cases.'
    )
    claims = extract_claims(answer)
    by_id = {c.claim_id: c for c in claims}

    check("extracts exactly the expected number of claims", len(claims) == 4,
          f"got {len(claims)}: {[c.statement for c in claims]}")

    c1 = claims[0] if claims else None
    check("cited claim carries source_id", bool(c1 and c1.source_id == "johnson2021"))
    check("cited claim carries quote verbatim", bool(c1 and c1.quote == "identify three primary deployment patterns"))
    check("subject is a short prefix of the quote, not the whole thing", bool(c1 and c1.subject and len(c1.subject) < len(c1.quote)))
    check("citation brackets stripped from statement", bool(c1 and "[" not in c1.statement and "]" not in c1.statement))

    uncited = [c for c in claims if c.source_id is None and c.cited is False]
    check("uncited-but-claim-like sentence IS extracted (source_id=None)", len(uncited) == 1,
          f"got {[c.statement for c in uncited]}")

    quoteless = [c for c in claims if c.cited and c.quote is None]
    check("citation without a quote is extracted with quote=None (not silently dropped)", len(quoteless) == 1)

    check("question sentence is NOT extracted", not any("reliable?" in c.statement for c in claims))
    check("hedged sentence ('might') is NOT extracted", not any("might work" in c.statement for c in claims))

    print()
    sources_delim = "=== SOURCE: a ===\ntext a\n=== SOURCE: b ===\ntext b\n"
    parsed = parse_sources(sources_delim)
    check("delimited source block format parses both sources", parsed == {"a": "text a", "b": "text b"}, str(parsed))

    parsed_json = parse_sources('{"a": "text a", "b": "text b"}')
    check("JSON source format parses identically", parsed_json == {"a": "text a", "b": "text b"}, str(parsed_json))

    check("empty sources text parses to empty corpus, not an error", parse_sources("   ") == {})

    print()
    if ok:
        print("=== all claim_extract.py checks PASSED ===")
    else:
        print("=== claim_extract.py: SOME CHECKS FAILED ===")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if _self_test() else 1)
