#!/usr/bin/env python3
"""Cumulative install counter for GentleQuest Stage 1 gate (250 installs).

Aggregates install counts from three sources:

  1. Play Store        — Android Publisher API (statistics) via the
                         service account at ~/Downloads/gentlequest-prod-83ff55c0b550.json.
                         Checks whether the Android Publisher API is enabled for the
                         service account's project; if not, reports the blocker.
  2. App Store         — App Store Connect API. Requires a separate API key
                         (*.p8) in ~/Downloads/. If none is present, reports the
                         blocker. The ASC API does not expose a real-time
                         cumulative-install endpoint; the script authenticates
                         and lists apps to validate the key, then reports the
                         install-count gap honestly.
  3. GA4 web installs  — BetaAnalyticsDataClient against property 551876340 (gentlequestapp).
                         Counts totalUsers with a first_open / session_start
                         event filter, falling back to totalUsers as a proxy.

Output: one line per source (source, count, status), then the running total and
whether the 250-install Stage 1 gate is met.

Exit codes:
  0  — ran to completion (check stdout for per-source status; a source-level
        blocker does NOT make the run fail — the script reports it and continues)
  1  — fatal error (could not run at all, e.g. missing SA key file)

Run:  python3 metrics/install_count.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

# --- Configuration -----------------------------------------------------------

PLAY_SA_KEY = Path.home() / "Downloads" / "gentlequest-prod-83ff55c0b550.json"
PLAY_PACKAGE = "app.gentlequest.www"  # from docs/STORE_DEPLOYMENT.md

ASC_KEY_ID = "L6BQY5DFKM"
ASC_ISSUER_ID = "aa60935b-8c0a-4055-b26f-f44d84c265f7"
ASC_KEY_GLOBS = ("AuthKey_*.p8", "ApiKey_*.p8")
ASC_KEY_DIR = Path.home() / "Downloads"

GA4_PROPERTY = "551876340"  # gentlequestapp GA4 property (created 2026-08-27; old 516568186 = abandoned gentlequest-prod)

STAGE1_GATE = 250


# --- Helpers -----------------------------------------------------------------

def _emit(source: str, count: Optional[int], status: str, blocker: str = "") -> None:
    """Print one structured line for a source."""
    count_str = "n/a" if count is None else str(count)
    line = f"{source:<12} count={count_str:<8} status={status}"
    if blocker:
        line += f"  blocker={blocker}"
    print(line)


# --- Source 1: Play Store (Android Publisher API) ----------------------------

def count_play_store() -> tuple[Optional[int], str, str]:
    """Return (count, status, blocker) for Play Store installs.

    Uses the Android Publisher API statistics endpoint. If the API is not
    enabled for the service account's project, or the SA lacks permission,
    reports the blocker instead of a count.
    """
    if not PLAY_SA_KEY.exists():
        return None, "BLOCKED", f"service account key not found at {PLAY_SA_KEY}"

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        from google.auth.exceptions import GoogleAuthError
    except ImportError as e:
        return None, "BLOCKED", f"missing google client library: {e}"

    try:
        creds = service_account.Credentials.from_service_account_file(
            str(PLAY_SA_KEY),
            scopes=["https://www.googleapis.com/auth/androidpublisher"],
        )
    except (ValueError, GoogleAuthError) as e:
        return None, "BLOCKED", f"could not load service account: {e}"

    try:
        service = build("androidpublisher", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:  # discovery / network failure
        return None, "BLOCKED", f"could not build androidpublisher service: {e}"

    # The Android Publisher API v3 does NOT expose a statistics collection.
    # Introspection of the discovered service confirms the root resources are:
    #   applications, edits, purchases, reviews, inappproducts, monetization,
    #   users, systemapks, ... — there is no `stats` resource.
    # Cumulative install counts are available only via the Play Console UI or
    # the Cloud Storage statistics export, not the public v3 API. We still
    # probe for a `stats` resource so the script stays correct if Apple/Google
    # add one later; if absent, report the real blocker.
    if not hasattr(service, "stats"):
        return (
            None,
            "BLOCKED",
            "Android Publisher API v3 exposes no statistics endpoint "
            "(service has no `stats` resource). Cumulative install counts are "
            "only available via the Play Console UI or the Cloud Storage "
            "statistics export — not the public API. To unblock: enable the "
            "Play Console Cloud Storage statistics export and read the CSV, "
            "or scrape the Play Console UI.",
        )

    try:
        stats = service.stats()  # type: ignore[attr-defined]
        try:
            req = stats.list(
                packageName=PLAY_PACKAGE,
                metrics="install_event",
                dimension="app_version",
                range="lifetime",
            )
        except (AttributeError, TypeError):
            req = stats.get(packageName=PLAY_PACKAGE)  # type: ignore[attr-defined]
        resp = req.execute()
    except HttpError as e:
        status_code = e.resp.status if e.resp is not None else 0
        reason = _http_error_reason(e)
        if status_code in (403, 404):
            return (
                None,
                "BLOCKED",
                f"Android Publisher API not enabled or SA lacks role "
                f"(HTTP {status_code}: {reason}). Enable the API in Google "
                f"Cloud Console for project {creds.project_id} and grant the "
                f"service account the Play Console role, or use the dedicated "
                f"play-store-upload SA.",
            )
        return None, "BLOCKED", f"Android Publisher API HTTP {status_code}: {reason}"
    except Exception as e:
        return None, "BLOCKED", f"Android Publisher API call failed: {e}"

    # Parse the response. The stats response shape varies; pull a total if
    # present, otherwise sum the rows.
    total = _extract_install_total(resp)
    if total is None:
        return None, "BLOCKED", "stats endpoint returned no parseable install count"
    return total, "OK", ""


def _http_error_reason(e) -> str:
    try:
        content = e.content.decode("utf-8") if getattr(e, "content", None) else ""
        if content:
            data = json.loads(content)
            return data.get("error", {}).get("message", str(e))
    except Exception:
        pass
    return str(e)


def _extract_install_total(resp: dict) -> Optional[int]:
    """Best-effort extraction of a cumulative install count from a stats response."""
    if not isinstance(resp, dict):
        return None
    # Some responses carry an explicit total.
    for key in ("totalInstalls", "total_installs", "installs"):
        if key in resp and isinstance(resp[key], (int, float)):
            return int(resp[key])
    rows = resp.get("rows") or resp.get("stats") or []
    if isinstance(rows, list) and rows:
        total = 0
        found = False
        for row in rows:
            # Rows are typically [dimension_values..., metric_values...].
            if isinstance(row, dict):
                for v in row.values():
                    if isinstance(v, (int, float)):
                        total += int(v)
                        found = True
            elif isinstance(row, (list, tuple)) and row:
                try:
                    total += int(row[-1])
                    found = True
                except (ValueError, TypeError):
                    pass
        if found:
            return total
    return None


# --- Source 2: App Store (App Store Connect API) -----------------------------

def count_app_store() -> tuple[Optional[int], str, str]:
    """Return (count, status, blocker) for App Store installs.

    The App Store Connect API does not expose a real-time cumulative install
    count. We authenticate with the .p8 key (validating it works) and report
    the install-count gap as a blocker rather than fabricating a number.
    """
    key_path = _find_asc_key()
    if key_path is None:
        return (
            None,
            "BLOCKED",
            f"no App Store Connect API key (*.p8) found in {ASC_KEY_DIR}",
        )

    try:
        import jwt  # PyJWT
    except ImportError:
        return None, "BLOCKED", "PyJWT not installed (needed to sign ASC JWT)"

    try:
        private_key = key_path.read_bytes()
    except OSError as e:
        return None, "BLOCKED", f"could not read ASC key {key_path}: {e}"

    token = _make_asc_jwt(private_key, jwt)
    if token is None:
        return None, "BLOCKED", "could not sign ASC JWT (key may be malformed)"

    # Validate the key by listing apps. This proves the key works end-to-end.
    ok, apps, err = _asc_list_apps(token)
    if not ok:
        return None, "BLOCKED", f"ASC API auth/list failed: {err}"

    # The ASC API has no cumulative-install endpoint. Sales and Trends reports
    # (the historical source) are delivered as scheduled CSV downloads, not a
    # synchronous count. Report this honestly.
    app_count = len(apps) if isinstance(apps, list) else None
    note = (
        "ASC key valid; API exposes no real-time cumulative install endpoint "
        "(Sales & Trends is scheduled CSV export only). "
        f"Apps visible to key: {app_count}."
    )
    return None, "BLOCKED", note


def _find_asc_key() -> Optional[Path]:
    # Prefer the key file whose name contains the configured key ID — the JWT
    # `kid` header MUST match the actual key, so a name-mismatched .p8 would
    # authenticate as 401 NOT_AUTHORIZED. Fall back to the first sorted match
    # only if no name-matched key exists (e.g. key ID unknown).
    preferred = ASC_KEY_DIR / f"AuthKey_{ASC_KEY_ID}.p8"
    if preferred.exists():
        return preferred
    for glob in ASC_KEY_GLOBS:
        matches = sorted(ASC_KEY_DIR.glob(glob))
        if matches:
            return matches[0]
    return None


def _make_asc_jwt(private_key: bytes, jwt_module) -> Optional[str]:
    try:
        now = int(time.time())
        payload = {
            "iss": ASC_ISSUER_ID,
            "iat": now,
            # Apple rejects tokens with exp >= 20min after iat (clock skew).
            # 1190s = 19:50 stays safely inside the window.
            "exp": now + 1190,
            # Apple requires this exact audience string for the ASC API.
            "aud": "appstoreconnect-v1",
        }
        headers = {"alg": "ES256", "typ": "JWT", "kid": ASC_KEY_ID}
        return jwt_module.encode(payload, private_key, algorithm="ES256", headers=headers)
    except Exception:
        return None


def _asc_list_apps(token: str) -> tuple[bool, Optional[list], str]:
    import urllib.request
    import urllib.error

    url = "https://api.appstoreconnect.apple.com/v1/apps?limit=200"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return True, data.get("data", []), ""
    except urllib.error.HTTPError as e:
        return False, None, f"HTTP {e.code}"
    except Exception as e:
        return False, None, str(e)


# --- Source 3: GA4 web installs ----------------------------------------------

def count_ga4() -> tuple[Optional[int], str, str]:
    """Return (count, status, blocker) for GA4 web installs.

    Counts totalUsers with a first_open / session_start event filter, falling
    back to plain totalUsers as a proxy.
    """
    if not PLAY_SA_KEY.exists():
        return None, "BLOCKED", f"service account key not found at {PLAY_SA_KEY}"

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            DateRange,
            Dimension,
            Filter,
            FilterExpression,
            FilterExpressionList,
            GetMetadataRequest,
            Metric,
            RunReportRequest,
        )
        from google.oauth2 import service_account
    except ImportError as e:
        return None, "BLOCKED", f"missing GA4 client library: {e}"

    try:
        creds = service_account.Credentials.from_service_account_file(
            str(PLAY_SA_KEY),
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
    except Exception as e:
        return None, "BLOCKED", f"could not load service account for GA4: {e}"

    client = BetaAnalyticsDataClient(credentials=creds)

    def _run(event_filter: Optional[FilterExpression]) -> Optional[int]:
        request = RunReportRequest(
            property=f"properties/{GA4_PROPERTY}",
            date_ranges=[DateRange(start_date="2020-01-01", end_date="today")],
            metrics=[Metric(name="totalUsers")],
            dimension_filter=event_filter,
        )
        report = client.run_report(request)
        if report.rows:
            return int(report.rows[0].metric_values[0].value)
        return None

    # Try event-filtered counts first (first_open, then session_start).
    for event_name in ("first_open", "session_start"):
        try:
            expr = FilterExpression(
                filter=Filter(
                    field_name="eventName",
                    string_filter=Filter.StringFilter(value=event_name),
                )
            )
            n = _run(expr)
            if n is not None:
                return n, "OK", f"totalUsers filtered by {event_name}"
        except Exception:
            continue

    # Fallback: plain totalUsers as a proxy.
    try:
        n = _run(None)
        if n is not None:
            return n, "OK", "totalUsers (proxy, no event filter)"
        return None, "BLOCKED", "GA4 returned no rows for totalUsers"
    except Exception as e:
        return None, "BLOCKED", f"GA4 report failed: {e}"


# --- Main --------------------------------------------------------------------

def main() -> int:
    print(f"GentleQuest cumulative install count — Stage 1 gate: {STAGE1_GATE}")
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("-" * 72)

    if not PLAY_SA_KEY.exists():
        print(f"FATAL: service account key missing at {PLAY_SA_KEY}", file=sys.stderr)
        return 1

    results: list[tuple[str, Optional[int], str, str]] = []

    for source, fn in (
        ("Play Store", count_play_store),
        ("App Store", count_app_store),
        ("GA4 web", count_ga4),
    ):
        try:
            count, status, blocker = fn()
        except Exception as e:
            count, status, blocker = None, "BLOCKED", f"unexpected error: {e}"
        _emit(source, count, status, blocker)
        results.append((source, count, status, blocker))

    print("-" * 72)

    available = [c for _, c, s, _ in results if c is not None and s == "OK"]
    total = sum(available)
    blocked = [s for _, _, s, b in results if s == "BLOCKED" and b]

    print(f"Total (sum of available sources): {total}")
    print(f"Stage 1 gate ({STAGE1_GATE} installs): {'MET' if total >= STAGE1_GATE else 'NOT MET'}")
    if blocked:
        print(f"Blocked sources: {len(blocked)} — counts above are partial.")
    print(
        "Note: counts are cumulative per available source. Blocked sources "
        "contribute 0 to the total; resolve blockers for a complete count."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
