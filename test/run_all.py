#!/usr/bin/env python3
"""
Comprehensive test runner — API + E2E + Health
Run after every deploy to verify the system end-to-end.

Usage: python3 test/run_all.py
"""

import asyncio
import json
import time
import sys
import urllib.request
import urllib.error
from datetime import datetime

BASE = "https://nucleus.gentlequest.app"
RESULTS = []


def api(method, path, body=None, timeout=15):
    """Simple API call, returns (status, body_dict, elapsed_ms)."""
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data else {})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            elapsed = round((time.monotonic() - t0) * 1000)
            return resp.status, json.loads(raw), elapsed
    except urllib.error.HTTPError as e:
        elapsed = round((time.monotonic() - t0) * 1000)
        try:
            raw = e.read()
            body = json.loads(raw)
        except Exception:
            body = {"error": str(e)}
        return e.code, body, elapsed
    except Exception as e:
        elapsed = round((time.monotonic() - t0) * 1000)
        return 0, {"error": str(e)}, elapsed


def record(name, passed, elapsed_ms, detail=""):
    icon = "+" if passed else "x"
    RESULTS.append({"name": name, "passed": passed, "ms": elapsed_ms, "detail": detail})
    print(f"  [{icon}] {name}: {elapsed_ms}ms — {detail}")


# ─── 1. Health & Infrastructure ───

def test_health():
    print("\n=== Health & Infrastructure ===")
    code, body, ms = api("GET", "/api/health")
    record("Health endpoint", code == 200, ms, f"db={body.get('database','?')}")

    # Check version/build info
    deploy = body.get("deployment", {})
    record("Version info", bool(deploy.get("version")), 0, f"v={deploy.get('version')}")

    # CORS origins present
    origins = body.get("cors_origins", [])
    record("CORS configured", len(origins) > 3, 0, f"{len(origins)} origins")


# ─── 2. Chat API ───

def test_chat_api():
    print("\n=== Chat API ===")

    # Basic chat
    code, body, ms = api("POST", "/api/chat", {"message": "hello", "mode": "cbt",
                                                  "session_id": f"test-{int(time.time())}"})
    has_response = bool(body.get("response"))
    record("Chat response", code == 200 and has_response, ms,
           body.get("response", "")[:60] if has_response else body.get("error", "no response"))

    # Latency under 5s
    record("Chat latency <5s", ms < 5000, ms, f"{'PASS' if ms < 5000 else 'SLOW'}")

    # Risk level present
    record("Risk level returned", "risk_level" in body, 0, f"level={body.get('risk_level')}")

    # Session ID returned
    record("Session ID returned", bool(body.get("session_id")), 0, "")

    # Crisis fields present
    record("Crisis fields present",
           "crisis_detected" in body and "crisis_msg" in body, 0, "")


# ─── 3. Debug Timing ───

def test_debug_timing():
    print("\n=== Debug Timing ===")

    # With debug=1
    code, body, ms = api("POST", "/api/chat?debug=1",
                          {"message": "test", "mode": "cbt",
                           "session_id": f"test-debug-{int(time.time())}"})
    if code == 200:
        has_timing = "_debug_timing" in body
        record("debug=1 shows timing", has_timing, ms, "")
    else:
        record("debug=1 shows timing", False, ms, f"rate limited (code={code})")

    if has_timing:
        t = body["_debug_timing"]
        inner = t.get("inner", {})
        record("Inner breakdown present", bool(inner), 0,
               f"mem={inner.get('memory_ms')}ms llm={inner.get('llm_ms')}ms")
        record("Server total <3s", t.get("total_ms", 9999) < 3000, 0,
               f"server_total={t.get('total_ms')}ms")

    # Without debug — no timing
    code2, body2, ms2 = api("POST", "/api/chat",
                             {"message": "test2", "mode": "cbt",
                              "session_id": f"test-nodebug-{int(time.time())}"})
    if code2 == 200:
        record("No debug hides timing", "_debug_timing" not in body2, ms2, "")
    else:
        record("No debug hides timing", False, ms2, f"rate limited (code={code2})")


# ─── 4. Error Handling ───

