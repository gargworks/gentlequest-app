"""
Alert Manager for GentleQuest
Manages counselor alerts for crisis events with email/SMS delivery
"""

import os
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy import text
from models import db, CounselorAlert, Message

class AlertSeverity:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertManager:
    """Manage counselor alerts for crisis events"""
    
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL', 'alerts@gentlequest.com')
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    @staticmethod
    def determine_severity(risk_level: str, risk_score: float) -> str:
        """Map crisis detection risk to alert severity"""
        if risk_level == 'crisis' or risk_score >= 0.9:
            return AlertSeverity.CRITICAL
        elif risk_level == 'high' or risk_score >= 0.7:
            return AlertSeverity.HIGH
        elif risk_level == 'medium' or risk_score >= 0.5:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    @staticmethod
    def should_send_alert(severity: str, session_id: str) -> bool:
        """Rate limiting: Don't spam counselors with duplicate alerts"""
        # Don't send LOW severity alerts
        if severity == AlertSeverity.LOW:
            return False
        
        # Check if alert sent in last hour for this session
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_alert = CounselorAlert.query.filter(
            CounselorAlert.session_id == session_id,
            CounselorAlert.sent_at > one_hour_ago
        ).order_by(CounselorAlert.sent_at.desc()).first()
        
        if recent_alert:
            recent_severity = recent_alert.severity
            # Only send if new alert is more severe
            severity_order = {AlertSeverity.LOW: 0, AlertSeverity.MEDIUM: 1, 
                            AlertSeverity.HIGH: 2, AlertSeverity.CRITICAL: 3}
            if severity_order.get(severity, 0) > severity_order.get(recent_severity, 0):
                return True
            return False
        
        return True
    
    @staticmethod
    def get_conversation_excerpt(session_id: str, num_messages: int = 5) -> str:
        """Get last N messages for context"""
        messages = Message.query.filter_by(session_id=session_id)\
            .order_by(Message.timestamp.desc())\
            .limit(num_messages).all()
        
        excerpt = []
        for msg in reversed(messages):
            role = "Student" if msg.is_user else "Luna"
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            excerpt.append(f"{role}: {content}")
        
        return "\\n".join(excerpt)
    
    @staticmethod
    def create_alert(session_id: str, trigger_message: str, risk_level: str, 
                    risk_score: float, keywords: List[str], 
                    university_id: int = None) -> Optional[int]:
        """
        Create alert record in database
        
        Returns alert_id if created, None if rate-limited
        """
        severity = AlertManager.determine_severity(risk_level, risk_score)
        
        if not AlertManager.should_send_alert(severity, session_id):
            return None
        
        alert = CounselorAlert(
            session_id=session_id,
            university_id=university_id or 1,
            severity=severity,
            trigger_message=trigger_message[:500],
            conversation_excerpt=AlertManager.get_conversation_excerpt(session_id),
            risk_keywords=','.join(keywords) if keywords else ''
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return alert.id
    
    @staticmethod
    def send_email_alert(alert_id: int, counselor_email: str, counselor_name: str) -> bool:
        """Send email alert via SendGrid"""
        if not AlertManager.SENDGRID_API_KEY:
            print("SendGrid not configured, skipping email")
            return False
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            # Get alert details
            alert = db.session.execute(
                text("""
                    SELECT session_id, severity, trigger_message, conversation_excerpt, 
                           risk_keywords, sent_at
                    FROM counselor_alerts 
                    WHERE id = :alert_id
                """),
                {"alert_id": alert_id}
            ).fetchone()
            
            if not alert:
                return False
            
            session_id, severity, trigger_msg, excerpt, keywords, sent_at = alert
            
            severity_colors = {
                'critical': '#DC2626',
                'high': '#EA580C',
                'medium': '#F59E0B',
                'low': '#10B981'
            }
            
            color = severity_colors.get(severity, '#6B7280')
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .header {{ background: {color}; color: white; padding: 20px; }}
        .content {{ padding: 20px; }}
        .excerpt {{ background: #F3F4F6; padding: 15px; border-left: 4px solid {color}; margin: 15px 0; }}
        .action {{ background: #EEF2FF; padding: 15px; margin-top: 20px; border-radius: 8px; }}
        .button {{ display: inline-block; background: #4F46E5; color: white; 
                   padding: 12px 24px; text-decoration: none; border-radius: 6px; 
                   margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 Crisis Alert - {severity.upper()} Priority</h1>
    </div>
    
    <div class="content">
        <p><strong>Time:</strong> {sent_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p><strong>Session ID:</strong> {session_id}</p>
        <p><strong>Severity:</strong> {severity.upper()}</p>
        
        <h3>Trigger Message:</h3>
        <p>{trigger_msg}</p>
        
        <h3>Detected Keywords:</h3>
        <p>{keywords}</p>
        
        <h3>Recent Conversation:</h3>
        <div class="excerpt">
            <pre style="white-space: pre-wrap; font-family: Arial;">{excerpt}</pre>
        </div>
        
        <div class="action">
            <h3>Recommended Action:</h3>
            <ul>
                <li>{'<strong>Contact student IMMEDIATELY</strong>' if severity == 'critical' else 'Review and contact student within 24 hours'}</li>
                <li>Review full conversation in CAPS dashboard</li>
                <li>Document response in alert acknowledgment</li>
            </ul>
        </div>
        
        <a href="https://gentlequest.com/caps/alerts/{alert_id}" class="button">
            View Full Alert in Dashboard
        </a>
    </div>
    
    <div style="padding: 20px; background: #F9FAFB; color: #6B7280; font-size: 12px; margin-top: 20px;">
        <p>This is an automated alert from GentleQuest. Do not reply to this email.</p>
        <p>For support, contact support@gentlequest.com</p>
    </div>
</body>
</html>
            """
            
            message = Mail(
                from_email=AlertManager.SENDGRID_FROM_EMAIL,
                to_emails=counselor_email,
                subject=f'[{severity.upper()}] Student Crisis Alert - GentleQuest',
                html_content=html_content
            )
            
            sg = SendGridAPIClient(AlertManager.SENDGRID_API_KEY)
            response = sg.send(message)
            
            # Update alert record
            db.session.execute(
                text("UPDATE counselor_alerts SET email_sent = true WHERE id = :alert_id"),
                {"alert_id": alert_id}
            )
            db.session.commit()
            
            return response.status_code == 202
            
        except Exception as e:
            print(f"Email send failed: {e}")
            return False
    
    @staticmethod
    def send_sms_alert(alert_id: int, counselor_phone: str, severity: str) -> bool:
        """Send SMS via Twilio (CRITICAL only)"""
        if severity != AlertSeverity.CRITICAL:
            return False
        
        if not all([AlertManager.TWILIO_ACCOUNT_SID, AlertManager.TWILIO_AUTH_TOKEN]):
            print("Twilio not configured, skipping SMS")
            return False
        
        try:
            from twilio.rest import Client
            
            # Get alert details
            alert = db.session.execute(
                text("""
                    SELECT session_id, risk_keywords
                    FROM counselor_alerts 
                    WHERE id = :alert_id
                """),
                {"alert_id": alert_id}
            ).fetchone()
            
            if not alert:
                return False
            
            session_id, keywords = alert
            
            body = (f"🚨 CRITICAL ALERT: Student crisis detected.\n"
                   f"Session: {session_id[:8]}...\n"
                   f"Keywords: {keywords}\n"
                   f"Check email for full details.")
            
            client = Client(AlertManager.TWILIO_ACCOUNT_SID, AlertManager.TWILIO_AUTH_TOKEN)
            
            message = client.messages.create(
                body=body,
                from_=AlertManager.TWILIO_PHONE_NUMBER,
                to=counselor_phone
            )
            
            # Update alert record
            db.session.execute(
                text("UPDATE counselor_alerts SET sms_sent = true WHERE id = :alert_id"),
                {"alert_id": alert_id}
            )
            db.session.commit()
            
            return message.sid is not None
            
        except Exception as e:
            print(f"SMS send failed: {e}")
            return False
    
    @staticmethod
    def send_alert(alert_id: int) -> Dict[str, bool]:
        """Send alert to all active counselors for the university"""
        if not alert_id:
            return {'email': False, 'sms': False}
        
        # Get alert details
        alert = db.session.execute(
            text("SELECT university_id, severity FROM counselor_alerts WHERE id = :alert_id"),
            {"alert_id": alert_id}
        ).fetchone()
        
        if not alert:
            return {'email': False, 'sms': False}
        
        university_id, severity = alert
        
        # Get counselors for this university
        counselors = db.session.execute(
            text("""
                SELECT id, name, email, phone, alert_methods
                FROM university_counselors
                WHERE university_id = :university_id
                AND is_active = true
                AND receives_alerts = true
            """),
            {"university_id": university_id}
        ).fetchall()
        
        if not counselors:
            print(f"No counselors configured for university {university_id}")
            return {'email': False, 'sms': False}
        
        results = {'email': False, 'sms': False}
        
        for counselor in counselors:
            counselor_id, name, email, phone, alert_methods = counselor
            
            # Send email
            if 'email' in alert_methods:
                if AlertManager.send_email_alert(alert_id, email, name):
                    results['email'] = True
            
            # Send SMS for critical alerts
            if 'sms' in alert_methods and phone:
                if AlertManager.send_sms_alert(alert_id, phone, severity):
                    results['sms'] = True
        
        return results
