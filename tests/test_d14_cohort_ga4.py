"""Unit tests for the native GA4 D1/D7/D14 retention gate collector.

These tests never call the GA4 network.  They exercise credential resolution,
cohort aggregation, offset-specific eligible subcohorts, platform exclusion,
and the gate state machine using synthetic rows and mocks.
"""

import os
import sys
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import metrics.d14_cohort_ga4 as ga4


WINDOW_START = date(2026, 8, 15)
WINDOW_END = date(2026, 9, 24)


def _make_rows(platform_totals, retained_counts, report_day):
    """Build synthetic GA4 rows from cohort sizes and per-offset retained counts.

    platform_totals: {platform: [(first_session_date, cohort_size), ...]}
    retained_counts: {(platform, first_session_date, offset): retained_count}
    """
    rows = []
    for platform, cohorts in platform_totals.items():
        for fs, size in cohorts:
            rows.append((fs, fs, platform, size))
            for offset in (1, 7, 14):
                retained = retained_counts.get((platform, fs, offset), 0)
                activity = fs + timedelta(days=offset)
                if activity <= report_day:
                    rows.append((fs, activity, platform, retained))
    return rows


@pytest.fixture
def mock_google_libs(monkeypatch):
    """Patch google library module references so tests run without the package."""
    if ga4.BetaAnalyticsDataClient is None:
        monkeypatch.setattr(ga4, "BetaAnalyticsDataClient", Mock)
    monkeypatch.setattr(
        ga4,
        "service_account",
        SimpleNamespace(
            Credentials=Mock(
                from_service_account_info=Mock(
                    return_value=Mock(scopes=(ga4.ANALYTICS_READONLY_SCOPE,))
                ),
                from_service_account_file=Mock(
                    return_value=Mock(scopes=(ga4.ANALYTICS_READONLY_SCOPE,))
                ),
            )
        ),
    )
    monkeypatch.setattr(
        ga4,
        "load_credentials_from_file",
        Mock(return_value=(Mock(scopes=(ga4.ANALYTICS_READONLY_SCOPE,)), "project")),
    )
    monkeypatch.setattr(
        ga4,
        "default",
        Mock(return_value=(Mock(scopes=(ga4.ANALYTICS_READONLY_SCOPE,)), "project")),
    )


class TestCanonicalPlatform:
    def test_known_platforms(self):
        assert ga4._canonical_platform("iOS") == "iOS"
        assert ga4._canonical_platform("android") == "Android"
        assert ga4._canonical_platform("Web") == "Web"

    def test_unknown_platform_left_as_is(self):
        assert ga4._canonical_platform("iPadOS") == "iPadOS"


class TestResolveCredentials:
    def test_gq_ga_sa_json_plain(self, monkeypatch, mock_google_libs):
        json_text = '{"type": "service_account"}'
        monkeypatch.setenv("GQ_GA_SA_JSON", json_text)
        monkeypatch.delenv("GQ_GA_SA_PATH", raising=False)
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        creds = ga4._resolve_credentials()
        assert creds is not None
        ga4.service_account.Credentials.from_service_account_info.assert_called_once()

    def test_gq_ga_sa_json_base64(self, monkeypatch, mock_google_libs):
        import base64

        json_text = '{"type": "service_account"}'
        monkeypatch.setenv("GQ_GA_SA_JSON", base64.b64encode(json_text.encode()).decode())
        monkeypatch.delenv("GQ_GA_SA_PATH", raising=False)
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        creds = ga4._resolve_credentials()
        assert creds is not None

    def test_gq_ga_sa_json_malformed(self, monkeypatch, mock_google_libs):
        monkeypatch.setenv("GQ_GA_SA_JSON", "not-json")
        with pytest.raises(ga4.GateError) as exc:
            ga4._resolve_credentials()
        assert exc.value.reason == "malformed_service_account_json"

    def test_credentials_missing(self, monkeypatch, mock_google_libs):
        monkeypatch.delenv("GQ_GA_SA_JSON", raising=False)
        monkeypatch.delenv("GQ_GA_SA_PATH", raising=False)
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        ga4.default.side_effect = Exception("no credentials")
        with pytest.raises(ga4.GateError) as exc:
            ga4._resolve_credentials()
        assert exc.value.reason == "credentials_missing"

    def test_gq_ga_sa_path_priority(self, monkeypatch, mock_google_libs, tmp_path):
        path = tmp_path / "sa.json"
        path.write_text('{"type": "service_account"}')
        monkeypatch.setenv("GQ_GA_SA_PATH", str(path))
        monkeypatch.delenv("GQ_GA_SA_JSON", raising=False)
        creds = ga4._resolve_credentials()
        assert creds is not None
        ga4.load_credentials_from_file.assert_called_once()


