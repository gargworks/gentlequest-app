#!/usr/bin/env python3
"""Weekly Trajectory Report — Family delegation health dashboard.

Reads git log, GitHub PRs, and test results to produce a snapshot of
how the delegation system is performing. Designed to be run weekly
by heartbeat or manually by father.

Usage:
    python .brain/tools/trajectory_report.py           # human-readable
    python .brain/tools/trajectory_report.py --json    # machine-readable
    python .brain/tools/trajectory_report.py --save    # write to .brain/reports/
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

BRAIN_DIR = Path(__file__).resolve().parent.parent  # .brain/
REPO_ROOT = BRAIN_DIR.parent
REPORT_DIR = BRAIN_DIR / "reports"
DELEGATION_LOG = BRAIN_DIR / "delegation_log.jsonl"


# ── Helpers ──────────────────────────────────────────────────

def _run(cmd: list[str], cwd=None) -> str:
    """Run a command and return stdout, empty string on failure."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=cwd or REPO_ROOT)
        return r.stdout.strip()
    except Exception:
        return ""


def _git_log_since(days: int = 7) -> list[dict]:
    """Parse git log from the last N days."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    raw = _run(["git", "log", f"--since={since}", "--pretty=format:%H|%s|%an|%aI", "--no-merges"])
    if not raw:
        return []
    commits = []
    for line in raw.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "sha": parts[0][:8],
                "message": parts[1],
                "author": parts[2],
                "date": parts[3],
            })
    return commits


def _count_tests() -> int:
    """Count test functions across the test suite."""
    test_dir = REPO_ROOT / "mcp-server-nucleus" / "tests"
    if not test_dir.exists():
        return 0
    count = 0
    for f in test_dir.glob("test_*.py"):
        try:
            for line in f.read_text().splitlines():
                if line.strip().startswith("def test_"):
                    count += 1
        except Exception:
            pass
    return count


def _get_open_prs() -> list[dict]:
    """Fetch open PRs from GitHub via gh CLI."""
    raw = _run(["gh", "pr", "list", "--state", "open", "--json", "number,title,createdAt,headRefName"])
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def _get_merged_prs_since(days: int = 7) -> list[dict]:
    """Fetch recently merged PRs."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    raw = _run(["gh", "pr", "list", "--state", "merged", "--json", "number,title,mergedAt",
                 "--search", f"merged:>={since}"])
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def _read_delegation_log() -> list[dict]:
    """Read delegation_log.jsonl if it exists."""
    if not DELEGATION_LOG.exists():
        return []
    entries = []
    try:
        for line in DELEGATION_LOG.read_text().splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    except Exception:
        pass
    return entries


def _ci_status() -> str:
    """Check latest CI run status."""
    raw = _run(["gh", "run", "list", "--limit", "3", "--json", "status,conclusion,name,createdAt"])
    if not raw:
        return "unknown"
    try:
        runs = json.loads(raw)
        if runs:
            latest = runs[0]
            return f"{latest.get('conclusion', latest.get('status', 'unknown'))}"
    except Exception:
        pass
    return "unknown"


# ── Report Generation ────────────────────────────────────────

def generate_report(days: int = 7) -> dict:
    """Build the full trajectory report."""
    commits = _git_log_since(days)
    open_prs = _get_open_prs()
    merged_prs = _get_merged_prs_since(days)
    delegation_entries = _read_delegation_log()
    test_count = _count_tests()
    ci = _ci_status()

    # Categorize commits
    feat_count = sum(1 for c in commits if c["message"].startswith("feat"))
    fix_count = sum(1 for c in commits if c["message"].startswith("fix"))
    test_commits = sum(1 for c in commits if c["message"].startswith("test"))
    docs_count = sum(1 for c in commits if c["message"].startswith("doc"))

    # Delegation health
    successful_cycles = sum(1 for e in delegation_entries if e.get("outcome") == "success")
    total_cycles = len(delegation_entries)
    trips = sum(1 for e in delegation_entries if e.get("outcome") == "trip")

    # Family PRs (branches starting with family/)
    family_prs_open = [p for p in open_prs if p.get("headRefName", "").startswith("family/")]
    family_prs_merged = [p for p in merged_prs if True]  # all merged PRs count

    report = {
        "generated_at": datetime.now().isoformat(),
        "period_days": days,
        "summary": {
            "commits": len(commits),
            "features": feat_count,
            "fixes": fix_count,
            "tests_added": test_commits,
            "docs": docs_count,
        },
        "tests": {
            "total_test_functions": test_count,
        },
        "ci": {
            "latest_status": ci,
        },
        "prs": {
            "open": len(open_prs),
            "merged_this_period": len(merged_prs),
            "family_open": [{"number": p["number"], "title": p["title"]} for p in family_prs_open],
        },
        "delegation": {
            "total_cycles": total_cycles,
            "successful": successful_cycles,
            "trips": trips,
            "success_rate": f"{(successful_cycles / total_cycles * 100):.0f}%" if total_cycles > 0 else "N/A",
        },
        "recent_commits": commits[:10],
    }
    return report


def format_human(report: dict) -> str:
    """Render report as readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("  NUCLEUS WEEKLY TRAJECTORY REPORT")
    lines.append(f"  Period: last {report['period_days']} days")
    lines.append(f"  Generated: {report['generated_at'][:19]}")
    lines.append("=" * 60)

    s = report["summary"]
    lines.append("")
    lines.append(f"  Commits:  {s['commits']}  (feat: {s['features']}, fix: {s['fixes']}, test: {s['tests_added']}, docs: {s['docs']})")
    lines.append(f"  Tests:    {report['tests']['total_test_functions']} test functions in suite")
    lines.append(f"  CI:       {report['ci']['latest_status']}")

    p = report["prs"]
    lines.append(f"  PRs:      {p['open']} open, {p['merged_this_period']} merged this period")
    if p["family_open"]:
        for pr in p["family_open"]:
            lines.append(f"            #{pr['number']} {pr['title']}")

    d = report["delegation"]
    lines.append("")
    lines.append("  DELEGATION HEALTH")
    lines.append(f"  Cycles:       {d['total_cycles']} total, {d['successful']} successful, {d['trips']} trips")
    lines.append(f"  Success rate: {d['success_rate']}")

    if report["recent_commits"]:
        lines.append("")
        lines.append("  RECENT COMMITS")
        for c in report["recent_commits"][:7]:
            lines.append(f"    {c['sha']}  {c['message'][:60]}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    days = 7

    # Parse --days=N
    for a in args:
        if a.startswith("--days="):
            try:
                days = int(a.split("=", 1)[1])
            except ValueError:
                pass

    report = generate_report(days)

    if "--json" in args:
        print(json.dumps(report, indent=2))
    else:
        print(format_human(report))

    if "--save" in args:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = REPORT_DIR / f"trajectory_{ts}.json"
        out.write_text(json.dumps(report, indent=2))
        print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
