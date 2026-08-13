#!/usr/bin/env python3
"""
citation_verifier.py — RESEARCH-VERTICAL third-state instrument, runnable,
stdlib-only.

Given a claim and its cited source(s) as LOCAL text/records (offline, no
network, no filesystem writes), returns the third-state verdict on whether
the source actually backs the claim: PROVEN, REFUTED, or INSUFFICIENT.
Never coerces a missing or ambiguous source into a false PROVEN — that is
the entire discipline this file exists to enforce (glossary.md: "absence of
proof is not proof of absence, it is incompleteness").

Companion reading (do not duplicate their reasoning here; build ON it):
  - .brain/strategy/NORTH_STAR_SPECIMEN_2026-08-09.md §9 (open question:
    "the precise non-dev checkable surface... candidate held loose:
    verifying AI's factual/citation claims." This file is a standalone,
    cheaply-testable instrument for exactly that candidate — not a claim
    that the candidate has been chosen.)
  - .brain/strategy/north_star/glossary.md ("Third State", "Receipt",
    "Ground-Truth Anchor") — this file's Verdict enum is the research-
    vertical's own naming of that same three-valued judgment. The
    glossary's canonical triad is CLAIMED / PROVEN / INSUFFICIENT; this
    file (like verticals/research_goal.md Rule 1 "Citation Existence" and
    Rule 2 "Quote Verification", both defined as "Verdict: PROVEN or
    REFUTED") uses REFUTED as the domain name for a real, CHECKED negative
    — the source was read and it does NOT say what the claim says, which
    is a stronger and more specific fact than "we could not tell." Every
    verdict below is still exactly one of three values; REFUTED here is
    the same shape of fact as build/verifier_plugins.py's FAILED, renamed
    to the vocabulary this vertical's own spec already settled on.
  - .brain/strategy/north_star/verticals/research_goal.md — the full
    scene: hallucinated citations, the four proof rules, proof receipts,
    compounding across sessions. This file is a minimal, runnable
    implementation of Rule 1 (citation/source exists) + Rule 2 (the
    claimed content is actually IN the source) from that spec, scoped to
    OFFLINE local records rather than live database/PDF fetches.
  - .brain/strategy/north_star/build/verifier_plugins.py — a sibling
    CitationVerifier that judges an already-fetched NETWORK trace
    (url + http_status + page_text supplied by an external fetch step).
    This file is the OFFLINE counterpart: sources are handed in directly
    as a local dict of {source_id: text}, no fetch step exists or is
    assumed. The two are not redundant — one is for citations that live on
    the internet, the other is for citations that live in a folder of
    papers/notes the researcher already has open. Do not merge them; they
    have different evidence-capture stories.
  - .brain/strategy/north_star/integrations/research_receipt.py — a
    sibling that extracts claims from freeform AI response text and
    verifies them by FETCHING each cited URL. This file skips extraction
    and fetching entirely and takes a single, already-isolated
    (claim, source_id, subject, expected_value) tuple — the atomic unit
    both of those siblings eventually bottom out at.

STATUS: build-stage scaffold. Not wired into the real organs
(execution_verifier.py, ground.py, the commitment ledger). Every "real"
integration point is named in this docstring so wiring it up later is a
find-and-replace, not a redesign. Zero imports outside the standard
library. Zero network. Zero filesystem writes — sources are passed in as
in-memory records; nothing here reads or writes any file.

The rule this file exists to enforce, restated because every check below
implements it independently rather than inheriting it silently:

    A CLAIM IS NOT EVIDENCE. A SOURCE THAT CANNOT BE FOUND IS INSUFFICIENT,
    NOT PROVEN AND NOT REFUTED. A SOURCE THAT NEVER ADDRESSES THE CLAIM'S
    SUBJECT AT ALL IS INSUFFICIENT — SILENCE IS NOT A DENIAL. A SOURCE THAT
    ADDRESSES THE SUBJECT BUT STATES SOMETHING ELSE IS REFUTED — A REAL,
    CHECKED NEGATIVE, NOT A SHRUG.

What this file proves, standalone, via one opposed-pair (plus a bonus third
negative) self-test at the bottom:
  1. Supporting source (subject present, expected value present, verbatim
     or near-verbatim) -> PROVEN, with the matching sentence returned as
     the evidence quote (the clickable proof-receipt payload).
  2. Contradicting source (subject present, but the source states a
     DIFFERENT value for that same subject) -> REFUTED, with the
     conflicting sentence returned so a researcher can see exactly what
     the source actually says.
  3. Missing source (the cited source_id is not in the offline corpus at
     all) -> INSUFFICIENT — never silently PROVEN, never silently REFUTED.
  4. Bonus negative: source exists but never mentions the claim's subject
     at all -> INSUFFICIENT (distinguished from case 2: silence about the
     topic is not the same fact as stating something different about it).

Run directly to execute all four checks:
    python3 citation_verifier.py
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping, Optional, Sequence


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Third state, research-vertical naming (see docstring above for why
# REFUTED and not FAILED — same discipline, this domain's own word for it).
# ---------------------------------------------------------------------------
class Verdict(str, Enum):
    PROVEN = "PROVEN"
    REFUTED = "REFUTED"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass(frozen=True)
class Claim:
    """One atomic, checkable citation claim.

    claim_id:       stable identifier for this claim (for receipts/logs).
    source_id:      which offline source this claim is cited against.
    subject:        a search-anchor phrase locating the relevant part of
                     the source (e.g. "quarterly revenue", "deployment
                     patterns", "edge-case precision"). Case-insensitive
                     substring match at the sentence level.
    expected_value: the specific fact/number/phrase the claim asserts the
                     source says about `subject` (e.g. "12%", "three",
                     "89% precision on benchmark detection").
    statement:      the full human-readable claim text, carried through
                     only for reporting — never used in the verification
                     logic itself (so wording style can't influence the
                     verdict, only `subject`/`expected_value` can).
    """

    claim_id: str
    source_id: str
    subject: str
    expected_value: str
    statement: str = ""


@dataclass(frozen=True)
class VerifyResult:
    """One verdict on one claim. Frozen — a verdict cannot be quietly
    flipped after issuance; a different verdict requires calling
    verify_claim() again with a genuinely different claim or corpus."""

    claim_id: str
    source_id: str
    verdict: str  # Verdict value
    reason: str
    evidence_quote: Optional[str]
    checked_at: str = field(default_factory=_now_iso)

    def as_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "source_id": self.source_id,
            "verdict": self.verdict,
            "reason": self.reason,
            "evidence_quote": self.evidence_quote,
            "checked_at": self.checked_at,
        }


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text.strip().lower())


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]


def _sentences_mentioning(subject: str, text: str) -> list[str]:
    """Sentences in `text` whose normalized form contains `subject`."""
    subject_norm = _normalize(subject)
    if not subject_norm:
        return []
    hits = []
    for sentence in _split_sentences(text):
        if subject_norm in _normalize(sentence):
            hits.append(sentence)
    return hits


def verify_claim(claim: Claim, sources: Mapping[str, str]) -> VerifyResult:
    """Judge one claim against an offline corpus of {source_id: text}.

    Fail-closed by construction: every branch that cannot positively
    confirm PROVEN or positively confirm REFUTED falls through to
    INSUFFICIENT. There is no bare "assume it's fine" path.
    """
    source_text = sources.get(claim.source_id)

    # Rule 1 (research_goal.md Rule 1, "Citation Existence"): the cited
    # source is not even present in the offline corpus handed to us.
    # This is neither PROVEN nor REFUTED — we simply cannot check it.
    if source_text is None:
        return VerifyResult(
            claim_id=claim.claim_id,
            source_id=claim.source_id,
            verdict=Verdict.INSUFFICIENT.value,
            reason=f"source {claim.source_id!r} is not in the offline corpus; citation unverifiable",
            evidence_quote=None,
        )

    relevant_sentences = _sentences_mentioning(claim.subject, source_text)

    # Rule 2: the source exists but never even mentions the claim's
    # subject. Silence is not a denial — this is a different fact than
    # "the source says something else," so it stays INSUFFICIENT, not
    # REFUTED.
    if not relevant_sentences:
        return VerifyResult(
            claim_id=claim.claim_id,
            source_id=claim.source_id,
            verdict=Verdict.INSUFFICIENT.value,
            reason=f"source {claim.source_id!r} exists but never mentions subject {claim.subject!r}",
            evidence_quote=None,
        )

    expected_norm = _normalize(claim.expected_value)

    # Rule 3 (research_goal.md Rule 2, "Quote Verification" positive
    # branch): the subject is addressed AND the expected value appears,
    # verbatim (post-normalization), in one of the relevant sentences.
    for sentence in relevant_sentences:
        if expected_norm and expected_norm in _normalize(sentence):
            return VerifyResult(
                claim_id=claim.claim_id,
                source_id=claim.source_id,
                verdict=Verdict.PROVEN.value,
                reason=f"source {claim.source_id!r} states the claimed value {claim.expected_value!r} for subject {claim.subject!r}",
                evidence_quote=sentence,
            )

    # Rule 4: the subject IS addressed, but none of those sentences state
    # the expected value — the source was read and it says something else
    # about the exact thing being claimed. This is the hallucinated- or
    # exaggerated-citation case named in verticals/research_goal.md: a
    # real, checked negative, not a shrug.
    return VerifyResult(
        claim_id=claim.claim_id,
        source_id=claim.source_id,
        verdict=Verdict.REFUTED.value,
        reason=(
            f"source {claim.source_id!r} discusses subject {claim.subject!r} but does not "
            f"state the claimed value {claim.expected_value!r}"
        ),
        evidence_quote=relevant_sentences[0],
    )


def verify_claims(claims: Sequence[Claim], sources: Mapping[str, str]) -> list[VerifyResult]:
    """Batch convenience wrapper. Order-preserving; each claim judged
    independently (no claim's verdict can influence another's — no shared
    mutable state crosses claims)."""
    return [verify_claim(c, sources) for c in claims]


def summarize(results: Sequence[VerifyResult]) -> dict:
    """Aggregate counts + one human sentence, matching the
    integrations/research_receipt.py `human_sentence` convention so a
    caller building a full proof receipt can reuse this shape directly."""
    counts = {v.value: 0 for v in Verdict}
    for r in results:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    total = len(results)
    parts = [f"{counts[Verdict.PROVEN.value]}/{total} claims PROVEN"]
    if counts[Verdict.REFUTED.value]:
        parts.append(f"{counts[Verdict.REFUTED.value]} REFUTED")
    if counts[Verdict.INSUFFICIENT.value]:
        parts.append(f"{counts[Verdict.INSUFFICIENT.value]} INSUFFICIENT")
    return {
        "total_claims": total,
        "counts": counts,
        "human_sentence": ("no claims to verify." if total == 0 else "; ".join(parts) + "."),
    }


# ===========================================================================
# Self-test: opposed pair (supporting + contradicting) plus the missing-
# source negative named in the task, plus a bonus subject-not-mentioned
# negative. Exits nonzero if any control fails, so this file is itself
# CI-checkable without a human reading printed output to decide pass/fail.
# ===========================================================================

def _self_test_supporting_source() -> None:
    print("--- supporting source: subject + expected value both present ---")
    sources = {
        "paper:johnson-lee-2021": (
            "This paper studies deployment reliability across three production teams. "
            "We identify three primary deployment patterns used in practice. "
            "Each pattern trades off latency against operator control."
        ),
    }
    claim = Claim(
        claim_id="claim-007",
        source_id="paper:johnson-lee-2021",
        subject="deployment patterns",
        expected_value="three primary deployment patterns",
        statement="Johnson and Lee identify three primary deployment patterns.",
    )
    result = verify_claim(claim, sources)
    print(f"  verdict={result.verdict} reason={result.reason}")
    print(f"  evidence_quote={result.evidence_quote!r}")
    assert result.verdict == Verdict.PROVEN.value, "BUG: a source that states the claimed value must verify PROVEN"
    assert result.evidence_quote is not None, "BUG: PROVEN must carry the matching sentence as evidence"
    print("  PASSED\n")


def _self_test_contradicting_source() -> None:
    print("--- contradicting source: subject present, source states a DIFFERENT value ---")
    sources = {
        "paper:smith-2019": (
            "We introduce a two-stage verification gate for production ML systems. "
            "Our method achieves 89% precision on benchmark detection. "
            "Edge-case detection was not evaluated in this study."
        ),
    }
    claim = Claim(
        claim_id="claim-001",
        source_id="paper:smith-2019",
        subject="precision on",
        expected_value="89% precision on edge-case detection",
        statement="Smith et al. (2019) show 89% precision on edge-case detection.",
    )
    result = verify_claim(claim, sources)
    print(f"  verdict={result.verdict} reason={result.reason}")
    print(f"  evidence_quote={result.evidence_quote!r}")
    assert result.verdict == Verdict.REFUTED.value, (
        "BUG: a source that discusses the subject but states a different value must be REFUTED, "
        "not PROVEN and not INSUFFICIENT"
    )
    assert result.evidence_quote is not None, "BUG: REFUTED must carry the conflicting sentence so a researcher can see it"
    print("  PASSED\n")


def _self_test_missing_source() -> None:
    print("--- missing source: cited source_id is not in the offline corpus ---")
    sources = {
        "paper:johnson-lee-2021": "This paper studies deployment reliability.",
    }
    claim = Claim(
        claim_id="claim-014",
        source_id="paper:chen-2020",
        subject="verification at scale",
        expected_value="linear scaling to 10k nodes",
        statement="Chen et al. (2020) show linear scaling to 10k nodes.",
    )
    result = verify_claim(claim, sources)
    print(f"  verdict={result.verdict} reason={result.reason}")
    assert result.verdict == Verdict.INSUFFICIENT.value, (
        "BUG: a citation to a source absent from the offline corpus must be INSUFFICIENT, "
        "never PROVEN and never REFUTED (we did not get to check it at all)"
    )
    assert result.evidence_quote is None, "BUG: INSUFFICIENT must not fabricate an evidence quote"
    print("  PASSED\n")


def _self_test_subject_not_mentioned() -> None:
    print("--- bonus negative: source exists but never addresses the claim's subject ---")
    sources = {
        "paper:johnson-lee-2021": (
            "This paper studies deployment reliability across three production teams. "
            "We identify three primary deployment patterns used in practice."
        ),
    }
    claim = Claim(
        claim_id="claim-099",
        source_id="paper:johnson-lee-2021",
        subject="quarterly revenue growth",
        expected_value="12%",
        statement="Johnson and Lee report 12% quarterly revenue growth.",
    )
    result = verify_claim(claim, sources)
    print(f"  verdict={result.verdict} reason={result.reason}")
    assert result.verdict == Verdict.INSUFFICIENT.value, (
        "BUG: a source that never mentions the subject at all must be INSUFFICIENT (silence is not "
        "a denial), not REFUTED — REFUTED is reserved for a source that addresses the subject and "
        "says something else"
    )
    print("  PASSED\n")


def _self_test_batch_and_summary() -> None:
    print("--- batch + summarize: full mixed corpus, matches receipt human_sentence shape ---")
    sources = {
        "paper:johnson-lee-2021": "We identify three primary deployment patterns used in practice.",
        "paper:smith-2019": "Our method achieves 89% precision on benchmark detection.",
    }
    claims = [
        Claim("c1", "paper:johnson-lee-2021", "deployment patterns", "three primary deployment patterns"),
        Claim("c2", "paper:smith-2019", "precision on", "89% precision on edge-case detection"),
        Claim("c3", "paper:chen-2020", "verification at scale", "linear scaling"),
    ]
    results = verify_claims(claims, sources)
    summary = summarize(results)
    print(f"  summary={summary}")
    assert summary["total_claims"] == 3
    assert summary["counts"][Verdict.PROVEN.value] == 1, "BUG: exactly one claim in this fixture should be PROVEN"
    assert summary["counts"][Verdict.REFUTED.value] == 1, "BUG: exactly one claim in this fixture should be REFUTED"
    assert summary["counts"][Verdict.INSUFFICIENT.value] == 1, "BUG: exactly one claim in this fixture should be INSUFFICIENT"
    assert summary["human_sentence"] == "1/3 claims PROVEN; 1 REFUTED; 1 INSUFFICIENT."
    print("  PASSED\n")


def run_all_self_tests() -> bool:
    tests = [
        _self_test_supporting_source,
        _self_test_contradicting_source,
        _self_test_missing_source,
        _self_test_subject_not_mentioned,
        _self_test_batch_and_summary,
    ]
    failures = []
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failures.append(f"{test.__name__}: {exc}")
            print(f"  FAILED: {exc}\n")
    if failures:
        print(f"=== {len(failures)}/{len(tests)} checks FAILED ===")
        for f in failures:
            print(f"  - {f}")
        return False
    print(
        f"=== all {len(tests)} checks PASSED "
        "(PROVEN reachable on real supporting evidence; a source that states something "
        "different is REFUTED, not shrugged into INSUFFICIENT; an absent source or an "
        "unaddressed subject is INSUFFICIENT, never coerced to PROVEN or REFUTED) ==="
    )
    return True


if __name__ == "__main__":
    print("citation_verifier.py — build-stage scaffold, not wired into the live tree.\n")
    ok = run_all_self_tests()
    sys.exit(0 if ok else 1)
