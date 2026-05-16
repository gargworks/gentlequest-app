#!/usr/bin/env python3
"""flywheel_capture_extractor — mine Claude Code session captures for failures.

The Layer 0 conversation capture daemon writes one JSONL per session under
`~/.claude/projects/<project>/<session-uuid>.jsonl`. Each line is a turn —
either a user message, an assistant message, or a tool call.

This script walks those JSONLs, looks for two failure signals:

  1. **Tool-call errors.** A `tool_use_result` whose `is_error` is true (or
     whose content includes an error string).
  2. **User corrections.** A user message immediately after an assistant turn
     containing words like "no", "stop", "don't", "wrong", "instead".

Each detected failure becomes a seed DPO pair appended to the brain's
`unified_dpo_pending.jsonl`:

  - `prompt`     = the preceding context (last user message + assistant
                   action that triggered the failure)
  - `rejected`   = the failing tool result OR the assistant message the user
                   corrected
  - `chosen`     = filled in by `flywheel_curriculum.py` later, when the
                   matching step survives verification.

A processed-files ledger at `<brain>/flywheel/capture_extractor_ledger.jsonl`
prevents re-processing the same session twice.

Usage:
    python scripts/flywheel_capture_extractor.py                # all sessions
    python scripts/flywheel_capture_extractor.py --limit 10     # first 10 only
    python scripts/flywheel_capture_extractor.py --dry-run      # don't write
    python scripts/flywheel_capture_extractor.py --captures DIR # custom path
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


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
    if not ledger_path.exists():
        return set()
    seen: set = set()
    try:
        with open(ledger_path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    seen.add(entry.get("session_id"))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return seen


def _append_ledger(ledger_path: Path, session_id: str, pair_count: int) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger_path, "a") as f:
        f.write(json.dumps({
            "session_id": session_id,
            "pairs": pair_count,
            "processed_at": _now_iso(),
        }) + "\n")


def _append_pairs(out_path: Path, pairs: List[Dict[str, Any]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "a") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
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

    seen = _load_ledger(ledger_path)
    total_sessions = 0
    total_pairs = 0
    skipped = 0

    for session_file in _iter_session_files(captures, limit=args.limit):
        session_id = session_file.stem
        if session_id in seen:
            skipped += 1
            continue
        total_sessions += 1
        turns = _read_turns(session_file)
        if not turns:
            continue
        pairs = _extract_pairs(turns, session_id)
        if pairs:
            total_pairs += len(pairs)
            if not args.dry_run:
                _append_pairs(out_path, pairs)
        if not args.dry_run:
            _append_ledger(ledger_path, session_id, len(pairs))

    summary = {
        "captures_root": str(captures),
        "brain_path": str(brain),
        "sessions_processed": total_sessions,
        "sessions_skipped": skipped,
        "pairs_extracted": total_pairs,
        "dry_run": args.dry_run,
        "out": str(out_path),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
