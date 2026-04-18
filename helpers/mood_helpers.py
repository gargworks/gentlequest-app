"""
Mood analytics helpers: recommendations, pattern analysis, and data purge.
Extracted from app.py monolith.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from flask import current_app

from models import Message, UserSession


def _get_personalized_recommendations(
    avg_mood: float, recent_entries: List
) -> List[Dict[str, Any]]:
    """Get personalized wellness recommendations based on mood"""
    recommendations = []

    if avg_mood <= 2.0:
        # Low mood recommendations
        recommendations.extend(
            [
                {
                    "type": "immediate",
                    "title": "Reach Out for Support",
                    "description": "Consider talking to a trusted friend, family member, or mental health professional.",
                    "action": "Call a friend or family member",
                },
                {
                    "type": "activity",
                    "title": "Gentle Physical Activity",
                    "description": "Even a short walk can help improve your mood and energy levels.",
                    "action": "Take a 10-minute walk outside",
                },
                {
                    "type": "self_care",
                    "title": "Practice Self-Compassion",
                    "description": "Be kind to yourself. It's okay to not be okay.",
                    "action": "Write down 3 things you're grateful for",
                },
            ]
        )
    elif avg_mood <= 3.5:
        # Moderate mood recommendations
        recommendations.extend(
            [
                {
                    "type": "activity",
                    "title": "Engage in Enjoyable Activities",
                    "description": "Do something you normally enjoy, even if you don't feel like it initially.",
                    "action": "Listen to your favorite music or watch a movie",
                },
                {
                    "type": "social",
                    "title": "Social Connection",
                    "description": "Connect with others, even if it's just a brief conversation.",
                    "action": "Send a message to a friend",
                },
                {
                    "type": "routine",
                    "title": "Maintain Daily Routine",
                    "description": "Stick to your regular schedule to provide structure and stability.",
                    "action": "Follow your usual daily routine",
                },
            ]
        )
    else:
        # Good mood recommendations
        recommendations.extend(
            [
                {
                    "type": "maintenance",
                    "title": "Maintain Positive Habits",
                    "description": "Keep up with activities that contribute to your well-being.",
                    "action": "Continue your current positive routines",
                },
                {
                    "type": "growth",
                    "title": "Personal Development",
                    "description": "Use your positive energy to work on personal goals.",
                    "action": "Set a small goal for the week",
                },
                {
                    "type": "gratitude",
                    "title": "Practice Gratitude",
                    "description": "Reflect on what's going well in your life.",
                    "action": "Write down 5 things you appreciate today",
                },
            ]
        )

    return recommendations


def _get_default_recommendations() -> List[Dict[str, Any]]:
    """Get default wellness recommendations"""
    return [
        {
            "type": "general",
            "title": "Start with Small Steps",
            "description": "Begin with simple activities that can improve your mood.",
            "action": "Take a few deep breaths and stretch",
        },
        {
            "type": "connection",
            "title": "Reach Out",
            "description": "Connect with someone you trust.",
            "action": "Send a message to a friend or family member",
        },
        {
            "type": "self_care",
            "title": "Practice Self-Care",
            "description": "Do something kind for yourself.",
            "action": "Take a warm shower or bath",
        },
    ]


def _analyze_mood_pattern(entries: List) -> Dict[str, Any]:
    """Analyze mood patterns from recent entries"""
    if not entries:
        return {"pattern": "insufficient_data", "trend": "unknown"}

    mood_levels = [entry.mood_level for entry in entries]

    # Calculate trend. Requires both a "recent" window and an "older" window to
    # compare; if the older window is empty we can't compute a trend.
    older_slice = mood_levels[3:6]
    if len(mood_levels) >= 2 and older_slice:
        recent_avg = sum(mood_levels[:3]) / min(3, len(mood_levels))
        older_avg = sum(older_slice) / len(older_slice)

        if recent_avg > older_avg + 0.5:
            trend = "improving"
        elif recent_avg < older_avg - 0.5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    # Identify patterns
    if len(mood_levels) >= 3:
        if all(level <= 2 for level in mood_levels[:3]):
            pattern = "consistently_low"
        elif all(level >= 4 for level in mood_levels[:3]):
            pattern = "consistently_high"
        elif mood_levels[0] < mood_levels[1] < mood_levels[2]:
            pattern = "improving"
        elif mood_levels[0] > mood_levels[1] > mood_levels[2]:
            pattern = "declining"
        else:
            pattern = "fluctuating"
    else:
        pattern = "insufficient_data"

    return {
        "pattern": pattern,
        "trend": trend,
        "recent_moods": mood_levels[:5],
        "average": round(sum(mood_levels) / len(mood_levels), 2),
    }


def _purge_old_data_inner():
    """Inner function to purge old data based on retention settings"""
    counts = {}

    # Purge old messages
    message_days = current_app.config.get("MESSAGE_RETENTION_DAYS", 30)
    if message_days > 0:
        cutoff = datetime.utcnow() - timedelta(days=message_days)
        result = Message.query.filter(Message.timestamp < cutoff).delete()
        counts["messages"] = result

    # Purge old sessions
    session_days = current_app.config.get("SESSION_RETENTION_DAYS", 90)
    if session_days > 0:
        cutoff = datetime.utcnow() - timedelta(days=session_days)
        result = UserSession.query.filter(UserSession.created_at < cutoff).delete()
        counts["sessions"] = result

    # Purge expired memories (pgvector)
    try:
        from providers.memory import MEMORY_ENABLED, cleanup_expired_memories
        if MEMORY_ENABLED:
            expired = cleanup_expired_memories()
            counts["expired_memories"] = expired
    except Exception:
        pass

    return counts
