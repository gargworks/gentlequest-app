"""Unit tests for helpers/quest_matcher.py (pure rule engine)."""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from helpers.quest_matcher import (
    ACHIEVEMENTS,
    check_achievements,
    classify_from_keywords,
    classify_mood_state,
    compute_streak,
    pick_quest_types,
    select_daily_quests,
)


class _Mood:
    def __init__(self, level, days_ago=0):
        self.mood_level = level
        self.timestamp = datetime.utcnow() - timedelta(days=days_ago)


class _Msg:
    def __init__(self, content, is_user=True):
        self.content = content
        self.is_user = is_user
        self.timestamp = datetime.utcnow()


class _Quest:
    _next_id = 1

    def __init__(self, quest_type, qid=None):
        self.id = qid or _Quest._next_id
        _Quest._next_id += 1
        self.quest_type = quest_type


# ---------------------------------------------------------------------------
# classify_mood_state
# ---------------------------------------------------------------------------

class TestClassifyMoodState:
    def test_no_entries_moderate(self):
        assert classify_mood_state([]) == "moderate"

    def test_all_old_entries_moderate(self):
        # Entries outside window fall through
        old = [_Mood(5, days_ago=30)]
        assert classify_mood_state(old, window_days=7) == "moderate"

    def test_low_mean(self):
        moods = [_Mood(1), _Mood(2), _Mood(1)]
        assert classify_mood_state(moods) == "low"

    def test_high_mean(self):
        moods = [_Mood(5), _Mood(4), _Mood(4)]
        assert classify_mood_state(moods) == "high"

    def test_moderate_mean(self):
        moods = [_Mood(3), _Mood(3), _Mood(3)]
        assert classify_mood_state(moods) == "moderate"

    def test_unstable_wide_spread(self):
        moods = [_Mood(1), _Mood(5), _Mood(3)]
        assert classify_mood_state(moods) == "unstable"

    def test_small_sample_skips_variability_check(self):
        # 2 entries: can't trigger unstable, falls to mean classification
        moods = [_Mood(1), _Mood(5)]
        # mean = 3 → moderate
        assert classify_mood_state(moods) == "moderate"


# ---------------------------------------------------------------------------
# classify_from_keywords
# ---------------------------------------------------------------------------

class TestClassifyFromKeywords:
    def test_empty_messages_none(self):
        assert classify_from_keywords([]) is None

    def test_single_anxiety_not_enough(self):
        assert classify_from_keywords([_Msg("I feel anxious")]) is None

    def test_double_anxiety_triggers(self):
        msgs = [_Msg("I am anxious"), _Msg("more panic")]
        assert classify_from_keywords(msgs) == "anxious"

    def test_isolation_triggers_low(self):
        msgs = [_Msg("I feel so alone"), _Msg("nobody cares")]
        assert classify_from_keywords(msgs) == "low"

    def test_hopelessness_triggers_low(self):
        msgs = [_Msg("hopeless"), _Msg("worthless")]
        assert classify_from_keywords(msgs) == "low"

    def test_ai_messages_ignored(self):
        msgs = [
            _Msg("I feel anxious", is_user=False),
            _Msg("panic attack", is_user=False),
        ]
        assert classify_from_keywords(msgs) is None


# ---------------------------------------------------------------------------
# pick_quest_types
# ---------------------------------------------------------------------------

class TestPickQuestTypes:
    def test_returns_n_types(self):
        types = pick_quest_types([], [], n=3)
        assert len(types) == 3

    def test_anxious_override_starts_with_breathing(self):
        msgs = [_Msg("anxious"), _Msg("panic")]
        types = pick_quest_types([], msgs, n=3)
        assert types[0] == "breathing"

    def test_low_mood_prioritizes_gratitude(self):
        moods = [_Mood(1), _Mood(2), _Mood(1)]
        types = pick_quest_types(moods, [], n=3)
        assert types[0] == "gratitude"

    def test_unstable_prioritizes_grounding(self):
        moods = [_Mood(1), _Mood(5), _Mood(3)]
        types = pick_quest_types(moods, [], n=3)
        assert types[0] == "grounding"

    def test_no_duplicates(self):
        types = pick_quest_types([], [], n=5)
        assert len(types) == len(set(types))