class TestBuildPlatformStats:
    def test_single_cohort_d1_d7_d14(self):
        fs = date(2026, 9, 10)
        report_day = date(2026, 10, 8)
        rows = _make_rows(
            {"iOS": [(fs, 20)]},
            {("iOS", fs, 1): 10, ("iOS", fs, 7): 5, ("iOS", fs, 14): 3},
            report_day,
        )
        stats = ga4._build_platform_stats(
            rows,
            acquisition_start=WINDOW_START,
            acquisition_end=WINDOW_END,
            report_day=report_day,
            window_end=WINDOW_END,
        )
        ios = stats["iOS"]
        assert ios["total_n"] == 20
        assert ios["d1"] == {"eligible_n": 20, "returned": 10, "rate": 0.5}
        assert ios["d7"] == {"eligible_n": 20, "returned": 5, "rate": 0.25}
        assert ios["d14"] == {"eligible_n": 20, "returned": 3, "rate": 0.15}

    def test_offset_specific_eligible_subcohorts(self):
        """D7 and D14 only include cohorts that have reached those days."""
        fs1 = date(2026, 9, 24)  # only D1 observed on report_day 2026-09-25
        fs2 = date(2026, 9, 17)  # D1 and D7 observed
        fs3 = date(2026, 9, 10)  # D1, D7 and D14 observed
        report_day = date(2026, 9, 25)
        rows = _make_rows(
            {"iOS": [(fs1, 10), (fs2, 10), (fs3, 10)]},
            {("iOS", fs1, 1): 5, ("iOS", fs2, 1): 5, ("iOS", fs2, 7): 3,
             ("iOS", fs3, 1): 5, ("iOS", fs3, 7): 3, ("iOS", fs3, 14): 1},
            report_day,
        )
        stats = ga4._build_platform_stats(
            rows,
            acquisition_start=WINDOW_START,
            acquisition_end=WINDOW_END,
            report_day=report_day,
            window_end=WINDOW_END,
        )
        # D1 eligible: fs1, fs2, fs3 (all <= 2026-09-24)
        # D7 eligible: fs2, fs3 (<= 2026-09-18)
        # D14 eligible: fs3 only (<= 2026-09-10)
        assert stats["iOS"]["d1"]["eligible_n"] == 30
        assert stats["iOS"]["d7"]["eligible_n"] == 20
        assert stats["iOS"]["d14"]["eligible_n"] == 10

    def test_native_and_web_separated(self):
        fs = date(2026, 9, 10)
        report_day = date(2026, 10, 8)
        rows = _make_rows(
            {
                "iOS": [(fs, 20)],
                "Android": [(fs, 15)],
                "Web": [(fs, 100)],
            },
            {
                ("iOS", fs, 14): 3,
                ("Android", fs, 14): 2,
                ("Web", fs, 14): 10,
            },
            report_day,
        )
        stats = ga4._build_platform_stats(
            rows,
            acquisition_start=WINDOW_START,
            acquisition_end=WINDOW_END,
            report_day=report_day,
            window_end=WINDOW_END,
        )
        assert stats["iOS"]["total_n"] == 20
        assert stats["Android"]["total_n"] == 15
        assert stats["Web"]["total_n"] == 100


