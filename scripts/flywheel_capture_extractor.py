#!/usr/bin/env python3
"""flywheel_capture_extractor — mine Claude Code session captures.

The Layer 0 conversation capture daemon writes one JSONL per session under
`~/.claude/projects/<project>/<session-uuid>.jsonl`. Each line is a turn —
either a user message, an assistant message, or a tool call.

Two modes (select via --kind):

  correction (default, historical behavior):
    Scans for tool-call errors and user corrections, emits DPO seed pairs
    with kind=tool_error / kind=user_correction.

  audit (Wave 10):
    Scans for audit-plans subagent runs — sessions whose first user turn
    contains the "## Plan Audit: " marker from TB's STRUCTURED_AUDIT_TEMPLATE.
    Joins verdict from .brain/audit/results.json (session_id primary,
    plan_name + audited_at proximity fallback). Emits kind=audit_dpo pairs
    with the subagent's reasoning chain as `chosen`.

All pairs share the same top-level envelope (source, session_id, quality,
prompt, rejected, chosen, at, kind) so downstream curriculum tooling
doesn't need to branch on kind.

Output: `<brain>/training/exports/unified_dpo_pending.jsonl`.
Ledger: `<brain>/flywheel/capture_extractor_ledger.jsonl` (per-kind,
per-session idempotency; legacy entries without kind treated as correction).

Usage:
    python scripts/flywheel_capture_extractor.py                    # correction
    python scripts/flywheel_capture_extractor.py --kind audit       # audit
    python scripts/flywheel_capture_extractor.py --limit 10         # first 10
    python scripts/flywheel_capture_extractor.py --dry-run          # count only
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


_DEFAULT_CAPTURES = Path.home() / ".claude" / "projects"

_CORRECTION_MARKERS = (
    "no, ",
    "no don't",
    "don't ",
    "stop ",
    "wrong",
    "that's wrong",
    "that's not",
    "instead",
    "actually",
    "no — ",
)

# Wave 10 audit mode
_AUDIT_MARKER = "## Plan Audit: "
_PROXIMITY_WINDOW_S = 600  # ±10 minutes for audited_at fallback join
_REASONING_CAP = 1500      # matches existing pair truncation convention


def _looks_like_audit_prompt(text: str) -> bool:
    """True iff text is a TB-spawned audit-subagent first user turn.

    Two genuine shapes observed in the corpus:
      1. starts with ``## Plan Audit: <title>\\nSource: <file>``
      2. starts with ``## Task: Audit: <title>\\n\\n## Plan Audit: …``
    Sparring sessions begin with ``Score Third Brother's …`` and QUOTE the
    full template later as context — they match the naive substring/line-
    start tests but must NOT produce audit_dpo pairs. Filter by requiring
    the text to begin with a markdown heading (``##``), which excludes
    every sparring prompt observed in 979-session corpus.
    """
    stripped = text.lstrip()
    if not stripped.startswith("## "):
        return False
    if stripped.startswith(_AUDIT_MARKER):
        return True
    return f"\n{_AUDIT_MARKER}" in text


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iter_session_files(root: Path, limit: Optional[int] = None) -> Iterable[Path]:
    """Yield session JSONL files under root, newest first."""
    if not root.exists():
        return
    files: List[Path] = []
    for p in root.rglob("*.jsonl"):
        try:
            files.append(p)
        except OSError:
            continue
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    if limit:
        files = files[:limit]
    for f in files:
        yield f


def _read_turns(path: Path) -> List[Dict[str, Any]]:
    """Parse a session JSONL into a list of turn dicts. Skips bad lines."""
    out: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except (OSError, UnicodeDecodeError):
        return []
    return out


def _looks_like_correction(text: str) -> bool:
    if not text:
        return False
    low = text.strip().lower()
    return any(low.startswith(m) or m in low[:80] for m in _CORRECTION_MARKERS)


def _extract_text(message: Any) -> str:
    """Pull plain text out of a turn. Schemas vary across capture versions."""
    if isinstance(message, str):
        return message
    if isinstance(message, dict):
        # Common shapes:
        # {"role": "user", "content": "..."}
        # {"role": "assistant", "content": [{"type": "text", "text": "..."}]}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
            return "\n".join(parts)
    return ""


def _is_tool_error(turn: Dict[str, Any]) -> bool:
    msg = turn.get("message") or turn
    content = msg.get("content") if isinstance(msg, dict) else None
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                if item.get("is_error"):
                    return True
                txt = item.get("content")
                if isinstance(txt, str) and ("error" in txt.lower() or "traceback" in txt.lower()):
                    return True
    return False


def _extract_pairs(turns: List[Dict[str, Any]], session_id: str) -> List[Dict[str, Any]]:
    """Walk turns and yield DPO seed pairs for failures we recognize."""
    pairs: List[Dict[str, Any]] = []
    prev_text = ""
    prev_role = ""

    for i, turn in enumerate(turns):
        msg = turn.get("message", turn)
        role = msg.get("role", turn.get("type", "")) if isinstance(msg, dict) else ""
        text = _extract_text(msg)

        # Tool-call errors are the cleanest failure signal.
        if _is_tool_error(turn) and prev_text:
            pairs.append({
                "source": "capture_extractor",
                "session_id": session_id,
                "quality": "pending",
                "prompt": f"Step: capture_tool_call\nPhase: layer0\nContext: {prev_text[:500]}",
                "rejected": text[:1500] or "(tool error)",
                "chosen": "",
                "at": _now_iso(),
                "kind": "tool_error",
            })

        # User corrections following an assistant turn.
        if role == "user" and prev_role == "assistant" and _looks_like_correction(text):
            # The next assistant turn is the corrected response (if any).
            chosen = ""
            if i + 1 < len(turns):
                nxt_msg = turns[i + 1].get("message", turns[i + 1])
                if isinstance(nxt_msg, dict) and nxt_msg.get("role") == "assistant":
                    chosen = _extract_text(nxt_msg)[:1500]
            pairs.append({
                "source": "capture_extractor",
                "session_id": session_id,
                "quality": "pending" if not chosen else "ready",
                "prompt": f"Step: capture_user_correction\nPhase: layer0\nUser said: {text[:300]}",
                "rejected": prev_text[:1500] or "(prior assistant turn)",
                "chosen": chosen,
                "at": _now_iso(),
                "kind": "user_correction",
            })

        prev_text = text
        prev_role = role

    return pairs


def _load_ledger(ledger_path: Path) -> set:
    """Return seen (kind, session_id) tuples. Legacy entries without kind
    are interpreted as kind=correction (R21 migration default)."""
    if not ledger_path.exists():
        return set()
    seen: set = set()
    try:
        with open(ledger_path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sid = entry.get("session_id")
                if not sid:
                    continue
                kind = entry.get("kind", "correction")
                seen.add((kind, sid))
    except OSError:
        pass
    return seen


def _append_ledger(ledger_path: Path, kind: str, session_id: str,
                   pair_count: int) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger_path, "a") as f:
        f.write(json.dumps({
            "kind": kind,
            "session_id": session_id,
            "pairs": pair_count,
            "processed_at": _now_iso(),
        }) + "\n")


def _append_pairs(out_path: Path, pairs: List[Dict[str, Any]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "a") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")


# ═══════════════════════════════════════════════════════════════
# Wave 10: audit mode — mine STRUCTURED_AUDIT_TEMPLATE subagent runs
# ═══════════════════════════════════════════════════════════════
#
# Per-session flow:
#
#   _first_user_turn(path)          ← fast-path: read until first "user"
#          │                          turn only; skip non-audit sessions
#          │                          without full _read_turns parse (R20)
#          ▼
#   marker "## Plan Audit: " present?
#          │ no  → skip_reason=no_marker
#          │ yes
#          ▼
#   _extract_plan_name(prompt_text)  ← parse "Source: <filename>" line
#          │
#          ▼
#   _join_verdict(plan_name, sid, ts, results)
#       1° sid exact match in results.json
#       2° plan_name match AND audited_at within ±10min of first-turn ts
#          ≥2 candidates → skip_reason=ambiguous_verdict
#          │
#          ▼
#   _extract_reasoning(turns)        ← concat type:text across ALL
#          │                          assistant turns, truncate [:1500]
#          │                          (R18)
#          │ empty → skip_reason=no_reasoning
#          ▼
#   emit pair with same envelope as correction pairs (R17) +
#   audit-specific sidecars (plan_name, verdict, audited_at)


def _first_user_turn(path: Path) -> Optional[Dict[str, Any]]:
    """Stream lines until the first user turn; return the parsed dict.

    For audit-mode filtering: avoids full _read_turns parse on the ~99%
    of sessions that aren't audit subagents (R20 fast-path).
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    turn = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = turn.get("message", turn)
                role = ""
                if isinstance(msg, dict):
                    role = msg.get("role", turn.get("type", ""))
                if role == "user":
                    return turn
    except (OSError, UnicodeDecodeError):
        return None
    return None


def _parse_iso(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _load_audit_results(results_path: Path) -> Dict[str, Any]:
    """Read .brain/audit/results.json. Returns {} on missing/malformed."""
    try:
        raw = results_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _extract_plan_name(prompt_text: str) -> str:
    """Extract plan filename from the 'Source: <filename>' line that
    follows the audit marker in STRUCTURED_AUDIT_TEMPLATE."""
    lines = prompt_text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(_AUDIT_MARKER):
            for j in range(i + 1, min(i + 5, len(lines))):
                src = lines[j].strip()
                if src.startswith("Source:"):
                    return src[len("Source:"):].strip()
            return ""
    return ""


def _extract_reasoning(turns: List[Dict[str, Any]]) -> str:
    """Concat type:text from all assistant turns; truncate to cap."""
    parts: List[str] = []
    for turn in turns:
        msg = turn.get("message", turn)
        role = ""
        if isinstance(msg, dict):
            role = msg.get("role", turn.get("type", ""))
        if role != "assistant":
            continue
        text = _extract_text(msg)
        if text:
            parts.append(text)
    return "\n".join(parts)[:_REASONING_CAP]


def _join_verdict(
    plan_name: str,
    session_id: str,
    first_turn_ts: Optional[datetime],
    results: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Resolve results.json entry via session_id primary, proximity fallback.

    Returns (entry, skip_reason). Exactly one is None.
    """
    # Primary: session_id match. Writer truncates to 16 chars
    # (``session_id[:16]``) in third_brother_driver._record_audit_result
    # → match on prefix, not equality. Skip empty entry sids so they
    # don't spuriously "match" the empty-sid of other sessions.
    if session_id:
        for entry in results.values():
            if not isinstance(entry, dict):
                continue
            entry_sid = entry.get("session_id", "")
            if entry_sid and session_id.startswith(entry_sid):
                return entry, None

    # Fallback: plan_name + audited_at proximity window.
    if first_turn_ts is None:
        return None, "no_timestamp_for_fallback"

    candidates: List[Dict[str, Any]] = []
    for name, entry in results.items():
        if not isinstance(entry, dict):
            continue
        # Prefer explicit entry["plan_name"] when present (future-proofs
        # against schema expansion where results may carry multiple entries
        # per plan); fall back to dict key (current writer semantics).
        entry_plan_name = entry.get("plan_name", name)
        if entry_plan_name != plan_name:
            continue
        audited_at = _parse_iso(entry.get("audited_at"))
        if audited_at is None:
            continue
        delta = abs((first_turn_ts - audited_at).total_seconds())
        if delta <= _PROXIMITY_WINDOW_S:
            candidates.append(entry)

    if not candidates:
        return None, "no_verdict_found"
    if len(candidates) >= 2:
        return None, "ambiguous_verdict"
    return candidates[0], None


def _extract_audit_pairs(
    turns: List[Dict[str, Any]],
    session_id: str,
    results: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Extract one audit_dpo pair from a subagent session. See diagram above.

    Returns (pairs, skip_reason). skip_reason is None on success; otherwise
    no_user_turn / no_marker / no_plan_name / no_verdict_found /
    ambiguous_verdict / no_timestamp_for_fallback / no_reasoning.
    """
    first_user_idx = -1
    for i, turn in enumerate(turns):
        msg = turn.get("message", turn)
        role = ""
        if isinstance(msg, dict):
            role = msg.get("role", turn.get("type", ""))
        if role == "user":
            first_user_idx = i
            break
    if first_user_idx < 0:
        return [], "no_user_turn"

    first_turn = turns[first_user_idx]
    first_msg = first_turn.get("message", first_turn)
    prompt_text = _extract_text(first_msg)
    if not _looks_like_audit_prompt(prompt_text):
        return [], "no_marker"

    plan_name = _extract_plan_name(prompt_text)
    if not plan_name:
        return [], "no_plan_name"

    first_turn_ts = _parse_iso(first_turn.get("timestamp"))
    entry, skip_reason = _join_verdict(plan_name, session_id, first_turn_ts, results)
    if entry is None:
        return [], skip_reason

    reasoning = _extract_reasoning(turns[first_user_idx + 1:])
    if not reasoning:
        return [], "no_reasoning"

    verdict = entry.get("verdict", "")
    audited_at = entry.get("audited_at", "")
    chosen = f"{reasoning}\n\nVerdict: {verdict}"[:_REASONING_CAP]

    pair = {
        "source": "capture_extractor",
        "session_id": session_id,
        "quality": "ready",
        "prompt": prompt_text[:_REASONING_CAP],
        "rejected": "",
        "chosen": chosen,
        "at": _now_iso(),
        "kind": "audit_dpo",
        "plan_name": plan_name,
        "verdict": verdict,
        "audited_at": audited_at,
    }
    return [pair], None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--kind", choices=("correction", "audit"),
                        default="correction",
                        help="extraction mode (default: correction)")
    parser.add_argument("--captures", default=str(_DEFAULT_CAPTURES),
                        help="root directory holding session JSONLs")
    parser.add_argument("--brain-path", default=os.environ.get("NUCLEUS_BRAIN_PATH"),
                        help="brain path (default: $NUCLEUS_BRAIN_PATH or ./.brain)")
    parser.add_argument("--limit", type=int, default=None,
                        help="process only the N most-recent sessions")
    parser.add_argument("--dry-run", action="store_true",
                        help="don't write pairs or ledger; just report counts")
    args = parser.parse_args()

    captures = Path(args.captures)
    brain = Path(args.brain_path) if args.brain_path else Path.cwd() / ".brain"
    out_path = brain / "training" / "exports" / "unified_dpo_pending.jsonl"
    ledger_path = brain / "flywheel" / "capture_extractor_ledger.jsonl"
    results_path = brain / "audit" / "results.json"

    seen = _load_ledger(ledger_path)
    results: Dict[str, Any] = (
        _load_audit_results(results_path) if args.kind == "audit" else {}
    )

    total_sessions = 0
    total_pairs = 0
    skipped = 0
    skip_reasons: Dict[str, int] = {}

    for session_file in _iter_session_files(captures, limit=args.limit):
        session_id = session_file.stem
        if (args.kind, session_id) in seen:
            skipped += 1
            continue

        if args.kind == "audit":
            # Fast-path: only process TB-spawned audit-subagent sessions.
            # Genuine subagent invocations place `## Plan Audit: ` at the
            # start of a line (either line 1, or right after TB's
            # `## Task: Audit: …` wrapper). Sparring sessions embed the
            # marker mid-line and must be skipped without paying full
            # _read_turns IO cost. (R20 + live-fire tightening.)
            first = _first_user_turn(session_file)
            if first is None:
                continue
            first_msg = first.get("message", first)
            if not _looks_like_audit_prompt(_extract_text(first_msg)):
                continue

        total_sessions += 1
        turns = _read_turns(session_file)
        if not turns:
            continue

        if args.kind == "audit":
            pairs, skip_reason = _extract_audit_pairs(turns, session_id, results)
            if skip_reason:
                skip_reasons[skip_reason] = skip_reasons.get(skip_reason, 0) + 1
        else:
            pairs = _extract_pairs(turns, session_id)

        if pairs:
            total_pairs += len(pairs)
            if not args.dry_run:
                _append_pairs(out_path, pairs)
        if not args.dry_run:
            _append_ledger(ledger_path, args.kind, session_id, len(pairs))

    summary = {
        "kind": args.kind,
        "captures_root": str(captures),
        "brain_path": str(brain),
        "sessions_processed": total_sessions,
        "sessions_skipped": skipped,
        "pairs_extracted": total_pairs,
        "dry_run": args.dry_run,
        "out": str(out_path),
    }
    if skip_reasons:
        summary["skip_reasons"] = skip_reasons
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
