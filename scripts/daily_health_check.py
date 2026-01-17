"""Daily Health Check Script - Run every morning"""
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
        print("🏥 DAILY HEALTH CHECK")
        print("=" * 80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Total users
        total = db.session.execute(text("SELECT COUNT(*) FROM sessions")).scalar()
        
        # DAU
        dau = db.session.execute(text("""
            SELECT COUNT(DISTINCT session_id) FROM messages
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """)).scalar() or 0
        
        # Crisis events
        crisis = db.session.execute(text("""
            SELECT COUNT(*) FROM counselor_alerts
            WHERE sent_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """)).scalar() or 0
        
        # Pending alerts
        pending = db.session.execute(text("""
            SELECT COUNT(*) FROM counselor_alerts
            WHERE acknowledged_at IS NULL
        """)).scalar() or 0
        
        print(f"Users: {total}")
        print(f"DAU: {dau} ({dau/total*100:.1f}%)" if total > 0 else "DAU: 0")
        print(f"Crisis (24h): {crisis}")
        print(f"Pending Alerts: {pending}")
        print()
        
        # Health status
        if pending > 5:
            print("⚠️  HIGH PENDING ALERTS")
        elif dau/total < 0.3 if total > 0 else False:
            print("⚠️  LOW ENGAGEMENT")
        else:
            print("✅ HEALTHY")

if __name__ == '__main__':
    main()