# ---------------------------------------------------------------------------
# select_daily_quests
# ---------------------------------------------------------------------------

class TestSelectDailyQuests:
    def test_empty_quests_returns_empty(self):
        assert select_daily_quests([], ["breathing"], n=3) == []

    def test_matches_preferred_type_first(self):
        quests = [
            _Quest("journaling", qid=1),
            _Quest("breathing", qid=2),
        ]
        picked = select_daily_quests(quests, ["breathing", "journaling"], n=2)
        assert picked[0].id == 2
        assert picked[1].id == 1

    def test_fills_from_remaining_when_no_match(self):
        quests = [_Quest("check_in", qid=1), _Quest("check_in", qid=2)]
        picked = select_daily_quests(quests, ["breathing"], n=2)
        # No breathing quests, falls through to remainder
        assert len(picked) == 2

    def test_skips_already_completed(self):
        quests = [_Quest("breathing", qid=1), _Quest("breathing", qid=2)]
        picked = select_daily_quests(quests, ["breathing"], completed_today_ids=[1], n=1)
        assert picked[0].id == 2

    def test_respects_n_limit(self):
        quests = [_Quest("check_in", qid=i) for i in range(10)]
        picked = select_daily_quests(quests, ["check_in"], n=3)
        assert len(picked) == 3


# ---------------------------------------------------------------------------
# compute_streak
# ---------------------------------------------------------------------------

class TestComputeStreak:
    def test_empty(self):
        assert compute_streak([]) == {"current": 0, "longest": 0}

    def test_single_today(self):
        s = compute_streak([datetime.utcnow()])
        assert s["current"] == 1
        assert s["longest"] == 1

    def test_consecutive_days(self):
        now = datetime.utcnow()
        dates = [now - timedelta(days=i) for i in range(3)]
        s = compute_streak(dates)
        assert s["current"] == 3
        assert s["longest"] == 3

    def test_broken_streak_current_zero(self):
        now = datetime.utcnow()
        dates = [now - timedelta(days=10)]  # Old, >1 day ago
        s = compute_streak(dates)
        assert s["current"] == 0
        assert s["longest"] == 1

    def test_longest_exceeds_current(self):
        now = datetime.utcnow()
        # 5-day streak ending 10 days ago (broken), 2-day streak ending today
        dates = (
            [now - timedelta(days=d) for d in [10, 11, 12, 13, 14]]
            + [now - timedelta(days=d) for d in [0, 1]]
        )
        s = compute_streak(dates)
        assert s["current"] == 2
        assert s["longest"] == 5

    def test_dedupes_same_day(self):
        now = datetime.utcnow()
        s = compute_streak([now, now, now])
        assert s["current"] == 1
        assert s["longest"] == 1

    def test_yesterday_still_counts(self):
        now = datetime.utcnow()
        s = compute_streak([now - timedelta(days=1)])
        assert s["current"] == 1


# ---------------------------------------------------------------------------
# check_achievements
# ---------------------------------------------------------------------------

class TestCheckAchievements:
    def test_no_stats_no_achievements(self):
        assert check_achievements({}) == []

    def test_first_quest_awarded(self):
        new = check_achievements({"total_completed": 1})
        assert "first_quest" in new

    def test_already_earned_not_returned(self):
        new = check_achievements(
            {"total_completed": 1},
            already_earned=["first_quest"],
        )
        assert "first_quest" not in new

    def test_streak_badges_cascade(self):
        new = check_achievements({"current_streak": 30, "total_completed": 10})
        assert "seven_day_streak" in new
        assert "thirty_day_streak" in new
        assert "ten_quests" in new

    def test_mood_lifter_awarded_for_positive_delta(self):
        new = check_achievements({"max_mood_delta": 2, "total_completed": 1})
        assert "mood_lifter" in new

    def test_all_keys_in_ACHIEVEMENTS(self):
        new = check_achievements({
            "total_completed": 100,
            "current_streak": 30,
            "max_mood_delta": 5,
        })
        for key in new:
            assert key in ACHIEVEMENTS
