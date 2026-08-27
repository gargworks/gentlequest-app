"""Native-only GA4 D1/D7/D14 retention gate collector.

This module is intentionally self-contained: no import-time network work, no
checked-in credential files, and no marketing/web traffic in the canonical
verdict.  The canonical population is iOS + Android; web is reported as
excluded.

The google-analytics-data client libraries are wrapped in an import guard so
that the module can be imported in environments without the package (e.g. when
only the bot-filter rules from ``scripts/analytics_dashboard`` are needed).
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

try:  # pragma: no cover - optional dependency guard
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Metric,
        RunReportRequest,
    )
    from google.api_core import exceptions as google_exceptions
    from google.auth import default, load_credentials_from_file
    from google.oauth2 import service_account
except ImportError:  # pragma: no cover - optional dependency guard
    BetaAnalyticsDataClient = None  # type: ignore[assignment,misc]
    DateRange = None  # type: ignore[assignment,misc]
    Dimension = None  # type: ignore[assignment,misc]
    Metric = None  # type: ignore[assignment,misc]
    RunReportRequest = None  # type: ignore[assignment,misc]
    google_exceptions = None  # type: ignore[assignment,misc]
    default = None  # type: ignore[assignment,misc]
    load_credentials_from_file = None  # type: ignore[assignment,misc]
    service_account = None  # type: ignore[assignment,misc]

logger = logging.getLogger("d14_cohort_ga4")

ANALYTICS_READONLY_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
# GA4 property for the gentlequestapp Firebase project (315814630048),
# created + linked 2026-08-27. The previous value, 516568186, belonged to
# the ABANDONED gentlequest-prod project — its native app data froze at
# v1.3.1 while the app shipped 1.7.x, so querying it produced
# plausible-looking numbers about the wrong population. If this default
# ever goes stale again, prefer deleting it over updating it: an explicit
# GQ_GA_PROPERTY_ID env var is the honest configuration.
DEFAULT_PROPERTY_ID = "551876340"
DEFAULT_MIN_N = 40
DEFAULT_PASS_THRESHOLD = 0.15
DEFAULT_KILL_THRESHOLD = 0.07
NATIVE_PLATFORMS = {"iOS", "Android"}
WEB_PLATFORM = "Web"


class GateError(Exception):
    """Structured, non-secret error produced by the gate collector."""

    def __init__(self, reason: str, message: Optional[str] = None):
        self.reason = reason
        self.message = message or reason
        super().__init__(self.message)


def _resolve_credentials():
    """Resolve scoped GA4 Viewer credentials without logging secrets.

    Resolution order (first wins):
      1. GQ_GA_SA_JSON - inline service-account JSON (plaintext or base64).
      2. GQ_GA_SA_PATH - product-specific credential file.
      3. GOOGLE_APPLICATION_CREDENTIALS / ADC with explicit analytics.readonly
         scope.  File credentials are not assumed to be service-account keys.
    """
    env_json = os.environ.get("GQ_GA_SA_JSON")
    if env_json:
        try:
            raw = env_json.strip()
            if raw.startswith("{"):
                info = json.loads(raw)
            else:
                info = json.loads(base64.b64decode(raw).decode("utf-8"))
            return service_account.Credentials.from_service_account_info(
                info, scopes=(ANALYTICS_READONLY_SCOPE,)
            )
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            raise GateError("malformed_service_account_json") from exc

    path = os.environ.get("GQ_GA_SA_PATH")
    if not path:
        path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    if path:
        try:
            credentials, _ = load_credentials_from_file(
                path, scopes=(ANALYTICS_READONLY_SCOPE,)
            )
            return credentials
        except (ValueError, OSError) as exc:
            raise GateError("credentials_file_unusable") from exc

    try:
        credentials, _ = default(scopes=(ANALYTICS_READONLY_SCOPE,))
        return credentials
    except Exception as exc:
        raise GateError("credentials_missing") from exc


def _build_client(credentials) -> BetaAnalyticsDataClient:
    return BetaAnalyticsDataClient(credentials=credentials)


def build_ga4_client() -> BetaAnalyticsDataClient:
    """Public helper used by ``scripts/analytics_dashboard.py`` and tests.

    Raises ``GateError`` with a machine-readable ``reason`` on credential or
    environment issues.  Never logs or returns secret material.
    """
    if BetaAnalyticsDataClient is None:
        raise GateError("google_analytics_unavailable")
    credentials = _resolve_credentials()
    return _build_client(credentials)


def _canonical_platform(raw: str) -> str:
    lower = (raw or "").strip().lower()
    if lower == "ios":
        return "iOS"
    if lower == "android":
        return "Android"
    if lower == "web":
        return "Web"
    return raw


def _fetch_rows(
    client: BetaAnalyticsDataClient,
    property_id: str,
    activity_start: date,
    activity_end: date,
    acquisition_start: date,
    acquisition_end: date,
) -> List[Tuple[date, date, str, int]]:
    """Fetch activeUsers by firstSessionDate, date, and platform.

    The GA4 `date` range covers activity from `activity_start` through
    `activity_end` (the latest complete analytics day).  We then filter to the
    acquisition window in code, keeping the request simple and avoiding
    unsupported date-dimension filters.
    """
    if BetaAnalyticsDataClient is None or RunReportRequest is None:
        raise GateError("google_analytics_unavailable")

    rows: List[Tuple[date, date, str, int]] = []
    offset = 0
    limit = 100_000

    while True:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[
                Dimension(name="firstSessionDate"),
                Dimension(name="date"),
                Dimension(name="platform"),
            ],
            metrics=[Metric(name="activeUsers")],
            date_ranges=[
                DateRange(
                    start_date=activity_start.isoformat(),
                    end_date=activity_end.isoformat(),
                )
            ],
            limit=limit,
            offset=offset,
        )
        try:
            response = client.run_report(request)
        except google_exceptions.Unauthenticated as exc:
            raise GateError("authentication_failed") from exc
        except google_exceptions.Forbidden as exc:
            raise GateError("permission_denied") from exc
        except (
            google_exceptions.DeadlineExceeded,
            google_exceptions.ServiceUnavailable,
            google_exceptions.InternalServerError,
        ) as exc:
            raise GateError("upstream_unavailable") from exc
        except google_exceptions.InvalidArgument as exc:
            raise GateError("invalid_request") from exc
        except google_exceptions.GoogleAPIError as exc:
            raise GateError("upstream_unavailable") from exc
        except Exception as exc:
            # RefreshError / DefaultCredentialsError surface as google.auth
            # exceptions, not GoogleAPIError.  Classify auth-ish failures.
            module = type(exc).__module__.lower()
            name = type(exc).__name__.lower()
            if "auth" in module or "credential" in name or "refresh" in name:
                raise GateError("authentication_failed") from exc
            raise GateError("unexpected_error") from exc

        if not response.rows:
            break

        for row in response.rows:
            first_session_date = date.fromisoformat(row.dimension_values[0].value)
            activity_date = date.fromisoformat(row.dimension_values[1].value)
            platform = _canonical_platform(row.dimension_values[2].value)
            active_users = int(row.metric_values[0].value)

            if first_session_date < acquisition_start or first_session_date > acquisition_end:
                continue

            rows.append((first_session_date, activity_date, platform, active_users))

        returned_so_far = offset + len(response.rows)
        if response.row_count <= returned_so_far:
            break
        offset = returned_so_far

        if offset >= 200_000:
            logger.warning("Hit hard pagination limit for GA4 retention report")
            break

    return rows


def _build_platform_stats(
    rows: List[Tuple[date, date, str, int]],
    acquisition_start: date,
    acquisition_end: date,
    report_day: date,
    window_end: date,
) -> Dict[str, Dict[str, Any]]:
    """Aggregate rows into per-platform totals and D1/D7/D14 stats.

    Each offset metric uses only its offset-eligible subcohort:
    firstSessionDate <= min(window_end, report_day - offset).
    """
    data: Dict[Tuple[str, date, date], int] = {}
    for first_session_date, activity_date, platform, active_users in rows:
        data[(platform, first_session_date, activity_date)] = active_users

    platforms = sorted({key[0] for key in data})
    stats: Dict[str, Dict[str, Any]] = {}

    for platform in platforms:
        # All first-session dates in the acquisition window for this platform.
        first_session_dates = sorted(
            {
                fs
                for plat, fs, _ in data
                if plat == platform and acquisition_start <= fs <= acquisition_end
            }
        )

        total_n = 0
        for fs in first_session_dates:
            total_n += data.get((platform, fs, fs), 0)

        offset_stats: Dict[str, Dict[str, Any]] = {}
        for offset in (1, 7, 14):
            eligible_end = min(window_end, report_day - timedelta(days=offset))
            if eligible_end < acquisition_start:
                eligible_n = 0
                returned = 0
            else:
                eligible_fs = [
                    fs for fs in first_session_dates if fs <= eligible_end
                ]
                eligible_n = 0
                returned = 0
                for fs in eligible_fs:
                    eligible_n += data.get((platform, fs, fs), 0)
                    returned += data.get(
                        (platform, fs, fs + timedelta(days=offset)), 0
                    )
            rate = round(returned / eligible_n, 4) if eligible_n > 0 else 0.0
            offset_name = f"d{offset}"
            offset_stats[offset_name] = {
                "eligible_n": eligible_n,
                "returned": returned,
                "rate": rate,
            }

        stats[platform] = {
            "total_n": total_n,
            "d1": offset_stats["d1"],
            "d7": offset_stats["d7"],
            "d14": offset_stats["d14"],
        }

    return stats


def _empty_platform() -> Dict[str, Any]:
    return {
        "total_n": 0,
        "d1": {"eligible_n": 0, "returned": 0, "rate": 0.0},
        "d7": {"eligible_n": 0, "returned": 0, "rate": 0.0},
        "d14": {"eligible_n": 0, "returned": 0, "rate": 0.0},
    }


def _native_stats(
    platform_stats: Dict[str, Dict[str, Any]]
) -> Tuple[int, Dict[str, Dict[str, Any]]]:
    """Sum iOS + Android stats into a native aggregate."""
    total_n = 0
    native = {
        "d1": {"eligible_n": 0, "returned": 0, "rate": 0.0},
        "d7": {"eligible_n": 0, "returned": 0, "rate": 0.0},
        "d14": {"eligible_n": 0, "returned": 0, "rate": 0.0},
    }
    for platform in NATIVE_PLATFORMS:
        p = platform_stats.get(platform)
        if not p:
            continue
        total_n += p["total_n"]
        for offset in ("d1", "d7", "d14"):
            native[offset]["eligible_n"] += p[offset]["eligible_n"]
            native[offset]["returned"] += p[offset]["returned"]

    for offset in ("d1", "d7", "d14"):
        eligible = native[offset]["eligible_n"]
        returned = native[offset]["returned"]
        native[offset]["rate"] = round(returned / eligible, 4) if eligible > 0 else 0.0

    return total_n, native


def _build_result(
    platform_stats: Dict[str, Dict[str, Any]],
    window_start: date,
    window_end: date,
    report_day: date,
    observed_at: datetime,
    min_n: int,
    pass_rate: float,
    kill_rate: float,
) -> Dict[str, Any]:
    """Turn platform stats into the canonical gate result."""
    native_total, native = _native_stats(platform_stats)
    d14 = native["d14"]
    d14_eligible = d14["eligible_n"]
    d14_returned = d14["returned"]
    d14_rate = d14_returned / d14_eligible if d14_eligible > 0 else 0.0

    web_stats = platform_stats.get(WEB_PLATFORM, _empty_platform())
    web_total = web_stats["total_n"]

    mature = report_day >= window_end + timedelta(days=14)

    if native_total == 0:
        if web_total > 0:
            status, reason = "insufficient", "no_native_data"
        elif report_day < window_start or not mature:
            status, reason = "insufficient", "not_mature"
        else:
            status, reason = "insufficient", "no_data"
    elif not mature:
        status, reason = "insufficient", "not_mature"
    elif d14_eligible < min_n:
        status, reason = "insufficient", "min_n"
    elif d14_rate >= pass_rate:
        status, reason = "pass", "above_threshold"
    else:
        status, reason = "fail", "below_threshold"

    below_kill_line = status == "fail" and d14_rate < kill_rate

    platforms_out = {p: platform_stats.get(p, _empty_platform()) for p in NATIVE_PLATFORMS}
    excluded_web = {
        "reason": "unqualified_marketing_mix",
        "total_n": web_total,
        "d1": web_stats["d1"],
        "d7": web_stats["d7"],
        "d14": web_stats["d14"],
    }

    return {
        "schema_version": 1,
        "population": "native",
        "window": {
            "start": window_start.isoformat(),
            "end": window_end.isoformat(),
        },
        "observed_at": observed_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "report_day": report_day.isoformat(),
        "status": status,
        "reason": reason,
        "below_kill_line": below_kill_line,
        "native": {"total_n": native_total, **native},
        "platforms": platforms_out,
        "excluded_web": excluded_web,
        "thresholds": {
            "min_n": min_n,
            "pass": pass_rate,
            "kill": kill_rate,
        },
    }


def _error_result(
    reason: str,
    window_start: date,
    window_end: date,
    report_day: date,
    observed_at: datetime,
    min_n: int,
    pass_rate: float,
    kill_rate: float,
) -> Dict[str, Any]:
    empty = _empty_platform()
    return {
        "schema_version": 1,
        "population": "native",
        "window": {
            "start": window_start.isoformat(),
            "end": window_end.isoformat(),
        },
        "observed_at": observed_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "report_day": report_day.isoformat(),
        "status": "error",
        "reason": reason,
        "below_kill_line": False,
        "native": {"total_n": 0, **empty},
        "platforms": {"iOS": empty, "Android": empty},
        "excluded_web": {
            "reason": "unqualified_marketing_mix",
            **empty,
        },
        "thresholds": {
            "min_n": min_n,
            "pass": pass_rate,
            "kill": kill_rate,
        },
    }


def collect_native_retention_gate(
    window_start: Optional[date] = None,
    window_end: Optional[date] = None,
    property_id: Optional[str] = None,
    observed_at: Optional[datetime] = None,
    thresholds: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Collect the native D1/D7/D14 retention gate for the configured window.

    Returns a structured dict with status ``pass``, ``fail``, ``insufficient``,
    or ``error``.  The underlying funnel scheduler can always attach this dict
    because exceptions are caught and converted to ``status=error``.
    """
    thresholds = thresholds or {}
    min_n = int(thresholds.get("min_n", DEFAULT_MIN_N))
    pass_rate = float(thresholds.get("pass", DEFAULT_PASS_THRESHOLD))
    kill_rate = float(thresholds.get("kill", DEFAULT_KILL_THRESHOLD))

    window_start = window_start or date.fromisoformat("2026-08-15")
    window_end = window_end or date.fromisoformat("2026-09-24")
    property_id = property_id or os.environ.get("GQ_GA_PROPERTY_ID", DEFAULT_PROPERTY_ID)

    if observed_at is None:
        observed_at = datetime.now(timezone.utc)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)

    # The latest analytics day considered complete is the day before the run.
    report_day = (observed_at - timedelta(days=1)).date()
    acquisition_end = min(report_day, window_end)

    if BetaAnalyticsDataClient is None:
        return _error_result(
            "google_analytics_unavailable",
            window_start,
            window_end,
            report_day,
            observed_at,
            min_n,
            pass_rate,
            kill_rate,
        )

    try:
        credentials = _resolve_credentials()
        client = _build_client(credentials)
        rows = _fetch_rows(
            client,
            property_id,
            activity_start=window_start,
            activity_end=report_day,
            acquisition_start=window_start,
            acquisition_end=acquisition_end,
        )
        platform_stats = _build_platform_stats(
            rows,
            acquisition_start=window_start,
            acquisition_end=acquisition_end,
            report_day=report_day,
            window_end=window_end,
        )
        return _build_result(
            platform_stats,
            window_start,
            window_end,
            report_day,
            observed_at,
            min_n,
            pass_rate,
            kill_rate,
        )
    except GateError as exc:
        return _error_result(
            exc.reason,
            window_start,
            window_end,
            report_day,
            observed_at,
            min_n,
            pass_rate,
            kill_rate,
        )
    except Exception:
        logger.exception("Unexpected error collecting retention gate")
        return _error_result(
            "unexpected_error",
            window_start,
            window_end,
            report_day,
            observed_at,
            min_n,
            pass_rate,
            kill_rate,
        )


