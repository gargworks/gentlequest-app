"""Test crisis alert delivery end-to-end"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text
from providers.alert_manager import AlertManager

def test_alert_delivery():
    app = create_app()
    
    with app.app_context():
        print("🚨 CRISIS ALERT DELIVERY TEST")
        print("=" * 80)
        
        # Create test session
        db.session.execute(text("INSERT INTO sessions (id) VALUES ('test_crisis') ON CONFLICT DO NOTHING"))
        db.session.commit()
        
        # Create test alert
        print("Creating test alert...")
        alert_id = AlertManager.create_alert(
            session_id='test_crisis',
            trigger_message='TEST: I want to kill myself (this is a test)',
            risk_level='critical',
            risk_score=0.95,
            keywords=['kill', 'myself', 'TEST'],
            university_id=1
        )
        
        if alert_id:
            print(f"✅ Alert created (ID: {alert_id})")
            
            # Send alert
            print("Sending alert to counselors...")
            results = AlertManager.send_alert(alert_id)
            
            print(f"  Email sent: {results['email']}")
            print(f"  SMS sent: {results['sms']}")
            
            if results['email']:
                print("✅ Email delivery successful")
            else:
                print("⚠️  Email delivery failed (check SendGrid configuration)")
            
            if results['sms']:
                print("✅ SMS delivery successful")
            else:
                print("ℹ️  SMS not sent (CRITICAL only or Twilio not configured)")
        else:
            print("⚠️  Alert not created (rate limited or low severity)")
        
        print()
        print("=" * 80)
        print("Test complete. Check counselor email/SMS for test alert.")
        print()
        print("⚠️  IMPORTANT: This was a TEST alert. Notify counselors it's not real.")

if __name__ == '__main__':
    test_alert_delivery()
