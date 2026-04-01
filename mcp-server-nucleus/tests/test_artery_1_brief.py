"""Artery 1: Morning brief persists recommendation as Strategy engram.

Verifies _find_engram_by_key, _check_recommendation_followed,
and the Artery 1 block in _morning_brief_impl that writes
brief_rec_{today} engrams and compares to yesterday.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server_nucleus.runtime.morning_brief_ops import (
    _find_engram_by_key,
    _check_recommendation_followed,
)


@pytest.fixture
def brief_brain(tmp_path):
    """Brain with engrams directory for brief engram tests."""
    brain = tmp_path / ".brain"
    (brain / "engrams").mkdir(parents=True)
    (brain / "ledger").mkdir(parents=True)
    return brain


class TestFindEngramByKey:
    """Verify _find_engram_by_key searches engram ledger correctly."""

    def test_finds_existing_key(self, brief_brain):
        """Should return engram matching the exact key."""
        engram = {
            "key": "brief_rec_20260401",
            "value": "[CONTINUE] Deploy auth fix",
            "context": "Strategy",
            "intensity": 7,
            "timestamp": datetime.now().isoformat(),
        }
        (brief_brain / "engrams" / "ledger.jsonl").write_text(
            json.dumps(engram) + "\n"
        )

        result = _find_engram_by_key(brief_brain, "brief_rec_20260401")
        assert result is not None
        assert result["key"] == "brief_rec_20260401"
        assert result["value"] == "[CONTINUE] Deploy auth fix"

    def test_returns_none_for_missing_key(self, brief_brain):
        """Should return None when key doesn't exist."""
        (brief_brain / "engrams" / "ledger.jsonl").write_text(
            json.dumps({"key": "other_key", "value": "x"}) + "\n"
        )

        result = _find_engram_by_key(brief_brain, "nonexistent")
        assert result is None

    def test_returns_none_for_missing_ledger(self, brief_brain):
        """Should return None when ledger.jsonl doesn't exist."""
        result = _find_engram_by_key(brief_brain, "any_key")
        assert result is None

    def test_skips_deleted_engrams(self, brief_brain):
        """Should skip engrams marked as deleted."""
        deleted = {
            "key": "brief_rec_20260401",
            "value": "[START] Old rec",
            "deleted": True,
            "timestamp": datetime.now().isoformat(),
        }
        (brief_brain / "engrams" / "ledger.jsonl").write_text(
            json.dumps(deleted) + "\n"
        )

        result = _find_engram_by_key(brief_brain, "brief_rec_20260401")
        assert result is None

    def test_returns_latest_entry_for_duplicate_keys(self, brief_brain):
        """When multiple entries have same key, return the latest."""
        old = {"key": "my_key", "value": "old value", "timestamp": "2026-03-30"}
        new = {"key": "my_key", "value": "new value", "timestamp": "2026-03-31"}
        with open(brief_brain / "engrams" / "ledger.jsonl", "w") as f:
            f.write(json.dumps(old) + "\n")
            f.write(json.dumps(new) + "\n")

        result = _find_engram_by_key(brief_brain, "my_key")
        assert result["value"] == "new value"

    def test_skips_corrupt_lines(self, brief_brain):
        """Corrupt JSON lines should be skipped gracefully."""
        valid = {
            "key": "target",
            "value": "found it",
            "timestamp": datetime.now().isoformat(),
        }
        with open(brief_brain / "engrams" / "ledger.jsonl", "w") as f:
            f.write("CORRUPT\n")
            f.write(json.dumps(valid) + "\n")
            f.write("{bad json\n")

        result = _find_engram_by_key(brief_brain, "target")
        assert result is not None
        assert result["value"] == "found it"


class TestCheckRecommendationFollowed:
    """Verify _check_recommendation_followed matches events to recs."""

    def test_followed_when_matching_event(self):
        """Should return True when task_completed event matches rec."""
        yesterday_rec = {"value": "[CONTINUE] Deploy auth fix"}
        events = [
            {
                "type": "task_completed",
                "data": {"task": "Deploy auth fix for production"},
            }
        ]
        assert _check_recommendation_followed(yesterday_rec, {}, events) is True

    def test_not_followed_when_no_matching_event(self):
        """Should return False when no events match the recommendation."""
        yesterday_rec = {"value": "[CONTINUE] Deploy auth fix"}
        events = [
            {"type": "task_completed", "data": {"task": "Update README"}},
        ]
        assert _check_recommendation_followed(yesterday_rec, {}, events) is False

    def test_followed_via_in_progress_task(self):
        """Should return True when rec matches an in-progress task."""
        yesterday_rec = {"value": "[START] Deploy auth fix"}
        tasks_data = {
            "in_progress": [
                {"description": "Deploy the auth fix to staging"},
            ]
        }
        assert _check_recommendation_followed(yesterday_rec, tasks_data, []) is True

    def test_pending_task_not_counted(self):
        """Pending (not yet claimed) tasks should NOT count as followed."""
        yesterday_rec = {"value": "[START] Deploy auth fix"}
        tasks_data = {
            "pending": [
                {"description": "Deploy the auth fix to staging"},
            ]
        }
        assert _check_recommendation_followed(yesterday_rec, tasks_data, []) is False

    def test_false_when_rec_has_no_bracket(self):
        """Rec without ] bracket → can't extract task ref → False."""
        yesterday_rec = {"value": "Deploy auth fix"}
        assert _check_recommendation_followed(yesterday_rec, {}, []) is False

    def test_false_when_task_ref_too_short(self):
        """Single-word task ref → too vague → False."""
        yesterday_rec = {"value": "[CONTINUE] deploy"}
        events = [{"type": "task_completed", "data": {"task": "deploy something"}}]
        assert _check_recommendation_followed(yesterday_rec, {}, events) is False

    def test_multiple_event_types_checked(self):
        """Should match task_claimed, slot_task_completed, etc."""
        yesterday_rec = {"value": "[START] Deploy auth fix"}
        for event_type in ("task_claimed", "slot_task_completed",
                           "task_completed_with_fence", "task_state_changed"):
            events = [
                {"type": event_type, "data": {"task": "Deploy auth fix now"}},
            ]
            assert _check_recommendation_followed(yesterday_rec, {}, events) is True

    def test_context_suffix_stripped(self):
        """Recommendation with '| Context: ...' should still match."""
        yesterday_rec = {
            "value": "[CONTINUE] Deploy auth fix | Context: auth_architecture"
        }
        events = [
            {"type": "task_completed", "data": {"task": "Deploy auth fix done"}},
        ]
        assert _check_recommendation_followed(yesterday_rec, {}, events) is True
