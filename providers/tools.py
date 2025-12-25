"""
Wellness Tools for Luna AI
Implements function calling capabilities for proactive wellness actions.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from flask import current_app
from sqlalchemy import text

# Import db from models to avoid circular imports
from models import db


# ============================================================================
# BREATHING EXERCISES
# ============================================================================

BREATHING_EXERCISES = {
    "calm": {
        "name": "4-7-8 Calming Breath",
        "description": "A relaxing breathing pattern that activates your parasympathetic nervous system.",
        "steps": [
            {"action": "breathe_in", "duration": 4, "instruction": "Breathe in slowly through your nose"},
            {"action": "hold", "duration": 7, "instruction": "Hold your breath gently"},
            {"action": "breathe_out", "duration": 8, "instruction": "Exhale slowly through your mouth"},
        ],
        "cycles": 4,
        "total_time_seconds": 76,
    },
    "quick": {
        "name": "Box Breathing",
        "description": "A simple, balanced breathing pattern used by Navy SEALs to stay calm.",
        "steps": [
            {"action": "breathe_in", "duration": 4, "instruction": "Breathe in"},
            {"action": "hold", "duration": 4, "instruction": "Hold"},
            {"action": "breathe_out", "duration": 4, "instruction": "Breathe out"},
            {"action": "hold", "duration": 4, "instruction": "Hold"},
        ],
        "cycles": 4,
        "total_time_seconds": 64,
    },
    "energize": {
        "name": "Energizing Breath",
        "description": "A gentle pattern to increase alertness and energy.",
        "steps": [
            {"action": "breathe_in", "duration": 4, "instruction": "Deep breath in through your nose"},
            {"action": "breathe_out", "duration": 2, "instruction": "Quick exhale through your mouth"},
        ],
        "cycles": 6,
        "total_time_seconds": 36,
    },
}


# ============================================================================
# GROUNDING EXERCISES
# ============================================================================

GROUNDING_EXERCISES = [
    {
        "name": "5-4-3-2-1 Senses",
        "description": "Ground yourself by connecting with your five senses.",
        "steps": [
            "Name 5 things you can SEE around you",
            "Name 4 things you can TOUCH or feel",
            "Name 3 things you can HEAR",
            "Name 2 things you can SMELL",
            "Name 1 thing you can TASTE",
        ],
    },
    {
        "name": "Body Scan",
        "description": "Bring awareness to your body, starting from your toes.",
        "steps": [
            "Notice your feet on the ground",
            "Feel your legs and how they're supported",
            "Notice your hands - are they tense or relaxed?",
            "Feel your shoulders - let them drop if they're raised",
            "Notice your breath - don't change it, just observe",
        ],
    },
]


# ============================================================================
# JOURNAL PROMPTS
# ============================================================================

JOURNAL_PROMPTS = {
    "general": [
        "What's one small thing that made you smile today?",
        "What's something you're looking forward to, even if it's small?",
        "Describe your current mood in three words. Why those words?",
        "What would you tell a friend who was feeling the way you feel right now?",
        "What's one thing you did well today, even if it felt hard?",
    ],
    "anxiety": [
        "What's worrying you most right now? Write it all out.",
        "What's one thing within your control about this situation?",
        "Imagine your worry as a cloud passing by. Describe what you see.",
        "What would 'future you' say about this moment?",
        "List three things that are going okay right now.",
    ],
    "sadness": [
        "It's okay to feel sad. What triggered this feeling?",
        "What's one kind thing you can do for yourself today?",
        "Write about a time when you felt better after feeling low.",
        "Who in your life cares about you? List them.",
        "What's one thing you're grateful for, even in this moment?",
    ],
    "stress": [
        "What's the biggest source of stress right now?",
        "Break it down: what's the next tiny step you could take?",
        "What usually helps you relax? Can you do that today?",
        "Write about a time you handled stress well.",
        "What would 'calm you' tell 'stressed you' right now?",
    ],
    "sleep": [
        "What's on your mind as you try to sleep?",
        "Write a 'brain dump' of everything swirling in your head.",
        "What's one thing you can let go of worrying about tonight?",
        "Describe your ideal calm, restful night.",
        "What are you looking forward to tomorrow?",
    ],
}


# ============================================================================
# TOOL EXECUTION FUNCTIONS
# ============================================================================

def execute_tool(name: str, args: dict, session_id: str) -> Dict[str, Any]:
    """
    Execute a wellness tool and return the result.
    
    Args:
        name: The function name to execute
        args: Arguments passed by Gemini
        session_id: Current user session
        
    Returns:
        Dict with tool result and any data
    """
    try:
        if name == "log_mood":
            return _log_mood(session_id, args)
        elif name == "get_breathing_exercise":
            return _get_breathing_exercise(args)
        elif name == "get_grounding_exercise":
            return _get_grounding_exercise()
        elif name == "get_journal_prompt":
            return _get_journal_prompt(args)
        elif name == "get_mood_history":
            return _get_mood_history(session_id, args)
        else:
            return {"success": False, "error": f"Unknown tool: {name}"}
    except Exception as e:
        current_app.logger.error(f"Tool execution error [{name}]: {e}")
        return {"success": False, "error": str(e)}


def _log_mood(session_id: str, args: dict) -> Dict[str, Any]:
    """Log user's mood from conversation context."""
    level = args.get("level", 3)
    emotion = args.get("emotion", "neutral")
    note = args.get("note", "")
    
    # Validate level
    if not isinstance(level, int) or level < 1 or level > 5:
        level = 3
    
    try:
        db.session.execute(
            text("""
                INSERT INTO mood_entries (session_id, mood_level, note, timestamp)
                VALUES (:session_id, :mood_level, :note, :timestamp)
            """),
            {
                "session_id": session_id,
                "mood_level": level,
                "note": f"[{emotion}] {note}".strip(),
                "timestamp": datetime.utcnow(),
            },
        )
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Logged mood: {emotion} (level {level})",
            "logged": {"level": level, "emotion": emotion},
        }
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


