"""Unit tests for the GA4-sourced per-channel install collector.

Never calls the GA4 network. Exercises multi-channel aggregation, native/web
separation, descending sort, the zero-rows case, and the error-passthrough
path using synthetic GA4 report rows and mocks -- mirrors
tests/test_onboarding_funnel_ga4.py's pattern.
"""

import os
import sys
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import metrics.channel_installs_ga4 as channel_mod
from metrics.d14_cohort_ga4 import GateError


def _mock_response(rows):
    """rows: list of (channel, platform, event_count)."""
    mock_rows = []
    for channel, platform, count in rows:
        row = Mock()
        row.dimension_values = [
            SimpleNamespace(value=channel),
            SimpleNamespace(value=platform),
        ]
        row.metric_values = [SimpleNamespace(value=str(count))]
        mock_rows.append(row)
    return Mock(rows=mock_rows)


class TestCanonicalPlatform:
    def test_known_platforms(self):
        assert channel_mod._canonical_platform("iOS") == "iOS"
        assert channel_mod._canonical_platform("android") == "Android"
        assert channel_mod._canonical_platform("Web") == "Web"

    def test_unknown_platform_left_as_is(self):
        assert channel_mod._canonical_platform("Smart TV") == "Smart TV"


def _patch_ga4_types():
    """Patch all GA4 type imports so tests run without the library installed.

    The template (test_onboarding_funnel_ga4.py) patches only RunReportRequest
    and google_exceptions, which works when the library IS installed but fails
    when it isn't (Dimension/Metric/DateRange are None). Patching all types
    makes the tests robust regardless of install state while preserving the
    same mock-response pattern.
    """
    return [
        patch.object(channel_mod, "RunReportRequest", Mock()),
        patch.object(channel_mod, "Dimension", Mock()),
        patch.object(channel_mod, "Metric", Mock()),
        patch.object(channel_mod, "DateRange", Mock()),
        patch.object(channel_mod, "FilterExpression", Mock()),
        patch.object(channel_mod, "Filter", Mock()),
        patch.object(channel_mod, "google_exceptions", Mock()),
    ]


class TestFetchChannelInstalls:
    def test_returns_channel_platform_count_rows(self):
        client = Mock()
        client.run_report.return_value = _mock_response(
            [
                ("google / organic", "iOS", 10),
                ("google / organic", "Android", 5),
                ("(direct) / (none)", "Web", 100),
            ]
        )
        patches = _patch_ga4_types()
        for p in patches:
            p.start()
        try:
            rows = channel_mod._fetch_channel_installs(
                client, "12345", date(2026, 8, 1), date(2026, 8, 7)
            )
        finally:
            for p in patches:
                p.stop()
        assert ("google / organic", "iOS", 10) in rows
        assert ("google / organic", "Android", 5) in rows
        assert ("(direct) / (none)", "Web", 100) in rows
        assert len(rows) == 3

    def test_raises_gate_error_when_client_missing(self):
        with patch.object(channel_mod, "RunReportRequest", None):
            with pytest.raises(GateError) as exc_info:
                channel_mod._fetch_channel_installs(
                    Mock(), "12345", date(2026, 8, 1), date(2026, 8, 7)
                )
        assert exc_info.value.reason == "google_analytics_unavailable"


