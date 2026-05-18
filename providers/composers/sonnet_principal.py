"""Sonnet principal subprocess wrapper.

Extracted from scripts/run_tb_principal.py:201-234 so both the wrapper
and tb_endpoint.py can share the subprocess + fallback pattern. Behavior
is identical to the original call_sonnet_principal — same caveat banner,
same timeout handling, same error-tuple shape.
"""

import os
import subprocess
import time
from typing import Tuple

# launchd-managed processes don't inherit the user shell PATH, so a bare
# "claude" call resolves to "command not found" even when claude is
# installed via nvm or in ~/.local/bin. Allow CLAUDE_BIN env to point at
# the absolute path; fall back to PATH-resolved "claude" when unset.
_CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")

# Phase 1 (charter commitment #2 — token budget, not count budget).
# TB advice was previously truncated at 3000 chars (~750 tokens). Phase 1
# bumped to 12000 (~3000 tokens). Phase 3 (2026-05-10) bumped further to
# 40000 (~10000 tokens) per Lokesh "comprehensive complete response"
# direction. Composer (Sonnet 4.6 / Opus 4.7 = 200K context) has plenty
# of room. Env tunable for downshift via TB_ADVICE_CHAR_BUDGET.
_TB_ADVICE_CHAR_BUDGET = int(os.environ.get("TB_ADVICE_CHAR_BUDGET", "40000"))


def wrap_tb_advice(tb_advice: str, query_summary: str) -> str:
    """Wrap TB's grounding read in a caveat banner for Sonnet's prompt prefix.

    Empty advice → empty wrapper (Sonnet runs without TB context). The
    caveat banner tells Sonnet to treat TB's text as alpha/beta input and
    decide what to keep.

    Phase 3.5 temporal-context (2026-05-10): banner now embeds today's
    date so composer can reason about staleness in TB's grounded text.
    Resolves Anjali-meetup-tomorrow temporal blindspot bug.
    """
    if not tb_advice:
        return ""
    advice = tb_advice[:_TB_ADVICE_CHAR_BUDGET]
    import datetime as _dt
    today_str = _dt.datetime.now(_dt.timezone.utc).astimezone().strftime(
        "%Y-%m-%d (%A)"
    )
    return (
        "═══════════════════════════════════════════════════════════════\n"
        f"[TB-CONTEXT — alpha/beta, TB v14 may hallucinate. TODAY = {today_str}]\n"
        f"TB's RAG-grounded read on: {query_summary[:140]}\n"
        "Use, discard fully, or take partial signal — your call. Treat any\n"
        "'tomorrow / yesterday / last week' inside this block as RELATIVE\n"
        "to the chunk's [|when] tag, NOT relative to today.\n"
        "───────────────────────────────────────────────────────────────\n"
        f"{advice}\n"
        "═══════════════════════════════════════════════════════════════\n\n"
    )


def compose_with_sonnet(prompt: str, query_summary: str = "",
                        tb_advice: str = "",
                        timeout: int = 600,
                        model: str = "sonnet") -> Tuple[str, int, dict]:
    """Call Sonnet/Haiku via `claude -p --model {model}` subprocess.

    Prepends a wrapped TB-advice block (if non-empty) to the prompt so
    the principal sees TB's RAG-grounded read alongside the task. The
    caveat banner makes the alpha/beta status of TB's input explicit.

    Returns (text, duration_ms, response_dict). On error, text starts
    with [SONNET_PRINCIPAL_ERROR] and response_dict is empty {}; callers
    should detect the error prefix and fall back to TB-only.

    Args:
        prompt: The actual task prompt for the principal.
        query_summary: Short string used in the TB-context banner.
        tb_advice: Pre-fetched TB grounding text. Empty = no TB context.
        timeout: Subprocess wall-clock seconds. Default 600.
        model: claude -p --model value. Default "sonnet"; pass "haiku"
               for cheaper budget runs.
    """
    advice_block = wrap_tb_advice(tb_advice, query_summary)
    full_prompt = advice_block + prompt
    t0 = time.time()
    try:
        proc = subprocess.run(
            [_CLAUDE_BIN, "-p", "--model", model],
            input=full_prompt, capture_output=True, text=True,
            timeout=timeout,
        )
        duration_ms = int((time.time() - t0) * 1000)
        text = (proc.stdout or "").strip()
        if proc.returncode != 0:
            err = (proc.stderr or "").strip()[:500]
            return (
                f"[SONNET_PRINCIPAL_ERROR] exit={proc.returncode}: {err}",
                duration_ms,
                {},
            )
        return text, duration_ms, {
            "ok": True,
            "output": text,
            "tb_advice_chars": len(tb_advice),
            "model": model,
        }
    except subprocess.TimeoutExpired:
        return (
            f"[SONNET_PRINCIPAL_ERROR] timeout after {timeout}s",
            int((time.time() - t0) * 1000),
            {},
        )
    except FileNotFoundError:
        return (
            "[SONNET_PRINCIPAL_ERROR] claude CLI not found in PATH",
            int((time.time() - t0) * 1000),
            {},
        )
    except Exception as e:
        return (
            f"[SONNET_PRINCIPAL_ERROR] {type(e).__name__}: {e}",
            int((time.time() - t0) * 1000),
            {},
        )


