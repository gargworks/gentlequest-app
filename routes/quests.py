"""
Phase G gamification endpoints — extends existing app_quest_routes.

New endpoints:
- GET  /api/quests/today         — picks 3 quests for today
- POST /api/quests/<id>/start    — mark quest in_progress (+ capture mood_before)
- GET  /api/quests/streak        — current + longest streak
- GET  /api/quests/achievements  — badges earned

Existing endpoints in app_quest_routes.py (untouched):
- GET  /api/quests               — list weekly quests
- POST /api/quests/<id>/complete — complete quest (now captures mood_after)
- GET  /api/user/profile         — profile
"""

from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from extensions import limiter
from helpers.quest_matcher import (
    ACHIEVEMENTS,
    check_achievements,
    compute_streak,
    pick_quest_types,
    select_daily_quests,
)
from models import (
    InterventionOutcome,
    Message,
    MoodEntry,
    Quest,
    QuestProgress,
    UserProfile,
    db,
)

quests_bp = Blueprint("quests_v2", __name__)


def _sid() -> str:
    return (
        request.headers.get("X-Session-ID")
        or request.args.get("session_id")
        or ""
    ).strip()


def _today_utc():
    now = datetime.utcnow()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# /api/quests/today
# ---------------------------------------------------------------------------

@quests_bp.route("/api/quests/today", methods=["GET"])
@limiter.limit("30 per minute")
def quests_today():
    """Pick 3 quests based on recent mood + keyword signals."""
    sid = _sid()
    if not sid:
        return jsonify({"error": "X-Session-ID header required"}), 400

    try:
        today = _today_utc()
        moods = MoodEntry.query.filter_by(session_id=sid).all()
        messages = Message.query.filter_by(session_id=sid).all()

        # Skip quests already completed today
        completed_today = (
            db.session.query(QuestProgress.quest_id)
            .filter(
                QuestProgress.session_id == sid,
                QuestProgress.status == "completed",
                QuestProgress.completed_at >= today,
            )
            .all()
        )
        completed_ids = [row[0] for row in completed_today]

        # Optional ?type= filter (from Phase F's CTA links)
        quest_type_filter = request.args.get("type")
        quests_q = Quest.query
        if quest_type_filter:
            quests_q = quests_q.filter_by(quest_type=quest_type_filter)
        quests = quests_q.all()

        types = pick_quest_types(moods, messages, n=5)
        picked = select_daily_quests(quests, types, completed_ids, n=3)

        return jsonify({
            "quests": [
                {
                    "id": q.id,
                    "title": q.title,
                    "description": q.description,
                    "quest_type": q.quest_type,
                    "xp_reward": q.xp_reward,
                    "difficulty": q.difficulty,
                    "target": q.target,
                }
                for q in picked
            ],
            "preferred_types": types,
        }), 200
    except Exception as e:
        current_app.logger.error(f"quests/today error: {e}")
        return jsonify({"error": "Failed to pick quests"}), 500


# ---------------------------------------------------------------------------
# /api/quests/<id>/start
# ---------------------------------------------------------------------------

