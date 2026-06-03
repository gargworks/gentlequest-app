#!/usr/bin/env python3
"""Submit an App Store Version for Apple's review (irreversible).

Three-step flow per App Store Connect API:
    1. POST  /v1/reviewSubmissions             — create container (per platform)
    2. POST  /v1/reviewSubmissionItems         — attach version as item
    3. PATCH /v1/reviewSubmissions/{id}        — set submitted=true (fires review)

Usage:
    python3 scripts/asc_submit_for_review.py \\
        --app-id 6756537464 \\
        --version-id <APP_STORE_VERSION_UUID> \\
        --platform IOS

Pre-flight requires appStoreState == PREPARE_FOR_SUBMISSION.

Pre-reqs:
    ~/.appstoreconnect/private_keys/AuthKey_<KEY_ID>.p8 (mode 600)
    ~/.appstoreconnect/issuer_id.txt                    (mode 600)

Reference: docs/release/MANUAL_RELEASE_PLAYBOOK.md §2.8
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    import jwt
except ImportError:
    print("ERROR: pyjwt not installed. Install: pip3 install pyjwt", file=sys.stderr)
    sys.exit(2)

KEY_ID = os.environ.get("ASC_KEY_ID", "L6BQY5DFKM")
ISSUER_ID_FILE = Path.home() / ".appstoreconnect" / "issuer_id.txt"


def _token() -> str:
    issuer_id = ISSUER_ID_FILE.read_text().strip()
    key_path = (Path.home() / ".appstoreconnect" / "private_keys" / f"AuthKey_{KEY_ID}.p8")
    now = int(time.time())
    return jwt.encode(
        {"iss": issuer_id, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
        key_path.read_text(),
        algorithm="ES256",
        headers={"kid": KEY_ID, "typ": "JWT"},
    )


def _call(path: str, *, method: str = "GET", body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {_token()}"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"https://api.appstoreconnect.apple.com/v1/{path}",
        headers=headers,
        method=method,
        data=data,
    )
    try:
        with urllib.request.urlopen(req) as r:
            s = r.read().decode()
            return json.loads(s) if s.strip() else {"_ok": True, "_status": r.status}
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode()[:2000]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--app-id", required=True, help="ASC app numeric ID (e.g., 6756537464)")
    p.add_argument("--version-id", required=True, help="appStoreVersion UUID to submit")
    p.add_argument("--platform", default="IOS", choices=["IOS", "MAC_OS", "TV_OS"], help="Target platform")
    p.add_argument("--force", action="store_true", help="Skip pre-flight state check")
    args = p.parse_args()

    # Pre-flight
    print("=== Pre-flight ===", flush=True)
    v = _call(f"appStoreVersions/{args.version_id}")
    if "_err" in v:
        raise SystemExit(f"Could not load version: {v}")
    state = v["data"]["attributes"].get("appStoreState")
    version = v["data"]["attributes"].get("versionString")
    print(f"  v{version} state={state}", flush=True)
    if state != "PREPARE_FOR_SUBMISSION" and not args.force:
        raise SystemExit(f"Expected PREPARE_FOR_SUBMISSION, got {state}. Use --force to override.")

    # Step 1
    print("\n=== Step 1: Create reviewSubmission ===", flush=True)
    rs = _call("reviewSubmissions", method="POST", body={
        "data": {
            "type": "reviewSubmissions",
            "attributes": {"platform": args.platform},
            "relationships": {"app": {"data": {"type": "apps", "id": args.app_id}}},
        }
    })
    if "_err" in rs:
        # If a non-COMPLETE submission already exists, try to reuse it
        print(f"  Create failed: {rs}", flush=True)
        listv = _call(f"apps/{args.app_id}/reviewSubmissions?limit=10")
        rs_id = None
        for d in listv.get("data", []):
            if d["attributes"].get("state") in ("READY_FOR_REVIEW", "INCOMPLETE", "UNRESOLVED_ISSUES"):
                rs_id = d["id"]
                print(f"  Reusing existing reviewSubmission id={rs_id} state={d['attributes'].get('state')}", flush=True)
                break
        if not rs_id:
            raise SystemExit(f"Could not create or reuse submission. List: {listv}")
    else:
        rs_id = rs["data"]["id"]
        print(f"  Created reviewSubmission id={rs_id}", flush=True)

    # Step 2
    print(f"\n=== Step 2: Add version to submission ===", flush=True)
    rsi = _call("reviewSubmissionItems", method="POST", body={
        "data": {
            "type": "reviewSubmissionItems",
            "relationships": {
                "reviewSubmission": {"data": {"type": "reviewSubmissions", "id": rs_id}},
                "appStoreVersion": {"data": {"type": "appStoreVersions", "id": args.version_id}},
            },
        }
    })
    if "_err" in rsi:
        if rsi.get("_err") == 409:
            print(f"  Item already exists in submission (409): proceeding", flush=True)
        else:
            raise SystemExit(f"Add item failed: {rsi}")
    else:
        print(f"  Item added id={rsi['data']['id']}", flush=True)

    # Step 3 (IRREVERSIBLE)
    print(f"\n=== Step 3: Fire submit (IRREVERSIBLE) ===", flush=True)
    submit = _call(f"reviewSubmissions/{rs_id}", method="PATCH", body={
        "data": {
            "type": "reviewSubmissions",
            "id": rs_id,
            "attributes": {"submitted": True},
        }
    })
    if "_err" in submit:
        raise SystemExit(f"SUBMIT FAILED: {submit}")
    a = submit.get("data", {}).get("attributes", {})
    print(f"  ✓ SUBMITTED state={a.get('state')} submittedDate={a.get('submittedDate')}", flush=True)

    # Verify
    print(f"\n=== Verify version state ===", flush=True)
    v2 = _call(f"appStoreVersions/{args.version_id}")
    final_state = v2["data"]["attributes"].get("appStoreState")
    print(f"  v{version} state={final_state}", flush=True)
    return 0 if final_state == "WAITING_FOR_REVIEW" else 4


if __name__ == "__main__":
    sys.exit(main())