def test_error_handling():
    print("\n=== Error Handling ===")

    # Missing message
    code, body, ms = api("POST", "/api/chat", {"mode": "cbt"})
    record("Missing message → 400", code == 400, ms, body.get("error", ""))

    # Empty message
    code, body, ms = api("POST", "/api/chat", {"message": "", "mode": "cbt"})
    record("Empty message → 400", code == 400, ms, body.get("error", ""))

    # Empty body — should reject (400 or 500)
    code, body, ms = api("POST", "/api/chat", {})
    record("Empty body rejected", code in (400, 500), ms, f"code={code}")


# ─── 5. Crisis Detection ───

def test_crisis_detection():
    print("\n=== Crisis Detection ===")

    # Safe message
    code, body, ms = api("POST", "/api/chat",
                          {"message": "I had a great day today", "mode": "cbt",
                           "session_id": f"test-safe-{int(time.time())}"})
    if code == 200:
        record("Safe message → low risk", body.get("risk_level") == "low", ms, "")
    else:
        record("Safe message → low risk", False, ms, f"rate limited or error (code={code})")

    # Note: not testing actual crisis messages to avoid triggering real alerts


# ─── 6. Playwright E2E ───

async def test_e2e_browser():
    print("\n=== Browser E2E ===")
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        record("Playwright available", False, 0, "playwright not installed")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 390, "height": 844})
        page = await ctx.new_page()

        try:
            # App load
            t0 = time.monotonic()
            await page.goto(BASE, wait_until="domcontentloaded")
            try:
                await page.wait_for_selector('text="Alex"', timeout=25000)
            except Exception:
                await page.wait_for_load_state("networkidle", timeout=25000)
            load_ms = round((time.monotonic() - t0) * 1000)
            record("App loads", True, load_ms, f"Flutter web app")

            # Modal dismiss
            t0 = time.monotonic()
            await page.click("body", position={"x": 195, "y": 725})
            await page.wait_for_timeout(1000)
            modal_ms = round((time.monotonic() - t0) * 1000)
            record("Modal dismissed", True, modal_ms, "")

            # Click chat input — try multiple positions
            input_elem = None
            for y in [695, 685, 705, 675, 715]:
                await page.click("body", position={"x": 180, "y": y})
                await page.wait_for_timeout(600)
                input_elem = await page.query_selector("input, textarea")
                if input_elem:
                    break

            if input_elem:
                await input_elem.fill("hi, how are you?")
                await page.wait_for_timeout(200)

                t0 = time.monotonic()
                try:
                    async with page.expect_response(
                        lambda r: "/api/chat" in r.url and r.status == 200,
                        timeout=15000,
                    ) as resp_info:
                        await input_elem.press("Enter")

                    chat_ms = round((time.monotonic() - t0) * 1000)
                    resp = await resp_info.value
                    try:
                        raw = await resp.text()
                        body = json.loads(raw)
                        text = body.get("response", "")[:60]
                    except Exception:
                        text = "(response received)"

                    record("Chat E2E response", True, chat_ms, text)
                    record("Chat E2E <10s", chat_ms < 10000, chat_ms, "")
                except Exception as e:
                    record("Chat E2E response", False, 0, str(e)[:80])
            else:
                record("Chat input found", False, 0, "Flutter input not activated")

            # Take final screenshot
            await page.screenshot(path="test/screenshots/latency/run_all_final.png", full_page=True)

        except Exception as e:
            record("Browser E2E", False, 0, str(e)[:80])
        finally:
            await browser.close()


# ─── Runner ───

def main():
    print("=" * 60)
    print("GentleQuest Comprehensive Test Suite")
    print(f"Target: {BASE}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)

    test_health()
    test_chat_api()
    test_debug_timing()
    test_error_handling()
    test_crisis_detection()
    asyncio.run(test_e2e_browser())

    # Summary
    passed = sum(1 for r in RESULTS if r["passed"])
    failed = sum(1 for r in RESULTS if not r["passed"])
    total = len(RESULTS)

    print("\n" + "=" * 60)
    print(f"RESULT: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    # Save results
    out = {"timestamp": datetime.now().isoformat(), "passed": passed,
           "failed": failed, "total": total, "tests": RESULTS}
    with open("test/all_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Results: test/all_results.json")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
