"""
Counselor Alert API Routes for GentleQuest
Add these routes to app.py in _register_routes() function
"""

from flask import request, jsonify, current_app
from datetime import datetime
from models import db
from sqlalchemy import text
from providers.alert_manager import AlertManager


def register_alert_routes(app):
    """Register alert-related API routes"""
    
    @app.route("/api/alerts/history", methods=["GET"])
    def get_alert_history():
        """Get all alerts for a university (CAPS dashboard)"""
        # TODO: Add counselor authentication
        
        try:
            university_id = request.args.get('university_id', 1, type=int)
            status = request.args.get('status')  # 'acknowledged', 'pending'
            severity = request.args.get('severity')  # 'low', 'medium', 'high', 'critical'
            
            where_clauses = ["university_id = :university_id"]
            params = {"university_id": university_id}
            
            if status == 'pending':
                where_clauses.append("acknowledged_at IS NULL")
            elif status == 'acknowledged':
                where_clauses.append("acknowledged_at IS NOT NULL")
            
            if severity:
                where_clauses.append("severity = :severity")
                params['severity'] = severity
            
            where_sql = " AND ".join(where_clauses)
            
            alerts = db.session.execute(
                text(f"""
                    SELECT id, session_id, severity, trigger_message, sent_at, 
                           acknowledged_at, acknowledged_by, email_sent, sms_sent
                    FROM counselor_alerts
                    WHERE {where_sql}
                    ORDER BY sent_at DESC
                    LIMIT 100
                """),
                params
            ).fetchall()
            
            def format_date(dt):
                if not dt: return None
                if isinstance(dt, str): return dt
                return dt.isoformat()

            alert_list = []
            for a in alerts:
                alert_list.append({
                    'id': a[0],
                    'session_id': a[1],
                    'severity': a[2],
                    'trigger_message': a[3],
                    'sent_at': format_date(a[4]),
                    'acknowledged_at': format_date(a[5]),
                    'acknowledged_by': a[6],
                    'email_sent': a[7],
                    'sms_sent': a[8]
                })
            
            return jsonify({
                "alerts": alert_list,
                "count": len(alert_list)
            })
            
        except Exception as e:
            current_app.logger.error(f"Error fetching alert history: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/alerts/<int:alert_id>", methods=["GET"])
    def get_alert_detail(alert_id):
        """Get full alert details including conversation"""
        # TODO: Add counselor authentication
        
        try:
            # Get alert
            alert = db.session.execute(
                text("""
                    SELECT id, session_id, severity, trigger_message, conversation_excerpt,
                           risk_keywords, sent_at, acknowledged_at, acknowledged_by
                    FROM counselor_alerts
                    WHERE id = :id
                """),
                {"id": alert_id}
            ).fetchone()
            
            if not alert:
                return jsonify({"error": "Alert not found"}), 404
            
            # Get full conversation
            messages = db.session.execute(
                text("""
                    SELECT content, is_user, timestamp
                    FROM messages
                    WHERE session_id = :session_id
                    ORDER BY timestamp ASC
                """),
                {"session_id": alert[1]}
            ).fetchall()
            
            # Get acknowledgments
            acks = db.session.execute(
                text("""
                    SELECT counselor_id, response_notes, action_taken, responded_at
                    FROM alert_acknowledgments
                    WHERE alert_id = :alert_id
                    ORDER BY responded_at DESC
                """),
                {"alert_id": alert_id}
            ).fetchall()
            
            def format_date(dt):
                if not dt: return None
                if isinstance(dt, str): return dt
                return dt.isoformat()

            return jsonify({
                "alert": {
                    'id': alert[0],
                    'session_id': alert[1],
                    'severity': alert[2],
                    'trigger_message': alert[3],
                    'conversation_excerpt': alert[4],
                    'risk_keywords': alert[5],
                    'sent_at': format_date(alert[6]),
                    'acknowledged_at': format_date(alert[7]),
                    'acknowledged_by': alert[8]
                },
                "conversation": [
                    {
                        "role": "student" if m[1] else "luna",
                        "content": m[0],
                        "timestamp": format_date(m[2])
                    }
                    for m in messages
                ],
                "acknowledgments": [
                    {
                        "counselor_id": ack[0],
                        "notes": ack[1],
                        "action": ack[2],
                        "timestamp": format_date(ack[3])
                    }
                    for ack in acks
                ]
            })
            
        except Exception as e:
            current_app.logger.error(f"Error fetching alert detail: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/alerts/<int:alert_id>/acknowledge", methods=["POST"])
    def acknowledge_alert(alert_id):
        """Mark alert as acknowledged by counselor"""
        # TODO: Add counselor authentication
        
        try:
            data = request.get_json()
            counselor_id = data.get('counselor_id')
            response_notes = data.get('response_notes', '')
            action_taken = data.get('action_taken', '')
            
            if not counselor_id:
                return jsonify({"error": "Counselor ID required"}), 400
            
            # Verify alert exists
            alert = db.session.execute(
                text("SELECT id FROM counselor_alerts WHERE id = :id"),
                {"id": alert_id}
            ).fetchone()
            
            if not alert:
                return jsonify({"error": "Alert not found"}), 404
            
            # Update alert
            db.session.execute(
                text("""
                    UPDATE counselor_alerts 
                    SET acknowledged_at = CURRENT_TIMESTAMP, acknowledged_by = :counselor_id
                    WHERE id = :id
                """),
                {"id": alert_id, "counselor_id": counselor_id}
            )
            
            # Create acknowledgment record
            db.session.execute(
                text("""
                    INSERT INTO alert_acknowledgments (alert_id, counselor_id, response_notes, action_taken)
                    VALUES (:alert_id, :counselor_id, :notes, :action)
                """),
                {
                    "alert_id": alert_id,
                    "counselor_id": counselor_id,
                    "notes": response_notes,
                    "action": action_taken
                }
            )
            
            db.session.commit()
            
            return jsonify({"success": True})
            
        except Exception as e:
            current_app.logger.error(f"Error acknowledging alert: {e}")
            db.session.rollback()
            return jsonify({"error": "Internal server error"}), 500
