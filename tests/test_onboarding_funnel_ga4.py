"""Unit tests for the GA4-sourced onboarding funnel collector.

Never calls the GA4 network. Exercises stage aggregation, native/web
separation, conversion-rate math, and the error-passthrough path using
synthetic GA4 report rows and mocks -- mirrors tests/test_d14_cohort_ga4.py's
pattern.
"""

import os
import sys
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import metrics.onboarding_funnel_ga4 as funnel_mod
from metrics.d14_cohort_ga4 import GateError


def _mock_response(rows):
    """rows: list of (event_name, platform, event_count)."""
    mock_rows = []
    for event_name, platform, count in rows:
        row = Mock()
        row.dimension_values = [SimpleNamespace(value=event_name), SimpleNamespace(value=platform)]
        row.metric_values = [SimpleNamespace(value=str(count))]
        mock_rows.append(row)
    return Mock(rows=mock_rows)


class TestCanonicalPlatform:
    def test_known_platforms(self):
        assert funnel_mod._canonical_platform("iOS") == "iOS"
        assert funnel_mod._canonical_platform("android") == "Android"
        assert funnel_mod._canonical_platform("Web") == "Web"

    def test_unknown_platform_left_as_is(self):
        assert funnel_mod._canonical_platform("Smart TV") == "Smart TV"


class TestFetchEventCounts:
    def test_aggregates_by_event_and_platform_native_and_web(self):
        client = Mock()
        client.run_report.return_value = _mock_response(
            [
                ("first_open", "iOS", 10),
                ("first_open", "Android", 5),
                ("first_open", "Web", 100),  # must not leak into native totals
                ("compliance_check_started", "iOS", 6),
                ("some_unrelated_event", "iOS", 999),  # must be dropped
            ]
        )
        with patch.object(funnel_mod, "RunReportRequest", Mock()), \
             patch.object(funnel_mod, "google_exceptions", Mock()):
            counts = funnel_mod._fetch_event_counts(client, "12345", date(2026, 8, 1), date(2026, 8, 7))
        assert counts["first_open"] == {"iOS": 10, "Android": 5, "Web": 100}
        assert counts["compliance_check_started"] == {"iOS": 6}
        assert "some_unrelated_event" not in counts

    def test_raises_gate_error_when_client_missing(self):
        with patch.object(funnel_mod, "RunReportRequest", None):
            with pytest.raises(GateError) as exc_info:
                funnel_mod._fetch_event_counts(Mock(), "12345", date(2026, 8, 1), date(2026, 8, 7))
        assert exc_info.value.reason == "google_analytics_unavailable"


