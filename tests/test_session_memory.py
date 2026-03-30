"""
Tests for providers/session_memory.py — intervention tracking and conversation history.
Uses in-memory SQLite via Flask-SQLAlchemy (same pattern as test_app.py).
"""

import os
import sys
import pytest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import db, UserSession, Message, InterventionOutcome


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
        # Seed a session for FK constraints
        db.session.add(UserSession(id="test-session-001"))
        db.session.add(UserSession(id="test-session-002"))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


# ═══════════════════════════════════════════════════════════════
# get_session_interventions
# ═══════════════════════════════════════════════════════════════

class TestGetSessionInterventions:
    def test_empty_session_returns_empty(self, app):
        from providers.session_memory import get_session_interventions
        with app.app_context():
            result = get_session_interventions("test-session-001")
        assert result == []

    def test_returns_interventions_for_session(self, app):
        from providers.session_memory import get_session_interventions
        with app.app_context():
            db.session.add(InterventionOutcome(
                session_id="test-session-001",
                intervention_id="breathing-001",
                issue="anxiety",
                offer_stage=1,
                outcome="offered",
                completed=False,
                timestamp=datetime.utcnow(),
            ))
            db.session.commit()

            result = get_session_interventions("test-session-001")

        assert len(result) == 1
        assert result[0]["intervention_id"] == "breathing-001"
        assert result[0]["issue"] == "anxiety"
        assert result[0]["outcome"] == "offered"
        assert result[0]["offer_stage"] == 1

    def test_does_not_leak_across_sessions(self, app):
        from providers.session_memory import get_session_interventions
        with app.app_context():
            db.session.add(InterventionOutcome(
                session_id="test-session-001",
                intervention_id="breathing-001",
                issue="anxiety",
                offer_stage=1, outcome="offered", completed=False,
                timestamp=datetime.utcnow(),
            ))
            db.session.commit()

            result = get_session_interventions("test-session-002")

        assert result == []

    def test_respects_limit(self, app):
        from providers.session_memory import get_session_interventions
        with app.app_context():
            for i in range(5):
                db.session.add(InterventionOutcome(
                    session_id="test-session-001",
                    intervention_id=f"int-{i}",
                    issue="stress",
                    offer_stage=1, outcome="offered", completed=False,
                    timestamp=datetime.utcnow() + timedelta(seconds=i),
                ))
            db.session.commit()

            result = get_session_interventions("test-session-001", limit=3)

        assert len(result) == 3


# ═══════════════════════════════════════════════════════════════
# record_intervention_shown
# ═══════════════════════════════════════════════════════════════

class TestRecordInterventionShown:
    def test_writes_correct_schema(self, app):
        from providers.session_memory import record_intervention_shown
        with app.app_context():
            ok = record_intervention_shown(
                session_id="test-session-001",
                issue="anxiety",
                intervention_type="breathing",
                intervention_id="breathing-box",
                offer_stage=2,
            )

            assert ok is True

            row = InterventionOutcome.query.filter_by(
                session_id="test-session-001"
            ).first()

        assert row is not None
        assert row.intervention_id == "breathing-box"
        assert row.issue == "anxiety"
        assert row.offer_stage == 2
        assert row.outcome == "offered"
        assert row.completed is False
        assert row.timestamp is not None

    def test_returns_true_on_success(self, app):
        from providers.session_memory import record_intervention_shown
        with app.app_context():
            result = record_intervention_shown(
                "test-session-001", "stress", "grounding", "ground-5-4-3"
            )
        assert result is True


# ═══════════════════════════════════════════════════════════════
# get_intervention_variety
# ═══════════════════════════════════════════════════════════════

class TestGetInterventionVariety:
    def test_first_time_returns_breathing(self, app):
        from providers.session_memory import get_intervention_variety
        with app.app_context():
            result = get_intervention_variety("test-session-001", "anxiety")

        assert result["offer_stage"] == 1
        assert result["intervention_type"] == "breathing"
        assert result["previous_interventions"] == []

    def test_second_time_returns_grounding(self, app):
        from providers.session_memory import get_intervention_variety
        with app.app_context():
            db.session.add(InterventionOutcome(
                session_id="test-session-001",
                intervention_id="breathing-001",
                issue="anxiety",
                offer_stage=1, outcome="completed", completed=True,
                timestamp=datetime.utcnow(),
            ))
            db.session.commit()

            result = get_intervention_variety("test-session-001", "anxiety")

        assert result["offer_stage"] == 2
        assert result["intervention_type"] == "grounding"
        assert len(result["previous_interventions"]) == 1

    def test_third_time_returns_journaling(self, app):
        from providers.session_memory import get_intervention_variety
        with app.app_context():
            for i in range(2):
                db.session.add(InterventionOutcome(
                    session_id="test-session-001",
                    intervention_id=f"int-{i}",
                    issue="stressed",
                    offer_stage=i + 1, outcome="completed", completed=True,
                    timestamp=datetime.utcnow() + timedelta(seconds=i),
                ))
            db.session.commit()

            result = get_intervention_variety("test-session-001", "stressed")

        assert result["offer_stage"] == 3
        assert result["intervention_type"] == "journaling"

    def test_fourth_time_returns_talk(self, app):
        from providers.session_memory import get_intervention_variety
        with app.app_context():
            for i in range(3):
                db.session.add(InterventionOutcome(
                    session_id="test-session-001",
                    intervention_id=f"int-{i}",
                    issue="anxiety",
                    offer_stage=i + 1, outcome="completed", completed=True,
                    timestamp=datetime.utcnow() + timedelta(seconds=i),
                ))
            db.session.commit()

            result = get_intervention_variety("test-session-001", "anxiety")

        assert result["offer_stage"] == 4
        assert result["intervention_type"] == "talk"

    def test_counts_across_wellness_bucket(self, app):
        """anxiety and stressed are in same wellness bucket — count together."""
        from providers.session_memory import get_intervention_variety
        with app.app_context():
            db.session.add(InterventionOutcome(
                session_id="test-session-001",
                intervention_id="int-anxiety",
                issue="anxiety",
                offer_stage=1, outcome="completed", completed=True,
                timestamp=datetime.utcnow(),
            ))
            db.session.commit()

            # Query with "stressed" — same bucket as anxiety
            result = get_intervention_variety("test-session-001", "stressed")

        assert result["offer_stage"] == 2
        assert result["intervention_type"] == "grounding"


