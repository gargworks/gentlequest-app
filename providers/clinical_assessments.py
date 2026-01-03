"""
Clinical Assessments for GentleQuest
PHQ-9 (Depression) and GAD-7 (Anxiety) validated screening tools.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json
# psycopg2 imports moved to functions to allow running without postgres driver


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
    
    Args:
        responses: List of 9 integers (0-3) for each question
        
    Returns:
        Dict with total_score, severity, message, and question 9 flag
    """
    if len(responses) != 9:
        raise ValueError(f"PHQ-9 requires exactly 9 responses, got {len(responses)}")
    
    if not all(0 <= r <= 3 for r in responses):
        raise ValueError("All responses must be between 0 and 3")
    
    total_score = sum(responses)
    
    # Determine severity
    severity = "minimal"
    message = ""
    for low, high, sev, msg in PHQ9_SEVERITY_THRESHOLDS:
        if low <= total_score <= high:
            severity = sev
            message = msg
            break
    
    # Check question 9 (suicidal ideation) - requires special attention
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
    
    Args:
        responses: List of 7 integers (0-3) for each question
        
    Returns:
        Dict with total_score, severity, and message
    """
    if len(responses) != 7:
        raise ValueError(f"GAD-7 requires exactly 7 responses, got {len(responses)}")
    
    if not all(0 <= r <= 3 for r in responses):
        raise ValueError("All responses must be between 0 and 3")
    
    total_score = sum(responses)
    
    # Determine severity
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
    """Get recommendations based on PHQ-9 severity."""
    recommendations = []
    
    if has_suicidal_ideation:
        recommendations.append("🆘 If you're having thoughts of self-harm, please reach out to a crisis helpline or trusted person immediately.")
    
    if severity == "minimal":
        recommendations.extend([
            "Continue maintaining your mental wellness habits",
            "Practice regular self-care and check in with yourself",
        ])
    elif severity == "mild":
        recommendations.extend([
            "Consider talking to someone you trust about how you're feeling",
            "Try incorporating stress-reduction activities like exercise or meditation",
            "Monitor your symptoms over the next few weeks",
        ])
    elif severity == "moderate":
        recommendations.extend([
            "Consider speaking with a counselor or therapist",
            "Reach out to a primary care provider",
            "Continue using Luna for daily support",
        ])
    elif severity in ("moderately_severe", "severe"):
        recommendations.extend([
            "We strongly recommend consulting a mental health professional",
            "Consider reaching out to a crisis helpline if needed",
            "Talk to someone you trust about how you're feeling",
        ])
    
    return recommendations


def get_gad7_recommendations(severity: str) -> List[str]:
    """Get recommendations based on GAD-7 severity."""
    recommendations = []
    
    if severity == "minimal":
        recommendations.extend([
            "Continue your current wellness practices",
            "Stay mindful of any changes in your anxiety levels",
        ])
    elif severity == "mild":
        recommendations.extend([
            "Try breathing exercises when feeling anxious",
            "Practice grounding techniques",
            "Consider reducing caffeine and improving sleep habits",
        ])
    elif severity == "moderate":
        recommendations.extend([
            "Consider speaking with a mental health professional",
            "Practice relaxation techniques daily",
            "Use Luna's breathing and grounding exercises regularly",
        ])
    elif severity == "severe":
        recommendations.extend([
            "We recommend consulting a mental health professional",
            "Talk to someone you trust about your anxiety",
            "Consider cognitive behavioral therapy (CBT)",
        ])
    
    return recommendations


# ============================================================================
# API HELPERS
# ============================================================================

def get_assessment_questions(assessment_type: str) -> Dict:
    """Get questions and options for an assessment type."""
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
    """Validate responses for an assessment."""
    if assessment_type == "phq9":
        if len(responses) != 9:
            return False, f"PHQ-9 requires 9 responses, got {len(responses)}"
    elif assessment_type == "gad7":
        if len(responses) != 7:
            return False, f"GAD-7 requires 7 responses, got {len(responses)}"
    else:
        return False, f"Unknown assessment type: {assessment_type}"
    
    if not all(isinstance(r, int) and 0 <= r <= 3 for r in responses):
        return False, "All responses must be integers between 0 and 3"
    
    return True, None


# ============================================================================
# PERSISTENCE (DATABASE)
# ============================================================================

def init_assessment_tables(conn):
    """
    Initialize clinical assessments table if it doesn't exist.
    """
    try:
        import psycopg2
    except ImportError:
        # If running with SQLite or without psycopg2, we might be in test mode or local dev using sqlite
        # If conn is sqlite, we can try to run SQL but syntax might differ slightly (JSONB etc)
        # But for now, just return or print warning if we strictly need Postgres features.
        print("⚠️ psycopg2 not found. init_assessment_tables skipped (unless mocked).")
        return

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS clinical_assessments (
        id SERIAL PRIMARY KEY,
        session_id TEXT NOT NULL,
        assessment_type TEXT NOT NULL,  -- 'phq9' or 'gad7'
        total_score INTEGER NOT NULL,
        severity TEXT NOT NULL,
        responses JSONB NOT NULL,       -- Stored as list of integers
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        metadata JSONB DEFAULT '{}'::jsonb
    );
    
    CREATE WITH INDEX IF NOT EXISTS idx_assessments_session_id ON clinical_assessments(session_id);
    """
    # Note: postgres doesn't support CREATE WITH INDEX directly like that for idx, 
    # but we can do CREATE INDEX separately.
    
    # Correct SQL for Postgres:
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS clinical_assessments (
        id SERIAL PRIMARY KEY,
        session_id TEXT NOT NULL,
        assessment_type TEXT NOT NULL,
        total_score INTEGER NOT NULL,
        severity TEXT NOT NULL,
        responses JSONB NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        metadata JSONB DEFAULT '{}'::jsonb
    );
    
    CREATE INDEX IF NOT EXISTS idx_assessments_session_id ON clinical_assessments(session_id);
    CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON clinical_assessments(created_at);
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute(create_table_sql)
        conn.commit()
        print("✅ Clinical assessments table initialized.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error initializing assessment tables: {e}")
        raise e


