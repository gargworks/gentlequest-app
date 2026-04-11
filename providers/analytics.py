"""
Analytics Module for GentleQuest
Provides queries and metrics for intervention effectiveness and user engagement.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import text
from flask import current_app

from models import db, InterventionOutcome
from sqlalchemy import func, case, and_


# ============================================================================
# INTERVENTION EFFECTIVENESS METRICS
# ============================================================================

def get_intervention_stats(days: int = 30) -> Dict[str, Any]:
    """
    Get overall intervention statistics for the last N days.
    
    Returns:
        {
            'total_interventions': int,
            'total_started': int,
            'total_completed': int,
            'total_skipped': int,
            'completion_rate': float,
            'avg_mood_improvement': float,
            'avg_time_spent': float
        }
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = db.session.query(
            func.count(InterventionOutcome.id).label('total'),
            func.count(case((InterventionOutcome.outcome == 'started', 1), else_=None)).label('started'),
            func.count(case((InterventionOutcome.outcome == 'completed', 1), else_=None)).label('completed'),
            func.count(case((InterventionOutcome.outcome == 'skipped', 1), else_=None)).label('skipped'),
            func.avg(case(
                (and_(InterventionOutcome.mood_after != None, InterventionOutcome.mood_before != None), 
                 InterventionOutcome.mood_after - InterventionOutcome.mood_before),
                else_=None
            )).label('avg_mood_improvement'),
            func.avg(InterventionOutcome.time_spent_seconds).label('avg_time_spent')
        ).filter(InterventionOutcome.timestamp >= cutoff_date).first()
        
        total = result.total or 0
        completed = result.completed or 0
        
        return {
            'total_interventions': total,
            'total_started': result.started or 0,
            'total_completed': completed,
            'total_skipped': result.skipped or 0,
            'completion_rate': (completed / total) if total > 0 else 0.0,
            'avg_mood_improvement': float(result.avg_mood_improvement or 0),
            'avg_time_spent': float(result.avg_time_spent or 0),
        }
        
    except Exception as e:
        current_app.logger.error(f"get_intervention_stats error: {e}")
        return {
            'total_interventions': 0,
            'total_started': 0,
            'total_completed': 0,
            'total_skipped': 0,
            'completion_rate': 0.0,
            'avg_mood_improvement': 0.0,
            'avg_time_spent': 0.0,
        }


def get_completion_rates_by_type(days: int = 30) -> Dict[str, Dict[str, Any]]:
    """
    Get completion rates broken down by intervention type.
    
    Returns:
        {
            'breathing': {
                'total': 50,
                'completed': 35,
                'skipped': 10,
                'completion_rate': 0.70,
                'avg_mood_improvement': 2.5,
                'avg_time_spent': 120
            },
            'grounding': {...},
            'journaling': {...}
        }
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.session.query(
            InterventionOutcome.exercise_type,
            func.count(InterventionOutcome.id).label('total'),
            func.count(case((InterventionOutcome.outcome == 'completed', 1), else_=None)).label('completed'),
            func.count(case((InterventionOutcome.outcome == 'skipped', 1), else_=None)).label('skipped'),
            func.avg(case(
                (and_(InterventionOutcome.mood_after != None, InterventionOutcome.mood_before != None), 
                 InterventionOutcome.mood_after - InterventionOutcome.mood_before),
                else_=None
            )).label('avg_mood_improvement'),
            func.avg(InterventionOutcome.time_spent_seconds).label('avg_time_spent')
        ).filter(InterventionOutcome.timestamp >= cutoff_date)\
         .filter(InterventionOutcome.exercise_type != None)\
         .group_by(InterventionOutcome.exercise_type)\
         .order_by(func.count(InterventionOutcome.id).desc()).all()
        
        stats = {}
        for row in results:
            total = row.total or 0
            completed = row.completed or 0
            
            stats[row.exercise_type] = {
                'total': total,
                'completed': completed,
                'skipped': row.skipped or 0,
                'completion_rate': (completed / total) if total > 0 else 0.0,
                'avg_mood_improvement': float(row.avg_mood_improvement or 0),
                'avg_time_spent': float(row.avg_time_spent or 0),
            }
        
        return stats
        
    except Exception as e:
        current_app.logger.error(f"get_completion_rates_by_type error: {e}")
        return {}


def get_mood_improvement_by_type(days: int = 30) -> Dict[str, float]:
    """
    Get average mood improvement for each intervention type.
    
    Returns:
        {
            'breathing': 2.3,
            'grounding': 1.8,
            'journaling': 3.1
        }
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.session.query(
            InterventionOutcome.exercise_type,
            func.avg(InterventionOutcome.mood_after - InterventionOutcome.mood_before).label('avg_improvement')
        ).filter(InterventionOutcome.timestamp >= cutoff_date)\
         .filter(InterventionOutcome.exercise_type != None)\
         .filter(InterventionOutcome.mood_before != None)\
         .filter(InterventionOutcome.mood_after != None)\
         .filter(InterventionOutcome.outcome == 'completed')\
         .group_by(InterventionOutcome.exercise_type).all()
        
        return {
            row.exercise_type: float(row.avg_improvement or 0)
            for row in results
        }
        
    except Exception as e:
        current_app.logger.error(f"get_mood_improvement_by_type error: {e}")
        return {}


