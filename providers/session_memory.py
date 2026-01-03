"""
Session Memory for GentleQuest
Tracks interventions shown per session for variety and learning.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import text
from flask import current_app

from models import db


# ============================================================================
# INTERVENTION TRACKING
# ============================================================================

def get_session_interventions(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get interventions shown in this session.
    
    Returns:
        List of {issue, intervention_type, intervention_id, outcome, timestamp}
    """
    try:
        result = db.session.execute(
            text("""
                SELECT 
                    intervention_id,
                    issue,
                    offer_stage,
                    outcome,
                    timestamp
                FROM intervention_outcomes
                WHERE session_id = :session_id
                ORDER BY timestamp DESC
                LIMIT :limit
            """),
            {"session_id": session_id, "limit": limit}
        ).fetchall()
        
        interventions = []
        for row in result:
            interventions.append({
                "intervention_id": row.intervention_id,
                "issue": row.issue if hasattr(row, 'issue') else None,
                "offer_stage": row.offer_stage if hasattr(row, 'offer_stage') else 1,
                "outcome": row.outcome if hasattr(row, 'outcome') else "offered",
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            })
        
        return interventions
        
    except Exception as e:
        current_app.logger.warning(f"get_session_interventions error: {e}")
        return []


def record_intervention_shown(
    session_id: str,
    issue: str,
    intervention_type: str,
    intervention_id: str,
    offer_stage: int = 1,
) -> bool:
    """
    Record that an intervention was shown to the user.
    
    Args:
        session_id: User session
        issue: Issue type (anxiety, stress, etc.)
        intervention_type: Type (breathing, grounding, journaling)
        intervention_id: Specific intervention ID
        offer_stage: 1st, 2nd, 3rd offer for this issue
        
    Returns:
        True if recorded successfully
    """
    try:
        db.session.execute(
            text("""
                INSERT INTO intervention_outcomes 
                (session_id, intervention_id, issue, offer_stage, outcome, completed, timestamp)
                VALUES (:session_id, :intervention_id, :issue, :offer_stage, 'offered', FALSE, :timestamp)
            """),
            {
                "session_id": session_id,
                "intervention_id": intervention_id,
                "issue": issue,
                "offer_stage": offer_stage,
                "timestamp": datetime.utcnow(),
            }
        )
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"record_intervention_shown error: {e}")
        return False


def get_intervention_variety(session_id: str, issue: str) -> Dict[str, Any]:
    """
    Determine what variety of intervention to offer for this issue.
    
    Logic:
    - 1st time: breathing
    - 2nd time: grounding  
    - 3rd time: journaling
    - 4th+ time: talk mode (no exercise, just conversation)
    
    Returns:
        {
            'offer_stage': 1-4,
            'intervention_type': 'breathing' | 'grounding' | 'journaling' | 'talk',
            'previous_interventions': [...]
        }
    """
    try:
        # Get previous interventions for this specific issue
        result = db.session.execute(
            text("""
                SELECT intervention_id, offer_stage, outcome
                FROM intervention_outcomes
                WHERE session_id = :session_id 
                AND issue = :issue
                ORDER BY timestamp DESC
            """),
            {"session_id": session_id, "issue": issue}
        ).fetchall()
        
        previous = [{"id": r.intervention_id, "stage": r.offer_stage, "outcome": r.outcome} for r in result]
        count = len(previous)
        
        # Determine next offer stage
        if count == 0:
            return {
                "offer_stage": 1,
                "intervention_type": "breathing",
                "previous_interventions": [],
            }
        elif count == 1:
            return {
                "offer_stage": 2,
                "intervention_type": "grounding",
                "previous_interventions": previous,
            }
        elif count == 2:
            return {
                "offer_stage": 3,
                "intervention_type": "journaling",
                "previous_interventions": previous,
            }
        else:
            return {
                "offer_stage": 4,
                "intervention_type": "talk",
                "previous_interventions": previous,
            }
            
    except Exception as e:
        current_app.logger.warning(f"get_intervention_variety error: {e}")
        # Fallback to stage 1
        return {
            "offer_stage": 1,
            "intervention_type": "breathing",
            "previous_interventions": [],
        }


