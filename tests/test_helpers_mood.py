"""Unit tests for helpers/mood_helpers.py (augments tests/test_mood_provider.py)."""

import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app
from helpers.mood_helpers import (
    _analyze_mood_pattern,
    _get_default_recommendations,
    _get_personalized_recommendations,
    _purge_old_data_inner,
)
from models import Message, UserSession, db


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "RATE_LIMIT_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# ---------------------------------------------------------------------------
# _get_default_recommendations
# ---------------------------------------------------------------------------

class TestDefaultRecommendations:
    def test_returns_nonempty_list(self):
        recs = _get_default_recommendations()
        assert isinstance(recs, list)
        assert len(recs) >= 3

    def test_each_entry_has_required_keys(self):
        for r in _get_default_recommendations():
            assert "type" in r
            assert "title" in r
            assert "description" in r
            assert "action" in r


# ---------------------------------------------------------------------------
# _get_personalized_recommendations — boundary coverage
# ---------------------------------------------------------------------------

class TestPersonalizedRecommendationsBoundaries:
    def test_exactly_2_0_is_low_tier(self):
        recs = _get_personalized_recommendations(2.0, [])
        titles = [r["title"] for r in recs]
        assert "Reach Out for Support" in titles

    def test_just_above_2_0_is_moderate(self):
        recs = _get_personalized_recommendations(2.01, [])
        titles = [r["title"] for r in recs]
        assert "Engage in Enjoyable Activities" in titles

    def test_exactly_3_5_is_moderate(self):
        recs = _get_personalized_recommendations(3.5, [])
        titles = [r["title"] for r in recs]
        assert "Engage in Enjoyable Activities" in titles

    def test_above_3_5_is_positive(self):
        recs = _get_personalized_recommendations(4.0, [])
        titles = [r["title"] for r in recs]
        assert "Maintain Positive Habits" in titles

    def test_always_returns_three_items(self):
        for avg in [1.0, 2.0, 2.5, 3.5, 4.0, 5.0]:
            assert len(_get_personalized_recommendations(avg, [])) == 3


# ---------------------------------------------------------------------------
# _analyze_mood_pattern — extra edge cases
# ---------------------------------------------------------------------------

class _Entry:
    def __init__(self, mood):
        self.mood_level = mood


class TestAnalyzeMoodPatternExtras:
    def test_average_rounded_to_two_decimals(self):
        result = _analyze_mood_pattern([_Entry(1), _Entry(2), _Entry(2)])
        assert result["average"] == round((1 + 2 + 2) / 3, 2)

    def test_recent_moods_capped_at_five(self):
        entries = [_Entry(i) for i in range(1, 11)]
        result = _analyze_mood_pattern(entries)
        assert len(result["recent_moods"]) == 5
        assert result["recent_moods"] == [1, 2, 3, 4, 5]

    def test_two_entries_trend_insufficient(self):
        # Only 2 entries: older_slice (mood_levels[3:6]) is empty -> insufficient
        result = _analyze_mood_pattern([_Entry(1), _Entry(5)])
        assert result["trend"] == "insufficient_data"


# ---------------------------------------------------------------------------
# _purge_old_data_inner
# ---------------------------------------------------------------------------

class TestPurgeOldDataInner:
    def _make_session(self, created_at=None):
        sid = str(uuid.uuid4())
        s = UserSession(id=sid)
        if created_at is not None:
            s.created_at = created_at
        db.session.add(s)
        db.session.commit()
        return sid

    def _make_message(self, session_id, timestamp):
        msg = Message(
            session_id=session_id,
            content="x",
            is_user=True,
            timestamp=timestamp,
        )
        db.session.add(msg)
        db.session.commit()

    def test_purges_messages_older_than_retention(self, app):
        app.config["MESSAGE_RETENTION_DAYS"] = 30
        app.config["SESSION_RETENTION_DAYS"] = 0  # disable session purge
        sid = self._make_session()
        self._make_message(sid, datetime.utcnow() - timedelta(days=60))
        self._make_message(sid, datetime.utcnow() - timedelta(days=5))

        # Disable pgvector cleanup (sqlite doesn't support its cursor CM,
        # causing a rollback that undoes our deletes)
        with patch("providers.memory.MEMORY_ENABLED", False):
            counts = _purge_old_data_inner()
            db.session.commit()
        remaining = Message.query.count()

        assert counts["messages"] == 1
        assert remaining == 1

    def test_zero_retention_disables_message_purge(self, app):
        app.config["MESSAGE_RETENTION_DAYS"] = 0
        app.config["SESSION_RETENTION_DAYS"] = 0
        sid = self._make_session()
        self._make_message(sid, datetime.utcnow() - timedelta(days=9999))

        counts = _purge_old_data_inner()

        assert "messages" not in counts
        assert Message.query.count() == 1

    def test_purges_sessions_older_than_retention(self, app):
        app.config["MESSAGE_RETENTION_DAYS"] = 0
        app.config["SESSION_RETENTION_DAYS"] = 14
        old = self._make_session(datetime.utcnow() - timedelta(days=30))
        new = self._make_session(datetime.utcnow() - timedelta(days=1))

        with patch("providers.memory.MEMORY_ENABLED", False):
            counts = _purge_old_data_inner()
            db.session.commit()

        assert counts["sessions"] == 1
        remaining_ids = [s.id for s in UserSession.query.all()]
        assert new in remaining_ids
        assert old not in remaining_ids

    def test_missing_memory_provider_is_non_fatal(self, app):
        app.config["MESSAGE_RETENTION_DAYS"] = 0
        app.config["SESSION_RETENTION_DAYS"] = 0
        # Simulate memory cleanup raising - should be silently swallowed
        with patch(
            "providers.memory.cleanup_expired_memories",
            side_effect=Exception("unavailable"),
        ):
            counts = _purge_old_data_inner()
        assert isinstance(counts, dict)

    def test_returns_dict(self, app):
        app.config["MESSAGE_RETENTION_DAYS"] = 0
        app.config["SESSION_RETENTION_DAYS"] = 0
        assert isinstance(_purge_old_data_inner(), dict)
