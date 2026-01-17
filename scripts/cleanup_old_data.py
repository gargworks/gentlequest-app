"""Cleanup old data per retention policy"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text
from datetime import datetime, timedelta

def main():
    app = create_app()
    
    with app.app_context():
        print("🧹 DATA CLEANUP")
        print("=" * 80)
        
        # Messages (30 days)
        cutoff_messages = datetime.utcnow() - timedelta(days=30)
        deleted_messages = db.session.execute(
            text("DELETE FROM messages WHERE timestamp < :cutoff RETURNING id"),
            {'cutoff': cutoff_messages}
        ).rowcount
        
        # Sessions (14 days inactive)
        cutoff_sessions = datetime.utcnow() - timedelta(days=14)
        deleted_sessions = db.session.execute(
            text("DELETE FROM sessions WHERE last_activity < :cutoff RETURNING id"),
            {'cutoff': cutoff_sessions}
        ).rowcount
        
        # Analytics (90 days)
        cutoff_analytics = datetime.utcnow() - timedelta(days=90)
        deleted_analytics = db.session.execute(
            text("DELETE FROM analytics_events WHERE timestamp < :cutoff RETURNING id"),
            {'cutoff': cutoff_analytics}
        ).rowcount
        
        # Alerts (90 days)
        cutoff_alerts = datetime.utcnow() - timedelta(days=90)
        deleted_alerts = db.session.execute(
            text("DELETE FROM counselor_alerts WHERE sent_at < :cutoff RETURNING id"),
            {'cutoff': cutoff_alerts}
        ).rowcount
        
        db.session.commit()
        
        print(f"Deleted:")
        print(f"  Messages: {deleted_messages}")
        print(f"  Sessions: {deleted_sessions}")
        print(f"  Analytics: {deleted_analytics}")
        print(f"  Alerts: {deleted_alerts}")
        print()
        print("✅ Cleanup complete")

if __name__ == '__main__':
    main()
