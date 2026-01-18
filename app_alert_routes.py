"""
Counselor Alert API Routes for GentleQuest
Add these routes to app.py in _register_routes() function
"""

from flask import request, jsonify, current_app
from datetime import datetime
from models import db, CounselorAlert, AlertAcknowledgment, Message
from sqlalchemy import text


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
            
            query = CounselorAlert.query.filter_by(university_id=university_id)
            
            if status == 'pending':
                query = query.filter(CounselorAlert.acknowledged_at == None)
            elif status == 'acknowledged':
                query = query.filter(CounselorAlert.acknowledged_at != None)
            
            if severity:
                query = query.filter(CounselorAlert.severity == severity)
            
            alerts = query.order_by(CounselorAlert.sent_at.desc()).limit(100).all()
            
            def format_date(dt):
                if not dt: return None
                return dt.isoformat()

            alert_list = []
            for a in alerts:
                alert_list.append({
                    'id': a.id,
                    'session_id': a.session_id,
                    'severity': a.severity,
                    'trigger_message': a.trigger_message,
                    'sent_at': format_date(a.sent_at),
                    'acknowledged_at': format_date(a.acknowledged_at),
                    'acknowledged_by': a.acknowledged_by,
                    'email_sent': a.email_sent,
                    'sms_sent': a.sms_sent
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
            alert = CounselorAlert.query.get(alert_id)
            if not alert:
                return jsonify({"error": "Alert not found"}), 404
            
            # Get full conversation for that session
            messages = Message.query.filter_by(session_id=alert.session_id).order_by(Message.timestamp.asc()).all()
            
            # Get acknowledgments
            acks = AlertAcknowledgment.query.filter_by(alert_id=alert_id).order_by(AlertAcknowledgment.responded_at.desc()).all()
            
            def format_date(dt):
                if not dt: return None
                return dt.isoformat()

            return jsonify({
                "alert": {
                    'id': alert.id,
                    'session_id': alert.session_id,
                    'severity': alert.severity,
                    'trigger_message': alert.trigger_message,
                    'conversation_excerpt': alert.conversation_excerpt,
                    'risk_keywords': alert.risk_keywords,
                    'sent_at': format_date(alert.sent_at),
                    'acknowledged_at': format_date(alert.acknowledged_at),
                    'acknowledged_by': alert.acknowledged_by
                },
                "conversation": [
                    {
                        "role": "student" if m.is_user else "luna",
                        "content": m.content,
                        "timestamp": format_date(m.timestamp)
                    }
                    for m in messages
                ],
                "acknowledgments": [
                    {
                        "counselor_id": ack.counselor_id,
                        "notes": ack.response_notes,
                        "action": ack.action_taken,
                        "timestamp": format_date(ack.responded_at)
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
            alert = CounselorAlert.query.get(alert_id)
            if not alert:
                return jsonify({"error": "Alert not found"}), 404
            
            # Update alert
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = counselor_id
            
            # Create acknowledgment record
            ack = AlertAcknowledgment(
                alert_id=alert_id,
                counselor_id=counselor_id,
                response_notes=response_notes,
                action_taken=action_taken
            )
            db.session.add(ack)
            db.session.commit()
            
            return jsonify({"success": True})
            
        except Exception as e:
            current_app.logger.error(f"Error acknowledging alert: {e}")
            db.session.rollback()
            return jsonify({"error": "Internal server error"}), 500
