"""GA4-sourced per-channel INSTALL counts (first_open by acquisition source/medium).

Why this exists (2026-09-02): metrics/install_count.py aggregates a CUMULATIVE
total across Play Store / App Store / GA4 for the Stage-1 250-install gate, but
it does NOT break installs down by acquisition channel. This module does: it
queries GA4 for the ``first_open`` event count dimensioned by acquisition
source/medium AND platform, so we can see which channels are actually driving
installs. GA4 attributes ``first_open`` to the acquisition source natively (no
new app instrumentation needed) — ``first_open`` is the automatic SDK event
fired once per user on first app open, and the first-user traffic-source
dimensions are set at user-acquisition time and persist for the user's lifetime.

Dimension choice — ``firstUserSourceMedium`` (NOT session-scoped):
  Candidates evaluated against the GA4 Data API schema
  (https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema):
    - ``firstUserSource``        — First user source (user-scoped)
    - ``firstUserMedium``        — First user medium (user-scoped)
    - ``firstUserSourceMedium``  — combined "source / medium" (user-scoped)  [CHOSEN]
    - ``sessionSource``          — Session source (session-scoped)
    - ``sessionMedium``          — Session medium (session-scoped)
    - ``sessionSourceMedium``    — combined session source/medium (session-scoped)
  An install is a FIRST-TOUCH event (the user's first session). The first-user
  (acquisition) dimensions represent "the source / medium that acquired the
  user in the first session" and remain fixed as users return — so they
  attribute ``first_open`` to the channel that drove the install, not to
  whatever channel brought a later returning session. The session-scoped
  dimensions would mis-attribute installs for any returning user whose later
  session had a different source. ``firstUserSourceMedium`` (the combined
  dimension) is chosen over separate ``firstUserSource`` + ``firstUserMedium``
  because it matches GA4's own User Acquisition report and yields a single
  clean channel key (e.g. "google / organic", "(direct) / (none)").
  If GA4 rejects the dimension combination, the error surfaces as
  ``GateError('invalid_request')`` per the existing taxonomy in
  d14_cohort_ga4.py — it is NOT silently swallowed.

Population: native (iOS + Android) and web are reported SEPARATELY, never
summed. This mirrors ADR-007's convention (web is
``unqualified_marketing_mix``) and onboarding_funnel_ga4.py's
``NATIVE_PLATFORMS`` handling. A web-heavy channel must not inflate the native
install count.

Deliberately self-contained and reuses the credential/client plumbing from
d14_cohort_ga4.py rather than re-implementing it.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from metrics.d14_cohort_ga4 import (
    DEFAULT_PROPERTY_ID,
    GateError,
    build_ga4_client,
)

try:  # pragma: no cover - optional dependency guard
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Filter,
        FilterExpression,
        Metric,
        RunReportRequest,
    )
    from google.api_core import exceptions as google_exceptions
except ImportError:  # pragma: no cover - optional dependency guard
    DateRange = None  # type: ignore[assignment,misc]
    Dimension = None  # type: ignore[assignment,misc]
    Filter = None  # type: ignore[assignment,misc]
    FilterExpression = None  # type: ignore[assignment,misc]
    Metric = None  # type: ignore[assignment,misc]
    RunReportRequest = None  # type: ignore[assignment,misc]
    google_exceptions = None  # type: ignore[assignment,misc]

logger = logging.getLogger("channel_installs_ga4")

NATIVE_PLATFORMS = {"iOS", "Android"}

# The GA4 acquisition dimension — see module docstring for the rationale.
CHANNEL_DIMENSION = "firstUserSourceMedium"
INSTALL_EVENT = "first_open"


def _canonical_platform(raw: str) -> str:
    lower = (raw or "").strip().lower()
    if lower == "ios":
        return "iOS"
    if lower == "android":
        return "Android"
    if lower == "web":
        return "Web"
    return raw


def _fetch_channel_installs(
    client,
    property_id: str,
    start: date,
    end: date,
) -> List[Tuple[str, str, int]]:
    """Return list of (channel, platform, install_count) rows for first_open.

    Queries GA4 for the ``first_open`` event count, dimensioned by
    ``firstUserSourceMedium`` (acquisition source/medium) and ``platform``.
    """
    if RunReportRequest is None:
        raise GateError("google_analytics_unavailable")

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name=CHANNEL_DIMENSION),
            Dimension(name="platform"),
        ],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(value=INSTALL_EVENT),
            )
        ),
        limit=100_000,
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
        module = type(exc).__module__.lower()
        name = type(exc).__name__.lower()
        if "auth" in module or "credential" in name or "refresh" in name:
            raise GateError("authentication_failed") from exc
        raise GateError("unexpected_error") from exc

    rows: List[Tuple[str, str, int]] = []
    for row in response.rows:
        channel = row.dimension_values[0].value
        platform = _canonical_platform(row.dimension_values[1].value)
        count = int(row.metric_values[0].value)
        rows.append((channel, platform, count))
    return rows


def collect_channel_installs(
    *,
    days: int = 7,
    property_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the per-channel install report and return a structured result.

    Never raises for expected failure modes -- returns
    {"status": "error", "reason": ...} instead, matching the d14 gate's
    convention of persisted, non-silent failure over a thrown exception.
    """
    property_id = property_id or DEFAULT_PROPERTY_ID
    end = date.today()
    start = end - timedelta(days=days - 1)

    try:
        client = build_ga4_client()
        raw_rows = _fetch_channel_installs(client, property_id, start, end)
    except GateError as exc:
        return {
            "status": "error",
            "reason": exc.reason,
            "window": {"start": start.isoformat(), "end": end.isoformat()},
        }

    # Aggregate by (channel, platform) — GA4 may return multiple rows per
    # combination if pagination or other splitting occurred.
    agg: Dict[Tuple[str, str], int] = {}
    for channel, platform, count in raw_rows:
        agg[(channel, platform)] = agg.get((channel, platform), 0) + count

    # Build per-channel records. Native (iOS+Android) and web are kept
    # SEPARATE — never summed into a single total that would let a web-heavy
    # channel inflate the native install count.
    channels_map: Dict[str, Dict[str, Any]] = {}
    for (channel, platform), count in agg.items():
        rec = channels_map.setdefault(
            channel,
            {
                "channel": channel,
                "native": 0,
                "ios": 0,
                "android": 0,
                "web_excluded": 0,
            },
        )
        if platform in NATIVE_PLATFORMS:
            rec["native"] += count
            if platform == "iOS":
                rec["ios"] += count
            elif platform == "Android":
                rec["android"] += count
        elif platform == "Web":
            rec["web_excluded"] += count
        else:
            # Unknown platform (e.g. Smart TV) — count toward native as a
            # conservative default but do not blend into iOS/Android sub-totals.
            rec["native"] += count

    # Sort channels by native install count descending. Web-only channels
    # (native == 0) sort to the bottom by their web count so they remain
    # visible but never dominate the native ordering.
    channels = sorted(
        channels_map.values(),
        key=lambda c: (c["native"], c["web_excluded"]),
        reverse=True,
    )

    native_total = sum(c["native"] for c in channels)
    web_total = sum(c["web_excluded"] for c in channels)

    return {
        "status": "ok",
        "window": {"start": start.isoformat(), "end": end.isoformat(), "days": days},
        "property_id": property_id,
        "population": "native (iOS + Android); web reported separately, never blended",
        "install_event": INSTALL_EVENT,
        "channel_dimension": CHANNEL_DIMENSION,
        "channels": channels,
        "total": {"native": native_total, "web_excluded": web_total},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _render_human(result: Dict[str, Any]) -> None:
    if result.get("status") != "ok":
        print(f"ERROR: {result.get('reason', 'unknown')}")
        return
    w = result["window"]
    print(f"Channel installs — {w['start']} to {w['end']} ({w['days']}d), native only")
    print(f"Event: {result['install_event']}  Dimension: {result['channel_dimension']}")
    print(f"{'channel':<28} {'native':>7} {'iOS':>5} {'Android':>8} {'web_excl':>9}")
    print("-" * 62)
    for c in result["channels"]:
        print(
            f"{c['channel']:<28} {c['native']:>7} {c['ios']:>5} "
            f"{c['android']:>8} {c['web_excluded']:>9}"
        )
    print("-" * 62)
    t = result["total"]
    print(f"{'TOTAL':<28} {t['native']:>7} {'':>5} {'':>8} {t['web_excluded']:>9}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--property-id", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = collect_channel_installs(days=args.days, property_id=args.property_id)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _render_human(result)
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
