"""Integration tests for routes/quests.py (Phase G)."""

import os
import sys
import uuid
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app
from models import (
    InterventionOutcome,
    MoodEntry,
    Quest,
    QuestProgress,
    UserProfile,
    UserSession,
    db,
)


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


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session_id(app):
    sid = str(uuid.uuid4())
    with app.app_context():
        db.session.add(UserSession(id=sid))
        db.session.commit()
    return sid


def _seed_quests(app, rows):
    with app.app_context():
        now = datetime.utcnow()
        for title, qtype in rows:
            db.session.add(Quest(
                title=title, description=f"{title} desc",
                quest_type=qtype, xp_reward=10, difficulty=1, target=1,
                week_number=now.isocalendar()[1], year=now.year,
            ))
        db.session.commit()


def _seed_moods(app, sid, levels_days):
    with app.app_context():
        now = datetime.utcnow()
        for level, days in levels_days:
            db.session.add(MoodEntry(
                session_id=sid, mood_level=level,
                timestamp=now - timedelta(days=days),
            ))
        db.session.commit()


# ---------------------------------------------------------------------------
# /api/quests/today
# ---------------------------------------------------------------------------

class TestQuestsToday:
    def test_missing_session_400(self, client):
        r = client.get("/api/quests/today")
        assert r.status_code == 400

    def test_empty_quests_returns_empty_list(self, client, session_id):
        r = client.get("/api/quests/today", headers={"X-Session-ID": session_id})
        assert r.status_code == 200
        assert r.json["quests"] == []
        assert len(r.json["preferred_types"]) > 0

    def test_picks_up_to_three(self, client, app, session_id):
        _seed_quests(app, [
            ("Breathe", "breathing"),
            ("Journal", "journaling"),
            ("Walk", "movement"),
            ("Ground", "grounding"),
        ])
        r = client.get("/api/quests/today", headers={"X-Session-ID": session_id})
        assert r.status_code == 200
        assert len(r.json["quests"]) == 3

    def test_response_shape(self, client, app, session_id):
        _seed_quests(app, [("Breathe", "breathing")])
        r = client.get("/api/quests/today", headers={"X-Session-ID": session_id})
        q = r.json["quests"][0]
        assert set(q.keys()) == {
            "id", "title", "description", "quest_type",
            "xp_reward", "difficulty", "target",
        }

    def test_anxiety_signal_picks_breathing(self, client, app, session_id):
        from models import Message
        with app.app_context():
            now = datetime.utcnow()
            db.session.add(Message(
                session_id=session_id, content="I am anxious about everything",
                is_user=True, timestamp=now - timedelta(hours=1),
            ))
            db.session.add(Message(
                session_id=session_id, content="Having another panic",
                is_user=True, timestamp=now,
            ))
            db.session.commit()

        _seed_quests(app, [
            ("Breathe", "breathing"),
            ("Journal", "journaling"),
        ])
        r = client.get("/api/quests/today", headers={"X-Session-ID": session_id})
        types = [q["quest_type"] for q in r.json["quests"]]
        # Breathing must be first pick when anxiety signal present
        assert types[0] == "breathing"

    def test_type_filter_applied(self, client, app, session_id):
        _seed_quests(app, [("Breathe", "breathing"), ("Walk", "movement")])
        r = client.get(
            "/api/quests/today?type=breathing",
            headers={"X-Session-ID": session_id},
        )
        assert all(q["quest_type"] == "breathing" for q in r.json["quests"])


# ---------------------------------------------------------------------------
# /api/quests/<id>/start
# ---------------------------------------------------------------------------

