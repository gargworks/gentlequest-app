import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ============================================================================
# PHQ-9 (Patient Health Questionnaire-9)
# ============================================================================

PHQ9_QUESTIONS = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
    "Trouble concentrating on things, such as reading the newspaper or watching television",
    "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual",
    "Thoughts that you would be better off dead, or of hurting yourself in some way",
]

PHQ9_RESPONSE_OPTIONS = [
    {"value": 0, "label": "Not at all"},
    {"value": 1, "label": "Several days"},
    {"value": 2, "label": "More than half the days"},
    {"value": 3, "label": "Nearly every day"},
]

PHQ9_SEVERITY_THRESHOLDS = [
    (0, 4, "minimal", "Your symptoms suggest minimal depression."),
    (5, 9, "mild", "Your symptoms suggest mild depression. Consider monitoring and self-care."),
    (10, 14, "moderate", "Your symptoms suggest moderate depression. Consider speaking with a mental health professional."),
    (15, 19, "moderately_severe", "Your symptoms suggest moderately severe depression. We recommend consulting a mental health professional."),
    (20, 27, "severe", "Your symptoms suggest severe depression. Please reach out to a mental health professional or crisis line."),
]


# ============================================================================
# GAD-7 (Generalized Anxiety Disorder-7)
# ============================================================================

GAD7_QUESTIONS = [
    "Feeling nervous, anxious, or on edge",
    "Not being able to stop or control worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being so restless that it's hard to sit still",
    "Becoming easily annoyed or irritable",
    "Feeling afraid as if something awful might happen",
]

GAD7_RESPONSE_OPTIONS = [
    {"value": 0, "label": "Not at all"},
    {"value": 1, "label": "Several days"},
    {"value": 2, "label": "More than half the days"},
    {"value": 3, "label": "Nearly every day"},
]

GAD7_SEVERITY_THRESHOLDS = [
    (0, 4, "minimal", "Your symptoms suggest minimal anxiety."),
    (5, 9, "mild", "Your symptoms suggest mild anxiety. Consider relaxation techniques and self-care."),
    (10, 14, "moderate", "Your symptoms suggest moderate anxiety. Consider speaking with a mental health professional."),
    (15, 21, "severe", "Your symptoms suggest severe anxiety. We recommend consulting a mental health professional."),
]


# ============================================================================
# SCORING FUNCTIONS
# ============================================================================

def score_phq9(responses: List[int]) -> Dict:
    """
    Score PHQ-9 assessment.
    """
    valid, error = validate_responses("phq9", responses)
    if not valid:
        if "must be integers" in (error or ""):
            raise TypeError(error)
        raise ValueError(error)
    
    total_score = sum(responses)
    
    severity = "minimal"
    message = ""
    for low, high, sev, msg in PHQ9_SEVERITY_THRESHOLDS:
        if low <= total_score <= high:
            severity = sev
            message = msg
            break
    
    q9_score = responses[8]
    requires_follow_up = q9_score > 0
    
    return {
        "assessment_type": "phq9",
        "total_score": total_score,
        "max_score": 27,
        "severity": severity,
        "message": message,
        "requires_follow_up": requires_follow_up,
        "follow_up_reason": "Question 9 indicates thoughts of self-harm" if requires_follow_up else None,
        "recommendations": get_phq9_recommendations(severity, requires_follow_up),
    }


def score_gad7(responses: List[int]) -> Dict:
    """
    Score GAD-7 assessment.
    """
    valid, error = validate_responses("gad7", responses)
    if not valid:
        if "must be integers" in (error or ""):
            raise TypeError(error)
        raise ValueError(error)
    
    total_score = sum(responses)
    
    severity = "minimal"
    message = ""
    for low, high, sev, msg in GAD7_SEVERITY_THRESHOLDS:
        if low <= total_score <= high:
            severity = sev
            message = msg
            break
    
    return {
        "assessment_type": "gad7",
        "total_score": total_score,
        "max_score": 21,
        "severity": severity,
        "message": message,
        "recommendations": get_gad7_recommendations(severity),
    }


# ============================================================================
# RECOMMENDATIONS
# ============================================================================

