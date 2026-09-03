#!/usr/bin/env python3
"""Upload an AAB to the Google Play INTERNAL track.

Internal track only, by construction. This script cannot promote to
production: PRODUCTION_IS_NOT_A_TARGET below is the whole point. Promotion is
an operator decision made in the Play Console, not something a script should be
able to do by passing a different string.

Written 2026-09-03 after doing this by hand twice. Both hand-runs hit avoidable
failures worth recording, because a future reader will hit them too:

  * `bundles().insert(...)` does not exist. The method is `bundles().upload()`.
  * Play rejects the COMMIT, not the upload, when targetSdk is too low:
      403 "Target SDK of artifact is too low: <versionCode>"
    The bundle uploads fine and the track is set, so a naive script looks like
    it succeeded right up until the last call. Nothing is published.

Credential: a service account with the Play Developer API enabled AND an
account-level permission grant in the Play Console. Those are two different
things and each fails with its own 403 — see the error handler at the bottom.

Usage:
    python3 scripts/play_upload_internal.py --aab path/to/app-release.aab \
        --sa ~/path/play-store-upload.json
"""
from __future__ import annotations

import argparse
import sys

PACKAGE_NAME = "app.gentlequest.www"
TRACK = "internal"
PRODUCTION_IS_NOT_A_TARGET = True  # see module docstring


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--aab", required=True)
    ap.add_argument("--sa", required=True, help="service-account JSON path")
    ap.add_argument("--package", default=PACKAGE_NAME)
    args = ap.parse_args()

    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError

    creds = service_account.Credentials.from_service_account_file(
        args.sa, scopes=["https://www.googleapis.com/auth/androidpublisher"]
    )
    svc = build("androidpublisher", "v3", credentials=creds, cache_discovery=False)

    try:
        edit = svc.edits().insert(body={}, packageName=args.package).execute()
        edit_id = edit["id"]

        # upload(), NOT insert(). resumable matters: an AAB is ~86MB.
        bundle = (
            svc.edits()
            .bundles()
            .upload(
                editId=edit_id,
                packageName=args.package,
                media_body=MediaFileUpload(
                    args.aab,
                    mimetype="application/octet-stream",
                    resumable=True,
                ),
            )
            .execute()
        )
        version_code = bundle["versionCode"]
        print(f"uploaded versionCode {version_code}")

        svc.edits().tracks().update(
            editId=edit_id,
            track=TRACK,
            packageName=args.package,
            body={
                "releases": [
                    {"versionCodes": [str(version_code)], "status": "completed"}
                ]
            },
        ).execute()
        print(f"track '{TRACK}' set to {version_code}")

        # The gate that actually publishes. targetSdk failures surface HERE.
        svc.edits().commit(editId=edit_id, packageName=args.package).execute()
        print(f"COMMITTED: {version_code} live on '{TRACK}'")
        return 0

    except HttpError as e:
        detail = e.content.decode() if isinstance(e.content, bytes) else str(e.content)
        print(f"Play API error {e.resp.status}: {detail}", file=sys.stderr)
        if e.resp.status == 403:
            print(
                "\n403 has two unrelated causes; check BOTH:\n"
                "  1. Google Play Android Developer API not enabled on the "
                "service account's PROJECT (fix in Cloud Console)\n"
                "  2. the service account has no permission grant in the Play "
                "Console (fix in Play Console > Users and permissions)\n"
                "  ...and 'Target SDK of artifact is too low' is a THIRD, "
                "unrelated 403 that appears only at commit time.",
                file=sys.stderr,
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
