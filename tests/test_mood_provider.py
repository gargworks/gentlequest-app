"""Unit tests for mood detection, routing logic, and edge cases."""

import os
import sys
import json
import uuid
import pytest
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, _analyze_mood_pattern, _get_personalized_recommendations
from models import db, MoodEntry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    os.environ["PYTEST_CURRENT_TEST"] = "true"
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
        "RATE_LIMIT_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _entry(mood_level):
    """Helper to create a lightweight object with a .mood_level attribute."""
    return SimpleNamespace(mood_level=mood_level)


# ---------------------------------------------------------------------------
# _analyze_mood_pattern — mood detection
# ---------------------------------------------------------------------------

class TestAnalyzeMoodPattern:
    def test_empty_entries_returns_insufficient(self):
        result = _analyze_mood_pattern([])
        assert result["pattern"] == "insufficient_data"
        assert result["trend"] == "unknown"

    def test_single_entry_insufficient_trend(self):
        result = _analyze_mood_pattern([_entry(3)])
        assert result["trend"] == "insufficient_data"
        assert result["pattern"] == "insufficient_data"

    def test_consistently_low(self):
        entries = [_entry(1), _entry(2), _entry(1)]
        result = _analyze_mood_pattern(entries)
        assert result["pattern"] == "consistently_low"

    def test_consistently_high(self):
        entries = [_entry(5), _entry(4), _entry(5)]
        result = _analyze_mood_pattern(entries)
        assert result["pattern"] == "consistently_high"

    def test_improving_pattern(self):
        # mood_levels[0] < [1] < [2] — ascending order
        entries = [_entry(2), _entry(3), _entry(4)]
        result = _analyze_mood_pattern(entries)
        assert result["pattern"] == "improving"

    def test_declining_pattern(self):
        # mood_levels[0] > [1] > [2] — descending order
        entries = [_entry(4), _entry(3), _entry(2)]
        result = _analyze_mood_pattern(entries)
        assert result["pattern"] == "declining"

    def test_fluctuating_pattern(self):
        entries = [_entry(1), _entry(5), _entry(2)]
        result = _analyze_mood_pattern(entries)
        assert result["pattern"] == "fluctuating"

    def test_trend_improving_with_enough_data(self):
        # recent (first 3) avg high, older (3:6) avg low → improving
        entries = [_entry(5), _entry(5), _entry(5), _entry(1), _entry(1), _entry(1)]
        result = _analyze_mood_pattern(entries)
        assert result["trend"] == "improving"

    def test_trend_declining_with_enough_data(self):
        entries = [_entry(1), _entry(1), _entry(1), _entry(5), _entry(5), _entry(5)]
        result = _analyze_mood_pattern(entries)
        assert result["trend"] == "declining"

    def test_trend_stable(self):
        entries = [_entry(3), _entry(3), _entry(3), _entry(3), _entry(3), _entry(3)]
        result = _analyze_mood_pattern(entries)
        assert result["trend"] == "stable"

    def test_average_is_calculated(self):
        entries = [_entry(2), _entry(4)]
        result = _analyze_mood_pattern(entries)
        assert result["average"] == 3.0

    def test_recent_moods_capped_at_five(self):
        entries = [_entry(i) for i in [5, 4, 3, 2, 1, 5, 4]]
        result = _analyze_mood_pattern(entries)
        assert result["recent_moods"] == [5, 4, 3, 2, 1]


# ---------------------------------------------------------------------------
# _get_personalized_recommendations — routing logic
# ---------------------------------------------------------------------------

class TestPersonalizedRecommendations:
    def test_low_mood_returns_immediate_support(self):
        recs = _get_personalized_recommendations(1.5, [])
        types = [r["type"] for r in recs]
        assert "immediate" in types

    def test_moderate_mood_returns_social(self):
        recs = _get_personalized_recommendations(3.0, [])
        types = [r["type"] for r in recs]
        assert "social" in types

    def test_good_mood_returns_growth(self):
        recs = _get_personalized_recommendations(4.5, [])
        types = [r["type"] for r in recs]
        assert "growth" in types

    def test_boundary_low_to_moderate(self):
        """avg_mood == 2.0 should route to low mood path (<=2.0)."""
        recs = _get_personalized_recommendations(2.0, [])
        types = [r["type"] for r in recs]
        assert "immediate" in types

    def test_boundary_moderate_to_good(self):
        """avg_mood == 3.5 should route to moderate path (<=3.5)."""
        recs = _get_personalized_recommendations(3.5, [])
        types = [r["type"] for r in recs]
        assert "social" in types

    def test_boundary_just_above_moderate(self):
        """avg_mood == 3.6 should route to good mood path (>3.5)."""
        recs = _get_personalized_recommendations(3.6, [])
        types = [r["type"] for r in recs]
        assert "maintenance" in types

    def test_all_routes_return_non_empty(self):
        for avg in [1.0, 2.5, 4.0]:
            recs = _get_personalized_recommendations(avg, [])
            assert len(recs) > 0