def save_assessment_result(conn, session_id: str, assessment_data: Dict) -> int:
    """
    Save an assessment result to the database.
    
    Args:
        conn: Database connection
        session_id: User's session ID
        assessment_data: Dictionary returned by score_phq9 or score_gad7
                         (must contain assessment_type, total_score, severity)
        
    Returns:
        The ID of the inserted record.
    """
    import psycopg2
    
    insert_sql = """
    INSERT INTO clinical_assessments 
    (session_id, assessment_type, total_score, severity, responses, metadata)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id;
    """
    
    # Extract needed fields
    assessment_type = assessment_data.get('assessment_type')
    total_score = assessment_data.get('total_score')
    severity = assessment_data.get('severity')
    # We assume the caller passes the raw responses separately or we inject them into assessment_data
    # But score functions don't return responses.
    # We need the 'responses' list to be passed in or added to the dict.
    # Let's assume the API adds 'responses' to the dict before calling this.
    responses = json.dumps(assessment_data.get('responses', [])) 
    
    # Metadata could store the full result (recommendations, flags)
    metadata = json.dumps({
        "message": assessment_data.get('message'),
        "requires_follow_up": assessment_data.get('requires_follow_up', False),
        "follow_up_reason": assessment_data.get('follow_up_reason'),
        "recommendations": assessment_data.get('recommendations', [])
    })
    
    try:
        with conn.cursor() as cur:
            cur.execute(insert_sql, (
                session_id, 
                assessment_type, 
                total_score, 
                severity, 
                responses, 
                metadata
            ))
            new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    except Exception as e:
        conn.rollback()
        print(f"❌ Error saving assessment: {e}")
        raise e


def get_assessment_history(conn, session_id: str, limit: int = 10) -> List[Dict]:
    """
    Retrieve assessment history for a session.
    """
    try:
        from psycopg2.extras import RealDictCursor
    except ImportError:
        print("⚠️ psycopg2 not found. get_assessment_history returning empty.")
        return []

    sql = """
    SELECT id, assessment_type, total_score, severity, created_at, metadata
    FROM clinical_assessments
    WHERE session_id = %s
    ORDER BY created_at DESC
    LIMIT %s;
    """
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (session_id, limit))
            rows = cur.fetchall()
            
            # Convert rows to serializable dicts
            history = []
            for row in rows:
                row_dict = dict(row)
                if row_dict.get('created_at'):
                    row_dict['created_at'] = row_dict['created_at'].isoformat()
                history.append(row_dict)
            return history
    except Exception as e:
        print(f"❌ Error getting assessment history: {e}")
        return []