@quests_bp.route("/api/quests/<int:quest_id>/start", methods=["POST"])
@limiter.limit("20 per minute")
def quest_start(quest_id: int):
    """Mark quest as in_progress and record mood_before."""
    sid = _sid()
    if not sid:
        return jsonify({"error": "X-Session-ID header required"}), 400

    try:
        quest = Quest.query.get(quest_id)
        if not quest:
            return jsonify({"error": "Quest not found"}), 404

        body = request.get_json(silent=True) or {}
        mood_before = body.get("mood_before")

        # Find or create QuestProgress
        progress = QuestProgress.query.filter_by(
            session_id=sid, quest_id=quest_id
        ).first()
        if not progress:
            progress = QuestProgress(
                session_id=sid,
                quest_id=quest_id,
                status="in_progress",
                started_at=datetime.utcnow(),
            )
            db.session.add(progress)
        else:
            progress.status = "in_progress"
            progress.started_at = datetime.utcnow()

        # Record intervention outcome (captures mood_before for later correlation)
        outcome = InterventionOutcome(
            session_id=sid,
            intervention_id=f"quest-{quest_id}",
            exercise_type=quest.quest_type,
            mood_before=mood_before if isinstance(mood_before, int) else None,
            offer_stage=1,
        )
        db.session.add(outcome)
        db.session.commit()

        return jsonify({
            "ok": True,
            "quest_id": quest_id,
            "outcome_id": outcome.id,
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"quests/start error: {e}")
        return jsonify({"error": "Failed to start quest"}), 500


# ---------------------------------------------------------------------------
# /api/quests/streak
# ---------------------------------------------------------------------------

@quests_bp.route("/api/quests/streak", methods=["GET"])
@limiter.limit("60 per minute")
def quests_streak():
    """Compute current + longest completion streak."""
    sid = _sid()
    if not sid:
        return jsonify({"error": "X-Session-ID header required"}), 400

    try:
        rows = (
            QuestProgress.query
            .filter_by(session_id=sid, status="completed")
            .with_entities(QuestProgress.completed_at)
            .all()
        )
        timestamps = [r[0] for r in rows if r[0]]
        streak = compute_streak(timestamps)
        return jsonify(streak), 200
    except Exception as e:
        current_app.logger.error(f"quests/streak error: {e}")
        return jsonify({"error": "Failed to compute streak"}), 500


# ---------------------------------------------------------------------------
# /api/quests/achievements
# ---------------------------------------------------------------------------

@quests_bp.route("/api/quests/achievements", methods=["GET"])
@limiter.limit("30 per minute")
def quests_achievements():
    """Return earned badges + check for newly-earned ones (idempotent)."""
    sid = _sid()
    if not sid:
        return jsonify({"error": "X-Session-ID header required"}), 400

    try:
        profile = UserProfile.query.filter_by(session_id=sid).first()
        already = (profile.badges or "").split(",") if profile else []
        already = [b for b in already if b]

        # Compute stats for achievement evaluation
        total_completed = (
            QuestProgress.query
            .filter_by(session_id=sid, status="completed")
            .count()
        )

        rows = (
            QuestProgress.query
            .filter_by(session_id=sid, status="completed")
            .with_entities(QuestProgress.completed_at)
            .all()
        )
        timestamps = [r[0] for r in rows if r[0]]
        streak = compute_streak(timestamps)

        # Max mood delta across all intervention outcomes
        outcomes = (
            InterventionOutcome.query
            .filter_by(session_id=sid)
            .filter(InterventionOutcome.mood_before.isnot(None))
            .filter(InterventionOutcome.mood_after.isnot(None))
            .all()
        )
        deltas = [o.mood_after - o.mood_before for o in outcomes]
        max_delta = max(deltas) if deltas else 0

        stats = {
            "total_completed": total_completed,
            "current_streak": streak["current"],
            "longest_streak": streak["longest"],
            "max_mood_delta": max_delta,
        }

        new_badges = check_achievements(stats, already)

        # Persist new badges (create profile if needed)
        if new_badges:
            if not profile:
                profile = UserProfile(session_id=sid, badges=",".join(new_badges))
                db.session.add(profile)
            else:
                combined = [b for b in already if b] + new_badges
                profile.badges = ",".join(sorted(set(combined)))
                profile.updated_at = datetime.utcnow()
            try:
                db.session.commit()
            except Exception as commit_err:
                current_app.logger.warning(
                    "quests/achievements badge_commit_failed session_id=%s err=%s",
                    sid, commit_err,
                )
                db.session.rollback()
                # Re-query persisted badges; drop new_badges that didn't survive commit.
                persisted_profile = UserProfile.query.filter_by(session_id=sid).first()
                persisted = (persisted_profile.badges or "").split(",") if persisted_profile else []
                persisted = [b for b in persisted if b]
                already = persisted
                new_badges = [b for b in new_badges if b in persisted]

        # Build response
        all_earned = sorted(set(already + new_badges))
        return jsonify({
            "earned": [
                {
                    "key": k,
                    "title": ACHIEVEMENTS[k]["title"],
                    "description": ACHIEVEMENTS[k]["description"],
                    "new": k in new_badges,
                }
                for k in all_earned
                if k in ACHIEVEMENTS
            ],
            "stats": stats,
        }), 200
    except Exception as e:
        current_app.logger.error(f"quests/achievements error: {e}")
        return jsonify({"error": "Failed to compute achievements"}), 500