# ---------------------------------------------------------------------------
# Mood entry API — validation & edge cases
# ---------------------------------------------------------------------------

class TestMoodEntryAPI:
    def _post_mood(self, client, payload, session_id=None):
        if session_id is None:
            session_id = str(uuid.uuid4())
        return client.post(
            "/api/mood_entry",
            data=json.dumps(payload),
            content_type="application/json",
            headers={"X-Session-ID": session_id},
        )

    def test_valid_mood_entry(self, client):
        resp = self._post_mood(client, {"mood_level": 3, "note": "feeling ok"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["mood_level"] == 3

    def test_empty_body_rejected(self, client):
        resp = client.post(
            "/api/mood_entry",
            data="",
            content_type="application/json",
            headers={"X-Session-ID": "test-session-1"},
        )
        assert resp.status_code == 400

    def test_missing_mood_level_rejected(self, client):
        resp = self._post_mood(client, {"note": "no level"})
        assert resp.status_code == 400

    def test_mood_level_zero_rejected(self, client):
        resp = self._post_mood(client, {"mood_level": 0})
        assert resp.status_code == 400

    def test_mood_level_six_rejected(self, client):
        resp = self._post_mood(client, {"mood_level": 6})
        assert resp.status_code == 400

    def test_mood_level_negative_rejected(self, client):
        resp = self._post_mood(client, {"mood_level": -1})
        assert resp.status_code == 400

    def test_mood_level_string_rejected(self, client):
        resp = self._post_mood(client, {"mood_level": "happy"})
        assert resp.status_code == 400

    def test_empty_note_accepted(self, client):
        resp = self._post_mood(client, {"mood_level": 4, "note": ""})
        assert resp.status_code == 200

    def test_note_with_script_tag_sanitized(self, client):
        resp = self._post_mood(client, {"mood_level": 3, "note": "<script>alert(1)</script>"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "<script" not in data["note"]

    def test_non_english_note_accepted(self, client):
        resp = self._post_mood(client, {"mood_level": 4, "note": "je me sens bien aujourd'hui"})
        assert resp.status_code == 200
        assert resp.get_json()["note"] == "je me sens bien aujourd'hui"

    def test_unicode_emoji_note_accepted(self, client):
        resp = self._post_mood(client, {"mood_level": 5, "note": "feeling great! 🎉😊"})
        assert resp.status_code == 200
        assert "🎉" in resp.get_json()["note"]

    def test_cjk_characters_accepted(self, client):
        resp = self._post_mood(client, {"mood_level": 3, "note": "今日は気分がいい"})
        assert resp.status_code == 200
        assert resp.get_json()["note"] == "今日は気分がいい"

    def test_arabic_text_accepted(self, client):
        resp = self._post_mood(client, {"mood_level": 2, "note": "أشعر بالحزن"})
        assert resp.status_code == 200

    def test_mood_level_boundary_1_accepted(self, client):
        resp = self._post_mood(client, {"mood_level": 1})
        assert resp.status_code == 200

    def test_mood_level_boundary_5_accepted(self, client):
        resp = self._post_mood(client, {"mood_level": 5})
        assert resp.status_code == 200

    def test_feedback_prompt_on_third_checkin(self, client):
        sid = str(uuid.uuid4())
        for i in range(3):
            resp = self._post_mood(client, {"mood_level": 3}, session_id=sid)
            assert resp.status_code == 200
        data = resp.get_json()
        assert data["show_feedback_prompt"] is True

    def test_no_feedback_prompt_on_first_checkin(self, client):
        sid = str(uuid.uuid4())
        resp = self._post_mood(client, {"mood_level": 3}, session_id=sid)
        data = resp.get_json()
        assert data["show_feedback_prompt"] is False


# ---------------------------------------------------------------------------
# Chat endpoint — empty body validation
# ---------------------------------------------------------------------------

class TestChatEmptyBodyValidation:
    def test_empty_body_returns_400(self, client):
        """POST /api/chat with empty body must return 400, not 500."""
        resp = client.post(
            "/api/chat",
            data="",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_empty_json_object_returns_400(self, client):
        """POST /api/chat with {} (no message field) must return 400."""
        resp = client.post(
            "/api/chat",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_empty_message_string_returns_400(self, client):
        """POST /api/chat with empty message string must return 400."""
        resp = client.post(
            "/api/chat",
            data=json.dumps({"message": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_whitespace_only_message_returns_400(self, client):
        """POST /api/chat with whitespace-only message must return 400."""
        resp = client.post(
            "/api/chat",
            data=json.dumps({"message": "   "}),
            content_type="application/json",
        )
        assert resp.status_code == 400
