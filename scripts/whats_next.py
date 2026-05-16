#!/usr/bin/env python3
"""'What's next?' helper — rule-based ranking of next actions from substrate.

Per .brain/research/2026-04-28_tier_architecture/09_cloud_substrate_and_router_strategy.md
§4.5 + §4.7 — beta-user retention lever ("I don't know what to do next in
Nucleus" → 2 weeks → 2 hours of onboarding). v0.1 is rule-based, no LLM.

Sources scanned:
  - Open PRs flagged for me (gh pr list)
  - Unread relays in claude_code{,_peer,_main}/ + cowork/ buckets
  - Uncommitted git working tree
  - Active plans in .brain/plans/ with recent mtime
  - Recent coord-events from .brain/ledger/coordination_events.jsonl
  - Cross-trio health from cross_trio_dashboard.py (cross-talk / ack-latency / overhead)

Scoring: rule-based weights per source, with priority/urgency boosts.
Output: ranked list, top-N, with action_summary + source + why_it_matters.

This is NOT the router from §4 — it's the rule-based predecessor that
generates the corpus to eventually train the router on. Per §4.7: "make
the corpus inevitable, then the router emerges."

Usage:
    python3 scripts/whats_next.py                    # default: top 5, text
    python3 scripts/whats_next.py --top 10           # top 10
    python3 scripts/whats_next.py --format json      # machine-readable
    python3 scripts/whats_next.py --as peer          # peer's view (default)
    python3 scripts/whats_next.py --as founder       # founder's view (Lokesh-side)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

def _resolve_repo_root() -> Path:
    """Resolve the repo root containing the substrate to scan.

    Honors NUCLEUS_BRAIN_PATH env (per cross-worktree convention). When set,
    its parent is treated as the repo root. Otherwise, walks up from this
    script's path looking for AGENTS.md (canonical Nucleus marker), falling
    back to the script's grandparent dir.
    """
    env = os.environ.get("NUCLEUS_BRAIN_PATH")
    if env:
        return Path(env).resolve().parent
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "AGENTS.md").is_file():
            return parent
    return here.parent.parent


REPO_ROOT = _resolve_repo_root()
RELAY_BUCKETS = ["claude_code", "claude_code_peer", "claude_code_main", "cowork"]
PLANS_DIR = REPO_ROOT / ".brain" / "plans"
COORD_EVENTS_PATH = REPO_ROOT / ".brain" / "ledger" / "coordination_events.jsonl"

# Strip-anonymize patterns (lighter version of Tier 2's sub-step 3a — output
# may be shared, never leaks local-machine state).
_PATH_USER_HOME = re.compile(r"/Users/[a-zA-Z][\w.-]*", re.IGNORECASE)
_PATH_LINUX_HOME = re.compile(r"/home/[a-zA-Z][\w.-]*", re.IGNORECASE)


def _anon(s: str) -> str:
    if not s:
        return ""
    s = _PATH_USER_HOME.sub("<user-home>", s)
    s = _PATH_LINUX_HOME.sub("<user-home>", s)
    return s


@dataclass
class Action:
    score: float
    summary: str
    source: str        # "pr" | "relay" | "git" | "plan" | "coord"
    why: str
    metadata: dict = field(default_factory=dict)


# ----------------- Sources -----------------

def scan_open_prs(viewer: str = "peer") -> list[Action]:
    """Open PRs that need attention."""
    out: list[Action] = []
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--state", "open",
             "--json", "number,title,author,headRefName,mergeable,mergeStateStatus,createdAt"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return out
        prs = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return out
    now = datetime.now(timezone.utc)
    for pr in prs:
        n = pr["number"]
        title = pr.get("title", "")[:80]
        merge_state = pr.get("mergeStateStatus", "UNKNOWN")
        mergeable = pr.get("mergeable", "UNKNOWN")
        try:
            created_age_h = (now - datetime.fromisoformat(
                pr["createdAt"].replace("Z", "+00:00"))).total_seconds() / 3600
        except (KeyError, ValueError):
            created_age_h = 0.0
        score = 8.0
        why = f"Open PR — mergeStateStatus={merge_state}, mergeable={mergeable}"
        if merge_state == "UNSTABLE":
            score = 8.5
            why += "; CI unstable, may need bypass-merge"
        elif merge_state == "BLOCKED":
            score = 9.0
            why += "; BLOCKED — needs unblock action"
        elif merge_state == "DIRTY":
            score = 9.0
            why += "; DIRTY — merge conflicts"
        if created_age_h > 4:
            score += 0.5
            why += f"; aged {created_age_h:.1f}h"
        out.append(Action(
            score=score,
            summary=f"PR #{n}: {title}",
            source="pr",
            why=why,
            metadata={"pr_number": n, "merge_state": merge_state, "age_hours": created_age_h},
        ))
    return out


def scan_unread_relays(viewer: str = "peer") -> list[Action]:
    """Unread relays addressed to viewer."""
    relay_dir = REPO_ROOT / ".brain" / "relay"
    if not relay_dir.exists():
        return []
    # viewer determines which buckets to read
    if viewer == "peer":
        my_buckets = ["claude_code", "claude_code_peer"]
    elif viewer == "founder":
        my_buckets = ["claude_code", "claude_code_peer", "claude_code_main", "cowork"]
    else:
        my_buckets = [viewer] if viewer in RELAY_BUCKETS else ["claude_code"]

    out: list[Action] = []
    for bucket in my_buckets:
        bdir = relay_dir / bucket
        if not bdir.is_dir():
            continue
        for jfile in sorted(bdir.glob("*.json"))[-200:]:  # cap at 200 for sanity
            try:
                d = json.loads(jfile.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if d.get("read"):
                continue
            prio = (d.get("priority") or "").lower()
            subj = d.get("subject", "")[:80]
            sender = d.get("from", "?")
            score = 7.0
            if prio == "high":
                score = 9.5
            elif prio == "urgent":
                score = 10.0
            if d.get("in_reply_to"):
                score += 0.3  # thread-replies slightly favored
            why = f"Unread {prio or 'normal'}-priority relay from {sender}"
            out.append(Action(
                score=score,
                summary=f"Relay [{prio.upper()}] {sender} → {bucket}: {subj}",
                source="relay",
                why=why,
                metadata={
                    "id": d.get("id", ""),
                    "from": sender,
                    "bucket": bucket,
                    "priority": prio,
                },
            ))
    return out


def scan_git_state() -> list[Action]:
    """Uncommitted / un-pushed git work."""
    out: list[Action] = []
    try:
        status = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        ahead = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-list", "--count", "@{u}..HEAD"],
            capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return out
    if status.returncode == 0:
        modified = [l for l in status.stdout.splitlines() if l[:2].strip() in {"M", "MM", "A"}]
        if modified:
            out.append(Action(
                score=4.5,
                summary=f"{len(modified)} uncommitted file(s) in working tree",
                source="git",
                why="Uncommitted changes; review + commit or stash before next slice",
                metadata={"n_modified": len(modified)},
            ))
    if ahead.returncode == 0 and ahead.stdout.strip().isdigit():
        n = int(ahead.stdout.strip())
        if n > 0:
            out.append(Action(
                score=5.5,
                summary=f"Local branch is {n} commit(s) ahead of upstream",
                source="git",
                why="Push or open PR for unmerged commits",
                metadata={"commits_ahead": n},
            ))
    return out


def scan_recent_plans(active_window_hours: float = 24.0) -> list[Action]:
    """Plans modified within active_window_hours.

    Older plans (>24h) are background context, not actionable. Don't surface
    them in v0.1 — they create noise in the output. Future iterations may
    promote stale plans IF a related signal (PR, coord-event, relay) names
    them, but v0.1 keeps it simple.
    """
    out: list[Action] = []
    if not PLANS_DIR.is_dir():
        return out
    cutoff = datetime.now(timezone.utc).timestamp() - active_window_hours * 3600
    for p in PLANS_DIR.glob("*.md"):
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        if mtime < cutoff:
            continue
        age_h = (datetime.now(timezone.utc).timestamp() - mtime) / 3600
        # Sliding score: fresh = 6.0, decays linearly to 4.0 at 24h
        score = max(4.0, 6.0 - (age_h / 12.0))
        out.append(Action(
            score=score,
            summary=f"Plan: {p.stem} (modified {age_h:.1f}h ago)",
            source="plan",
            why="Active plan with recent edits — may have unexecuted next-slices",
            metadata={"plan_path": str(p.relative_to(REPO_ROOT)), "age_hours": age_h},
        ))
    return out


def baseline_idle_suggestion(actions: list[Action]) -> list[Action]:
    """If nothing scored above the urgent threshold, surface a default action.

    Per feedback_show_runs_always: 'Nothing queued' is not valid for peer.
    When no high-signal action exists, suggest concrete adjacent compounding
    work the operator can pick from instead of going idle.
    """
    if not actions or actions[0].score < 6.0:
        return [Action(
            score=2.0,
            summary="No urgent surface — suggest adjacent compounding",
            source="default",
            why=(
                "Options: (a) hole-poke main on next slice; (b) consume a "
                "deferred task from the queue (#110 VS Code Phase 2 / #111 "
                "Cloud Nucleus, gated on triggers); (c) read recent commits "
                "to surface anything missed."
            ),
            metadata={"viewer": "peer"},
        )]
    return []


def scan_recent_coord_events(window_hours: float = 6.0) -> list[Action]:
    """Recent coord-events that may need follow-up."""
    out: list[Action] = []
    if not COORD_EVENTS_PATH.exists():
        return out
    cutoff = datetime.now(timezone.utc).timestamp() - window_hours * 3600
    counts: dict[str, int] = {}
    last_seen: dict[str, str] = {}
    try:
        with COORD_EVENTS_PATH.open() as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts_str = rec.get("timestamp", "")
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
                except (ValueError, AttributeError):
                    continue
                if ts < cutoff:
                    continue
                t = rec.get("event_type", "?")
                counts[t] = counts.get(t, 0) + 1
                last_seen[t] = ts_str
    except OSError:
        return out
    if not counts:
        return out
    summary = ", ".join(f"{t}×{n}" for t, n in sorted(counts.items(), key=lambda kv: -kv[1])[:5])
    out.append(Action(
        score=3.5,
        summary=f"Coord-events last {window_hours:.0f}h: {summary}",
        source="coord",
        why="Recent coordination activity — context for current work",
        metadata={"counts": counts, "window_hours": window_hours},
    ))
    return out


def scan_cross_trio_health(window_hours: float = 24.0) -> list[Action]:
    """Surface cross-trio observability signals as next-actions.

    Subprocess-calls cross_trio_dashboard.py --json to read its computed
    metrics so this scanner stays in lockstep with the dashboard's logic
    (no metric duplication). Surfaces high-cross-talk, slow-ack-latency,
    and excessive coord-overhead as actionable signals.

    Failure mode: dashboard missing or returning non-zero → return empty list.
    Substrate-mature; never blocks whats_next on observability subsystem.
    """
    out: list[Action] = []
    repo_root = _resolve_repo_root()
    dashboard = repo_root / "mcp-server-nucleus" / "scripts" / "observability" / "cross_trio_dashboard.py"
    if not dashboard.exists():
        return out
    since = (datetime.now(timezone.utc).timestamp() - window_hours * 3600)
    since_iso = datetime.fromtimestamp(since, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    try:
        res = subprocess.run(
            [sys.executable, str(dashboard), "--json", "--since", since_iso],
            capture_output=True, text=True, timeout=15,
        )
        if res.returncode != 0:
            return out
        data = json.loads(res.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return out

    ct = data.get("cross_talk", {})
    if ct.get("total_relays", 0) >= 10 and ct.get("cross_talk_rate", 0) >= 0.30:
        rate_pct = ct["cross_talk_rate"] * 100
        top_pair = ct.get("top_pairs", [[None, 0]])[0] if ct.get("top_pairs") else (None, 0)
        pair_str = f" — top: {top_pair[0]}" if top_pair[0] else ""
        out.append(Action(
            score=6.5,
            summary=f"Cross-talk rate {rate_pct:.0f}% over last {window_hours:.0f}h ({ct['total_relays']} relays){pair_str}",
            source="cross-trio",
            why="Agents drifting into each other's lanes — scope-taxonomy may need refresh OR posture-correction relay",
            metadata={"cross_talk_rate": ct["cross_talk_rate"], "total_relays": ct["total_relays"]},
        ))

    al = data.get("ack_latency", {})
    if al.get("paired_count", 0) >= 5 and al.get("p95_seconds", 0) > 300:
        out.append(Action(
            score=5.0,
            summary=f"Ack-latency p95 {al['p95_seconds']:.0f}s over last {window_hours:.0f}h ({al['paired_count']} pairs)",
            source="cross-trio",
            why="Relay queue may be backing up — peer/main may not be polling inbox between turns",
            metadata={"p95_seconds": al["p95_seconds"], "paired_count": al["paired_count"]},
        ))

    co = data.get("coord_overhead", {})
    if co.get("pr_count", 0) >= 3 and co.get("events_per_pr", 0) > 3:
        out.append(Action(
            score=4.0,
            summary=f"Coord-overhead {co['events_per_pr']:.1f} events/PR over {co['pr_count']} PRs",
            source="cross-trio",
            why="Meta-talk may be exceeding work — consider tighter relay discipline",
            metadata={"events_per_pr": co["events_per_pr"], "pr_count": co["pr_count"]},
        ))

    return out


# ----------------- Render -----------------

def render_text(actions: list[Action], top_n: int) -> str:
    lines = []
    lines.append(f"# What's next? ({len(actions)} candidates, top {min(top_n, len(actions))})")
    lines.append("")
    for i, a in enumerate(actions[:top_n], 1):
        lines.append(f"## {i}. [{a.source}] {a.summary}")
        lines.append(f"   score: {a.score:.1f}")
        lines.append(f"   why:   {a.why}")
        lines.append("")
    if len(actions) > top_n:
        lines.append(f"... and {len(actions) - top_n} more (raise --top to see)")
    return "\n".join(lines) + "\n"


def render_json(actions: list[Action], top_n: int) -> str:
    payload = [
        {
            "rank": i + 1,
            "score": round(a.score, 2),
            "summary": a.summary,
            "source": a.source,
            "why": a.why,
            "metadata": a.metadata,
        }
        for i, a in enumerate(actions[:top_n])
    ]
    return json.dumps({"top_n": top_n, "n_total": len(actions), "actions": payload}, indent=2)


# ----------------- Main -----------------

def collect_actions(viewer: str) -> list[Action]:
    """Run all source scanners + sort by score descending."""
    actions: list[Action] = []
    actions.extend(scan_open_prs(viewer))
    actions.extend(scan_unread_relays(viewer))
    actions.extend(scan_git_state())
    actions.extend(scan_recent_plans())
    actions.extend(scan_recent_coord_events())
    actions.extend(scan_cross_trio_health())
    # Strip-anonymize summaries + reasons before returning
    for a in actions:
        a.summary = _anon(a.summary)
        a.why = _anon(a.why)
    actions.sort(key=lambda a: -a.score)
    actions.extend(baseline_idle_suggestion(actions))
    return actions


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=5, help="Number of actions to surface")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--as", dest="viewer", choices=["peer", "main", "cowork", "founder"], default="peer")
    args = ap.parse_args(argv)

    actions = collect_actions(args.viewer)
    if not actions:
        print("# What's next? — nothing to surface")
        print("(no open PRs / unread relays / dirty tree / recent plans / coord-events)")
        return 0
    if args.format == "json":
        print(render_json(actions, args.top))
    else:
        print(render_text(actions, args.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