class TestBuildResult:
    def _base_stats(self, ios_n, android_n, returned):
        fs = date(2026, 9, 10)
        report_day = date(2026, 10, 8)
        retained = {
            ("iOS", fs, 14): returned // 2 if ios_n and android_n else returned,
            ("Android", fs, 14): returned - returned // 2 if ios_n and android_n else 0,
        }
        rows = _make_rows(
            {"iOS": [(fs, ios_n)], "Android": [(fs, android_n)]},
            retained,
            report_day,
        )
        return ga4._build_platform_stats(
            rows,
            acquisition_start=WINDOW_START,
            acquisition_end=WINDOW_END,
            report_day=report_day,
            window_end=WINDOW_END,
        )

    def test_not_mature(self):
        fs = date(2026, 9, 10)
        report_day = date(2026, 10, 7)  # one day before the D14 window closes
        rows = _make_rows(
            {"iOS": [(fs, 20)], "Android": [(fs, 20)]},
            {("iOS", fs, 14): 3, ("Android", fs, 14): 3},
            report_day,
        )
        stats = ga4._build_platform_stats(
            rows,
            acquisition_start=WINDOW_START,
            acquisition_end=WINDOW_END,
            report_day=report_day,
            window_end=WINDOW_END,
        )
        result = ga4._build_result(
            stats,
            WINDOW_START,
            WINDOW_END,
            report_day,
            datetime(2026, 10, 8, 8, 0, 0, tzinfo=timezone.utc),
            40,
            0.15,
            0.07,
        )
        assert result["status"] == "insufficient"
        assert result["reason"] == "not_mature"

    def test_min_n(self):
        stats = self._base_stats(20, 19, 6)  # n=39, rate would pass
        result = ga4._build_result(
            stats,
            WINDOW_START,
            WINDOW_END,
            date(2026, 10, 8),
            datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc),
            40,
            0.15,
            0.07,
        )
        assert result["status"] == "insufficient"
        assert result["reason"] == "min_n"

    def test_pass_exact_threshold(self):
        stats = self._base_stats(20, 20, 6)  # 6/40 = 0.15
        result = ga4._build_result(
            stats,
            WINDOW_START,
            WINDOW_END,
            date(2026, 10, 8),
            datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc),
            40,
            0.15,
            0.07,
        )
        assert result["status"] == "pass"
        assert result["reason"] == "above_threshold"
        assert result["below_kill_line"] is False

    def test_fail_below_threshold(self):
        stats = self._base_stats(20, 20, 5)  # 5/40 = 0.125
        result = ga4._build_result(
            stats,
            WINDOW_START,
            WINDOW_END,
            date(2026, 10, 8),
            datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc),
            40,
            0.15,
            0.07,
        )
        assert result["status"] == "fail"
        assert result["reason"] == "below_threshold"
        assert result["below_kill_line"] is False

    def test_fail_below_kill_line(self):
        stats = self._base_stats(20, 20, 2)  # 2/40 = 0.05
        result = ga4._build_result(
            stats,
            WINDOW_START,
            WINDOW_END,
            date(2026, 10, 8),
            datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc),
            40,
            0.15,
            0.07,
        )
        assert result["status"] == "fail"
        assert result["below_kill_line"] is True

    def test_web_only_is_insufficient(self):
        fs = date(2026, 9, 10)
        report_day = date(2026, 10, 8)
        rows = _make_rows(
            {"Web": [(fs, 100)]},
            {("Web", fs, 14): 10},
            report_day,
        )
        stats = ga4._build_platform_stats(
            rows,
            acquisition_start=WINDOW_START,
            acquisition_end=WINDOW_END,
            report_day=report_day,
            window_end=WINDOW_END,
        )
        result = ga4._build_result(
            stats,
            WINDOW_START,
            WINDOW_END,
            report_day,
            datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc),
            40,
            0.15,
            0.07,
        )
        assert result["status"] == "insufficient"
        assert result["reason"] == "no_native_data"

    def test_no_data_mature(self):
        result = ga4._build_result(
            {},
            WINDOW_START,
            WINDOW_END,
            date(2026, 10, 8),
            datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc),
            40,
            0.15,
            0.07,
        )
        assert result["status"] == "insufficient"
        assert result["reason"] == "no_data"

    def test_web_excluded_in_output(self):
        fs = date(2026, 9, 10)
        report_day = date(2026, 10, 8)
        rows = _make_rows(
            {"iOS": [(fs, 20)], "Web": [(fs, 100)]},
            {("iOS", fs, 14): 3, ("Web", fs, 14): 10},
            report_day,
        )
        stats = ga4._build_platform_stats(
            rows,
            acquisition_start=WINDOW_START,
            acquisition_end=WINDOW_END,
            report_day=report_day,
            window_end=WINDOW_END,
        )
        result = ga4._build_result(
            stats,
            WINDOW_START,
            WINDOW_END,
            report_day,
            datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc),
            40,
            0.15,
            0.07,
        )
        assert "iOS" in result["platforms"]
        assert "Android" in result["platforms"]
        assert result["excluded_web"]["total_n"] == 100
        assert result["excluded_web"]["reason"] == "unqualified_marketing_mix"


