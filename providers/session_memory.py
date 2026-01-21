"""
Session Memory for GentleQuest
Tracks interventions shown per session for variety and learning.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import text
from flask import current_app

from models import db, InterventionOutcome, Message


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
        results = InterventionOutcome.query.filter_by(session_id=session_id)\
            .order_by(InterventionOutcome.timestamp.desc())\
            .limit(limit).all()
        
        interventions = []
        for row in results:
            ts = row.timestamp.isoformat() if row.timestamp and hasattr(row.timestamp, 'isoformat') else None
            
            interventions.append({
                "intervention_id": row.intervention_id,
                "issue": row.issue,
                "offer_stage": row.offer_stage,
                "outcome": row.outcome,
                "timestamp": ts,
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
        outcome = InterventionOutcome(
            session_id=session_id,
            intervention_id=intervention_id,
            issue=issue,
            offer_stage=offer_stage,
            outcome='offered',
            completed=False,
            timestamp=datetime.utcnow()
        )
        db.session.add(outcome)
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
    # Define issue buckets for variety tracking
    WELLNESS_BUCKET = ["anxious", "anxiety", "nervous", "worried", "panic", "overwhelmed", "stressed", "stress", "pressure"]
    MOOD_BUCKET = ["sad", "depressed", "down", "lonely", "hopeless"]
    
    try:
        import logging
        # Determine current category
        issue_lower = (issue or "wellness").lower()
        category_issues = [issue_lower]
        if issue_lower in WELLNESS_BUCKET:
            category_issues = WELLNESS_BUCKET
        elif issue_lower in MOOD_BUCKET:
            category_issues = MOOD_BUCKET

        # Get all previous interventions in this category for this session
        results = db.session.query(InterventionOutcome).filter(
            InterventionOutcome.session_id == session_id,
            InterventionOutcome.issue.in_(category_issues)
        ).order_by(InterventionOutcome.timestamp.desc()).all()
        
        previous = [{"id": r.intervention_id, "stage": r.offer_stage, "outcome": r.outcome} for r in results]
        
        # Use total count in category for variety stage
        count = len(previous)
        
        # Determine next offer stage (1-4)
        if count == 0:
            return {"offer_stage": 1, "intervention_type": "breathing", "previous_interventions": []}
        elif count == 1:
            return {"offer_stage": 2, "intervention_type": "grounding", "previous_interventions": previous}
        elif count == 2:
            return {"offer_stage": 3, "intervention_type": "journaling", "previous_interventions": previous}
        else:
            return {"offer_stage": 4, "intervention_type": "talk", "previous_interventions": previous}
            
    except Exception as e:
        import logging
        logging.error(f"🚨 get_intervention_variety error: {e}")
        return {"offer_stage": 1, "intervention_type": "breathing", "previous_interventions": []}


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
        # Update the most recent matching intervention via ORM
        outcome_entry = InterventionOutcome.query.filter_by(
            session_id=session_id, 
            intervention_id=intervention_id
        ).order_by(InterventionOutcome.timestamp.desc()).first()

        if not outcome_entry:
            return False

        outcome_entry.outcome = outcome
        outcome_entry.completed = (outcome == "completed")
        if exercise_type: outcome_entry.exercise_type = exercise_type
        if time_spent_seconds: outcome_entry.time_spent_seconds = time_spent_seconds
        if mood_before: outcome_entry.mood_before = mood_before
        if mood_after: outcome_entry.mood_after = mood_after
        if effectiveness_rating: outcome_entry.effectiveness_rating = effectiveness_rating
        if feedback: outcome_entry.feedback = feedback
        
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
        # Use Message ORM model (mapped to chat_messages table)
        results = Message.query.filter_by(session_id=session_id)\
            .order_by(Message.timestamp.desc())\
            .limit(limit * 2).all()
        
        messages = []
        # Result is chronological DESC (newest first). 
        # We need to reverse to get oldest -> newest
        
        for row in reversed(results):
            ts = row.timestamp.isoformat() if row.timestamp and hasattr(row.timestamp, 'isoformat') else None

            messages.append({
                "role": "user" if row.is_user else "assistant",
                "content": row.content,
                "timestamp": ts,
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
