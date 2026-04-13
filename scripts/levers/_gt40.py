"""Shared helpers for GT40-wrapping levers (gt40_typecheck, gt40_test_smoke).

Both levers run ``nucleus verify --tiers <chain> --json`` and translate the
structured receipt into a lever observation. Centralizing the parse +
classify logic here gives us:

  - One place that knows how to extract JSON from polluted stdout
    (nucleus prints urllib3 warnings + INSECURE-MODE banners before/after
    the receipt; receipt is always the last balanced ``{...}`` block).
  - One place that maps receipt fields → lever outcome, so both levers
    behave consistently.

Outcome map (matches TODOS.md TODO 4 spec):

  - ``tiers_failed`` non-empty           → ``found``  (real failures)
  - ``verified`` AND target tier reached → ``clean``
  - target tier not reached, no fails    → ``skipped`` (preconditions/env)
  - JSON unparseable                     → caller emits ``error``
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple


def parse_receipt(stdout: str, stderr: str = "") -> Optional[Dict[str, Any]]:
    """Extract the JSON receipt from nucleus verify output.

    Returns the parsed dict, or None if no valid receipt found. Handles:
      - Pre-JSON pollution (urllib3 warnings, INSECURE MODE banners)
      - Post-JSON noise (rare)
      - Argparse errors (no JSON at all → returns None)

    Strategy: scan stdout+stderr for balanced top-level ``{...}`` blocks,
    parse each that contains ``"verified"``, return the LAST one. Robust
    against nested braces in ``signals`` (which a regex can't handle) and
    against earlier JSON-looking blobs in warning text.
    """
    blob = (stdout or "") + "\n" + (stderr or "")
    last_receipt: Optional[Dict[str, Any]] = None
    for chunk in _iter_balanced_braces(blob):
        if '"verified"' not in chunk:
            continue
        try:
            parsed = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "verified" in parsed:
            last_receipt = parsed
    return last_receipt


def _iter_balanced_braces(text: str):
    """Yield each top-level balanced ``{...}`` substring in text.

    Walks the string char-by-char, tracking string-quote state so braces
    inside JSON strings don't throw off the count. Skips escapes."""
    i, n = 0, len(text)
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        depth = 0
        in_str = False
        escape = False
        start = i
        while i < n:
            ch = text[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        yield text[start:i + 1]
                        i += 1
                        break
            i += 1
        else:
            return  # unterminated brace, give up


def classify_receipt(
    receipt: Dict[str, Any],
    target_tier: int,
    *,
    findings_limit: int = 20,
) -> Tuple[str, Dict[str, Any]]:
    """Map a parsed receipt to (outcome, detail).

    Outcomes:
      - ``found``   — receipt['tiers_failed'] non-empty (real failures).
      - ``clean``   — receipt['verified'] AND tier_reached >= target_tier.
      - ``skipped`` — target tier not reached but no failures
                      (preconditions, env gap, or chain shortened).
    """
    tiers_failed = receipt.get("tiers_failed") or []
    tiers_passed = receipt.get("tiers_passed") or []
    tiers_skipped = receipt.get("tiers_skipped") or []
    tier_reached = receipt.get("tier_reached", -1)
    verified = bool(receipt.get("verified", False))
    signals = receipt.get("signals") or []

    base: Dict[str, Any] = {
        "tier": target_tier,
        "tier_reached": tier_reached,
        "tiers_passed": tiers_passed,
        "duration_s": receipt.get("duration_s"),
    }

    if tiers_failed:
        failed_signals = [s for s in signals if isinstance(s, dict) and not s.get("passed")]
        findings = [_signal_summary(s) for s in failed_signals[:findings_limit]]
        return ("found", {
            **base,
            "tiers_failed": tiers_failed,
            "findings": findings,
        })

    if verified and isinstance(tier_reached, int) and tier_reached >= target_tier:
        return ("clean", base)

    return ("skipped", {
        **base,
        "reason": f"tier {target_tier} not reached (preconditions/env)",
        "tiers_skipped": tiers_skipped,
    })


def _signal_summary(signal: Dict[str, Any]) -> str:
    tier = signal.get("tier", "?")
    check = signal.get("check", "?")
    target = signal.get("file") or signal.get("path") or ""
    detail = signal.get("error") or signal.get("reason") or ""
    pieces = [f"tier{tier}", check]
    if target:
        pieces.append(str(target))
    if detail:
        pieces.append(str(detail)[:120])
    return " | ".join(pieces)


def build_argv(
    nucleus_bin: str,
    chain: List[int],
    timeout_seconds: int,
) -> List[str]:
    """Build ``nucleus verify --tiers 0,1,...,N --json --timeout T`` argv."""
    return [
        nucleus_bin,
        "verify",
        "--tiers",
        ",".join(str(t) for t in chain),
        "--json",
        "--timeout",
        str(timeout_seconds),
    ]
