"""
Agentic Wellness Tools for Luna
Smart, context-aware interventions that learn from user history
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from flask import current_app
from sqlalchemy import text
from models import db, InterventionOutcome


# ============================================================================
# INTERVENTION LIBRARY
# ============================================================================


class Intervention:
    """Base class for wellness interventions"""

    def __init__(self, name: str, description: str, content: dict):
        self.name = name
        self.description = description
        self.content = content
        self.intervention_type = None

    def to_dict(self) -> dict:
        return {"name": self.name, "description": self.description, **self.content}


# Breathing Exercises
BREATHING_INTERVENTIONS = {
    "calm_478": {
        "name": "4-7-8 Calming Breath",
        "description": "A relaxing breathing pattern that activates your parasympathetic nervous system.",
        "steps": [
            {
                "action": "breathe_in",
                "duration": 4,
                "instruction": "Breathe in slowly through your nose",
            },
            {"action": "hold", "duration": 7, "instruction": "Hold your breath gently"},
            {
                "action": "breathe_out",
                "duration": 8,
                "instruction": "Exhale slowly through your mouth",
            },
        ],
        "cycles": 4,
        "total_time_seconds": 76,
        "intensity": "moderate",
        "best_for": ["anxiety", "stress", "sleep"],
    },
    "quick_box": {
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
        "intensity": "mild",
        "best_for": ["stress", "panic", "focus"],
    },
    "energize": {
        "name": "Energizing Breath",
        "description": "A gentle pattern to increase alertness and energy.",
        "steps": [
            {
                "action": "breathe_in",
                "duration": 4,
                "instruction": "Deep breath in through your nose",
            },
            {
                "action": "breathe_out",
                "duration": 2,
                "instruction": "Quick exhale through your mouth",
            },
        ],
        "cycles": 6,
        "total_time_seconds": 36,
        "intensity": "mild",
        "best_for": ["fatigue", "low_energy"],
    },
}

# Grounding Exercises
GROUNDING_INTERVENTIONS = {
    "54321_senses": {
        "name": "5-4-3-2-1 Senses",
        "description": "Ground yourself by connecting with your five senses.",
        "steps": [
            {
                "sense": "sight",
                "count": 5,
                "instruction": "Name 5 things you can SEE around you",
            },
            {
                "sense": "touch",
                "count": 4,
                "instruction": "Name 4 things you can TOUCH or feel",
            },
            {"sense": "hear", "count": 3, "instruction": "Name 3 things you can HEAR"},
            {
                "sense": "smell",
                "count": 2,
                "instruction": "Name 2 things you can SMELL",
            },
            {"sense": "taste", "count": 1, "instruction": "Name 1 thing you can TASTE"},
        ],
        "intensity": "moderate",
        "best_for": ["panic", "dissociation", "anxiety"],
    }
}

# Journaling Interventions (Stage 3)
JOURNALING_INTERVENTIONS = {
    "anxiety_reflection": {
        "name": "Anxiety Reflection",
        "description": "A guided journaling exercise to explore what's really worrying you.",
        "prompt": "What specifically am I worried about right now?",
        "follow_ups": [
            "What's the worst that could realistically happen?",
            "What would I tell a friend in this situation?",
            "What's one small thing I can control right now?",
        ],
        "intensity": "moderate",
        "best_for": ["anxiety", "stress", "overwhelmed"],
    },
    "mood_check": {
        "name": "Mood Check-In",
        "description": "A gentle prompt to explore your current feelings.",
        "prompt": "How am I really feeling right now, underneath everything?",
        "follow_ups": [
            "When did I start feeling this way?",
            "What do I need most right now?",
        ],
        "intensity": "mild",
        "best_for": ["sadness", "stress", "fatigue"],
    },
    "gratitude_moment": {
        "name": "Gratitude Moment",
        "description": "Shift perspective by finding small positives.",
        "prompt": "What's one small thing that went okay today?",
        "follow_ups": [
            "Who or what am I grateful for right now?",
        ],
        "intensity": "mild",
        "best_for": ["sadness", "fatigue"],
    },
}

# Talk Mode (Stage 4) - Conversation-based support
TALK_MODE_RESPONSES = {
    "anxiety": "I hear you're still feeling anxious. Sometimes exercises aren't enough - would you like to tell me more about what's really weighing on you?",
    "stress": "It sounds like the stress is still there. I'm here to listen. What's the biggest thing on your mind right now?",
    "sadness": "I'm sorry you're still feeling down. Sometimes it helps to talk it out. What's been going on?",
    "panic": "I can tell you're really struggling. You don't have to face this alone. What would help right now?",
    "sleep": "Sleep troubles can be tough. Let's talk about what's keeping your mind racing.",
    "overwhelmed": "Feeling overwhelmed is exhausting. Let's break things down together - what feels like the biggest weight right now?",
    "fatigue": "I understand you're drained. Sometimes rest isn't about sleep. What's been draining your energy?",
}


# ============================================================================
# INTERVENTION SELECTOR (Smart Tool)
# ============================================================================


class InterventionSelector:
    """Intelligently selects interventions based on user history and context"""

    def select_intervention(
        self,
        issue: str,
        intensity: str,
        user_effectiveness: Dict[str, float],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Select the best intervention for this user, this context

        Args:
            issue: "anxiety", "stress", "panic", "sleep", etc.
            intensity: "mild", "moderate", "severe"
            user_effectiveness: Past success rates {"breathing_calm_478": 0.85, ...}
            context: {"time": "night", "location": "home", ...}

        Returns:
            Intervention dict with personalization
        """
        # Get candidate interventions
        candidates = self._get_candidates(issue)

        # Score each based on context
        scored = []
        for intervention_id, intervention in candidates.items():
            score = self._score_intervention(
                intervention_id,
                intervention,
                issue,
                intensity,
                user_effectiveness,
                context,
            )
            scored.append((intervention_id, intervention, score))

        # Select best
        if not scored:
            # Fallback: breathing is always safe
            intervention_id = "calm_478"
            intervention = BREATHING_INTERVENTIONS[intervention_id]
        else:
            scored.sort(key=lambda x: x[2], reverse=True)
            intervention_id, intervention, score = scored[0]

        # Add personalization
        personalization = self._generate_personalization(
            intervention_id, user_effectiveness, context
        )

        # Determine type from intervention_id
        if intervention_id in BREATHING_INTERVENTIONS:
            intervention_type = "breathing"
        elif intervention_id in GROUNDING_INTERVENTIONS:
            intervention_type = "grounding"
        else:
            intervention_type = "general"

        return {
            "intervention_id": intervention_id,
            "type": intervention_type,
            "content": intervention,
            "personalization": personalization,
            "reasoning": f"Selected based on {issue} + past effectiveness",
        }

    def _get_candidates(self, issue: str) -> Dict[str, Any]:
        """Get intervention candidates for this issue"""
        candidates = {}

        # Check breathing exercises
        for intervention_id, intervention in BREATHING_INTERVENTIONS.items():
            if issue in intervention.get("best_for", []):
                candidates[intervention_id] = intervention

        # Check grounding exercises
        for intervention_id, intervention in GROUNDING_INTERVENTIONS.items():
            if issue in intervention.get("best_for", []):
                candidates[intervention_id] = intervention

        # If no specific matches, return all breathing (safe default)
        if not candidates:
            candidates = BREATHING_INTERVENTIONS.copy()

        return candidates

    def _score_intervention(
        self,
        intervention_id: str,
        intervention: dict,
        issue: str,
        intensity: str,
        user_effectiveness: Dict[str, float],
        context: Dict[str, Any],
    ) -> float:
        """Score an intervention for this context"""
        score = 0.5  # Base score

        # Factor 1: Past effectiveness (most important)
        if intervention_id in user_effectiveness:
            score += user_effectiveness[intervention_id] * 0.4

        # Factor 2: Intensity match
        if intervention.get("intensity") == intensity:
            score += 0.2

        # Factor 3: Time appropriateness
        time_of_day = context.get("time_of_day", "day")
        if time_of_day == "night" and intervention.get("total_time_seconds", 999) < 60:
            score += 0.1  # Prefer shorter exercises at night

        # Factor 4: Best for this issue
        if issue in intervention.get("best_for", []):
            score += 0.3

        return min(score, 1.0)

    def _generate_personalization(
        self,
        intervention_id: str,
        user_effectiveness: Dict[str, float],
        context: Dict[str, Any],
    ) -> str:
        """Generate personalized message"""
        effectiveness = user_effectiveness.get(intervention_id)

        if effectiveness and effectiveness > 0.7:
            return f"This worked well for you before ({int(effectiveness * 100)}% effective)"
        elif effectiveness:
            return "Let's try this approach together"
        else:
            return "This might be helpful right now"


