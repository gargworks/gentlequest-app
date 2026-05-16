#!/usr/bin/env python3
"""Stale-work lint — surface open PRs older than N days + unmerged branches without PRs.

Slice Obs-1 observability substrate. Two checks, structured JSON output,
silent if clean. Caller (brief hook, daily digest, CLI) picks the surface.

    (a) Stale PRs: gh pr list --author @me --state open --search updated:<cutoff
    (b) Unmerged branches: git for-each-ref refs/heads cross-referenced against
        gh pr list. Surface branches with commits NOT on origin/main AND no
        associated open PR (branch with PR skipped — covered by check a).

Usage:
    python3 scripts/stale_work_lint.py                    # human one-line output
    python3 scripts/stale_work_lint.py --days 7
    python3 scripts/stale_work_lint.py --json             # structured JSON
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


def _run(cmd: List[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return r.stdout if r.returncode == 0 else ""


def find_stale_prs(days: int = 3) -> List[Dict[str, Any]]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    out = _run([
        "gh", "pr", "list", "--author", "@me", "--state", "open",
        "--search", f"updated:<{cutoff}",
        "--json", "number,title,baseRefName,headRefName,updatedAt,url",
    ])
    if not out.strip():
        return []
    try:
        prs = json.loads(out)
    except json.JSONDecodeError:
        return []
    now = datetime.now(timezone.utc)
    stale = []
    for pr in prs:
        updated = datetime.fromisoformat(pr["updatedAt"].replace("Z", "+00:00"))
        stale.append({
            "number": pr["number"],
            "title": pr["title"],
            "base": pr["baseRefName"],
            "head": pr["headRefName"],
            "age_days": (now - updated).days,
            "url": pr["url"],
        })
    return stale


def _is_merged_upstream(sha: str) -> bool:
    """True if sha is reachable from any upstream/* ref. Quiet on missing remote."""
    out = _run(["git", "branch", "-r", "--contains", sha])
    if not out.strip():
        return False
    return any(line.strip().startswith("upstream/") for line in out.splitlines())


def find_unmerged_branches() -> List[Dict[str, Any]]:
    refs_out = _run(["git", "for-each-ref", "refs/heads",
                     "--format", "%(refname:short)|%(objectname)|%(committerdate:iso)"])
    if not refs_out.strip():
        return []
    pr_heads_out = _run([
        "gh", "pr", "list", "--author", "@me", "--state", "open",
        "--json", "headRefName", "--jq", ".[].headRefName",
    ])
    pr_heads = {line.strip() for line in pr_heads_out.splitlines() if line.strip()}
    unmerged = []
    for line in refs_out.splitlines():
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        branch, sha, committer_date = parts
        if branch in ("main", "master") or branch in pr_heads:
            continue
        ahead_out = _run(["git", "rev-list", "--count", f"origin/main..{sha}"])
        try:
            ahead = int(ahead_out.strip() or "0")
        except ValueError:
            ahead = 0
        if ahead == 0:
            continue
        topology = "topology-split" if _is_merged_upstream(sha) else "silent-lazy"
        unmerged.append({
            "branch": branch,
            "ahead_count": ahead,
            "last_commit_date": committer_date,
            "topology_type": topology,
        })
    return unmerged


def check_stale_work(days: int = 3) -> Dict[str, Any]:
    return {"stale_prs": find_stale_prs(days), "unmerged_branches": find_unmerged_branches()}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--days", type=int, default=3)
    p.add_argument("--json", action="store_true", help="Emit structured JSON")
    args = p.parse_args()
    report = check_stale_work(args.days)
    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    if not report["stale_prs"] and not report["unmerged_branches"]:
        return 0
    for pr in report["stale_prs"]:
        print(f"stale-pr: #{pr['number']} ({pr['age_days']}d) {pr['title']} {pr['url']}")
    for br in report["unmerged_branches"]:
        label = br.get("topology_type", "silent-lazy")
        print(f"{label}: {br['branch']} (+{br['ahead_count']} commits, last {br['last_commit_date']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