class TestCollectOnboardingFunnel:
    def test_full_funnel_conversion_math(self):
        # Stage chain as of 2026-09-02: the activation cliff between
        # compliance_result and first_chat_message_sent was split into three
        # sub-steps (chat_tab_viewed -> chat_composer_focused ->
        # chat_send_attempted) so the "land on Talk" fix can be measured.
        # home_tab_viewed fires but is deliberately NOT in this chain.
        counts = {
            "first_open": {"iOS": 18, "Android": 14, "Web": 500},
            "compliance_check_started": {"iOS": 13, "Android": 5},
            "compliance_result": {"iOS": 9, "Android": 3},
            "chat_tab_viewed": {"iOS": 6, "Android": 2},
            "chat_composer_focused": {"iOS": 4, "Android": 2},
            "chat_send_attempted": {"iOS": 1, "Android": 3},
            "first_chat_message_sent": {"iOS": 0, "Android": 3},
        }
        with patch.object(funnel_mod, "build_ga4_client", return_value=Mock()), \
             patch.object(funnel_mod, "_fetch_event_counts", return_value=counts):
            result = funnel_mod.collect_onboarding_funnel(days=5, property_id="551876340")

        assert result["status"] == "ok"
        assert result["property_id"] == "551876340"
        stages = {s["stage"]: s for s in result["stages"]}

        assert stages["install"]["native"] == 32  # 18 + 14, web (500) excluded
        assert stages["install"]["web_excluded"] == 500
        assert stages["install"]["conversion_from_previous_stage"] is None

        assert stages["compliance_started"]["native"] == 18  # 13 + 5
        assert stages["compliance_started"]["conversion_from_previous_stage"] == pytest.approx(18 / 32, abs=1e-4)

        assert stages["compliance_result"]["native"] == 12  # 9 + 3
        assert stages["compliance_result"]["conversion_from_previous_stage"] == pytest.approx(12 / 18, abs=1e-4)

        # The three new sub-steps, each measured against the one before it.
        assert stages["chat_tab_viewed"]["native"] == 8  # 6 + 2
        assert stages["chat_tab_viewed"]["conversion_from_previous_stage"] == pytest.approx(8 / 12, abs=1e-4)

        assert stages["chat_composer_focused"]["native"] == 6  # 4 + 2
        assert stages["chat_composer_focused"]["conversion_from_previous_stage"] == pytest.approx(6 / 8, abs=1e-4)

        assert stages["chat_send_attempted"]["native"] == 4  # 1 + 3
        assert stages["chat_send_attempted"]["conversion_from_previous_stage"] == pytest.approx(4 / 6, abs=1e-4)

        # first_chat_message now measures against send_attempted, which isolates
        # send FAILURE (4 attempted, 3 succeeded) as its own visible sub-step.
        assert stages["first_chat_message"]["native"] == 3  # 0 + 3
        assert stages["first_chat_message"]["ios"] == 0
        assert stages["first_chat_message"]["android"] == 3
        assert stages["first_chat_message"]["conversion_from_previous_stage"] == pytest.approx(3 / 4, abs=1e-4)

        # Overall is still install -> first chat, unaffected by the new middle.
        assert result["overall_install_to_chat_conversion"] == pytest.approx(3 / 32, abs=1e-4)

    def test_home_tab_viewed_is_not_a_funnel_stage(self):
        """home_tab_viewed must stay OUT of the sequential chain.

        First-run users land on Talk and skip Home entirely (2026-09-02), so as
        a stage it would read ~0 and zero out every downstream conversion. This
        is a deliberate design constraint, not an omission — assert it, so a
        future well-meaning edit that "completes" the funnel gets caught.
        """
        assert "home_tab_viewed" not in [key for key, _ in funnel_mod.FUNNEL_STAGES]
        assert "home_tab_viewed" not in [event for _, event in funnel_mod.FUNNEL_STAGES]

    def test_zero_installs_does_not_divide_by_zero(self):
        counts = {
            "first_open": {},
            "compliance_check_started": {},
            "compliance_result": {},
            "first_chat_message_sent": {},
        }
        with patch.object(funnel_mod, "build_ga4_client", return_value=Mock()), \
             patch.object(funnel_mod, "_fetch_event_counts", return_value=counts):
            result = funnel_mod.collect_onboarding_funnel(days=1)

        assert result["status"] == "ok"
        assert result["overall_install_to_chat_conversion"] is None
        for stage in result["stages"]:
            assert stage["native"] == 0

    def test_gate_error_becomes_structured_error_result_not_exception(self):
        with patch.object(funnel_mod, "build_ga4_client", side_effect=GateError("credentials_missing")):
            result = funnel_mod.collect_onboarding_funnel(days=7)

        assert result["status"] == "error"
        assert result["reason"] == "credentials_missing"
        assert "window" in result

    def test_default_property_id_used_when_not_specified(self):
        with patch.object(funnel_mod, "build_ga4_client", return_value=Mock()), \
             patch.object(funnel_mod, "_fetch_event_counts", return_value={
                 "first_open": {}, "compliance_check_started": {},
                 "compliance_result": {}, "first_chat_message_sent": {},
             }):
            result = funnel_mod.collect_onboarding_funnel(days=1)
        assert result["property_id"] == funnel_mod.DEFAULT_PROPERTY_ID


class TestMainCli:
    def test_json_output_reflects_collector_result(self, capsys):
        ok_result = {"status": "ok", "stages": [], "window": {"start": "x", "end": "y", "days": 1}}
        with patch.object(funnel_mod, "collect_onboarding_funnel", return_value=ok_result):
            exit_code = funnel_mod.main(["--json"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert '"status": "ok"' in captured.out

    def test_error_status_returns_nonzero_exit(self):
        err_result = {"status": "error", "reason": "credentials_missing"}
        with patch.object(funnel_mod, "collect_onboarding_funnel", return_value=err_result):
            exit_code = funnel_mod.main(["--json"])
        assert exit_code == 1
