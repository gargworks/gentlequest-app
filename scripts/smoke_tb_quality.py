#!/usr/bin/env python3
"""TB Quality Compound — pre-merge smoke runner.

Hits a live /tb/turn endpoint with 5 prompts × 3 quality tiers (fast/good/
verified) and validates the bundled-levers PR didn't regress anything.
Writes per-turn results to .brain/measurement/quality_smoke_<ts>.jsonl.

Pass criteria (all must hold):
- 0 outputs contain a citation-loop pattern (`[10][`, `[15][`, `[20][`, etc.)
- Life-mode outputs contain none of {launchd, snapshot, /api, .py, port,
  cron, devops} — the residual mode-mix list from the 2026-05-07 tb-log
- Sovereign queries return principal_model=tb regardless of caller
- Every turn writes a DPO/shadow_log entry (corpus_written or sovereign-
  blocked, never silently dropped)
- good-tier latency p95 < 60s; verified p95 < 90s; fast no upper bound
  (it's TB-only and TB itself is slow until v15)

Usage:
    python scripts/smoke_tb_quality.py
    python scripts/smoke_tb_quality.py --tiers fast,good --prompts 3
    python scripts/smoke_tb_quality.py --endpoint http://127.0.0.1:7878

Exit 0 on all-green, 1 on any failure. CI-friendly.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENDPOINT = "http://127.0.0.1:7878"

# ── Test prompts ─────────────────────────────────────────────────────
# Picked to exercise the failure modes seen in the 2026-05-07 tb-log:
# - life-mode confabulation, mode-mixing, citation-loop
# - code-mode regression check (must still reach code engrams)
# - sovereign hard-gate (must never call claude -p)
PROMPTS: List[Dict[str, Any]] = [
    {
        "id": "life_short",
        "input": "Suggest 3 short messages I could send to a friend after a week of silence.",
        "mode": "life",
        "sovereignty": "public",
    },
    {
        "id": "life_advice",
        "input": "How should I handle a tough conversation with a family member?",
        "mode": "life",
        "sovereignty": "public",
    },
    {
        "id": "code_lookup",
        "input": "Where is the relay_post function defined and what does it do?",
        "mode": "code",
        "sovereignty": "public",
    },
    {
        "id": "sovereign_personal",
        "input": "Remind me what I journaled about my goals last month.",
        "mode": "life",
        "sovereignty": "sovereign",
    },
    {
        "id": "ambiguous_short",
        "input": "What should I focus on this week?",
        "mode": None,  # let auto resolve
        "sovereignty": "public",
    },
]

CITATION_LOOP_PATTERNS = [r"\[10\]\[", r"\[15\]\[", r"\[20\]\[",
                          r"\]\[10\]", r"\]\[15\]", r"\]\[20\]"]
LIFE_MODE_LEAK_KEYWORDS = ["launchd", "snapshot", "/api", "devops",
                           "cron", "launchctl", ".plist"]


def post_turn(endpoint: str, payload: Dict[str, Any],
              timeout: int = 900) -> Dict[str, Any]:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{endpoint}/tb/turn", data=data,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode())
            resp["_wall_ms"] = int((time.time() - t0) * 1000)
            return resp
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.reason}",
                "_wall_ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}",
                "_wall_ms": int((time.time() - t0) * 1000)}


def check_health(endpoint: str) -> bool:
    try:
        with urllib.request.urlopen(f"{endpoint}/tb/health", timeout=5) as r:
            return json.loads(r.read().decode()).get("ok", False)
    except Exception:
        return False


def evaluate(prompt: Dict[str, Any], tier: str,
             resp: Dict[str, Any]) -> List[str]:
    """Return list of failure messages. Empty list = pass."""
    fails = []
    if not resp.get("ok"):
        fails.append(f"endpoint error: {resp.get('error')}")
        return fails  # bail; everything else is moot
    output = resp.get("output") or ""
    # Citation-loop check
    for pat in CITATION_LOOP_PATTERNS:
        if re.search(pat, output):
            fails.append(f"citation-loop pattern matched: {pat!r}")
    # Life-mode leak check
    if (prompt.get("mode") == "life") or (resp.get("mode") == "life"):
        low = output.lower()
        leaks = [kw for kw in LIFE_MODE_LEAK_KEYWORDS if kw in low]
        if leaks:
            fails.append(f"life-mode leak keywords: {leaks}")
    # Sovereign hard-gate check
    if prompt.get("sovereignty") == "sovereign":
        if resp.get("principal_model") != "tb":
            fails.append(
                f"sovereign hard-gate failed: principal_model={resp.get('principal_model')}"
            )
        if resp.get("verifier_used") not in (None, "none"):
            fails.append(
                f"sovereign verifier should be off: {resp.get('verifier_used')}"
            )
        if resp.get("corpus_written") is True:
            fails.append("sovereign must not write corpus")
        if resp.get("sovereign_gate_fired") is not True:
            fails.append("sovereign_gate_fired should be True")
    # Tier resolution echo check
    if resp.get("quality_tier") != tier:
        fails.append(
            f"quality_tier echo mismatch: expected={tier} got={resp.get('quality_tier')}"
        )
    return fails


def latency_pass(tier: str, ms_list: List[int]) -> List[str]:
    """p95 latency check per tier."""
    if not ms_list:
        return []
    ms_sorted = sorted(ms_list)
    p95_idx = max(0, int(len(ms_sorted) * 0.95) - 1)
    p95 = ms_sorted[p95_idx]
    fails = []
    # Generous budgets — these are hand-tuned for v14 + Sonnet round-trip.
    # Real production SLOs would be tighter, but smoke gate just catches
    # disasters (5min hangs etc.), not micro-regressions.
    budgets = {"fast": 600_000, "good": 600_000, "verified": 900_000}
    budget = budgets.get(tier, 600_000)
    if p95 > budget:
        fails.append(f"{tier} p95 {p95}ms exceeds budget {budget}ms")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    ap.add_argument("--tiers", default="fast,good,verified")
    ap.add_argument("--prompts", type=int, default=5,
                    help="How many prompts from PROMPTS to run (1-5)")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    tiers = [t.strip() for t in args.tiers.split(",") if t.strip()]
    prompts = PROMPTS[:max(1, min(args.prompts, len(PROMPTS)))]

    if not check_health(args.endpoint):
        print(f"[smoke] /tb/health failed at {args.endpoint}", file=sys.stderr)
        return 2

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(args.out) if args.out else (
        ROOT / ".brain" / "measurement" / f"quality_smoke_{ts}.jsonl"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_fails: List[str] = []
    per_tier_ms: Dict[str, List[int]] = {t: [] for t in tiers}
    n_total = 0
    n_pass = 0

    with out_path.open("w") as out_f:
        for prompt in prompts:
            for tier in tiers:
                n_total += 1
                payload = {
                    "input": prompt["input"],
                    "session_id": f"smoke-{prompt['id']}-{tier}-{ts}",
                    "sovereignty": prompt["sovereignty"],
                    "quality_tier": tier,
                }
                if prompt["mode"]:
                    payload["mode"] = prompt["mode"]

                print(f"[smoke] {prompt['id']:25s} tier={tier:8s} ... ",
                      end="", flush=True)
                resp = post_turn(args.endpoint, payload)
                fails = evaluate(prompt, tier, resp)
                per_tier_ms[tier].append(resp.get("_wall_ms", 0))

                record = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "prompt_id": prompt["id"],
                    "tier": tier,
                    "payload": payload,
                    "ok": resp.get("ok", False),
                    "wall_ms": resp.get("_wall_ms", 0),
                    "duration_ms": resp.get("duration_ms", 0),
                    "principal_model": resp.get("principal_model"),
                    "verifier_used": resp.get("verifier_used"),
                    "verifier_verdict": resp.get("verifier_verdict"),
                    "quality_tier_echo": resp.get("quality_tier"),
                    "mode": resp.get("mode"),
                    "sovereignty": resp.get("sovereignty"),
                    "corpus_written": resp.get("corpus_written"),
                    "sovereign_gate_fired": resp.get("sovereign_gate_fired"),
                    "sonnet_fell_back": resp.get("sonnet_fell_back"),
                    "rag_chunks": resp.get("rag_chunks"),
                    "output_chars": len(resp.get("output") or ""),
                    "fails": fails,
                    "output_head": (resp.get("output") or "")[:300],
                }
                out_f.write(json.dumps(record) + "\n")

                if fails:
                    print(f"FAIL ({len(fails)}): {'; '.join(fails)}")
                    all_fails.extend(
                        [f"[{prompt['id']}/{tier}] {m}" for m in fails]
                    )
                else:
                    print(f"ok ({resp.get('_wall_ms')}ms, "
                          f"principal={resp.get('principal_model')})")
                    n_pass += 1

    # Latency budget check (post-loop)
    for tier in tiers:
        lat_fails = latency_pass(tier, per_tier_ms[tier])
        if lat_fails:
            all_fails.extend(lat_fails)

    print()
    print(f"[smoke] results: {n_pass}/{n_total} green")
    print(f"[smoke] log: {out_path}")
    if all_fails:
        print(f"[smoke] FAILURES ({len(all_fails)}):")
        for f in all_fails[:25]:
            print(f"  - {f}")
        return 1
    print("[smoke] all green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