class TestCollectChannelInstalls:
    def test_multi_channel_aggregation_and_native_web_separate(self):
        """A web-heavy channel must NOT inflate the native install count.

        google / organic has 100 web first_opens but only 15 native — the
        native total must be 15, not 115. Web is reported separately.
        """
        raw_rows = [
            ("google / organic", "iOS", 10),
            ("google / organic", "Android", 5),
            ("google / organic", "Web", 100),
            ("(direct) / (none)", "iOS", 3),
            ("(direct) / (none)", "Android", 2),
            ("reddit / referral", "Web", 50),
        ]
        with patch.object(channel_mod, "build_ga4_client", return_value=Mock()), \
             patch.object(channel_mod, "_fetch_channel_installs", return_value=raw_rows):
            result = channel_mod.collect_channel_installs(days=7, property_id="551876340")

        assert result["status"] == "ok"
        assert result["property_id"] == "551876340"
        channels = {c["channel"]: c for c in result["channels"]}

        # google / organic: native 15 (10 iOS + 5 Android), web 100 — NOT 115.
        assert channels["google / organic"]["native"] == 15
        assert channels["google / organic"]["ios"] == 10
        assert channels["google / organic"]["android"] == 5
        assert channels["google / organic"]["web_excluded"] == 100

        # (direct) / (none): native 5, web 0.
        assert channels["(direct) / (none)"]["native"] == 5
        assert channels["(direct) / (none)"]["web_excluded"] == 0

        # reddit / referral: web-only channel — native 0, web 50.
        assert channels["reddit / referral"]["native"] == 0
        assert channels["reddit / referral"]["web_excluded"] == 50

        # Totals: native 20, web 150 — never blended.
        assert result["total"]["native"] == 20
        assert result["total"]["web_excluded"] == 150

    def test_channels_sorted_by_native_install_count_descending(self):
        raw_rows = [
            ("small / channel", "iOS", 2),
            ("big / channel", "iOS", 50),
            ("medium / channel", "Android", 20),
            ("webonly / channel", "Web", 999),
        ]
        with patch.object(channel_mod, "build_ga4_client", return_value=Mock()), \
             patch.object(channel_mod, "_fetch_channel_installs", return_value=raw_rows):
            result = channel_mod.collect_channel_installs(days=7)

        native_counts = [c["native"] for c in result["channels"]]
        # Native channels sorted descending; web-only channel (native=0) last.
        assert native_counts == [50, 20, 2, 0]
        assert result["channels"][0]["channel"] == "big / channel"
        assert result["channels"][-1]["channel"] == "webonly / channel"

    def test_zero_rows_case(self):
        with patch.object(channel_mod, "build_ga4_client", return_value=Mock()), \
             patch.object(channel_mod, "_fetch_channel_installs", return_value=[]):
            result = channel_mod.collect_channel_installs(days=1)

        assert result["status"] == "ok"
        assert result["channels"] == []
        assert result["total"]["native"] == 0
        assert result["total"]["web_excluded"] == 0

    def test_gate_error_becomes_structured_error_result_not_exception(self):
        with patch.object(channel_mod, "build_ga4_client", side_effect=GateError("credentials_missing")):
            result = channel_mod.collect_channel_installs(days=7)

        assert result["status"] == "error"
        assert result["reason"] == "credentials_missing"
        assert "window" in result

    def test_default_property_id_used_when_not_specified(self):
        with patch.object(channel_mod, "build_ga4_client", return_value=Mock()), \
             patch.object(channel_mod, "_fetch_channel_installs", return_value=[]):
            result = channel_mod.collect_channel_installs(days=1)
        assert result["property_id"] == channel_mod.DEFAULT_PROPERTY_ID


class TestMainCli:
    def test_json_output_reflects_collector_result(self, capsys):
        ok_result = {
            "status": "ok",
            "channels": [],
            "total": {"native": 0, "web_excluded": 0},
            "window": {"start": "x", "end": "y", "days": 1},
        }
        with patch.object(channel_mod, "collect_channel_installs", return_value=ok_result):
            exit_code = channel_mod.main(["--json"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert '"status": "ok"' in captured.out

    def test_error_status_returns_nonzero_exit(self):
        err_result = {"status": "error", "reason": "credentials_missing"}
        with patch.object(channel_mod, "collect_channel_installs", return_value=err_result):
            exit_code = channel_mod.main(["--json"])
        assert exit_code == 1

class TestUnknownPlatformDoesNotInflateNative:
    """An unknown GA4 platform must NOT be counted as native.

    Folding it into `native` was the original behaviour. It broke the module's
    own invariant (native == ios + android) and silently inflated the exact
    population ADR-007 ratifies for the D14 gate. Reported separately so it is
    visible rather than silently discarded.
    """

    def test_unknown_platform_excluded_from_native_and_surfaced(self):
        # _fetch_channel_installs returns (channel, platform, count) tuples.
        counts = [
            ("(direct) / (none)", "iOS", 10),
            ("(direct) / (none)", "Android", 5),
            ("(direct) / (none)", "Smart TV", 7),
            ("(direct) / (none)", "Web", 3),
        ]
        with patch.object(channel_mod, "build_ga4_client", return_value=Mock()), \
             patch.object(channel_mod, "_fetch_channel_installs", return_value=counts):
            result = channel_mod.collect_channel_installs(days=7)

        assert result["status"] == "ok"
        row = result["channels"][0]
        # THE INVARIANT: native is exactly iOS + Android, nothing else.
        assert row["native"] == 15, "Smart TV must not be counted as native"
        assert row["native"] == row["ios"] + row["android"]
        assert row["web_excluded"] == 3
        assert row["unknown_platform"] == 7, "unknown platform must be visible, not dropped"
        assert result["total"]["native"] == 15
        assert result["total"]["unknown_platform"] == 7
