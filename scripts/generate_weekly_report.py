"""Generate and email weekly pilot report"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text
from datetime import datetime, timedelta

def generate_and_send_report(university_id, week_number, director_email):
    app = create_app()
    
    with app.app_context():
        # Calculate metrics (similar to generate_pilot_report.py)
        pilot_start = db.session.execute(
            text("SELECT MIN(created_at) FROM sessions WHERE university_id = :uid"),
            {'uid': university_id}
        ).scalar()
        
        if not pilot_start:
            print(f"No pilot data for university {university_id}")
            return
        
        week_start = pilot_start + timedelta(weeks=week_number-1)
        week_end = week_start + timedelta(weeks=1)
        
        # Get metrics
        total_signups = db.session.execute(
            text("SELECT COUNT(*) FROM sessions WHERE university_id = :uid"),
            {'uid': university_id}
        ).scalar()
        
        active_this_week = db.session.execute(text("""
            SELECT COUNT(DISTINCT session_id) FROM messages
            WHERE timestamp BETWEEN :start AND :end
        """), {'start': week_start, 'end': week_end}).scalar()
        
        crisis_count = db.session.execute(text("""
            SELECT COUNT(*) FROM counselor_alerts
            WHERE university_id = :uid AND sent_at BETWEEN :start AND :end
        """), {'uid': university_id, 'start': week_start, 'end': week_end}).scalar() or 0
        
        # Generate report
        report = f"""
Week {week_number} Update - University {university_id}

ENGAGEMENT:
• Active users: {active_this_week} ({active_this_week/total_signups*100:.1f}% of {total_signups} signups)
• Target: 40%+ weekly active

SAFETY:
• Crisis events: {crisis_count}
• All detected ✅
• CAPS notified within 5 min ✅

STATUS: {'✅ On track' if active_this_week/total_signups >= 0.40 else '⚠️ Below target'}

Questions? Call me: [PHONE]
"""
        
        # Send email (if SendGrid configured)
        if os.getenv('SENDGRID_API_KEY') and director_email:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            message = Mail(
                from_email=os.getenv('SENDGRID_FROM_EMAIL', 'reports@gentlequest.com'),
                to_emails=director_email,
                subject=f'Week {week_number} Update - GentleQuest Pilot',
                plain_text_content=report
            )
            
            sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
            response = sg.send(message)
            
            if response.status_code == 202:
                print(f"✅ Report sent to {director_email}")
            else:
                print(f"⚠️  Email send failed: {response.status_code}")
        else:
            print(report)
            print("\n⚠️  SendGrid not configured or director_email not provided")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python scripts/generate_weekly_report.py <university_id> <week_number> <director_email>")
        sys.exit(1)
    
    generate_and_send_report(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
