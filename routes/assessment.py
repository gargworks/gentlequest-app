"""
Clinical assessment endpoints (PHQ-9, GAD-7).
Extracted from app.py monolith.
"""

from flask import Blueprint, current_app, jsonify, request

from extensions import limiter  # noqa: F401 — available for future rate limits

assessment_bp = Blueprint("assessment", __name__)


@assessment_bp.route("/api/assessment/<assessment_type>/questions", methods=["GET"])
def get_assessment_questions_route(assessment_type):
    """Get questions for a specific assessment type"""
    try:
        from providers.clinical_assessments import get_assessment_questions
        questions = get_assessment_questions(assessment_type)
        return jsonify(questions)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error fetching assessment questions: {e}")
        return jsonify({"error": "Internal server error"}), 500


@assessment_bp.route("/api/assessment/<assessment_type>", methods=["POST"])
def submit_assessment(assessment_type):
    """Submit and score an assessment"""
    try:
        data = request.get_json() or {}
        session_id = request.headers.get("X-Session-ID") or data.get("session_id")

        if not session_id:
            return jsonify({"error": "Session ID required"}), 401

        responses = data.get("responses")
        if responses is None:
            return jsonify({"error": "Responses array required"}), 400

        # 1. Validate
        from providers.clinical_assessments import score_gad7, score_phq9, validate_responses
        is_valid, error = validate_responses(assessment_type, responses)
        if not is_valid:
            return jsonify({"error": error}), 400

        # 2. Score
        if assessment_type == "phq9":
            result = score_phq9(responses)
        elif assessment_type == "gad7":
            result = score_gad7(responses)
        else:
             return jsonify({"error": f"Unknown assessment type: {assessment_type}"}), 400

        # 3. Save using Provider (ORM enabled)
        from providers.clinical_assessments import save_assessment_result
        new_id = save_assessment_result(session_id, result)

        # AUTO-COMPLETE QUEST (Gamification Hook)
        try:
            from providers.quest_engine import QuestEngine
            QuestEngine.complete_quest_for_assessment(session_id, assessment_type)
        except Exception as qe:
            current_app.logger.error(f"Failed to auto-complete quest: {qe}")

        result["id"] = new_id

        # 4. Trigger Alert if High Severity (Crisis Watchdog Integration)
        severity = result.get("severity", "minimal")
        requires_follow_up = result.get("requires_follow_up", False)

        risk_level = "low"
        risk_score = 0.0
        should_alert = False
        trigger_reason = f"Clinical Assessment: {assessment_type.upper()} Result"

        if assessment_type == "phq9":
            if requires_follow_up:
                risk_level = "crisis"
                risk_score = 1.0
                should_alert = True
                trigger_reason += " - Suicide Ideation Detected (Q9)"
            elif severity in ["severe", "moderately_severe"]:
                risk_level = "high"
                risk_score = 0.8
                should_alert = True
                trigger_reason += f" - {severity.replace('_', ' ').title()}"

        elif assessment_type == "gad7":
            if severity == "severe":
                risk_level = "high"
                risk_score = 0.7
                should_alert = True
                trigger_reason += " - Severe Anxiety"

        alert_dispatched = False
        if should_alert:
            try:
                from app_alert_routes import AlertManager
                alert_id = AlertManager.create_alert(
                    session_id=session_id,
                    trigger_message=f"{trigger_reason}. Score: {result.get('total_score')}.",
                    risk_level=risk_level,
                    risk_score=risk_score,
                    keywords=[assessment_type.upper(), severity, "clinical_assessment"]
                )
                if alert_id:
                    AlertManager.send_alert(alert_id)
                    current_app.logger.info(f"🚨 Clinical Alert Triggered: {alert_id} for session {session_id}")
                    alert_dispatched = True
            except Exception as alert_err:
                current_app.logger.exception(
                    "alert_dispatch_failed assessment_id=%s err=%s",
                    new_id, alert_err,
                )

        if should_alert:
            result["alert_dispatched"] = alert_dispatched

        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error submitting assessment: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@assessment_bp.route("/api/assessment/history", methods=["GET"])
def get_assessment_history_route():
    """Get assessment history for the user"""
    try:
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            return jsonify({"error": "Session ID required"}), 401
        from providers.clinical_assessments import get_assessment_history
        history = get_assessment_history(session_id)
        return jsonify({"history": history})
    except Exception as e:
        current_app.logger.error(f"Error fetching history: {e}")
        return jsonify({"error": "Internal server error"}), 500
