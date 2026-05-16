#!/usr/bin/env python3
"""Deferred-items ledger — auto-append DEFERRED ship-report items to .brain/plans/deferred_work.md

Slice Obs-1 observability substrate. Scans relay ship-reports for DEFERRED
markers (ship-report tag + summary regex), idempotently appends to a markdown
table so deferred work stops rotting in old ship-report bodies.

Schema:
    | timestamp | origin_relay_id | deferred_item | reason | re_eval_trigger |

Idempotence: (origin_relay_id + deferred_item) hash dedup. Re-scans never
re-append existing rows.

Usage:
    python3 scripts/deferred_ledger.py            # scan + append new
    python3 scripts/deferred_ledger.py --dry-run  # preview
    python3 scripts/deferred_ledger.py --seed     # include initial seed rows
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO_ROOT / ".brain" / "plans" / "deferred_work.md"
BUCKETS = ("cowork", "claude_code", "claude_code_main", "claude_code_peer")
HEADER = (
    "# Deferred Work Ledger\n\n"
    "Append-only record of DEFERRED items surfaced in ship-report relays.\n"
    "Auto-populated by `scripts/deferred_ledger.py`. Re-run the scanner to update.\n\n"
    "| timestamp | origin_relay_id | deferred_item | reason | re_eval_trigger |\n"
    "|-----------|-----------------|---------------|--------|------------------|\n"
)
DEFERRED_RE = re.compile(r"DEFERRED\s*[:\-]\s*(.+?)(?:\.\s|\.$|$)", re.IGNORECASE)


def _row_hash(relay_id: str, item: str) -> str:
    return hashlib.sha256(f"{relay_id}|{item.strip()}".encode()).hexdigest()[:12]


def _existing_hashes(ledger_text: str) -> set:
    seen = set()
    for line in ledger_text.splitlines():
        if not line.startswith("| ") or "origin_relay_id" in line or "-----" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 3:
            seen.add(_row_hash(cells[1], cells[2]))
    return seen


def _parse_relay(path: Path) -> Optional[Dict[str, Any]]:
    try:
        env = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    body = env.get("body", "")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            body = {"summary": body, "tags": []}
    return {"env": env, "body": body}


def scan_relays(brain_root: Optional[Path] = None) -> List[Tuple[str, str, str, str, str]]:
    root = brain_root or (REPO_ROOT / ".brain" / "relay")
    rows: List[Tuple[str, str, str, str, str]] = []
    for bucket in BUCKETS:
        bpath = root / bucket
        if not bpath.exists():
            continue
        for f in sorted(bpath.glob("*.json")):
            parsed = _parse_relay(f)
            if not parsed:
                continue
            body = parsed["body"]
            summary = body.get("summary", "") if isinstance(body, dict) else ""
            tags = body.get("tags", []) if isinstance(body, dict) else []
            if "ship-report" not in tags and "DEFERRED" not in summary.upper():
                continue
            for m in DEFERRED_RE.finditer(summary):
                item = m.group(1).strip()[:120]
                if not item:
                    continue
                rows.append((
                    parsed["env"].get("created_at", "")[:19],
                    parsed["env"].get("id", ""),
                    item,
                    "",
                    "",
                ))
    return rows


def seed_rows() -> List[Tuple[str, str, str, str, str]]:
    base_id = "relay_20260420_115500_a3f4b821"
    ts = "2026-04-20T11:55:00"
    trigger_agents = "founder decision on AGENTS.md guardrail scope"
    trigger_obs2 = "post-Obs-2 scoping"
    return [
        (ts, base_id, "morning-brief SessionStart hook (commit 189c8737)",
         "scripts/relay_inbox_hook.py evolved since original commit; integration-design pass needed",
         trigger_obs2),
        (ts, base_id, "surfaced_at relay stamp (commit 45f19fcb)",
         "coupled to morning-brief revival; same integration scope",
         trigger_obs2),
        (ts, base_id, "CLAUDE.md operating-posture content (commit 5043671b)",
         "CLAUDE.md is now pointer to AGENTS.md; content needs adaptation not drop",
         trigger_agents),
        (ts, base_id, "CLAUDE.md temporal-narrative content (commit 366a25bc)",
         "content moved to per-Claude feedback memories; AGENTS.md lift decision pending",
         trigger_agents),
    ]


def append_rows(rows: List[Tuple[str, str, str, str, str]], dry_run: bool = False) -> int:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = LEDGER_PATH.read_text() if LEDGER_PATH.exists() else HEADER
    seen = _existing_hashes(existing)
    new_lines = []
    for ts, rid, item, reason, trigger in rows:
        h = _row_hash(rid, item)
        if h in seen:
            continue
        seen.add(h)
        new_lines.append(f"| {ts} | {rid} | {item} | {reason} | {trigger} |")
    if not new_lines:
        return 0
    if dry_run:
        for line in new_lines:
            print(line)
        return len(new_lines)
    updated = existing if existing.endswith("\n") else existing + "\n"
    if "origin_relay_id" not in updated:
        updated = HEADER
    updated += "\n".join(new_lines) + "\n"
    LEDGER_PATH.write_text(updated)
    return len(new_lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--seed", action="store_true", help="Include initial seed rows")
    args = p.parse_args()
    rows = scan_relays()
    if args.seed:
        rows = seed_rows() + rows
    n = append_rows(rows, dry_run=args.dry_run)
    verb = "would-append" if args.dry_run else "appended"
    rel = LEDGER_PATH.relative_to(REPO_ROOT)
    print(f"{verb} {n} deferred-item row(s) to {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