class TestQuestStart:
    def test_missing_session_400(self, client):
        r = client.post("/api/quests/1/start")
        assert r.status_code == 400

    def test_nonexistent_quest_404(self, client, session_id):
        r = client.post(
            "/api/quests/99999/start",
            headers={"X-Session-ID": session_id},
            json={},
        )
        assert r.status_code == 404

    def test_creates_progress_and_outcome(self, client, app, session_id):
        _seed_quests(app, [("Breathe", "breathing")])
        with app.app_context():
            qid = Quest.query.first().id

        r = client.post(
            f"/api/quests/{qid}/start",
            headers={"X-Session-ID": session_id},
            json={"mood_before": 3},
        )
        assert r.status_code == 200
        assert r.json["ok"] is True

        with app.app_context():
            prog = QuestProgress.query.filter_by(
                session_id=session_id, quest_id=qid
            ).first()
            assert prog.status == "in_progress"

            outcome = InterventionOutcome.query.filter_by(
                session_id=session_id,
                intervention_id=f"quest-{qid}",
            ).first()
            assert outcome is not None
            assert outcome.mood_before == 3
            assert outcome.exercise_type == "breathing"

    def test_idempotent_restart(self, client, app, session_id):
        _seed_quests(app, [("Breathe", "breathing")])
        with app.app_context():
            qid = Quest.query.first().id

        for _ in range(2):
            r = client.post(
                f"/api/quests/{qid}/start",
                headers={"X-Session-ID": session_id},
                json={},
            )
            assert r.status_code == 200

        with app.app_context():
            progs = QuestProgress.query.filter_by(
                session_id=session_id, quest_id=qid
            ).all()
            # Only one progress row (updated, not duplicated)
            assert len(progs) == 1


# ---------------------------------------------------------------------------
# /api/quests/streak
# ---------------------------------------------------------------------------

class TestQuestsStreak:
    def test_missing_session_400(self, client):
        r = client.get("/api/quests/streak")
        assert r.status_code == 400

    def test_no_completions_zero(self, client, session_id):
        r = client.get("/api/quests/streak", headers={"X-Session-ID": session_id})
        assert r.status_code == 200
        assert r.json == {"current": 0, "longest": 0}

    def test_three_day_streak(self, client, app, session_id):
        _seed_quests(app, [("A", "check_in"), ("B", "check_in"), ("C", "check_in")])
        with app.app_context():
            quests = Quest.query.all()
            now = datetime.utcnow()
            for i, q in enumerate(quests):
                db.session.add(QuestProgress(
                    session_id=session_id, quest_id=q.id,
                    status="completed",
                    started_at=now - timedelta(days=i),
                    completed_at=now - timedelta(days=i),
                ))
            db.session.commit()

        r = client.get("/api/quests/streak", headers={"X-Session-ID": session_id})
        assert r.json["current"] == 3
        assert r.json["longest"] == 3


# ---------------------------------------------------------------------------
# /api/quests/achievements
# ---------------------------------------------------------------------------

class TestAchievements:
    def test_missing_session_400(self, client):
        r = client.get("/api/quests/achievements")
        assert r.status_code == 400

    def test_no_data_empty_earned(self, client, session_id):
        r = client.get(
            "/api/quests/achievements",
            headers={"X-Session-ID": session_id},
        )
        assert r.status_code == 200
        assert r.json["earned"] == []
        assert r.json["stats"]["total_completed"] == 0

    def test_first_quest_awarded_and_persisted(self, client, app, session_id):
        _seed_quests(app, [("A", "check_in")])
        with app.app_context():
            q = Quest.query.first()
            db.session.add(QuestProgress(
                session_id=session_id, quest_id=q.id,
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            ))
            db.session.commit()

        r = client.get(
            "/api/quests/achievements",
            headers={"X-Session-ID": session_id},
        )
        keys = [e["key"] for e in r.json["earned"]]
        assert "first_quest" in keys

        with app.app_context():
            profile = UserProfile.query.filter_by(session_id=session_id).first()
            assert profile is not None
            assert "first_quest" in profile.badges

    def test_idempotent_no_duplicate_badges(self, client, app, session_id):
        _seed_quests(app, [("A", "check_in")])
        with app.app_context():
            q = Quest.query.first()
            db.session.add(QuestProgress(
                session_id=session_id, quest_id=q.id,
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            ))
            db.session.commit()

        # Call twice (second call should be idempotent)
        client.get("/api/quests/achievements", headers={"X-Session-ID": session_id})
        client.get("/api/quests/achievements", headers={"X-Session-ID": session_id})

        with app.app_context():
            profile = UserProfile.query.filter_by(session_id=session_id).first()
            badges = profile.badges.split(",")
            assert badges.count("first_quest") == 1


# ---------------------------------------------------------------------------
# Registration smoke
# ---------------------------------------------------------------------------

class TestEndpointsRegistered:
    def test_all_four_registered(self, app):
        rules = {r.rule for r in app.url_map.iter_rules()}
        for expected in [
            "/api/quests/today",
            "/api/quests/<int:quest_id>/start",
            "/api/quests/streak",
            "/api/quests/achievements",
        ]:
            assert expected in rules, f"Missing: {expected}"
