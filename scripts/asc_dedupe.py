#!/usr/bin/env python3
"""Deduplicate App Store screenshots within a single set by fileName.

Apple's auto-clone-from-previous-version occasionally re-fires *after*
your DELETE+upload race, leaving multiple screenshots with the same
fileName. This script keeps the newest (createdDate desc) of each
fileName and deletes the rest.

Usage:
    python3 scripts/asc_dedupe.py --set-id <APP_SCREENSHOT_SET_UUID>
    python3 scripts/asc_dedupe.py --version-id <VERSION_UUID> --set iphone67

Reference: docs/release/MANUAL_RELEASE_PLAYBOOK.md §4.3
"""
from __future__ import annotations

import argparse
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

DISPLAY_TYPES = {
    "iphone67": "APP_IPHONE_67",
    "ipad129": "APP_IPAD_PRO_3GEN_129",
    "ipad11": "APP_IPAD_PRO_129",
}


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


def _call(path: str, *, method: str = "GET") -> dict:
    req = urllib.request.Request(
        f"https://api.appstoreconnect.apple.com/v1/{path}",
        headers={"Authorization": f"Bearer {_token()}"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as r:
            s = r.read().decode()
            return json.loads(s) if s.strip() else {"_ok": True, "_status": r.status}
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode()[:500]}


def _resolve_set_id(args: argparse.Namespace) -> str:
    if args.set_id:
        return args.set_id
    sets = _call(f"appStoreVersions/{args.version_id}/appScreenshotSets?limit=20")
    target = DISPLAY_TYPES[args.set]
    for s in sets.get("data", []):
        if s["attributes"].get("screenshotDisplayType") == target:
            return s["id"]
    raise SystemExit(f"No set of type {target} on version {args.version_id}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--set-id", help="Direct set UUID")
    grp.add_argument("--version-id", help="Version UUID (combine with --set)")
    p.add_argument("--set", choices=list(DISPLAY_TYPES), help="Display type alias (with --version-id)")
    p.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    args = p.parse_args()

    if args.version_id and not args.set:
        raise SystemExit("--version-id requires --set")

    set_id = _resolve_set_id(args)
    print(f"=== Dedupe set {set_id} ===", flush=True)

    shots = _call(f"appScreenshotSets/{set_id}/appScreenshots?limit=20")
    if "_err" in shots:
        raise SystemExit(f"List failed: {shots}")

    groups: dict[str, list] = defaultdict(list)
    for s in shots.get("data", []):
        groups[s["attributes"].get("fileName")].append(s)

    n_dupes = 0
    for name, group in sorted(groups.items()):
        marker = " (DUP)" if len(group) > 1 else ""
        print(f"  {name}: {len(group)} entries{marker}", flush=True)
        if len(group) > 1:
            group.sort(key=lambda x: x["attributes"].get("createdDate", ""), reverse=True)
            for dup in group[1:]:
                n_dupes += 1
                if args.dry_run:
                    print(f"    DRY-RUN would delete: {dup['id']} (created {dup['attributes'].get('createdDate')})", flush=True)
                else:
                    r = _call(f"appScreenshots/{dup['id']}", method="DELETE")
                    print(f"    DELETE {dup['id']}: {r}", flush=True)

    print(f"\n{'Would delete' if args.dry_run else 'Deleted'} {n_dupes} duplicate(s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