def update_intervention_outcome(
    session_id: str,
    intervention_id: str,
    outcome: str,
    exercise_type: Optional[str] = None,
    time_spent_seconds: Optional[int] = None,
    mood_before: Optional[int] = None,
    mood_after: Optional[int] = None,
    effectiveness_rating: Optional[float] = None,
    feedback: Optional[str] = None,
) -> bool:
    """
    Update the outcome of an intervention with analytics data.
    
    Args:
        session_id: User session
        intervention_id: The intervention shown
        outcome: 'started' | 'completed' | 'skipped'
        exercise_type: breathing, grounding, journaling (optional)
        time_spent_seconds: How long user spent on exercise (optional)
        mood_before: User mood before exercise, 1-10 scale (optional)
        mood_after: User mood after exercise, 1-10 scale (optional)
        effectiveness_rating: 0-1 score (optional)
        feedback: User feedback text (optional)
        
    Returns:
        True if updated successfully
    """
    try:
        # Update the most recent matching intervention
        db.session.execute(
            text("""
                UPDATE intervention_outcomes
                SET outcome = :outcome,
                    completed = :completed,
                    exercise_type = COALESCE(:exercise_type, exercise_type),
                    time_spent_seconds = COALESCE(:time_spent, time_spent_seconds),
                    mood_before = COALESCE(:mood_before, mood_before),
                    mood_after = COALESCE(:mood_after, mood_after),
                    effectiveness_rating = COALESCE(:rating, effectiveness_rating),
                    feedback = COALESCE(:feedback, feedback)
                WHERE id = (
                    SELECT id FROM intervention_outcomes
                    WHERE session_id = :session_id 
                    AND intervention_id = :intervention_id
                    ORDER BY timestamp DESC
                    LIMIT 1
                )
            """),
            {
                "session_id": session_id,
                "intervention_id": intervention_id,
                "outcome": outcome,
                "completed": outcome == "completed",
                "exercise_type": exercise_type,
                "time_spent": time_spent_seconds,
                "mood_before": mood_before,
                "mood_after": mood_after,
                "rating": effectiveness_rating,
                "feedback": feedback,
            }
        )
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"update_intervention_outcome error: {e}")
        return False


# ============================================================================
# CONVERSATION HISTORY (for context)
# ============================================================================

def get_recent_messages(session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get recent messages for conversation context.
    
    Returns:
        List of {role: 'user'|'assistant', content: str, timestamp: str}
    """
    try:
        # Use messages table instead of broken conversation_logs
        result = db.session.execute(
            text("""
                SELECT content, is_user, timestamp
                FROM messages
                WHERE session_id = :session_id
                ORDER BY timestamp DESC
                LIMIT :limit
            """),
            {"session_id": session_id, "limit": limit * 2} # Query more to get turns
        ).fetchall()
        
        messages = []
        # Result is chronological DESC (newest first). 
        # We need to reverse to get oldest -> newest
        
        # Also, raw messages might be [User, AI, User, AI]
        # We want to preserve that order.
        
        for row in reversed(list(result)):
            messages.append({
                "role": "user" if row.is_user else "assistant",
                "content": row.content,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            })
            
        return messages
        
    except Exception as e:
        current_app.logger.warning(f"get_recent_messages error: {e}")
        return []


def format_history_for_prompt(messages: List[Dict[str, Any]]) -> str:
    """Format conversation history for Gemini prompt."""
    if not messages:
        return ""
    
    lines = ["Recent conversation:"]
    for msg in messages[-10:]:  # Last 10 messages (5 turns)
        role = "User" if msg["role"] == "user" else "Luna"
        content = msg["content"][:200]  # Truncate long messages
        lines.append(f"{role}: {content}")
    
    return "\n".join(lines)
