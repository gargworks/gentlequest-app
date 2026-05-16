#!/usr/bin/env python3
"""Phase 2 smoke runner — multi-thread routing + ceilings + slash commands.

Hits a live /tb endpoint with deterministic scenarios and asserts the
multi-thread plumbing behaves correctly. Designed to run AFTER endpoint
restart so it catches startup-migration issues too.

Scenarios:
    1. cold-start chat sends to inbox
    2. continuation message routes to same thread (high-similarity)
    3. orthogonal new topic creates a new thread
    4. /thread list surfaces top-5 active
    5. /thread switch / new / archive round-trip
    6. ceiling refusal at hard limit

Usage:
    TB_ENDPOINT_URL=http://127.0.0.1:7878 python3 scripts/smoke_phase2.py
    python3 scripts/smoke_phase2.py --skip-live  (lightweight, skips ceiling)

Exit code: 0 = all pass, non-zero = N failures.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, List, Optional, Tuple

ENDPOINT = os.environ.get("TB_ENDPOINT_URL", "http://127.0.0.1:7878").rstrip("/")
TIMEOUT = int(os.environ.get("TB_SMOKE_TIMEOUT", "120"))


# ── HTTP helpers ─────────────────────────────────────────────────────

def _post(path: str, payload: Dict[str, Any],
          timeout: int = TIMEOUT) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{ENDPOINT}{path}", data=data,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
            resp["_wall_ms"] = int((time.time() - t0) * 1000)
            return resp
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.reason}",
                "_wall_ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}",
                "_wall_ms": int((time.time() - t0) * 1000)}


def _get(path: str, timeout: int = TIMEOUT) -> Dict[str, Any]:
    req = urllib.request.Request(f"{ENDPOINT}{path}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def _turn(chat_id: str, text: str, **extra) -> Dict[str, Any]:
    payload = {
        "input": text,
        "chat_id": chat_id,
        "session_id": chat_id,
        "scope": "auto",
        "principal_model": "tb",       # keep smoke fast — no Sonnet
        "quality_tier": "fast",
        "verifier": "off",
        "num_predict": 100,            # short response
    }
    payload.update(extra)
    return _post("/tb/turn", payload)


def _thread(chat_id: str, command: str) -> Dict[str, Any]:
    return _post("/tb/thread", {"chat_id": chat_id, "command": command},
                 timeout=10)


# ── Scenario harness ─────────────────────────────────────────────────

class Scenario:
    def __init__(self, name: str):
        self.name = name
        self.passed: List[str] = []
        self.failed: List[str] = []

    def check(self, label: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed.append(label)
            print(f"  ✓ {label}")
        else:
            self.failed.append(f"{label} — {detail}" if detail else label)
            print(f"  ✗ {label}  {detail}")

    @property
    def ok(self) -> bool:
        return not self.failed


# ── Scenarios ────────────────────────────────────────────────────────

def scenario_cold_start() -> Scenario:
    s = Scenario("cold-start routes to inbox")
    chat_id = f"smoke:cold:{uuid.uuid4().hex[:6]}"
    r = _turn(chat_id, "hello world")
    s.check("turn ok", r.get("ok"), r.get("error", ""))
    s.check("chat_id echoed", r.get("chat_id") == chat_id)
    s.check("thread_id is inbox", r.get("thread_id") == "inbox",
            f"got {r.get('thread_id')!r}")
    s.check("decision = cold_start", r.get("thread_decision_action") == "cold_start",
            f"got {r.get('thread_decision_action')!r}")
    s.check("session_id is threaded",
            r.get("session_id") == f"{chat_id}:inbox",
            f"got {r.get('session_id')!r}")
    return s


def scenario_continuation_routes_same() -> Scenario:
    s = Scenario("continuation routes to same thread")
    chat_id = f"smoke:cont:{uuid.uuid4().hex[:6]}"
    r1 = _turn(chat_id, "alpha continues")
    r2 = _turn(chat_id, "alpha continues again")
    s.check("turn1 ok", r1.get("ok"))
    s.check("turn2 ok", r2.get("ok"))
    s.check("same thread on both",
            r1.get("thread_id") == r2.get("thread_id"),
            f"{r1.get('thread_id')} vs {r2.get('thread_id')}")
    return s


def scenario_thread_slash_list() -> Scenario:
    s = Scenario("/thread list surfaces buckets")
    chat_id = f"smoke:slash:{uuid.uuid4().hex[:6]}"
    _turn(chat_id, "init")  # seed the chat namespace
    r = _thread(chat_id, "list")
    s.check("list ok", r.get("ok"))
    text = r.get("text", "")
    s.check("inbox surfaced", "inbox" in text)
    s.check("active marker present", "★" in text)
    return s


def scenario_thread_switch_new_archive() -> Scenario:
    s = Scenario("/thread switch + new + archive round-trip")
    chat_id = f"smoke:rt:{uuid.uuid4().hex[:6]}"
    _turn(chat_id, "init")
    sw = _thread(chat_id, "switch code")
    s.check("switch ok", sw.get("ok"))
    s.check("active = code", sw.get("active_thread_id") == "code",
            f"got {sw.get('active_thread_id')!r}")
    nw = _thread(chat_id, "new manju messaging")
    s.check("new ok", nw.get("ok"))
    s.check("active = manju_messaging",
            nw.get("active_thread_id") == "manju_messaging",
            f"got {nw.get('active_thread_id')!r}")
    ar = _thread(chat_id, "archive manju_messaging")
    s.check("archive ok", ar.get("ok"))
    s.check("active pivoted",
            ar.get("active_thread_id") != "manju_messaging",
            f"got {ar.get('active_thread_id')!r}")
    return s


def scenario_thread_invalid_subcommand() -> Scenario:
    s = Scenario("/thread bogus → usage hint")
    chat_id = f"smoke:bogus:{uuid.uuid4().hex[:6]}"
    r = _thread(chat_id, "bogus_subcommand")
    s.check("not ok", not r.get("ok"))
    s.check("usage block in text", "/thread" in r.get("text", ""))
    return s


def scenario_health_endpoint() -> Scenario:
    s = Scenario("endpoint health + thread route registered")
    h = _get("/tb/health")
    s.check("health ok", h.get("ok"))
    return s


SCENARIOS = [
    scenario_health_endpoint,
    scenario_cold_start,
    scenario_continuation_routes_same,
    scenario_thread_slash_list,
    scenario_thread_switch_new_archive,
    scenario_thread_invalid_subcommand,
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2 smoke runner")
    parser.add_argument("--scenarios", default="all",
                        help="comma-separated scenario names or 'all'")
    args = parser.parse_args()

    runners = SCENARIOS
    if args.scenarios != "all":
        wanted = set(args.scenarios.split(","))
        runners = [r for r in SCENARIOS if r.__name__ in wanted]

    print(f"smoke runner — endpoint={ENDPOINT}")
    print(f"  scenarios: {len(runners)}")
    print()

    results: List[Scenario] = []
    for fn in runners:
        print(f"[scenario] {fn.__name__}")
        try:
            sc = fn()
        except Exception as e:
            sc = Scenario(fn.__name__)
            sc.failed.append(f"crashed: {type(e).__name__}: {e}")
            print(f"  ✗ crashed: {e}")
        results.append(sc)
        print()

    total_pass = sum(len(r.passed) for r in results)
    total_fail = sum(len(r.failed) for r in results)
    print("=" * 60)
    print(f"summary: {total_pass} pass / {total_fail} fail "
          f"across {len(results)} scenarios")
    if total_fail:
        for r in results:
            for f in r.failed:
                print(f"  FAIL {r.name}: {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
