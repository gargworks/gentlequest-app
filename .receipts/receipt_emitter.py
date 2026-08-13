# --- receipts_kit adaptation banner (added by build_single_file.sh; see that script's header) ---
# This file began as receipt_emitter.py in this project's
# .brain/strategy/north_star/agent_integration/. Verification LOGIC
# below is byte-identical to that source. The ONLY change is the
# _load() paths (and the NORTH_STAR constant they resolve against):
# the real organ resolves proven modules against the north_star repo
# layout; this packaged copy resolves them as FLAT SIBLINGS inside the
# installed .receipts/ directory, because a stranger's repo does not
# have -- and must not need -- the rest of this repo. Regenerate via
# receipts_kit/build_single_file.sh; never hand-edit this file.
# --- end banner ---

#!/usr/bin/env python3
"""
receipt_emitter.py -- the agent-integration bridge for the research
verifier. Stdlib only. Zero network. Zero filesystem writes (the caller
decides whether/where to persist -- this module only judges and renders).

WHY THIS FILE EXISTS (context, not decoration): the standalone paste-in
verifier app (../research_vertical/) proved the underlying judgment logic
works, but a first-user verdict on that app was blunt -- grounding and
citations are commoditized, the paste ritual is friction, and "how do I
really use it day to day" had no answer. The differentiated form is not a
tool a user opens: it's a receipt that shows up as an AUTOMATIC BYPRODUCT
of an agent's own work, with nothing extra for the user to do and no way
for the agent to skip it. This module is the one call an agent harness
makes at ANSWER TIME to get that receipt. See SKILL.md (how a session
adopts this) and hook_design.md (how to make it unavoidable, not
voluntary) in this same directory.

WHAT THIS FILE DOES NOT DO: it does not reimplement claim extraction or
citation judgment. Every judgment call is delegated, unchanged, to the
already-PROVEN modules one directory up:

  - research_vertical/lib/claim_extract.py   extract_claims() -- turns
    freeform answer text (with `[source_id: "quote"]` citation brackets)
    into structured claims. Carries the colon-in-source-id regex fix
    documented in research_vertical/VERDICT.md Section 7.
  - build/citation_verifier.py               Claim, verify_claim(),
    Verdict -- the actual PROVEN / REFUTED / INSUFFICIENT judgment,
    fail-closed by construction (see that file's own docstring).
  - research_vertical/entrypoint.py          verify_extracted_claims(),
    _counts(), _composite_verdict(), build_human_receipt() -- the exact
    orchestration + plain-text rendering research_vertical's own CLI uses
    for every receipt it writes to receipts.jsonl. Reused unchanged so an
    agent-emitted receipt is the SAME SHAPE as a standalone-tool receipt,
    not a second, subtly-different format invented here.

All three are loaded from their original, unmodified on-disk paths via
importlib (the identical loader pattern research_vertical/entrypoint.py
uses for its own proven-module imports -- one pattern, not a second one
invented here). There is no vendored copy anywhere in this directory:
"do not fork or degrade the verification logic" is enforced structurally
-- there is nothing here TO degrade.

THE ONE ENTRY POINT:

    emit_receipt(answer_text: str, sources: Dict[str, str]) -> Dict[str, Any]

Contract
--------
answer_text : str
    The agent's own draft answer, using the citation bracket syntax
    claim_extract.py already parses:

        [source_id: "exact or near-exact supporting phrase from the source"]

    The agent writes this naturally as part of composing the answer --
    there is no separate paste-in step. A factual-sounding sentence with
    no bracket at all is still caught (extracted, then judged
    INSUFFICIENT: "no source cited for this claim") -- catching that
    silent case is the whole reason this tool exists.

sources : Dict[str, str]
    {source_id: full_text} for every source the agent ACTUALLY used to
    answer -- never fetched by this module, never guessed. A source_id
    cited in answer_text but missing from this dict comes back
    INSUFFICIENT ("not in corpus") by citation_verifier's own Rule 1.
    Fail closed, never fail open: an agent cannot make a claim look
    checked by simply not passing the source that would refute it --
    omitting a source yields INSUFFICIENT, not PROVEN.

Returns
-------
Dict[str, Any] with keys:
    "overall_verdict" : "PROVEN" | "REFUTED" | "INSUFFICIENT"
        Fail-closed composite (worst constituent verdict wins) --
        computed by entrypoint.py's own _composite_verdict(), reused
        unchanged.
    "overall_note"     : str  -- one-line human summary of the counts.
    "counts"           : {"PROVEN": n, "REFUTED": n, "INSUFFICIENT": n,
                           "total": n}
    "claims"           : List[dict] -- one entry per extracted claim:
                           {claim_id, statement, source_id, verdict,
                            reason, evidence_quote}
    "receipt_text"     : str  -- plain-text receipt block, ready to
                           append verbatim to the agent's answer.

Never coerces: a claim with no citation, or a citation the sources dict
can't back up, reports INSUFFICIENT with a reason naming exactly what's
missing -- it is never silently dropped and never rounded up to PROVEN.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any, Dict, List

HERE = Path(__file__).resolve().parent
NORTH_STAR = HERE  # receipts-kit: flat-sibling layout under .receipts/


# ---------------------------------------------------------------------------
# Loader -- imports each proven module from its ORIGINAL, unmodified path.
# Identical to research_vertical/entrypoint.py's own _load() helper, reused
# verbatim rather than reinvented. Raises loudly if the north_star layout
# has moved; never silently falls back to a stub or a degraded copy.
# ---------------------------------------------------------------------------

def _load(mod_name: str, rel_path: str) -> types.ModuleType:
    path = NORTH_STAR / rel_path
    if not path.exists():
        raise FileNotFoundError(
            f"proven module {mod_name!r} expected at {path} -- has the north_star "
            "layout moved? receipt_emitter.py intentionally does not vendor a copy "
            "of the verification logic."
        )
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot build an import spec for {mod_name!r} at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


_MODS: Dict[str, types.ModuleType] = {}


def _mods() -> Dict[str, types.ModuleType]:
    """Lazy singleton -- proven modules are loaded once per process, not
    once per emit_receipt() call. Importing research_vertical/entrypoint.py
    only defines module-level constants and functions; it runs no CLI and
    writes nothing to disk (that logic lives behind `if __name__ ==
    "__main__"`, never triggered by import)."""
    global _MODS
    if not _MODS:
        _MODS = {
            "citation_verifier": _load("citation_verifier", "citation_verifier.py"),
            "claim_extract": _load("claim_extract", "claim_extract.py"),
            "rv_entrypoint": _load("rv_entrypoint", "entrypoint.py"),
        }
    return _MODS


def emit_receipt(answer_text: str, sources: Dict[str, str], *, label: str = "agent-answer") -> Dict[str, Any]:
    """The one function this module exists to provide. See module
    docstring for the full contract. `label` is a free-text tag carried
    into the receipt header only (e.g. a question id or turn id the
    calling harness wants echoed back) -- it plays no role in judgment."""
    mods = _mods()
    cv = mods["citation_verifier"]
    ce = mods["claim_extract"]
    ep = mods["rv_entrypoint"]

    extracted = ce.extract_claims(answer_text)
    claims: List[Dict[str, Any]] = ep.verify_extracted_claims(cv, extracted, sources)
    counts = ep._counts(claims)
    overall = ep._composite_verdict(counts)
    overall_note = (
        f"{counts.get('PROVEN', 0)}/{counts.get('total', 0)} claims PROVEN, "
        f"{counts.get('REFUTED', 0)} REFUTED, {counts.get('INSUFFICIENT', 0)} INSUFFICIENT "
        f"-> composite {overall}"
    )
    receipt_text = ep.build_human_receipt(label, overall, overall_note, claims)

    return {
        "overall_verdict": overall,
        "overall_note": overall_note,
        "counts": counts,
        "claims": claims,
        "receipt_text": receipt_text,
    }


# ===========================================================================
# Opposed-pair self-test -- a supported claim must come back PROVEN, a
# planted uncited claim must come back INSUFFICIENT, and the composite must
# never coerce the two into agreeing. This module trusts citation_verifier's
# own self-tests (run separately, in that file) for the deeper PROVEN /
# REFUTED / INSUFFICIENT judgment mechanics; this test only checks that
# emit_receipt's plumbing carries those verdicts through unmodified,
# end-to-end, from a realistic agent answer string.
# ===========================================================================

def _self_test() -> bool:
    ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        status = "PASS" if cond else "FAIL"
        if not cond:
            ok = False
        print(f"  [{status}] {label}" + (f" -- {detail}" if detail and not cond else ""))

    print("=== receipt_emitter.py opposed-pair self-test ===\n")

    # The supported claim: cited, and the source genuinely states the
    # exact quoted value -- the positive control.
    answer = (
        "The benchmark shows the system achieves 89% precision on edge-case "
        'detection [smith2019: "achieves 89% precision on edge-case detection"]. '
        # The planted uncited claim: reads as a factual assertion (contains
        # a claim verb, " has ") but carries NO citation bracket at all --
        # the negative control this whole tool exists to catch.
        "The vendor also has industry-leading throughput compared to prior work."
    )
    sources = {
        "smith2019": (
            "In our evaluation, the system achieves 89% precision on edge-case "
            "detection across all test scenarios."
        ),
    }

    result = emit_receipt(answer, sources, label="selftest-goal")

    check("emit_receipt returns the documented top-level keys", set(result.keys()) == {
        "overall_verdict", "overall_note", "counts", "claims", "receipt_text",
    }, str(sorted(result.keys())))

    check("exactly two claims extracted (one cited, one uncited)", len(result["claims"]) == 2,
          f"got {len(result['claims'])}: {result['claims']}")

    cited = [c for c in result["claims"] if c["source_id"] == "smith2019"]
    uncited = [c for c in result["claims"] if c["source_id"] is None]

    check("supported, quoted claim is PROVEN", bool(cited) and cited[0]["verdict"] == "PROVEN",
          str(cited))
    check("PROVEN claim carries the matching evidence quote", bool(
        cited and cited[0]["evidence_quote"] and "89% precision on edge-case detection" in cited[0]["evidence_quote"]
    ))

    check("planted uncited claim is INSUFFICIENT, not PROVEN and not silently dropped",
          bool(uncited) and uncited[0]["verdict"] == "INSUFFICIENT", str(uncited))
    check("INSUFFICIENT reason names exactly what's missing (no source cited)",
          bool(uncited and "no source cited" in uncited[0]["reason"]))

    check("never coerced: the two opposed claims do NOT share one verdict",
          bool(cited and uncited and cited[0]["verdict"] != uncited[0]["verdict"]),
          f"cited={cited[0]['verdict'] if cited else None} uncited={uncited[0]['verdict'] if uncited else None}")

    check("composite is fail-closed: one INSUFFICIENT claim drags overall to INSUFFICIENT",
          result["overall_verdict"] == "INSUFFICIENT", result["overall_verdict"])
    check("overall is never coerced to PROVEN despite one genuinely proven claim",
          result["overall_verdict"] != "PROVEN")

    check("receipt_text is plain text carrying both verdict labels",
          "PROVEN" in result["receipt_text"] and "INSUFFICIENT" in result["receipt_text"])
    check("receipt_text carries the caller-supplied label", "selftest-goal" in result["receipt_text"])

    # A second, independent call with a fresh sources dict that OMITS the
    # cited source entirely -- must not silently pass or reuse cached
    # judgment from the first call. Confirms Rule 1 (citation to a source
    # missing from the corpus is unverifiable, not PROVEN by omission).
    result2 = emit_receipt(
        'The system reports 99% accuracy [ghost2020: "99% accuracy on all tasks"].',
        sources={},  # ghost2020 is not in the corpus at all
        label="selftest-missing-source",
    )
    check("citation to a source absent from the corpus is INSUFFICIENT, never PROVEN",
          result2["overall_verdict"] == "INSUFFICIENT", result2["overall_verdict"])
    check("missing-source reason names the corpus gap", bool(
        result2["claims"] and "not in the offline corpus" in result2["claims"][0]["reason"]
    ))

    print()
    if ok:
        print("=== all receipt_emitter.py checks PASSED ===")
    else:
        print("=== receipt_emitter.py: SOME CHECKS FAILED ===")
    return ok


if __name__ == "__main__":
    sys.exit(0 if _self_test() else 1)