def is_principal_error(text: str) -> bool:
    """True if text was produced by an error fallback rather than the model."""
    return text.startswith("[SONNET_PRINCIPAL_ERROR]")


# Phase 1 §1.11: refusal detection patterns.
# Anthropic-typical refusal language. Used to flag turns where Sonnet/Opus
# declined to produce content. Captured to .brain/ledger/refusal_log.jsonl
# for v15 anti-refusal corpus assembly.
import re as _re
_REFUSAL_PATTERNS = [
    _re.compile(r"\bI (?:can't|cannot|won't|will not) (?:help with|assist with|provide|generate|create|write)\b", _re.IGNORECASE),
    _re.compile(r"\bI'm (?:not able to|unable to) (?:help|assist|provide|generate|create|write)\b", _re.IGNORECASE),
    _re.compile(r"\bI (?:can't|cannot|won't) (?:do|produce|engage with) that\b", _re.IGNORECASE),
    _re.compile(r"\b(?:against|violates) my (?:guidelines|values|principles|policy|policies)\b", _re.IGNORECASE),
    _re.compile(r"\bI (?:don't|do not) feel comfortable\b", _re.IGNORECASE),
    _re.compile(r"\bI'd (?:prefer|rather) not (?:to|engage)\b", _re.IGNORECASE),
    _re.compile(r"\bnot something I can (?:help|assist|do|engage)\b", _re.IGNORECASE),
    _re.compile(r"\bI need to decline\b", _re.IGNORECASE),
    _re.compile(r"\bI must respectfully decline\b", _re.IGNORECASE),
    _re.compile(r"\bI(?:'m| am) (?:going to|gonna) decline\b", _re.IGNORECASE),
    _re.compile(r"^I appreciate (?:your|the) (?:question|interest), but\b", _re.IGNORECASE | _re.MULTILINE),
]


def detect_refusal(text: str) -> dict:
    """Detect Anthropic-typical refusal language in composer output.

    Returns dict:
        {
          "refused": bool,
          "pattern": str | None,   # regex source that matched
          "snippet": str           # first 240 chars of refusal text
        }

    False-positive risk: low — patterns chosen to match common Anthropic
    refusal phrasing while skipping legitimate uses (e.g. "I can't tell
    you the answer, but here's a hint" — the second clause means it's
    not a refusal, but the regex catches "I can't tell". So we also
    require the refusal phrase to appear in the FIRST 400 chars and
    not be followed by a continuation that produces content.

    For now: simple pattern match. Phase 5+ refines with proper LLM
    judge (cheap haiku call) for borderline cases.
    """
    if not text:
        return {"refused": False, "pattern": None, "snippet": ""}
    head = text[:400]
    for pat in _REFUSAL_PATTERNS:
        m = pat.search(head)
        if m:
            return {
                "refused": True,
                "pattern": pat.pattern,
                "snippet": text[:240],
                "match_start": m.start(),
            }
    return {"refused": False, "pattern": None, "snippet": ""}