# ═══════════════════════════════════════════════════════════════
# update_intervention_outcome
# ═══════════════════════════════════════════════════════════════

class TestUpdateInterventionOutcome:
    def test_transitions_to_completed(self, app):
        from providers.session_memory import update_intervention_outcome
        with app.app_context():
            db.session.add(InterventionOutcome(
                session_id="test-session-001",
                intervention_id="breathing-box",
                issue="anxiety",
                offer_stage=1, outcome="offered", completed=False,
                timestamp=datetime.utcnow(),
            ))
            db.session.commit()

            ok = update_intervention_outcome(
                session_id="test-session-001",
                intervention_id="breathing-box",
                outcome="completed",
                time_spent_seconds=120,
                mood_before=3,
                mood_after=7,
            )

            assert ok is True

            row = InterventionOutcome.query.filter_by(
                intervention_id="breathing-box"
            ).first()

        assert row.outcome == "completed"
        assert row.completed is True
        assert row.time_spent_seconds == 120
        assert row.mood_before == 3
        assert row.mood_after == 7

    def test_transitions_to_skipped(self, app):
        from providers.session_memory import update_intervention_outcome
        with app.app_context():
            db.session.add(InterventionOutcome(
                session_id="test-session-001",
                intervention_id="ground-001",
                issue="stress",
                offer_stage=1, outcome="offered", completed=False,
                timestamp=datetime.utcnow(),
            ))
            db.session.commit()

            ok = update_intervention_outcome(
                "test-session-001", "ground-001", "skipped"
            )

            row = InterventionOutcome.query.filter_by(
                intervention_id="ground-001"
            ).first()

        assert ok is True
        assert row.outcome == "skipped"
        assert row.completed is False

    def test_returns_false_for_missing_intervention(self, app):
        from providers.session_memory import update_intervention_outcome
        with app.app_context():
            result = update_intervention_outcome(
                "test-session-001", "nonexistent", "completed"
            )
        assert result is False


# ═══════════════════════════════════════════════════════════════
# get_recent_messages
# ═══════════════════════════════════════════════════════════════

class TestGetRecentMessages:
    def test_empty_session_returns_empty(self, app):
        from providers.session_memory import get_recent_messages
        with app.app_context():
            result = get_recent_messages("test-session-001")
        assert result == []

    def test_returns_messages_chronological(self, app):
        from providers.session_memory import get_recent_messages
        with app.app_context():
            db.session.add(Message(
                session_id="test-session-001",
                content="Hello",
                is_user=True,
                timestamp=datetime.utcnow() - timedelta(seconds=10),
            ))
            db.session.add(Message(
                session_id="test-session-001",
                content="Hi there!",
                is_user=False,
                timestamp=datetime.utcnow(),
            ))
            db.session.commit()

            result = get_recent_messages("test-session-001")

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"
        assert result[1]["role"] == "assistant"
        assert result[1]["content"] == "Hi there!"


# ═══════════════════════════════════════════════════════════════
# format_history_for_prompt
# ═══════════════════════════════════════════════════════════════

class TestFormatHistoryForPrompt:
    def test_empty_returns_empty_string(self):
        from providers.session_memory import format_history_for_prompt
        assert format_history_for_prompt([]) == ""

    def test_produces_correct_chat_format(self):
        from providers.session_memory import format_history_for_prompt
        messages = [
            {"role": "user", "content": "I'm feeling anxious"},
            {"role": "assistant", "content": "I hear you. Let's work through this together."},
        ]
        result = format_history_for_prompt(messages)

        assert "Recent conversation:" in result
        assert "User: I'm feeling anxious" in result
        assert "Luna: I hear you" in result

    def test_truncates_long_messages(self):
        from providers.session_memory import format_history_for_prompt
        messages = [
            {"role": "user", "content": "x" * 500},
        ]
        result = format_history_for_prompt(messages)
        # Content should be truncated to 200 chars
        assert len(result.split("User: ")[1]) <= 201  # 200 + possible newline

    def test_limits_to_10_messages(self):
        from providers.session_memory import format_history_for_prompt
        messages = [
            {"role": "user", "content": f"msg {i}"}
            for i in range(15)
        ]
        result = format_history_for_prompt(messages)
        # Should only include last 10
        assert "msg 5" in result
        assert "msg 14" in result
        assert "msg 0" not in result