# ============================================================================
# AGENT TOOLS (Core Functions)
# ============================================================================

_intervention_selector = InterventionSelector()


def get_wellness_intervention(
    issue: str,
    intensity: str = "moderate",
    user_id: str = None,
    context: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Smart wellness intervention selection with VARIETY.
    
    Uses session history to avoid repeating the same intervention.
    Progression: breathing → grounding → journaling → talk mode

    Args:
        issue: "anxiety", "stress", "panic", "sleep", "sadness"
        intensity: "mild", "moderate", "severe"
        user_id: Session ID for personalization
        context: Additional context (time, location, etc.)

    Returns:
        {
            'success': True,
            'intervention_type': 'breathing',
            'intervention_id': 'calm_478',
            'exercise': {...},
            'interactive': True,
            'offer_stage': 1,
            'personalization': "..."
        }
    """
    try:
        context = context or {}
        issue_lower = issue.lower()
        
        # Get variety information from session
        variety = {"offer_stage": 1, "intervention_type": "breathing", "previous_interventions": []}
        if user_id:
            try:
                from providers.session_memory import get_intervention_variety, record_intervention_shown
                variety = get_intervention_variety(user_id, issue_lower)
            except Exception as e:
                current_app.logger.warning(f"Could not get variety: {e}")
        
        offer_stage = variety["offer_stage"]
        intervention_type = variety["intervention_type"]
        
        # Select intervention based on stage
        if intervention_type == "talk":
            # Stage 4: Talk mode - no exercise, just conversation
            talk_response = TALK_MODE_RESPONSES.get(
                issue_lower, 
                "I'm here to listen. Would you like to tell me more about what's going on?"
            )
            return {
                "success": True,
                "intervention_type": "talk",
                "intervention_id": f"talk_{issue_lower}",
                "exercise": None,
                "interactive": False,
                "offer_stage": offer_stage,
                "talk_prompt": talk_response,
                "personalization": "We've tried a few exercises. Let's talk instead.",
            }
        
        elif intervention_type == "journaling":
            # Stage 3: Journaling prompt
            journal = _select_journaling_intervention(issue_lower)
            intervention_id = f"journal_{issue_lower}"
            
            # Record this intervention was shown
            if user_id:
                try:
                    record_intervention_shown(user_id, issue_lower, "journaling", intervention_id, offer_stage)
                except Exception:
                    pass
            
            return {
                "success": True,
                "intervention_type": "journaling",
                "intervention_id": intervention_id,
                "exercise": journal,
                "interactive": True,
                "offer_stage": offer_stage,
                "personalization": "Sometimes writing helps process feelings.",
            }
        
        elif intervention_type == "grounding":
            # Stage 2: Grounding exercise
            intervention_id = "54321_senses"
            grounding = GROUNDING_INTERVENTIONS[intervention_id]
            
            # Record this intervention was shown
            if user_id:
                try:
                    from providers.session_memory import record_intervention_shown
                    record_intervention_shown(user_id, issue_lower, "grounding", intervention_id, offer_stage)
                except Exception:
                    pass
            
            return {
                "success": True,
                "intervention_type": "grounding",
                "intervention_id": intervention_id,
                "exercise": grounding,
                "interactive": True,
                "offer_stage": offer_stage,
                "personalization": "Let's try something different to ground you in the present.",
            }
        
        else:
            # Stage 1 (default): Breathing exercise
            user_effectiveness = _get_user_effectiveness(user_id) if user_id else {}
            
            # Add time context
            hour = datetime.now().hour
            context["time_of_day"] = "night" if (hour >= 21 or hour <= 6) else "day"
            
            # Use selector for best breathing exercise
            selection = _intervention_selector.select_intervention(
                issue=issue_lower,
                intensity=intensity.lower(),
                user_effectiveness=user_effectiveness,
                context=context,
            )
            
            # Record this intervention was shown
            if user_id:
                try:
                    from providers.session_memory import record_intervention_shown
                    record_intervention_shown(user_id, issue_lower, "breathing", selection["intervention_id"], offer_stage)
                except Exception:
                    pass
            
            return {
                "success": True,
                "intervention_type": selection["type"],
                "intervention_id": selection["intervention_id"],
                "exercise": selection["content"],
                "interactive": True,
                "offer_stage": offer_stage,
                "personalization": selection["personalization"],
                "reasoning": selection.get("reasoning", ""),
            }

    except Exception as e:
        current_app.logger.error(f"get_wellness_intervention error: {e}")
        # Fallback to safe default
        return {
            "success": True,
            "intervention_type": "breathing",
            "intervention_id": "calm_478",
            "exercise": BREATHING_INTERVENTIONS["calm_478"],
            "interactive": True,
            "offer_stage": 1,
            "personalization": "",
        }


def _select_journaling_intervention(issue: str) -> Dict[str, Any]:
    """Select best journaling intervention for issue."""
    # Map issues to journaling types
    issue_to_journal = {
        "anxiety": "anxiety_reflection",
        "stress": "anxiety_reflection",
        "overwhelmed": "anxiety_reflection",
        "sadness": "mood_check",
        "fatigue": "gratitude_moment",
        "panic": "mood_check",
        "sleep": "mood_check",
    }
    
    journal_id = issue_to_journal.get(issue, "mood_check")
    return JOURNALING_INTERVENTIONS.get(journal_id, JOURNALING_INTERVENTIONS["mood_check"])


def _get_user_effectiveness(user_id: str) -> Dict[str, float]:
    """
    Get user's past intervention effectiveness scores via ORM
    """
    try:
        results = InterventionOutcome.query.filter_by(session_id=user_id)\
            .filter(InterventionOutcome.effectiveness_rating != None)\
            .all()
        
        # Aggregate effectiveness by intervention_id
        stats = {}
        counts = {}
        for row in results:
            iid = row.intervention_id
            stats[iid] = stats.get(iid, 0) + row.effectiveness_rating
            counts[iid] = counts.get(iid, 0) + 1
            
        return {iid: stats[iid]/counts[iid] for iid in stats}
    except Exception as e:
        current_app.logger.warning(f"Error fetching user effectiveness: {e}")
        return {}


def record_interaction_outcome(
    user_id: str,
    intervention_id: str,
    completed: bool,
    effectiveness_rating: Optional[float] = None,
    user_feedback: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record intervention outcome for learning

    Args:
        user_id: Session ID
        intervention_id: ID of intervention used
        completed: Whether user completed it
        effectiveness_rating: 0-1 score (optional)
        user_feedback: Free text feedback (optional)
    """
    try:
        outcome = InterventionOutcome(
            session_id=user_id,
            intervention_id=intervention_id,
            completed=completed,
            effectiveness_rating=effectiveness_rating,
            feedback=user_feedback,
            timestamp=datetime.utcnow()
        )
        db.session.add(outcome)
        db.session.commit()

        return {"success": True, "message": "Outcome recorded"}
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"record_interaction_outcome error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# TOOL EXECUTION (Updated)
# ============================================================================


def execute_tool(name: str, args: dict, session_id: str) -> Dict[str, Any]:
    """
    Execute an agent tool

    Args:
        name: Tool name
        args: Tool arguments
        session_id: User session ID

    Returns:
        Tool result with success flag
    """
    try:
        if name == "get_wellness_intervention":
            return get_wellness_intervention(
                issue=args.get("issue", "anxiety"),
                intensity=args.get("intensity", "moderate"),
                user_id=session_id,
                context=args.get("context", {}),
            )
        elif name == "record_interaction_outcome":
            return record_interaction_outcome(
                user_id=session_id,
                intervention_id=args.get("intervention_id"),
                completed=args.get("completed", True),
                effectiveness_rating=args.get("effectiveness_rating"),
                user_feedback=args.get("user_feedback"),
            )
        else:
            return {"success": False, "error": f"Unknown tool: {name}"}

    except Exception as e:
        current_app.logger.error(f"Tool execution error [{name}]: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# RESPONSE FORMATTING
# ============================================================================


def format_tool_result_for_response(tool_name: str, result: Dict[str, Any]) -> str:
    """Format tool result for Luna's response"""
    if not result.get("success"):
        return ""

    if tool_name == "get_wellness_intervention":
        exercise = result.get("exercise", {})
        personalization = result.get("personalization", "")
        name = exercise.get("name", "wellness exercise")

        response = f"Let me guide you through {name}."
        if personalization:
            response += f" {personalization}"

        return response

    return ""