def _get_breathing_exercise(args: dict) -> Dict[str, Any]:
    """Return a structured breathing exercise."""
    exercise_type = args.get("type", "calm")
    
    exercise = BREATHING_EXERCISES.get(exercise_type, BREATHING_EXERCISES["calm"])
    
    return {
        "success": True,
        "exercise_type": "breathing",
        "exercise": exercise,
        "interactive": True,
    }


def _get_grounding_exercise() -> Dict[str, Any]:
    """Return a grounding exercise."""
    exercise = random.choice(GROUNDING_EXERCISES)
    
    return {
        "success": True,
        "exercise_type": "grounding",
        "exercise": exercise,
        "interactive": True,
    }


def _get_journal_prompt(args: dict) -> Dict[str, Any]:
    """Return a reflective journal prompt."""
    topic = args.get("topic", "general").lower()
    
    # Map common emotions to categories
    topic_map = {
        "anxious": "anxiety",
        "worried": "anxiety",
        "nervous": "anxiety",
        "sad": "sadness",
        "depressed": "sadness",
        "down": "sadness",
        "stressed": "stress",
        "overwhelmed": "stress",
        "tired": "sleep",
        "insomnia": "sleep",
        "can't sleep": "sleep",
    }
    
    category = topic_map.get(topic, topic)
    if category not in JOURNAL_PROMPTS:
        category = "general"
    
    prompt = random.choice(JOURNAL_PROMPTS[category])
    
    return {
        "success": True,
        "prompt": prompt,
        "category": category,
    }


def _get_mood_history(session_id: str, args: dict) -> Dict[str, Any]:
    """Retrieve user's mood history."""
    days = args.get("days", 7)
    if not isinstance(days, int) or days < 1 or days > 30:
        days = 7
    
    try:
        since = datetime.utcnow() - timedelta(days=days)
        
        entries = db.session.execute(
            text("""
                SELECT mood_level, note, timestamp
                FROM mood_entries
                WHERE session_id = :session_id AND timestamp >= :since
                ORDER BY timestamp DESC
                LIMIT 20
            """),
            {"session_id": session_id, "since": since},
        ).fetchall()
        
        history = [
            {
                "level": e.mood_level,
                "note": e.note,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in entries
        ]
        
        # Calculate average if we have data
        if history:
            avg = sum(h["level"] for h in history) / len(history)
            trend = "improving" if len(history) > 1 and history[0]["level"] > history[-1]["level"] else "stable"
        else:
            avg = None
            trend = None
        
        return {
            "success": True,
            "entries": history,
            "count": len(history),
            "average": round(avg, 1) if avg else None,
            "trend": trend,
            "days": days,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# TOOL RESULT FORMATTING
# ============================================================================

def format_tool_result_for_response(tool_name: str, result: Dict[str, Any]) -> str:
    """
    Format tool result into natural language for Luna's response.
    """
    if not result.get("success"):
        return ""  # Don't mention failed tools
    
    if tool_name == "log_mood":
        logged = result.get("logged", {})
        return f"I've noted that you're feeling {logged.get('emotion', 'this way')}."
    
    elif tool_name == "get_breathing_exercise":
        exercise = result.get("exercise", {})
        name = exercise.get("name", "breathing exercise")
        return f"Let me guide you through {name}."
    
    elif tool_name == "get_grounding_exercise":
        exercise = result.get("exercise", {})
        name = exercise.get("name", "a grounding exercise")
        return f"Let's try {name} together."
    
    elif tool_name == "get_journal_prompt":
        prompt = result.get("prompt", "")
        return f"Here's something to reflect on: {prompt}"
    
    elif tool_name == "get_mood_history":
        count = result.get("count", 0)
        avg = result.get("average")
        if count == 0:
            return "I don't have any mood logs from you yet."
        trend = result.get("trend", "stable")
        return f"Looking at your {count} recent check-ins, you've been averaging {avg}/5. Your trend looks {trend}."
    
    return ""