class TestCollectNativeRetentionGate:
    @pytest.fixture
    def mocked_collect(self, monkeypatch, mock_google_libs):
        """Patch the network/credential boundary so collect only sees rows."""
        monkeypatch.setattr(ga4, "_resolve_credentials", Mock(return_value=Mock()))
        monkeypatch.setattr(ga4, "_build_client", Mock(return_value=Mock()))

    def test_collect_returns_pass(self, monkeypatch, mocked_collect):
        fs = date(2026, 9, 10)
        report_day = date(2026, 10, 8)
        rows = _make_rows(
            {"iOS": [(fs, 20)], "Android": [(fs, 20)]},
            {("iOS", fs, 14): 3, ("Android", fs, 14): 3},
            report_day,
        )
        monkeypatch.setattr(ga4, "_fetch_rows", Mock(return_value=rows))

        result = ga4.collect_native_retention_gate(
            window_start=WINDOW_START,
            window_end=WINDOW_END,
            observed_at=datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc),
        )
        assert result["status"] == "pass"
        assert result["reason"] == "above_threshold"
        assert result["native"]["total_n"] == 40
        assert result["native"]["d14"]["eligible_n"] == 40
        assert result["native"]["d14"]["returned"] == 6

    def test_collect_credentials_missing(self, monkeypatch, mocked_collect):
        def boom():
            raise ga4.GateError("credentials_missing")

        monkeypatch.setattr(ga4, "_resolve_credentials", Mock(side_effect=boom))
        result = ga4.collect_native_retention_gate(
            window_start=WINDOW_START,
            window_end=WINDOW_END,
            observed_at=datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc),
        )
        assert result["status"] == "error"
        assert result["reason"] == "credentials_missing"

    def test_collect_api_error_isolated(self, monkeypatch, mocked_collect):
        monkeypatch.setattr(
            ga4,
            "_fetch_rows",
            Mock(side_effect=ga4.GateError("permission_denied")),
        )
        result = ga4.collect_native_retention_gate(
            window_start=WINDOW_START,
            window_end=WINDOW_END,
            observed_at=datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc),
        )
        assert result["status"] == "error"
        assert result["reason"] == "permission_denied"

    def test_collect_not_mature(self, monkeypatch, mocked_collect):
        fs = date(2026, 9, 10)
        report_day = date(2026, 10, 7)
        rows = _make_rows(
            {"iOS": [(fs, 20)], "Android": [(fs, 20)]},
            {("iOS", fs, 14): 3, ("Android", fs, 14): 3},
            report_day,
        )
        monkeypatch.setattr(ga4, "_fetch_rows", Mock(return_value=rows))

        result = ga4.collect_native_retention_gate(
            window_start=WINDOW_START,
            window_end=WINDOW_END,
            observed_at=datetime(2026, 10, 8, 8, 0, 0, tzinfo=timezone.utc),
        )
        assert result["status"] == "insufficient"
        assert result["reason"] == "not_mature"
