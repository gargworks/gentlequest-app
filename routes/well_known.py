"""
/.well-known/ universal-link verification documents.

iOS Universal Links + Android App Links require the OS to download a small
JSON document from the claimed domain over HTTPS before it will route taps
on https://gentlequest.app/... directly into the app instead of the browser.
That cryptographic-proof step is what closes the same-device hijack window
where a malicious app could otherwise register `gentlequest://` and steal
the magic-link token.

Endpoints:
  GET /.well-known/apple-app-site-association   (iOS — JSON, no .json suffix)
  GET /.well-known/assetlinks.json              (Android — JSON)

Both endpoints read identity values (team-id, bundle-id, package-name,
SHA-256 fingerprint) from env vars so we don't bake secrets into the repo
and so non-prod environments can serve their own variants. If the required
env vars are missing the endpoint returns 503 with an explicit error code
rather than 200-ing a broken document — silently serving garbage would let
verification fail in the field with zero telemetry.

Env vars (set on Render):
  IOS_TEAM_ID                 e.g. "ABCDE12345"
  IOS_BUNDLE_ID               e.g. "app.gentlequest.gentlequest"  (default)
  ANDROID_PACKAGE_NAME        e.g. "com.gentlequest.app"
  ANDROID_SHA256_FINGERPRINT  e.g. "14:6D:E9:...:5F"  (release keystore)

See docs/release/UNIVERSAL_LINKS_SETUP.md for the operator runbook.
"""

from __future__ import annotations

import os

from flask import Blueprint, jsonify


well_known_bp = Blueprint("well_known", __name__)


_DEFAULT_IOS_BUNDLE_ID = "app.gentlequest.gentlequest"


@well_known_bp.route("/.well-known/apple-app-site-association", methods=["GET"])
def apple_app_site_association():
    """Serve iOS Universal Links verification JSON.

    Apple dropped the application/pkcs7-mime requirement years ago — plain
    application/json with no .json suffix is the modern contract.
    """
    team_id = os.getenv("IOS_TEAM_ID", "").strip()
    bundle_id = os.getenv("IOS_BUNDLE_ID", _DEFAULT_IOS_BUNDLE_ID).strip()

    if not team_id or not bundle_id:
        response = jsonify({"error": "universal_links_not_configured"})
        response.status_code = 503
        return response

    payload = {
        "applinks": {
            "details": [
                {
                    "appIDs": [f"{team_id}.{bundle_id}"],
                    "components": [
                        {"/": "/auth/*"},
                    ],
                }
            ]
        }
    }

    response = jsonify(payload)
    response.headers["Content-Type"] = "application/json"
    return response


@well_known_bp.route("/.well-known/assetlinks.json", methods=["GET"])
def assetlinks_json():
    """Serve Android App Links verification JSON.

    Returns a JSON array (Android spec) — top-level is a list, not an
    object — declaring the `delegate_permission/common.handle_all_urls`
    relation to the named Android package + signing-cert fingerprint.
    """
    package_name = os.getenv("ANDROID_PACKAGE_NAME", "").strip()
    fingerprint = os.getenv("ANDROID_SHA256_FINGERPRINT", "").strip()

    if not package_name or not fingerprint:
        response = jsonify({"error": "universal_links_not_configured"})
        response.status_code = 503
        return response

    payload = [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": package_name,
                "sha256_cert_fingerprints": [fingerprint],
            },
        }
    ]

    response = jsonify(payload)
    response.headers["Content-Type"] = "application/json"
    return response
