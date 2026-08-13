# --- receipts_kit adaptation banner (added by build_single_file.sh; see that script's header) ---
# This file began as receipt_gate.py in this project's
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
receipt_gate.py -- Claude Code Stop-hook script implementing the design in
hook_design.md ("Where it plugs in" / "What the hook actually does" /
"Fail-safe"). Stdlib only. Zero network. Zero filesystem writes.

STATUS: implemented + proven (see the six-case proof run recorded in
hook_design.md's "STATUS" section). NOT WIRED into any live settings.json --
see receipt_gate_settings.snippet.json in this same directory for the exact
Stop-hook stanza an operator would paste, and wiring it in is a separate,
operator-approved step.

CONTRACT (Claude Code Stop hook)
---------------------------------
Claude Code invokes a Stop-hook command with the hook event JSON on stdin --
NOT the response text directly. The real shape (confirmed against this
repo's own existing Stop hooks, .claude/hooks/session_claim_gate_stop.sh and
.claude/hooks/stop_gates.sh, which already parse it) is:

    {"session_id": "...", "transcript_path": "/abs/path/to/transcript.jsonl",
     "hook_event_name": "Stop", "stop_hook_active": false, ...}

`transcript_path` points at a JSONL session transcript; each line is a
record whose "message" field (when present) carries {"role": ..., "content":
[...]} in the same shape as the Anthropic Messages API -- content is a list
of blocks, and the ones this gate cares about are {"type": "text", "text":
"..."}. This script defensively parses that file to recover the LAST
assistant-role message's text (concatenation of its text blocks, in order)
-- it never looks at the hook stdin JSON for the response text itself,
because the Stop event does not carry it there.

Exit codes, per Claude Code hook semantics:
    0  -- allow the Stop to proceed (pass, or kill-switched).
    2  -- BLOCK the Stop; stderr is fed back to the model so it can act on
          the message (per Claude Code's documented Stop-hook behavior).

FAIL-SAFE POLICY (hook_design.md's "Fail-safe" section, restated in code)
---------------------------------------------------------------------------
Every unexpected exception in this script's own judgment logic -> exit 2,
"receipt gate error -- answer unverified". A hook that fails OPEN on its own
bugs would silently convert a verification outage into a false pass, which
is the exact "coerce to green" failure this whole discipline exists to
refuse.

THE ONE DOCUMENTED EXCEPTION -- transcript-unreadable fails OPEN (exit 0 +
stderr warning), not closed. This is a deliberate tradeoff, not an
oversight: a missing/corrupt transcript is an INFRASTRUCTURE fact (harness
version skew changing the JSONL shape, a disk hiccup, a session whose
transcript file has not been flushed yet), not a claim the agent is trying
to sneak past the gate. Failing closed on it would block *every* Stop event
fleet-wide the moment one infra path breaks, which is a worse outage than
occasionally missing a check on one turn. See `_last_assistant_text` below
for exactly which conditions this exception covers (missing file, and a
transcript whose lines don't parse in a way "more than one bad line" would
flag as "format not understood", mirroring stop_gates.sh's own
`read_turn()` discipline in this same repo).

WHY NO REAL SOURCE-BACKED RECOMPUTE (hook_design.md "Where `sources` comes
from")
---------------------------------------------------------------------------
The design doc's stronger hardening -- re-deriving the agent's `sources`
dict from this turn's own Read/WebFetch tool-call log in the transcript --
needs a source_id <-> tool-call convention that does not exist yet (which
file/fetch corresponds to which cited source_id is not structurally
recoverable without the agent recording that mapping somewhere the hook can
read). Inventing a fuzzy mapping here would risk exactly the wrong kind of
BLOCK: flagging a genuinely PROVEN claim as INSUFFICIENT because the hook
guessed the wrong tool-call as its source. Per hook_design.md's own
instruction ("where sources are NOT recoverable from the transcript, do NOT
fake a recompute"), this script does NOT attempt that. Instead it does two
things that need NO source corpus at all, and are still real, unfaked
checks rather than a rubber stamp:

  1. Internal consistency -- the receipt's own "Overall verdict: X (...)"
     line states BOTH the verdict and a full count breakdown (P/total
     PROVEN, R REFUTED, I INSUFFICIENT); the per-claim `[VERDICT]` lines
     below it are counted directly and must match those stated counts
     exactly, and the composite recomputed from those counts via
     entrypoint.py's own (unchanged, imported) `_composite_verdict()` must
     match the stated overall verdict. A receipt that says "2/2 PROVEN"
     while one of its own per-claim lines says INSUFFICIENT is caught here,
     with no external sources needed to catch it.
  2. Claim-count cross-check against the answer text -- claim_extract.py's
     `extract_claims()` (imported unchanged) needs no source corpus either;
     it only parses citation brackets out of freeform text. Re-running it
     on the answer portion (the text above the receipt block) and comparing
     the count to the receipt's own stated total catches a receipt that
     silently dropped a claim the answer text actually makes -- again, no
     sources required, no verdict faked.

What this script does NOT do: it does not re-run citation_verifier's actual
PROVEN/REFUTED/INSUFFICIENT judgment against a source corpus, because it
has no trustworthy corpus to judge against. That is the known gap this file
inherits from hook_design.md, not a bug hidden here.

KILL SWITCH: NUCLEUS_RECEIPT_GATE_DISABLED=1 -> exit 0 silently (no stdout,
no stderr), checked before anything else, including before stdin is read.

macOS BSD-safe: this is a pure-stdlib Python script (json / os / re / sys /
types / importlib.util / pathlib / dataclasses via the imported modules) --
no GNU-only CLI flags, no third-party packages, no network calls.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import types
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

HERE = Path(__file__).resolve().parent          # .../agent_integration
NORTH_STAR = HERE  # receipts-kit: flat-sibling layout under .receipts/

_KILL_SWITCH_ENV = "NUCLEUS_RECEIPT_GATE_DISABLED"

# Matches the exact header build_human_receipt() (research_vertical/
# entrypoint.py) writes: f"RESEARCH RECEIPT -- {goal_slug}".
_RECEIPT_HEADER_RE = re.compile(r"^RESEARCH RECEIPT\s*--", re.MULTILINE)

# Matches the exact "Overall verdict: ..." line build_human_receipt() writes,
# built from emit_receipt()'s overall_note format string:
#   f"{P}/{total} claims PROVEN, {R} REFUTED, {I} INSUFFICIENT -> composite {overall}"
_OVERALL_RE = re.compile(
    r"^Overall verdict:\s*(PROVEN|REFUTED|INSUFFICIENT)\s*\(\s*"
    r"(\d+)/(\d+)\s*claims PROVEN,\s*(\d+)\s*REFUTED,\s*(\d+)\s*INSUFFICIENT\s*"
    r"->\s*composite\s*(PROVEN|REFUTED|INSUFFICIENT)\s*\)\s*$",
    re.MULTILINE,
)

# Matches each per-claim line build_human_receipt() writes:
#   f"  [{verdict:<12}] {statement}"
_CLAIM_LINE_RE = re.compile(r"^\s*\[(PROVEN|REFUTED|INSUFFICIENT)\s*\]", re.MULTILINE)


# ---------------------------------------------------------------------------
# Loader -- imports the proven modules from their ORIGINAL, unmodified
# paths, identical in spirit to receipt_emitter.py's own `_load()` (one
# pattern, not reinvented a third time). Raises loudly if the north_star
# layout has moved; the top-level fail-closed handler turns that into
# exit 2, never a silent stub.
# ---------------------------------------------------------------------------

def _load(mod_name: str, rel_path: str) -> types.ModuleType:
    path = NORTH_STAR / rel_path
    if not path.exists():
        raise FileNotFoundError(
            f"proven module {mod_name!r} expected at {path} -- has the north_star "
            "layout moved? receipt_gate.py intentionally does not vendor a copy "
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
    global _MODS
    if not _MODS:
        _MODS = {
            "claim_extract": _load("claim_extract", "claim_extract.py"),
            "rv_entrypoint": _load("rv_entrypoint", "entrypoint.py"),
        }
    return _MODS


class TranscriptUnreadable(Exception):
    """Raised when the transcript file itself cannot be found or parsed.
    Caught specially in main() -- this is the ONE case that exits 0 with a
    stderr warning instead of failing closed. See module docstring."""


def _read_stdin_event() -> Dict[str, Any]:
    """Read + parse the Stop-hook JSON event from stdin. Deliberately does
    NOT catch its own exceptions -- garbage/unparseable stdin must propagate
    to main()'s top-level fail-closed handler (exit 2), per the task's own
    'garbage stdin -> fail closed' requirement. This is a DIFFERENT failure
    mode than an unreadable transcript FILE (see TranscriptUnreadable) --
    malformed input to the hook itself is not the same fact as a transcript
    infra hiccup, and must not share the fail-open exception."""
    raw = sys.stdin.read()
    event = json.loads(raw)
    if not isinstance(event, dict):
        raise ValueError(f"Stop-hook stdin event must be a JSON object, got {type(event).__name__}")
    return event


def _last_assistant_text(transcript_path: str) -> str:
    """Defensively parse the Stop-hook transcript JSONL and return the
    concatenated text blocks of the last TEXT-BEARING assistant-role
    message (in document order). Deliberately not "the last assistant
    record": a trailing tool_use-only record makes no user-visible claim,
    and the receipt contract governs what the user READS. Two free-lane
    reviews (2026-08-10) flagged the `if texts:` guard as a stale-object
    leak; the opposed pair showed the opposite -- dropping it would
    validate an empty string and ship the visible citation unchecked. Raises TranscriptUnreadable -- never any other
    exception type -- for every way this can fail, so main() has exactly
    one thing to catch for the fail-open exception.

    'Nothing matched' and 'could not parse' are kept as different code
    paths on purpose (mirrors .claude/hooks/stop_gates.sh's own
    read_turn() comment on this exact point, in this same repo): an empty
    transcript with no assistant turns yet is a normal, valid state (no
    citations possible yet -> pass through with no warning at all); a
    transcript that exists but whose lines don't parse as JSON is a
    genuinely different, infra-level fact, and is what actually triggers
    the fail-open warning path.
    """
    if not transcript_path or not os.path.exists(transcript_path):
        raise TranscriptUnreadable(f"transcript_path missing or does not exist: {transcript_path!r}")

    bad_lines = 0
    last_line_bad = False
    last_text: Optional[str] = None
    try:
        with open(transcript_path, "r", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    bad_lines += 1
                    last_line_bad = True
                    continue
                last_line_bad = False
                if not isinstance(rec, dict):
                    continue
                message = rec.get("message")
                if not isinstance(message, dict) or message.get("role") != "assistant":
                    continue
                blocks = message.get("content")
                if not isinstance(blocks, list):
                    continue
                texts = [
                    b.get("text", "")
                    for b in blocks
                    if isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip()
                ]
                if texts:
                    last_text = "\n\n".join(texts)
    except OSError as exc:
        raise TranscriptUnreadable(f"transcript unreadable: {type(exc).__name__}: {exc}") from exc

    # A single unparseable trailing line is normal -- the transcript file is
    # actively being appended to while this hook reads it. More than one bad
    # line means the JSONL format changed under us (or the file is genuinely
    # corrupt); guessing past that would be inventing an answer, so it is
    # treated the same as a missing file.
    if bad_lines > 1:
        raise TranscriptUnreadable(f"{bad_lines} unparseable transcript lines -- format not understood")

    # Wrong-object guard (found by a free-lane Gemini review 2026-08-10,
    # confirmed by repro before this fix): if the ONE tolerated bad line is
    # the FINAL line, it is most plausibly the CURRENT assistant message
    # caught mid-append -- and returning here would validate the PREVIOUS
    # turn's text as if it were this one (silent wrong-object exit 0).
    # Unreadable-current-turn goes to the documented fail-open WARNING
    # path, which is visible, instead of a silent stale-object success.
    if last_line_bad:
        raise TranscriptUnreadable(
            "final transcript line unparseable -- current turn likely mid-append; "
            "refusing to validate the previous turn's text in its place"
        )

    return last_text or ""


def _split_answer_and_receipt(text: str) -> Tuple[str, Optional[str]]:
    """Split the final assistant text into (answer_portion, receipt_block).
    receipt_block is None if no 'RESEARCH RECEIPT --' header line is found
    anywhere in the text."""
    m = _RECEIPT_HEADER_RE.search(text)
    if not m:
        return text, None
    return text[: m.start()], text[m.start():]


def _validate_receipt_shape(receipt_text: str, answer_text: str, ep_mod, ce_mod) -> Tuple[bool, str]:
    """Structural + internal-consistency verification of an already-present
    receipt block. Needs no external source corpus (see module docstring
    'WHY NO REAL SOURCE-BACKED RECOMPUTE'). Returns (ok, reason); never
    raises for a malformed receipt -- a malformed receipt IS the answer,
    not an error in this function. Genuinely unexpected exceptions (e.g. an
    imported proven module's API shape changed) are left to propagate to
    main()'s fail-closed handler, which is correct: this function's own
    bugs must not silently read as 'receipt looked fine'."""
    m = _OVERALL_RE.search(receipt_text)
    if not m:
        return False, (
            "receipt block is present but its 'Overall verdict: ... (N/M claims PROVEN, "
            "R REFUTED, I INSUFFICIENT -> composite ...)' line is missing or does not match "
            "the expected build_human_receipt() format"
        )

    stated_overall, p_str, total_str, r_str, i_str, note_composite = m.groups()

    if stated_overall != note_composite:
        return False, (
            f"receipt is internally inconsistent: the header states 'Overall verdict: "
            f"{stated_overall}' but its own note's '-> composite' clause says "
            f"'{note_composite}' -- the two mentions of the same verdict disagree"
        )

    p_claimed, total_claimed, r_claimed, i_claimed = (
        int(p_str), int(total_str), int(r_str), int(i_str)
    )
    if p_claimed + r_claimed + i_claimed != total_claimed:
        return False, (
            f"receipt's own stated counts don't add up: {p_claimed} PROVEN + {r_claimed} REFUTED "
            f"+ {i_claimed} INSUFFICIENT != stated total {total_claimed}"
        )

    claim_lines = _CLAIM_LINE_RE.findall(receipt_text)
    p_actual = claim_lines.count("PROVEN")
    r_actual = claim_lines.count("REFUTED")
    i_actual = claim_lines.count("INSUFFICIENT")
    total_actual = len(claim_lines)

    if (p_actual, r_actual, i_actual, total_actual) != (p_claimed, r_claimed, i_claimed, total_claimed):
        return False, (
            "receipt's stated counts contradict its own per-claim lines: header note says "
            f"{p_claimed}/{total_claimed} claims PROVEN, {r_claimed} REFUTED, {i_claimed} "
            f"INSUFFICIENT, but the per-claim '[VERDICT]' lines in the same receipt actually "
            f"show {p_actual}/{total_actual} PROVEN, {r_actual} REFUTED, {i_actual} INSUFFICIENT"
        )

    # Recompute the composite from the receipt's OWN per-claim tally using
    # entrypoint.py's real, unchanged _composite_verdict() (fail-closed:
    # REFUTED wins if any REFUTED, else INSUFFICIENT if any INSUFFICIENT,
    # else PROVEN) -- not reinvented here.
    recomputed = ep_mod._composite_verdict(
        {"PROVEN": p_actual, "REFUTED": r_actual, "INSUFFICIENT": i_actual, "total": total_actual}
    )
    if recomputed != stated_overall:
        return False, (
            f"recomputing the composite verdict from the receipt's own per-claim lines via "
            f"entrypoint.py's _composite_verdict() gives {recomputed!r}, which disagrees with "
            f"the receipt's stated overall verdict {stated_overall!r}"
        )

    # Sources-independent cross-check against the answer text itself: does
    # the receipt account for every claim the answer text actually makes?
    # extract_claims() needs no source corpus -- it only parses citation
    # brackets and claim-shaped sentences out of freeform text -- so this
    # catches a receipt that silently dropped (or invented) a claim,
    # without faking any per-claim verdict.
    expected_claims = ce_mod.extract_claims(answer_text)
    if len(expected_claims) != total_actual:
        return False, (
            f"receipt accounts for {total_actual} claim(s), but re-extracting citations from "
            f"the answer text (claim_extract.extract_claims, unchanged) finds "
            f"{len(expected_claims)} -- the receipt does not match the claims actually present "
            "in the answer"
        )

    return True, "receipt shape, internal counts, and claim coverage are all self-consistent"


def _advise_naked_success_claims(answer_text: str) -> None:
    """Advisory-only scan for unreceipted success claims (exit code is
    never affected; every failure path is swallowed). Kill switch:
    NUCLEUS_CLAIM_ADVISORY_DISABLED=1. Hits go to stderr and are appended
    to claim_advisories.log beside this file for calibration review."""
    if os.environ.get("NUCLEUS_CLAIM_ADVISORY_DISABLED") == "1":
        return
    try:
        claim_scan = _load("claim_scan", "agent_integration/claim_scan.py")
        hits = claim_scan.scan_success_claims(answer_text)
        if not hits:
            return
        rendered = claim_scan.format_success_claim_hits(hits)
        print(f"receipt gate ADVISORY (non-blocking) -- {rendered}", file=sys.stderr)
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "claim_advisories.log")
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(rendered.rstrip("\n") + "\n---\n")
    except Exception:
        pass


def main() -> int:
    # Checked before anything else, including before stdin is read -- the
    # kill switch must work even if stdin itself would otherwise be
    # inspected.
    if os.environ.get(_KILL_SWITCH_ENV) == "1":
        return 0

    try:
        event = _read_stdin_event()
    except Exception as exc:
        print(
            f"receipt gate error -- answer unverified ({type(exc).__name__}: {exc}); "
            "stdin did not parse as the expected Claude Code Stop-hook JSON event.",
            file=sys.stderr,
        )
        return 2

    # Claude Code re-invokes Stop hooks after a blocking hook's stderr is
    # fed back to the model and the model responds again; stop_hook_active
    # marks that replay. Without this check, a hook that blocks could fire
    # on its own continuation and loop. Passing through on replay matches
    # the convention already used by this repo's own Stop hooks
    # (session_claim_gate_stop.sh, stop_gates.sh both check the same field).
    if event.get("stop_hook_active") is True:
        return 0

    transcript_path = event.get("transcript_path") or ""

    try:
        final_text = _last_assistant_text(transcript_path)
    except TranscriptUnreadable as exc:
        # THE ONE DOCUMENTED FAIL-OPEN EXCEPTION. See module docstring
        # "THE ONE DOCUMENTED EXCEPTION" for the full tradeoff rationale.
        print(
            f"receipt gate WARNING -- transcript unreadable, passing through unchecked: {exc}",
            file=sys.stderr,
        )
        return 0
    except Exception as exc:
        print(f"receipt gate error -- answer unverified ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 2

    try:
        mods = _mods()
        ce = mods["claim_extract"]
        ep = mods["rv_entrypoint"]

        answer_text, receipt_text = _split_answer_and_receipt(final_text)

        # Scan only the answer portion for citation brackets -- the
        # receipt block's own per-claim lines use "[VERDICT]" bracket
        # syntax too, and must not be mistaken for a NEW citation in the
        # answer. Reuses claim_extract.py's own _CITATION_RE unchanged
        # (the same pattern hook_design.md names explicitly), rather than
        # a second, possibly-drifting regex invented here.
        if not ce._CITATION_RE.search(answer_text):
            # ADVISORY ONLY (never blocks, never alters the exit code):
            # bracket-less answers are this gate's named blind spot, and
            # the wound-map corpus ranks naked "tests pass"-style success
            # claims as the most-repeated real failure shape. claim_scan's
            # Part-2 detector flags them; a scanner cannot verify truth,
            # only the absence of evidence-shaped text, so this stays a
            # warning by design.
            _advise_naked_success_claims(answer_text)
            return 0  # claimless -- nothing this gate checks for

        if receipt_text is None:
            print(
                "receipt gate BLOCK -- this response cites source(s) with bracket syntax "
                "([id: \"quote\"] or [id]) but ships with no RESEARCH RECEIPT block attached. "
                "Use receipt_emitter.emit_receipt() in .receipts/receipt_emitter.py to build a verified RESEARCH RECEIPT and attach it before finishing this turn.",
                file=sys.stderr,
            )
            return 2

        ok, reason = _validate_receipt_shape(receipt_text, answer_text, ep, ce)
        if not ok:
            print(f"receipt gate BLOCK -- malformed/self-contradictory receipt: {reason}", file=sys.stderr)
            return 2

        return 0
    except Exception as exc:
        print(f"receipt gate error -- answer unverified ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
