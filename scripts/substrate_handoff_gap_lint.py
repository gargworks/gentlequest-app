#!/usr/bin/env python3
"""Substrate-handoff-gap lint — flag relays that cite paths the recipient can't see.

Slice Obs-1 extension. When a sender (typically Cowork, with auto-memory invisible
to CC agents) fires a relay that references `.auto-memory/foo.md` or
`scripts/bar.py` and that path doesn't exist in the recipient's repo, the
recipient is asked to act on substrate they cannot grep. That's the gap that
caused main's Item-A deferral on the 7-blocker batch — the backlog file lived
in cowork's auto-memory, never in the repo.

Heuristic: regex-extract path-shaped tokens from relay body, filter to ones
that look like in-repo references (suffixes .md/.py/.sh/.json/.lua/.yaml; or
prefixes `scripts/`, `.brain/`, `.auto-memory/`, `mcp-server-nucleus/`), then
check `repo_root / path` exists. Recipients are inferred from the bucket name
(`.brain/relay/<recipient>/`); we treat all CC buckets as in-repo readers.

Output: JSON to stdout, one record per (relay, missing_path). Silent if clean.
Exit 0 always (advisory probe; non-zero would gate every brief hook).

Usage:
    python3 scripts/substrate_handoff_gap_lint.py [--days 14] [--brain-path PATH]
        [--repo-root PATH] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

CC_BUCKETS = ("claude_code", "claude_code_main", "claude_code_peer")
PATH_RE = re.compile(
    r"(?<![\w/.-])"
    r"(?:\.?[A-Za-z0-9_-]+/)+"
    r"[A-Za-z0-9_.-]+\.(?:md|py|sh|json|lua|yaml|yml|toml|txt)"
)
SUSPICIOUS_PREFIXES = (
    "scripts/", ".brain/", ".auto-memory/",
    "mcp-server-nucleus/", "docs/", "tests/",
)


def resolve_brain_path(cli_value: str | None) -> Path:
    env = os.environ.get("NUCLEUS_BRAIN_PATH")
    if env:
        return Path(env)
    if cli_value:
        return Path(cli_value)
    return Path("/Users/lokeshgarg/ai-mvp-backend/.brain")


def _extract_paths(text: str) -> set[str]:
    found = set()
    for m in PATH_RE.finditer(text):
        token = m.group(0)
        if token.startswith(SUSPICIOUS_PREFIXES):
            found.add(token)
            continue
        components = token.split("/")
        for prefix in SUSPICIOUS_PREFIXES:
            if prefix.rstrip("/") in components:
                found.add(token)
                break
    return found


def _scan_relay(path: Path, repo_root: Path) -> List[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    body = data.get("body", "")
    if isinstance(body, dict):
        body_text = json.dumps(body)
    else:
        body_text = str(body)
    subject = data.get("subject", "")
    haystack = f"{subject}\n{body_text}"
    candidates = _extract_paths(haystack)
    if not candidates:
        return []
    gaps = []
    for raw in sorted(candidates):
        rel = raw.split("#", 1)[0].split("?", 1)[0].rstrip(".,);")
        if not rel or "://" in rel:
            continue
        if (repo_root / rel).exists():
            continue
        gaps.append({
            "relay_id": data.get("id"),
            "from": data.get("from"),
            "to": data.get("to"),
            "subject": subject,
            "missing_path": rel,
        })
    return gaps


def find_handoff_gaps(brain_path: Path, repo_root: Path,
                      days: int = 14) -> List[Dict[str, Any]]:
    relay_root = brain_path / "relay"
    if not relay_root.is_dir():
        return []
    cutoff = time.time() - days * 86400
    gaps: List[Dict[str, Any]] = []
    for bucket in CC_BUCKETS:
        bucket_dir = relay_root / bucket
        if not bucket_dir.is_dir():
            continue
        for relay_path in bucket_dir.glob("*.json"):
            try:
                if relay_path.stat().st_mtime < cutoff:
                    continue
            except OSError:
                continue
            gaps.extend(_scan_relay(relay_path, repo_root))
    return gaps


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--brain-path", default=None)
    ap.add_argument("--repo-root", default="/Users/lokeshgarg/ai-mvp-backend")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    brain = resolve_brain_path(args.brain_path)
    repo = Path(args.repo_root)
    gaps = find_handoff_gaps(brain, repo, days=args.days)
    if args.json:
        print(json.dumps({"gaps": gaps, "count": len(gaps)}, indent=2))
        return 0
    for g in gaps:
        print(f"handoff-gap: {g['from']}→{g['to']} {g['relay_id']} missing={g['missing_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
