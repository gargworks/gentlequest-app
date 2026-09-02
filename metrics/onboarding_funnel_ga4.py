"""GA4-sourced onboarding funnel: install -> compliance -> first chat message.

Why this exists (2026-08-31): the backend's own `analytics_events` table
(`compliance_passed`, `first_chat_message`) is gated behind
`analytics_consent`, a SharedPreferences flag with no UI path that ever sets
it true (see `lib/services/analytics_service.dart`). That gate is a
deliberate, already-decided privacy stance — the shipped opt-out model is
Anonymity Mode, not this dead opt-in — and it is not being wired here. But it
means the backend's own event table has never been a reliable signal of real
onboarding completion for the general user population: it only reflects
whatever tiny, non-representative slice of sessions happens to carry that
flag. GA4 (gated only by Anonymity Mode, matching the shipped privacy
promise) is the trustworthy source for this funnel.

Stages, sourced from the actual FirebaseService().logEvent() call sites:
  1. first_open                   lib: automatic GA4 SDK event on install
  2. compliance_check_started     compliance_service.dart:328
  3. compliance_result            compliance_service.dart:376/477/488/506/517
  4. first_chat_message_sent      chat_provider.dart:347

Native only (iOS + Android), matching the D14 gate's population definition
in ADR-007 -- web is reported separately, never blended into the verdict.

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
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
    from google.api_core import exceptions as google_exceptions
except ImportError:  # pragma: no cover - optional dependency guard
    DateRange = None  # type: ignore[assignment,misc]
    Dimension = None  # type: ignore[assignment,misc]
    Metric = None  # type: ignore[assignment,misc]
    RunReportRequest = None  # type: ignore[assignment,misc]
    google_exceptions = None  # type: ignore[assignment,misc]

logger = logging.getLogger("onboarding_funnel_ga4")

NATIVE_PLATFORMS = {"iOS", "Android"}

# Ordered funnel stages. Each maps to the GA4 eventName that marks reaching
# that stage. Order matters for the printed table; it is not used to imply
# strict causal sequencing (a user could technically fire compliance_result
# without compliance_check_started in edge cases -- rare, not modeled here).
FUNNEL_STAGES: List[Tuple[str, str]] = [
    ("install", "first_open"),
    ("compliance_started", "compliance_check_started"),
    ("compliance_result", "compliance_result"),
    # NOTE: home_tab_viewed is deliberately NOT a stage in this chain. Since
    # 2026-09-02 first-run users land on the Talk tab and skip Home entirely,
    # so as a sequential stage it would read ~0 and make every downstream
    # conversion meaningless. The event still fires (wellness_home_screen.dart
    # initState) and is worth reading on its own for returning-user behaviour —
    # it is just not a step on the activation path any more.
    ("chat_tab_viewed", "chat_tab_viewed"),
    ("chat_composer_focused", "chat_composer_focused"),
    ("chat_send_attempted", "chat_send_attempted"),
    ("first_chat_message", "first_chat_message_sent"),
]


def _canonical_platform(raw: str) -> str:
    lower = (raw or "").strip().lower()
    if lower == "ios":
        return "iOS"
    if lower == "android":
        return "Android"
    if lower == "web":
        return "Web"
    return raw


def _fetch_event_counts(
    client,
    property_id: str,
    start: date,
    end: date,
) -> Dict[str, Dict[str, int]]:
    """Return {eventName: {platform: eventCount}} for the funnel's event set."""
    if RunReportRequest is None:
        raise GateError("google_analytics_unavailable")

    wanted_events = {name for _, name in FUNNEL_STAGES}
    counts: Dict[str, Dict[str, int]] = {name: {} for name in wanted_events}

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="eventName"), Dimension(name="platform")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date=start.isoformat(), end_date=end.isoformat())],
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

    for row in response.rows:
        event_name = row.dimension_values[0].value
        platform = _canonical_platform(row.dimension_values[1].value)
        event_count = int(row.metric_values[0].value)
        if event_name not in wanted_events:
            continue
        counts[event_name][platform] = counts[event_name].get(platform, 0) + event_count

    return counts


def collect_onboarding_funnel(
    *,
    days: int = 7,
    property_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the funnel report and return a structured result.

    Never raises for expected failure modes -- returns
    {"status": "error", "reason": ...} instead, matching the d14 gate's
    convention of persisted, non-silent failure over a thrown exception.
    """
    property_id = property_id or DEFAULT_PROPERTY_ID
    end = date.today()
    start = end - timedelta(days=days - 1)

    try:
        client = build_ga4_client()
        counts = _fetch_event_counts(client, property_id, start, end)
    except GateError as exc:
        return {
            "status": "error",
            "reason": exc.reason,
            "window": {"start": start.isoformat(), "end": end.isoformat()},
        }

    stages = []
    native_prev_total: Optional[int] = None
    for stage_key, event_name in FUNNEL_STAGES:
        by_platform = counts.get(event_name, {})
        native_total = sum(v for k, v in by_platform.items() if k in NATIVE_PLATFORMS)
        web_total = by_platform.get("Web", 0)
        conv_from_prev = (
            round(native_total / native_prev_total, 4)
            if native_prev_total and native_prev_total > 0
            else None
        )
        stages.append(
            {
                "stage": stage_key,
                "event_name": event_name,
                "native": native_total,
                "ios": by_platform.get("iOS", 0),
                "android": by_platform.get("Android", 0),
                "web_excluded": web_total,
                "conversion_from_previous_stage": conv_from_prev,
            }
        )
        native_prev_total = native_total

    overall_conv = None
    if stages and stages[0]["native"]:
        overall_conv = round(stages[-1]["native"] / stages[0]["native"], 4)

    return {
        "status": "ok",
        "window": {"start": start.isoformat(), "end": end.isoformat(), "days": days},
        "property_id": property_id,
        "population": "native (iOS + Android); web reported separately, never blended",
        "stages": stages,
        "overall_install_to_chat_conversion": overall_conv,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _render_human(result: Dict[str, Any]) -> None:
    if result.get("status") != "ok":
        print(f"ERROR: {result.get('reason', 'unknown')}")
        return
    w = result["window"]
    print(f"Onboarding funnel — {w['start']} to {w['end']} ({w['days']}d), native only")
    print(f"{'stage':<22} {'event':<26} {'native':>7} {'iOS':>5} {'Android':>8} {'conv%':>7}")
    for s in result["stages"]:
        conv = f"{s['conversion_from_previous_stage']*100:.0f}%" if s["conversion_from_previous_stage"] is not None else "-"
        print(f"{s['stage']:<22} {s['event_name']:<26} {s['native']:>7} {s['ios']:>5} {s['android']:>8} {conv:>7}")
    if result.get("overall_install_to_chat_conversion") is not None:
        print(f"\nOverall install -> first chat: {result['overall_install_to_chat_conversion']*100:.1f}%")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--property-id", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = collect_onboarding_funnel(days=args.days, property_id=args.property_id)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _render_human(result)
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