def _render_human(result: Dict[str, Any]) -> None:
    print(f"Status: {result['status']} ({result['reason']})")
    print(f"Window: {result['window']['start']} .. {result['window']['end']}")
    print(f"Observed: {result['observed_at']}  Report day: {result['report_day']}")
    print(f"Population: {result['population']}")
    native = result["native"]
    print(f"Native total n: {native['total_n']}")
    for offset in ("d1", "d7", "d14"):
        s = native[offset]
        print(
            f"  {offset.upper()}: eligible={s['eligible_n']}, "
            f"returned={s['returned']}, rate={s['rate']}"
        )
    print("Platforms:")
    for plat, p in result["platforms"].items():
        print(f"  {plat}: total={p['total_n']}, d14={p['d14']['rate']}")
    web = result["excluded_web"]
    print(f"Excluded web (unqualified): total={web['total_n']}, d14={web['d14']['rate']}")
    if result.get("below_kill_line"):
        print("Below kill line.")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="GA4 native D1/D7/D14 retention gate")
    parser.add_argument("--start", default="2026-08-15")
    parser.add_argument("--end", default="2026-09-24")
    parser.add_argument("--property-id", default=os.environ.get("GQ_GA_PROPERTY_ID", DEFAULT_PROPERTY_ID))
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON")
    parser.add_argument(
        "--observed-at",
        help="ISO timestamp for testing maturity/offsets (default: now UTC)",
    )
    args = parser.parse_args(argv)

    window_start = date.fromisoformat(args.start)
    window_end = date.fromisoformat(args.end)
    observed_at = None
    if args.observed_at:
        raw = args.observed_at.replace("Z", "+00:00")
        observed_at = datetime.fromisoformat(raw)
    else:
        observed_at = datetime.now(timezone.utc)

    result = collect_native_retention_gate(
        window_start=window_start,
        window_end=window_end,
        property_id=args.property_id,
        observed_at=observed_at,
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _render_human(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
