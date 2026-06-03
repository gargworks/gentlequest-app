#!/usr/bin/env python3
"""Replace an App Store Version's screenshot set with local PNGs.

Usage:
    python3 scripts/asc_screenshot_swap.py \\
        --version-id <APP_STORE_VERSION_UUID> \\
        --set iphone67 \\
        --src app_store_assets/v1.3.0/screenshots

Sets:
    iphone67  -> APP_IPHONE_67     (1290 x 2796)
    ipad129   -> APP_IPAD_PRO_3GEN_129 (2048 x 2732)
    ipad11    -> APP_IPAD_PRO_129  (2388 x 1668 etc.)

Pre-reqs:
    ~/.appstoreconnect/private_keys/AuthKey_<KEY_ID>.p8 (mode 600)
    ~/.appstoreconnect/issuer_id.txt                    (mode 600)

Behaviour:
    1. Lists existing screenshots in the target set
    2. DELETEs every existing entry
    3. Uploads each PNG in --src directory (sorted alphabetically)
    4. Dedupes by fileName afterward (Apple's auto-clone race)
    5. Verifies every fileName's sourceFileChecksum matches local MD5

Reference: docs/release/MANUAL_RELEASE_PLAYBOOK.md §4
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

try:
    import jwt
except ImportError:
    print("ERROR: pyjwt not installed. Install: pip3 install pyjwt", file=sys.stderr)
    sys.exit(2)

KEY_ID = os.environ.get("ASC_KEY_ID", "L6BQY5DFKM")
ISSUER_ID_FILE = Path.home() / ".appstoreconnect" / "issuer_id.txt"
KEY_FILE_TPL = "~/.appstoreconnect/private_keys/AuthKey_{key_id}.p8"

DISPLAY_TYPES = {
    "iphone67": "APP_IPHONE_67",
    "ipad129": "APP_IPAD_PRO_3GEN_129",
    "ipad11": "APP_IPAD_PRO_129",
}


def _token() -> str:
    issuer_id = ISSUER_ID_FILE.read_text().strip()
    key_path = Path(KEY_FILE_TPL.format(key_id=KEY_ID)).expanduser()
    private_key = key_path.read_text()
    now = int(time.time())
    return jwt.encode(
        {"iss": issuer_id, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
        private_key,
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
            if not s.strip():
                return {"_ok": True, "_status": r.status}
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return {"_ok": True, "_status": r.status, "_body": s[:300]}
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode()[:1500]}


def _find_set_id(version_id: str, display_type: str) -> str:
    sets = _call(f"appStoreVersions/{version_id}/appScreenshotSets?limit=20")
    if "_err" in sets:
        raise SystemExit(f"Could not list screenshot sets: {sets}")
    for s in sets.get("data", []):
        if s["attributes"].get("screenshotDisplayType") == display_type:
            return s["id"]
    # Set doesn't exist yet — create it
    print(f"Set {display_type} not found; creating", flush=True)
    res = _call("appScreenshotSets", method="POST", body={
        "data": {
            "type": "appScreenshotSets",
            "attributes": {"screenshotDisplayType": display_type},
            "relationships": {
                "appStoreVersionLocalization": {"data": {"type": "appStoreVersionLocalizations", "id": _en_us_loc(version_id)}}
            },
        }
    })
    if "_err" in res:
        raise SystemExit(f"Could not create set: {res}")
    return res["data"]["id"]


def _en_us_loc(version_id: str) -> str:
    locs = _call(f"appStoreVersions/{version_id}/appStoreVersionLocalizations?limit=10")
    for l in locs.get("data", []):
        if l["attributes"].get("locale") == "en-US":
            return l["id"]
    raise SystemExit("No en-US localization found on version")


def _delete_existing(set_id: str) -> None:
    shots = _call(f"appScreenshotSets/{set_id}/appScreenshots?limit=20")
    for s in shots.get("data", []):
        r = _call(f"appScreenshots/{s['id']}", method="DELETE")
        print(f"  DELETE {s['id']} ({s['attributes'].get('fileName')}): {r}", flush=True)


def _upload_one(set_id: str, path: Path) -> str | None:
    content = path.read_bytes()
    sz = len(content)
    md5 = hashlib.md5(content).hexdigest()
    print(f"\n--- {path.name} ({sz} bytes, md5 {md5[:8]}...) ---", flush=True)

    res = _call("appScreenshots", method="POST", body={
        "data": {
            "type": "appScreenshots",
            "attributes": {"fileName": path.name, "fileSize": sz},
            "relationships": {"appScreenshotSet": {"data": {"type": "appScreenshotSets", "id": set_id}}},
        }
    })
    if "_err" in res:
        print(f"  RESERVE FAIL: {res}", flush=True)
        return None

    sid = res["data"]["id"]
    ops = res["data"]["attributes"].get("uploadOperations", [])
    print(f"  reserved id={sid} ops={len(ops)}", flush=True)

    for op in ops:
        chunk = content[op["offset"]: op["offset"] + op["length"]]
        req_headers = {h["name"]: h["value"] for h in op.get("requestHeaders", [])}
        req = urllib.request.Request(op["url"], data=chunk, method=op["method"], headers=req_headers)
        try:
            with urllib.request.urlopen(req):
                pass
            print(f"    {op['method']} offset={op['offset']} len={op['length']} OK", flush=True)
        except urllib.error.HTTPError as e:
            print(f"    {op['method']} offset={op['offset']} FAIL {e.code}: {e.read()[:200]}", flush=True)
            return None

    final = _call(f"appScreenshots/{sid}", method="PATCH", body={
        "data": {
            "type": "appScreenshots",
            "id": sid,
            "attributes": {"uploaded": True, "sourceFileChecksum": md5},
        }
    })
    if "_err" in final:
        print(f"  FINALIZE FAIL: {final}", flush=True)
        return None
    state = final.get("data", {}).get("attributes", {}).get("assetDeliveryState", {}).get("state", "?")
    print(f"  FINALIZED id={sid} state={state}", flush=True)
    return sid


def _dedupe_by_name(set_id: str) -> None:
    shots = _call(f"appScreenshotSets/{set_id}/appScreenshots?limit=20")
    groups: dict[str, list] = defaultdict(list)
    for s in shots.get("data", []):
        groups[s["attributes"].get("fileName")].append(s)
    for name, group in groups.items():
        if len(group) > 1:
            group.sort(key=lambda x: x["attributes"].get("createdDate", ""), reverse=True)
            for dup in group[1:]:
                r = _call(f"appScreenshots/{dup['id']}", method="DELETE")
                print(f"  DEDUPE DELETE {dup['id']} ({name}): {r}", flush=True)


def _verify(set_id: str, expected_md5: dict[str, str]) -> bool:
    shots = _call(f"appScreenshotSets/{set_id}/appScreenshots?limit=20")
    all_match = True
    for s in shots.get("data", []):
        a = s["attributes"]
        name = a.get("fileName")
        chk = a.get("sourceFileChecksum")
        exp = expected_md5.get(name)
        match = chk == exp
        if not match:
            all_match = False
        print(f"  {name}: chk={(chk or '')[:16]}...  expected={(exp or '')[:16]}...  match={'YES' if match else 'NO'}", flush=True)
    return all_match


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--version-id", required=True, help="ASC appStoreVersion UUID")
    p.add_argument("--set", required=True, choices=list(DISPLAY_TYPES), help="Display type alias")
    p.add_argument("--src", required=True, help="Directory of PNGs to upload (sorted alpha)")
    p.add_argument("--skip-delete", action="store_true", help="Skip deleting existing (additive)")
    args = p.parse_args()

    src = Path(args.src)
    if not src.is_dir():
        raise SystemExit(f"--src must be a directory: {src}")
    files = sorted(src.glob("*.png"))
    if not files:
        raise SystemExit(f"No PNGs found in {src}")

    display_type = DISPLAY_TYPES[args.set]
    set_id = _find_set_id(args.version_id, display_type)
    print(f"=== Target set: {display_type} id={set_id} ===", flush=True)

    if not args.skip_delete:
        print(f"\n=== Step 1: Delete existing screenshots ===", flush=True)
        _delete_existing(set_id)

    print(f"\n=== Step 2: Upload {len(files)} new screenshots ===", flush=True)
    expected_md5 = {}
    for f in files:
        expected_md5[f.name] = hashlib.md5(f.read_bytes()).hexdigest()
        _upload_one(set_id, f)

    print(f"\n=== Step 3: Dedupe (Apple auto-clone race) ===", flush=True)
    _dedupe_by_name(set_id)

    print(f"\n=== Step 4: Verify checksums ===", flush=True)
    ok = _verify(set_id, expected_md5)
    print(f"\nAll match: {ok}", flush=True)
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
