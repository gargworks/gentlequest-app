#!/usr/bin/env python3
"""Audit proxy-token cost from `agent_spawn` / `agent_return` events.

Reads `.brain/ledger/events.jsonl`, filters the two org event types within a
lookback window, sums `prompt_chars + response_chars` per role × a per-tier
proxy rate, and prints a Markdown table.

Proxy rate acknowledged ~15% error vs claude.ai/usage — recalibrate after
dogfood. Malformed lines are counted and skipped (no silent data loss).
Orphan spawns (spawn without matching return) are reported separately.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_DEFAULT_RATE = {"opus": 0.25, "sonnet": 0.25, "haiku": 0.25}
_EVENT_TYPES = {"agent_spawn", "agent_return", "pair_heartbeat"}


def _brain_path() -> Path:
    env = os.environ.get("NUCLEAR_BRAIN_PATH")
    if env:
        return Path(env)
    cwd_brain = Path.cwd() / ".brain"
    if cwd_brain.exists():
        return cwd_brain
    return Path(".brain")


def _parse_ts(iso: str) -> datetime:
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"
    return datetime.fromisoformat(iso)


def read_events(events_path: Path, since: datetime):
    """Yield (events, malformed_count). Skips malformed lines and stale events."""
    if not events_path.exists():
        return [], 0
    events = []
    malformed = 0
    with open(events_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if ev.get("type") not in _EVENT_TYPES:
                continue
            ts_str = ev.get("timestamp", "")
            try:
                ts = _parse_ts(ts_str)
            except Exception:
                malformed += 1
                continue
            if ts < since:
                continue
            events.append(ev)
    return events, malformed


def summarize(events):
    """Group by role; count spawns, returns, char totals; flag orphans."""
    by_role = {}
    for ev in events:
        if ev.get("type") not in ("agent_spawn", "agent_return"):
            continue
        data = ev.get("data") or {}
        role = data.get("role") or "unknown"
        tier = data.get("tier") or "unknown"
        stats = by_role.setdefault(role, {
            "tier": tier,
            "spawns": 0, "returns": 0,
            "prompt_chars": 0, "response_chars": 0,
            "duration_ms": 0, "orphans": 0,
        })
        if ev["type"] == "agent_spawn":
            stats["spawns"] += 1
            stats["prompt_chars"] += int(data.get("prompt_chars") or 0)
        else:
            stats["returns"] += 1
            stats["response_chars"] += int(data.get("response_chars") or 0)
            stats["duration_ms"] += int(data.get("duration_ms") or 0)
    for stats in by_role.values():
        stats["orphans"] = max(0, stats["spawns"] - stats["returns"])
    return by_role


def summarize_by_pair(events):
    """Group by (parent_opus, sonnet_role) cost-pair.

    Per .brain/plans/sonnet_pair_authority_contract.md — when paired persistent
    Sonnets activate (gated on Phase-0 Reshape W3 audit), per-pair economics
    measure paired-vs-unpaired delegation cost cleanly: each cost-pair shows
    Opus principal's spawn rate (if it spawns sub-Sonnets) joined with the
    Sonnet's response volume.

    Returns dict keyed by `(parent, role)` tuple. Today (no paired Sonnets)
    just rolls up per Opus principal's ad-hoc spawn pattern; semantically
    identical to summarize() with parent-grouping added.
    """
    by_pair = {}
    for ev in events:
        if ev.get("type") not in ("agent_spawn", "agent_return"):
            continue
        data = ev.get("data") or {}
        parent = data.get("parent") or "unknown"
        role = data.get("role") or "unknown"
        tier = data.get("tier") or data.get("model") or "unknown"
        key = (parent, role)
        stats = by_pair.setdefault(key, {
            "tier": tier,
            "spawns": 0, "returns": 0,
            "prompt_chars": 0, "response_chars": 0,
            "duration_ms": 0, "orphans": 0,
        })
        if ev["type"] == "agent_spawn":
            stats["spawns"] += 1
            stats["prompt_chars"] += int(data.get("prompt_chars") or 0)
        else:
            stats["returns"] += 1
            stats["response_chars"] += int(data.get("response_chars") or 0)
            stats["duration_ms"] += int(data.get("duration_ms") or 0)
    for stats in by_pair.values():
        stats["orphans"] = max(0, stats["spawns"] - stats["returns"])
    return by_pair


def summarize_pair_utilization(events):
    """For L3 always-on pairs: compute latest busy_pct_1h per (lane, session_id).

    Reads `pair_heartbeat` events emitted by sonnet_pair_daemon. Returns
    `{lane: {session_id, busy_pct_1h, last_seen_ms, events_in_window, pid}}`.
    Latest heartbeat per lane wins; older heartbeats from prior daemon
    invocations are surfaced under their own session_id only if no fresher
    heartbeat exists for that lane.

    Per sonnet_pair_authority_contract.md, the >=40% utilization gate decides
    v0.2 expansion. Below threshold = tear down, do not ship more pairs.
    """
    latest: dict = {}
    for ev in events:
        if ev.get("type") != "pair_heartbeat":
            continue
        data = ev.get("data") or {}
        lane = data.get("lane")
        if not lane:
            continue
        now_ms = int(data.get("now_ms") or 0)
        prev = latest.get(lane)
        if prev is None or now_ms > prev.get("last_seen_ms", 0):
            latest[lane] = {
                "session_id": data.get("session_id"),
                "busy_pct_1h": float(data.get("busy_pct_1h") or 0.0),
                "events_in_window": int(data.get("events_in_window") or 0),
                "pid": data.get("pid"),
                "last_seen_ms": now_ms,
            }
    return latest


def format_pair_table(by_pair, rates=None, utilization=None) -> str:
    rates = rates or _DEFAULT_RATE
    if not by_pair and not utilization:
        return "_No agent_spawn/agent_return/pair_heartbeat events in window._\n"
    out = []
    if by_pair:
        out.extend([
            "## Spawn cost-pair rollup",
            "",
            "| parent | role | tier | spawns | returns | orphans | prompt_chars | response_chars | proxy_tokens |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|",
        ])
        grand = 0.0
        for (parent, role), s in sorted(by_pair.items()):
            rate = rates.get(s["tier"], 0.25)
            proxy = (s["prompt_chars"] + s["response_chars"]) * rate
            grand += proxy
            out.append(
                f"| {parent} | {role} | {s['tier']} | {s['spawns']} | {s['returns']} | "
                f"{s['orphans']} | {s['prompt_chars']} | {s['response_chars']} | {proxy:.0f} |"
            )
        out.append("")
        out.append(f"**Total proxy tokens:** {grand:.0f}")
        out.append("")
    if utilization:
        out.extend([
            "## L3 pair utilization (latest pair_heartbeat per lane)",
            "",
            "| lane | busy_pct_1h | events_in_window | pid | session_id | gate (>=40%) |",
            "|---|---:|---:|---:|---|:---:|",
        ])
        for lane in sorted(utilization):
            u = utilization[lane]
            sid = (u.get("session_id") or "")[:8]
            gate = "PASS" if u["busy_pct_1h"] >= 40.0 else "FAIL"
            out.append(
                f"| {lane} | {u['busy_pct_1h']:.2f}% | {u['events_in_window']} | "
                f"{u['pid']} | {sid} | {gate} |"
            )
        out.append("")
    return "\n".join(out) if out else "_No data in window._\n"


def format_table(by_role, rates=None) -> str:
    rates = rates or _DEFAULT_RATE
    if not by_role:
        return "_No agent_spawn/agent_return events in window._\n"
    lines = [
        "| role | tier | spawns | returns | orphans | prompt_chars | response_chars | proxy_tokens |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    grand = 0.0
    for role, s in sorted(by_role.items()):
        rate = rates.get(s["tier"], 0.25)
        proxy = (s["prompt_chars"] + s["response_chars"]) * rate
        grand += proxy
        lines.append(
            f"| {role} | {s['tier']} | {s['spawns']} | {s['returns']} | "
            f"{s['orphans']} | {s['prompt_chars']} | {s['response_chars']} | {proxy:.0f} |"
        )
    lines.append("")
    lines.append(f"**Total proxy tokens:** {grand:.0f}")
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Audit proxy-token cost from org agent_spawn/agent_return events."
    )
    p.add_argument("--since-hours", type=float, default=24.0,
                   help="Lookback window in hours (default 24)")
    p.add_argument("--events-path", default=None,
                   help="Override .brain/ledger/events.jsonl path")
    p.add_argument("--pair", action="store_true",
                   help="Group by (parent_opus, sonnet_role) cost-pair instead of by role. "
                        "Per sonnet_pair_authority_contract.md — surfaces paired-vs-unpaired economics.")
    args = p.parse_args(argv)
    events_path = Path(args.events_path) if args.events_path else (_brain_path() / "ledger" / "events.jsonl")
    since = datetime.now(timezone.utc) - timedelta(hours=args.since_hours)
    events, malformed = read_events(events_path, since)
    print(f"# Org proxy-token audit (last {args.since_hours:g}h)")
    print()
    print(f"Events: {len(events)} in window; malformed lines skipped: {malformed}")
    print()
    if args.pair:
        print(format_pair_table(
            summarize_by_pair(events),
            utilization=summarize_pair_utilization(events),
        ))
    else:
        print(format_table(summarize(events)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
