#!/usr/bin/env python3
"""
Post-deploy smoke test: hits 24 critical endpoints against a deployed URL.

Usage:
    python scripts/smoke_test.py https://gentlequest.onrender.com
    python scripts/smoke_test.py https://gentlequest.onrender.com --admin-token=xxx

Exit codes:
    0 — all endpoints healthy
    1 — one or more endpoints failed
"""

import argparse
import json
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

ENDPOINTS: List[Tuple[str, str, Optional[Dict[str, Any]], Any]] = [
    ("GET", "/api/health", None, 200),
    ("GET", "/api/ping", None, 200),
    ("GET", "/api/deploy-test", None, 200),
    ("GET", "/", None, 200),
    ("GET", "/health", None, 200),
    ("GET", "/app", None, 200),
    ("GET", "/privacy", None, 200),
    ("GET", "/terms", None, 200),
    ("GET", "/api/get_or_create_session", None, 200),
    ("GET", "/api/chat_history", None, 200),
    ("GET", "/api/mood_history", None, 200),
    ("POST", "/api/mood_entry", {"mood_level": 4, "note": "smoke"}, 200),
    ("POST", "/api/self_assessment", {
        "mood": "good", "energy": "high", "sleep": "8h", "stress": "low"
    }, (200, 201)),
    ("GET", "/api/mood_pulse", None, 200),
    ("GET", "/api/mood_analytics", None, 200),
    ("POST", "/api/analytics/log", {"event_type": "smoke"}, (200, 201)),
    ("GET", "/api/analytics/recent", None, 200),
    ("GET", "/api/analytics/overview", None, 200),
    ("GET", "/api/memory_status", None, 200),
    ("GET", "/api/memory/status", None, 200),
    ("GET", "/api/compliance/ip-region-check", None, 200),
    ("GET", "/api/assessment/phq9/questions", None, 200),
    ("GET", "/api/assessment/history", None, 200),
    ("POST", "/api/crisis_detection", {"message": "I feel a bit stressed"}, 200),
]


def _ok(status_code: int, expected: Any) -> bool:
    if isinstance(expected, int):
        return status_code == expected
    return status_code in expected


def run_smoke(
    base_url: str,
    admin_token: Optional[str] = None,
    timeout: float = 10.0,
) -> int:
    """Run smoke tests. Returns 0 on success, 1 if any endpoint failed."""
    session = requests.Session()
    session.headers.update({
        "X-Session-ID": "smoke-test",
        "X-Analytics-Consent": "true",
    })
    if admin_token:
        session.headers["X-Admin-Token"] = admin_token

    base_url = base_url.rstrip("/")
    passed = 0
    failed: List[str] = []
    total_time = 0.0

    for method, path, body, expected in ENDPOINTS:
        url = f"{base_url}{path}"
        t0 = time.time()
        try:
            if method == "GET":
                r = session.get(url, timeout=timeout)
            else:
                r = session.post(url, json=body, timeout=timeout)
            elapsed_ms = int((time.time() - t0) * 1000)
            total_time += elapsed_ms / 1000.0

            if _ok(r.status_code, expected):
                passed += 1
                print(f"  OK  {method:4s} {path:45s} -> {r.status_code} ({elapsed_ms}ms)")
            else:
                failed.append(f"{method} {path} -> {r.status_code} (expected {expected})")
                print(f"  FAIL{method:4s} {path:45s} -> {r.status_code} (expected {expected})")
        except Exception as e:
            failed.append(f"{method} {path} -> {e}")
            print(f"  ERR {method:4s} {path:45s} -> {e}")

    print(f"\nSmoke: {passed}/{len(ENDPOINTS)} passed  total={total_time:.1f}s")
    if failed:
        print("\nFailures:")
        for f in failed:
            print(f"  - {f}")
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Post-deploy smoke test")
    p.add_argument("url", help="Base URL (e.g., https://gentlequest.onrender.com)")
    p.add_argument("--admin-token", default=None, help="X-Admin-Token for deep health probe")
    p.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout seconds")
    p.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = p.parse_args()

    code = run_smoke(args.url, args.admin_token, args.timeout)
    if args.json:
        print(json.dumps({"passed": code == 0, "url": args.url}))
    return code


if __name__ == "__main__":
    sys.exit(main())