# ============================================================================
# USER ENGAGEMENT METRICS
# ============================================================================

def get_user_engagement_metrics(session_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
    """
    Get user engagement metrics (optionally for specific session).
    
    Returns:
        {
            'total_interventions': 10,
            'interventions_completed': 7,
            'interventions_skipped': 2,
            'avg_session_duration': 180,
            'favorite_intervention': 'journaling',
            'best_mood_improvement': 3.5
        }
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.session.query(
            func.count(InterventionOutcome.id).label('total'),
            func.count(case((InterventionOutcome.outcome == 'completed', 1), else_=None)).label('completed'),
            func.count(case((InterventionOutcome.outcome == 'skipped', 1), else_=None)).label('skipped'),
            func.avg(InterventionOutcome.time_spent_seconds).label('avg_time'),
            func.max(InterventionOutcome.mood_after - InterventionOutcome.mood_before).label('best_improvement')
        ).filter(InterventionOutcome.timestamp >= cutoff_date)
        
        if session_id:
            query = query.filter(InterventionOutcome.session_id == session_id)
        
        result = query.first()
        
        # Get favorite intervention type
        fav_query = db.session.query(
            InterventionOutcome.exercise_type,
            func.count(InterventionOutcome.id).label('count')
        ).filter(InterventionOutcome.timestamp >= cutoff_date)\
         .filter(InterventionOutcome.exercise_type != None)\
         .filter(InterventionOutcome.outcome == 'completed')
        
        if session_id:
            fav_query = fav_query.filter(InterventionOutcome.session_id == session_id)
            
        favorite_result = fav_query.group_by(InterventionOutcome.exercise_type)\
            .order_by(func.count(InterventionOutcome.id).desc())\
            .first()
        
        return {
            'total_interventions': result.total or 0,
            'interventions_completed': result.completed or 0,
            'interventions_skipped': result.skipped or 0,
            'avg_session_duration': float(result.avg_time or 0),
            'favorite_intervention': favorite_result.exercise_type if favorite_result else None,
            'best_mood_improvement': float(result.best_improvement or 0),
        }
        
    except Exception as e:
        current_app.logger.error(f"get_user_engagement_metrics error: {e}")
        return {
            'total_interventions': 0,
            'interventions_completed': 0,
            'interventions_skipped': 0,
            'avg_session_duration': 0.0,
            'favorite_intervention': None,
            'best_mood_improvement': 0.0,
        }


# ============================================================================
# FUNCTION CALLING ANALYTICS
# ============================================================================

def get_function_calling_stats(days: int = 7) -> Dict[str, Any]:
    """
    Track Gemini vs keyword fallback rates over time.
    
    Note: This requires tracking function_call_source in conversation_logs
    or a separate tracking table. For now, returns placeholder.
    
    Returns:
        {
            'total_calls': 100,
            'gemini_native': 75,
            'keyword_fallback': 25,
            'success_rate': 0.75
        }
    """
    # TODO: Implement once we add function_call_source tracking to database
    # For now, return placeholder
    return {
        'total_calls': 0,
        'gemini_native': 0,
        'keyword_fallback': 0,
        'success_rate': 0.0,
        'note': 'Function calling tracking not yet implemented in database'
    }


# ============================================================================
# PERSONALIZATION HELPERS
# ============================================================================

def get_best_intervention_for_user(session_id: str, issue: str = None) -> Optional[str]:
    """
    Determine the best intervention type for a user based on their history.
    
    Prioritizes interventions with:
    1. Highest completion rate
    2. Best mood improvement
    3. Longest engagement time
    
    Returns:
        'breathing' | 'grounding' | 'journaling' | None
    """
    try:
        # Get user's intervention history via ORM
        base_query = db.session.query(
            InterventionOutcome.exercise_type,
            func.count(case((InterventionOutcome.outcome == 'completed', 1), else_=None)).label('completed'),
            func.count(InterventionOutcome.id).label('total'),
            func.avg(case(
                (and_(InterventionOutcome.mood_after != None, InterventionOutcome.mood_before != None), 
                 InterventionOutcome.mood_after - InterventionOutcome.mood_before),
                else_=None
            )).label('avg_mood_improvement'),
            func.avg(InterventionOutcome.time_spent_seconds).label('avg_time_spent')
        ).filter(InterventionOutcome.session_id == session_id)\
         .filter(InterventionOutcome.exercise_type != None)
        
        if issue:
            base_query = base_query.filter(InterventionOutcome.issue == issue)
        
        results = base_query.group_by(InterventionOutcome.exercise_type)\
            .having(func.count(InterventionOutcome.id) >= 2).all()
        
        if not results:
            return None  # Not enough data, use default variety logic
        
        # Score each intervention type
        best_score = -1
        best_type = None
        
        for row in results:
            completion_rate = (row.completed / row.total) if row.total > 0 else 0
            mood_improvement = row.avg_mood_improvement or 0
            
            # Weighted score: 50% completion rate, 50% mood improvement
            score = (completion_rate * 0.5) + ((mood_improvement / 10) * 0.5)
            
            if score > best_score:
                best_score = score
                best_type = row.exercise_type
        
        return best_type
        
    except Exception as e:
        current_app.logger.error(f"get_best_intervention_for_user error: {e}")
        return None


def get_intervention_recommendations(days: int = 30) -> Dict[str, str]:
    """
    Get data-driven recommendations for improving interventions.
    
    Returns:
        {
            'highest_completion': 'journaling',
            'best_mood_improvement': 'breathing',
            'most_popular': 'grounding',
            'needs_improvement': 'breathing'
        }
    """
    try:
        stats = get_completion_rates_by_type(days)
        
        if not stats:
            return {}
        
        # Find best performers
        highest_completion = max(stats.items(), key=lambda x: x[1]['completion_rate'])
        best_mood = max(stats.items(), key=lambda x: x[1]['avg_mood_improvement'])
        most_popular = max(stats.items(), key=lambda x: x[1]['total'])
        needs_improvement = min(stats.items(), key=lambda x: x[1]['completion_rate'])
        
        return {
            'highest_completion': highest_completion[0],
            'best_mood_improvement': best_mood[0],
            'most_popular': most_popular[0],
            'needs_improvement': needs_improvement[0],
        }
        
    except Exception as e:
        current_app.logger.error(f"get_intervention_recommendations error: {e}")
        return {}