def get_phq9_recommendations(severity: str, has_suicidal_ideation: bool) -> List[str]:
    recommendations = []
    if has_suicidal_ideation:
        recommendations.append("\ud83c\udd98 If you're having thoughts of self-harm, please reach out to a crisis helpline or trusted person immediately.")
    
    if severity == "minimal":
        recommendations.extend(["Continue maintaining your mental wellness habits"])
    elif severity == "mild":
        recommendations.extend(["Monitor your symptoms over the next few weeks"])
    elif severity == "moderate":
        recommendations.extend(["Consider speaking with a counselor or therapist"])
    elif severity in ("moderately_severe", "severe"):
        recommendations.extend(["We strongly recommend consulting a mental health professional"])
    
    return recommendations


def get_gad7_recommendations(severity: str) -> List[str]:
    recommendations = []
    if severity == "minimal":
        recommendations.extend(["Continue your current wellness practices"])
    elif severity == "mild":
        recommendations.extend(["Try breathing exercises when feeling anxious"])
    elif severity == "moderate":
        recommendations.extend(["Consider speaking with a mental health professional"])
    elif severity == "severe":
        recommendations.extend(["We recommend consulting a mental health professional"])
    
    return recommendations


# ============================================================================
# API HELPERS
# ============================================================================

def get_assessment_questions(assessment_type: str) -> Dict:
    if assessment_type == "phq9":
        return {
            "type": "phq9",
            "name": "PHQ-9 Depression Screening",
            "description": "Over the last 2 weeks, how often have you been bothered by any of the following problems?",
            "questions": [{"id": i, "text": q} for i, q in enumerate(PHQ9_QUESTIONS)],
            "options": PHQ9_RESPONSE_OPTIONS,
            "total_questions": 9,
        }
    elif assessment_type == "gad7":
        return {
            "type": "gad7",
            "name": "GAD-7 Anxiety Screening",
            "description": "Over the last 2 weeks, how often have you been bothered by any of the following problems?",
            "questions": [{"id": i, "text": q} for i, q in enumerate(GAD7_QUESTIONS)],
            "options": GAD7_RESPONSE_OPTIONS,
            "total_questions": 7,
        }
    else:
        raise ValueError(f"Unknown assessment type: {assessment_type}")


def validate_responses(assessment_type: str, responses: List[int]) -> Tuple[bool, Optional[str]]:
    if assessment_type == "phq9":
        if len(responses) != 9:
            return False, f"PHQ-9 requires 9 responses, got {len(responses)}"
    elif assessment_type == "gad7":
        if len(responses) != 7:
            return False, f"GAD-7 requires 7 responses, got {len(responses)}"
    else:
        return False, f"Unknown assessment type: {assessment_type}"
    
    if not all(isinstance(r, int) for r in responses):
        return False, "All responses must be integers"
    
    if not all(0 <= r <= 3 for r in responses):
        return False, "All responses must be between 0 and 3"
    
    return True, None


# ============================================================================
# PERSISTENCE (ORM)
# ============================================================================

def save_assessment_result(session_id: str, assessment_data: Dict) -> int:
    """
    Save an assessment result using SQLAlchemy ORM.
    """
    from models import db, ClinicalAssessment
    
    assessment = ClinicalAssessment(
        session_id=session_id,
        assessment_type=assessment_data.get('assessment_type'),
        responses=assessment_data.get('responses', []),
        total_score=assessment_data.get('total_score'),
        severity=assessment_data.get('severity'),
        requires_follow_up=assessment_data.get('requires_follow_up', False),
        assessment_metadata={
            "message": assessment_data.get('message'),
            "follow_up_reason": assessment_data.get('follow_up_reason'),
            "recommendations": assessment_data.get('recommendations', [])
        }
    )
    
    db.session.add(assessment)
    db.session.commit()
    return assessment.id


def get_assessment_history(session_id: str, limit: int = 10) -> List[Dict]:
    """
    Retrieve assessment history for a session using SQLAlchemy ORM.
    """
    from models import ClinicalAssessment
    
    history = ClinicalAssessment.query.filter_by(session_id=session_id)\
        .order_by(ClinicalAssessment.timestamp.desc())\
        .limit(limit).all()
        
    results = []
    for item in history:
        results.append({
            "id": item.id,
            "session_id": item.session_id,
            "assessment_type": item.assessment_type,
            "total_score": item.total_score,
            "severity": item.severity,
            "responses": item.responses,
            "requires_follow_up": item.requires_follow_up,
            "timestamp": item.timestamp.isoformat() if item.timestamp else None,
            "assessment_metadata": item.assessment_metadata
        })
    return results
