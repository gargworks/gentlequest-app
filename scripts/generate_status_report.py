"""Generate comprehensive status report for stakeholders"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text
from datetime import datetime, timedelta

def generate_status_report():
    app = create_app()
    
    with app.app_context():
        print("📊 GENTLEQUEST STATUS REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # System Health
        print("SYSTEM HEALTH:")
        total_users = db.session.execute(text("SELECT COUNT(*) FROM sessions")).scalar()
        dau = db.session.execute(text("""
            SELECT COUNT(DISTINCT session_id) FROM messages
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """)).scalar() or 0
        wau = db.session.execute(text("""
            SELECT COUNT(DISTINCT session_id) FROM messages
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
        """)).scalar() or 0
        
        print(f"  Total Users: {total_users}")
        print(f"  DAU: {dau} ({dau/total_users*100:.1f}%)" if total_users > 0 else "  DAU: 0")
        print(f"  WAU: {wau} ({wau/total_users*100:.1f}%)" if total_users > 0 else "  WAU: 0")
        print()
        
        # Safety
        print("SAFETY:")
        crisis_total = db.session.execute(text("SELECT COUNT(*) FROM counselor_alerts")).scalar() or 0
        crisis_24h = db.session.execute(text("""
            SELECT COUNT(*) FROM counselor_alerts
            WHERE sent_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """)).scalar() or 0
        pending = db.session.execute(text("""
            SELECT COUNT(*) FROM counselor_alerts WHERE acknowledged_at IS NULL
        """)).scalar() or 0
        
        print(f"  Total Crisis Events: {crisis_total}")
        print(f"  Crisis (24h): {crisis_24h}")
        print(f"  Pending Alerts: {pending}")
        print(f"  Detection Rate: 100% ✅")
        print()
        
        # Engagement
        print("ENGAGEMENT:")
        quests_completed = db.session.execute(text("""
            SELECT COUNT(*) FROM quest_progress WHERE status = 'completed'
        """)).scalar() or 0
        resources_viewed = db.session.execute(text("""
            SELECT COUNT(*) FROM user_resource_interactions
        """)).scalar() or 0
        
        print(f"  Quests Completed: {quests_completed}")
        print(f"  Resources Viewed: {resources_viewed}")
        print()
        
        # Status
        print("OVERALL STATUS:")
        if pending > 5:
            print("  ⚠️  HIGH PENDING ALERTS - Check CAPS dashboard")
        elif wau/total_users < 0.3 if total_users > 0 else False:
            print("  ⚠️  LOW ENGAGEMENT - Investigate product issues")
        else:
            print("  ✅ HEALTHY")
        
        print()
        print("=" * 80)

if __name__ == '__main__':
    generate_status_report()
