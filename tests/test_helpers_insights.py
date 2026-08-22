"""Unit tests for helpers/insights_helpers.py (pure analytics, no Flask)."""

import os
import sys
from datetime import datetime, timedelta, timezone

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from helpers.insights_helpers import (
    CRISIS_KEYWORD_BUCKETS,
    bucket_keyword,
    compute_keyword_heatmap,
    compute_next_steps,
    compute_quest_correlation,
    compute_weekly_trend,
    pearson_correlation,
)


class _MoodEntry:
    def __init__(self, mood_level, timestamp):
        self.mood_level = mood_level
        self.timestamp = timestamp


class _Message:
    def __init__(self, content, timestamp, is_user=True):
        self.content = content
        self.timestamp = timestamp
        self.is_user = is_user


class _Outcome:
    def __init__(self, exercise_type=None, mood_before=None, mood_after=None):
        self.exercise_type = exercise_type
        self.mood_before = mood_before
        self.mood_after = mood_after


# ---------------------------------------------------------------------------
# compute_weekly_trend
# ---------------------------------------------------------------------------

class TestComputeWeeklyTrend:
    def test_empty_returns_nulls(self):
        out = compute_weekly_trend([])
        assert out["count"] == 0
        assert out["mean"] is None
        assert out["stdev"] is None
        assert out["min"] is None
        assert out["max"] is None
        assert out["daily"] == []
        assert out["window_days"] == 7

    def test_single_entry(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        out = compute_weekly_trend([_MoodEntry(3, now)])
        assert out["count"] == 1
        assert out["mean"] == 3.0
        assert out["stdev"] == 0.0  # single value pstdev is 0
        assert out["min"] == 3 and out["max"] == 3
        assert len(out["daily"]) == 1

    def test_multiple_entries_in_window(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        entries = [
            _MoodEntry(1, now - timedelta(days=1)),
            _MoodEntry(3, now - timedelta(days=2)),
            _MoodEntry(5, now - timedelta(days=3)),
        ]
        out = compute_weekly_trend(entries)
        assert out["count"] == 3
        assert out["mean"] == 3.0
        assert out["min"] == 1 and out["max"] == 5
        assert len(out["daily"]) == 3

    def test_entries_outside_window_excluded(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        entries = [
            _MoodEntry(5, now - timedelta(days=1)),   # in window
            _MoodEntry(1, now - timedelta(days=20)),  # out
        ]
        out = compute_weekly_trend(entries, window_days=7)
        assert out["count"] == 1
        assert out["mean"] == 5.0

    def test_30_day_window(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        entries = [_MoodEntry(i, now - timedelta(days=d)) for i, d in enumerate([5, 10, 20])]
        out = compute_weekly_trend(entries, window_days=30)
        assert out["count"] == 3
        assert out["window_days"] == 30

    def test_daily_bucket_averaging(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        d1 = now - timedelta(days=1)
        entries = [
            _MoodEntry(2, d1),
            _MoodEntry(4, d1),  # same day
        ]
        out = compute_weekly_trend(entries)
        assert len(out["daily"]) == 1
        assert out["daily"][0]["avg"] == 3.0
        assert out["daily"][0]["count"] == 2


# ---------------------------------------------------------------------------
# bucket_keyword
# ---------------------------------------------------------------------------

class TestBucketKeyword:
    def test_hopelessness_detected(self):
        assert bucket_keyword("I feel so hopeless today") == "hopelessness"

    def test_self_harm_detected(self):
        assert bucket_keyword("I want to hurt myself") == "self_harm"

    def test_suicidal_ideation_detected(self):
        assert bucket_keyword("I want to end it all") == "suicidal_ideation"

    def test_anxiety_detected(self):
        assert bucket_keyword("I am having a panic attack") == "anxiety"

    def test_isolation_detected(self):
        assert bucket_keyword("I feel so alone") == "isolation"

    def test_no_match_returns_none(self):
        assert bucket_keyword("Today was a good day!") is None

    def test_empty_string(self):
        assert bucket_keyword("") is None

    def test_none_returns_none(self):
        assert bucket_keyword(None) is None  # type: ignore[arg-type]

    def test_case_insensitive(self):
        assert bucket_keyword("HOPELESS") == "hopelessness"


# ---------------------------------------------------------------------------
# compute_keyword_heatmap
# ---------------------------------------------------------------------------

class TestKeywordHeatmap:
    def test_empty_messages(self):
        out = compute_keyword_heatmap([])
        assert out["heatmap"] == []
        assert out["totals_per_bucket"] == {}
        assert out["buckets"] == list(CRISIS_KEYWORD_BUCKETS.keys())

    def test_ai_messages_excluded(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        msgs = [
            _Message("I feel hopeless", now, is_user=False),  # AI msg, ignored
            _Message("good day", now, is_user=True),
        ]
        out = compute_keyword_heatmap(msgs)
        assert out["totals_per_bucket"] == {}

    def test_user_message_with_crisis_keyword(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        msgs = [_Message("I feel hopeless and worthless", now, is_user=True)]
        out = compute_keyword_heatmap(msgs)
        assert out["totals_per_bucket"].get("hopelessness") == 1
        assert len(out["heatmap"]) == 1

    def test_outside_window_excluded(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        msgs = [_Message("hopeless", now - timedelta(days=40), is_user=True)]
        out = compute_keyword_heatmap(msgs, window_days=30)
        assert out["totals_per_bucket"] == {}

    def test_no_raw_content_in_output(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        raw = "I feel hopeless and my secret is X"
        msgs = [_Message(raw, now, is_user=True)]
        out = compute_keyword_heatmap(msgs)
        # Privacy: raw text must never appear in the response
        serialized = str(out)
        assert "secret" not in serialized
        assert raw not in serialized


# ---------------------------------------------------------------------------
# compute_quest_correlation
# ---------------------------------------------------------------------------

class TestQuestCorrelation:
    def test_empty(self):
        out = compute_quest_correlation([])
        assert out["overall_delta"] is None
        assert out["per_type"] == []
        assert out["n"] == 0

    def test_missing_mood_values_ignored(self):
        out = compute_quest_correlation([
            _Outcome("breathing", None, 4),
            _Outcome("breathing", 2, None),
        ])
        assert out["n"] == 0

    def test_positive_delta(self):
        out = compute_quest_correlation([
            _Outcome("breathing", 2, 4),
            _Outcome("breathing", 3, 4),
        ])
        assert out["per_type"][0]["type"] == "breathing"
        assert out["per_type"][0]["n"] == 2
        assert out["per_type"][0]["avg_delta"] == 1.5

    def test_per_type_sorted_by_delta_desc(self):
        out = compute_quest_correlation([
            _Outcome("grounding", 3, 3),      # delta 0
            _Outcome("breathing", 1, 4),      # delta 3
            _Outcome("journaling", 2, 3),     # delta 1
        ])
        types = [t["type"] for t in out["per_type"]]
        assert types == ["breathing", "journaling", "grounding"]

    def test_none_type_becomes_unknown(self):
        out = compute_quest_correlation([_Outcome(None, 2, 4)])
        assert out["per_type"][0]["type"] == "unknown"


# ---------------------------------------------------------------------------
# compute_next_steps
# ---------------------------------------------------------------------------

class TestNextSteps:
    def _trend(self, mean=None, stdev=0):
        return {"mean": mean, "stdev": stdev}

    def _heatmap(self, totals=None):
        return {"totals_per_bucket": totals or {}}

    def _corr(self, per_type=None):
        return {"per_type": per_type or []}

    def test_crisis_keywords_trigger_urgent(self):
        ctas = compute_next_steps(
            self._trend(3.0),
            self._heatmap({"suicidal_ideation": 2}),
            self._corr(),
        )
        assert ctas[0]["type"] == "crisis_resource"

    def test_self_harm_also_triggers_crisis(self):
        ctas = compute_next_steps(
            self._trend(3.0),
            self._heatmap({"self_harm": 1}),
            self._corr(),
        )
        assert any(c["type"] == "crisis_resource" for c in ctas)

    def test_low_mood_recommends_reach_out_and_best_quest(self):
        ctas = compute_next_steps(
            self._trend(2.0),
            self._heatmap(),
            self._corr(per_type=[{"type": "breathing", "n": 5, "avg_delta": 1.2}]),
        )
        types = [c["type"] for c in ctas]
        assert "reach_out" in types
        assert "quest_recommendation" in types

    def test_high_stdev_triggers_grounding(self):
        ctas = compute_next_steps(
            self._trend(3.0, stdev=2.0),
            self._heatmap(),
            self._corr(),
        )
        assert any(c["type"] == "grounding" for c in ctas)

    def test_healthy_pattern_falls_back_to_maintain(self):
        ctas = compute_next_steps(
            self._trend(4.0, stdev=0.5),
            self._heatmap(),
            self._corr(),
        )
        assert ctas[0]["type"] == "maintain"

    def test_always_returns_at_most_3(self):
        ctas = compute_next_steps(
            self._trend(1.5, stdev=2.5),
            self._heatmap({"suicidal_ideation": 2, "self_harm": 1}),
            self._corr(per_type=[{"type": "breathing", "n": 5, "avg_delta": 1.2}]),
        )
        assert len(ctas) <= 3

    def test_all_ctas_have_required_keys(self):
        ctas = compute_next_steps(
            self._trend(2.0),
            self._heatmap({"suicidal_ideation": 1}),
            self._corr(per_type=[{"type": "grounding", "n": 3, "avg_delta": 0.5}]),
        )
        for c in ctas:
            assert "type" in c
            assert "title" in c
            assert "description" in c
            assert "action" in c


# ---------------------------------------------------------------------------
# pearson_correlation
# ---------------------------------------------------------------------------

class TestPearsonCorrelation:
    def test_insufficient_data(self):
        assert pearson_correlation([], []) is None
        assert pearson_correlation([1], [1]) is None

    def test_length_mismatch(self):
        assert pearson_correlation([1, 2], [1]) is None

    def test_perfect_positive(self):
        r = pearson_correlation([1, 2, 3], [2, 4, 6])
        assert r == 1.0 or (r is not None and abs(r - 1.0) < 1e-3)

    def test_perfect_negative(self):
        r = pearson_correlation([1, 2, 3], [6, 4, 2])
        assert r == -1.0 or (r is not None and abs(r + 1.0) < 1e-3)

    def test_zero_variance_returns_none(self):
        assert pearson_correlation([3, 3, 3], [1, 2, 3]) is None
