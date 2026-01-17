"""
Monitoring Setup Script
Configures health checks, alerts, and dashboards
Run with: python scripts/monitoring_setup.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text
from datetime import datetime, timedelta

def create_monitoring_views(app):
    """Create database views for monitoring"""
    with app.app_context():
        try:
            # Daily active users view
            db.session.execute(text("""
                CREATE OR REPLACE VIEW v_daily_active_users AS
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(DISTINCT session_id) as dau
                FROM messages
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '30 days'
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """))
            
            # Weekly active users view
            db.session.execute(text("""
                CREATE OR REPLACE VIEW v_weekly_active_users AS
                SELECT 
                    DATE_TRUNC('week', timestamp) as week,
                    COUNT(DISTINCT session_id) as wau
                FROM messages
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '90 days'
                GROUP BY DATE_TRUNC('week', timestamp)
                ORDER BY week DESC
            """))
            
            # Crisis events summary
            db.session.execute(text("""
                CREATE OR REPLACE VIEW v_crisis_events_summary AS
                SELECT 
                    DATE(sent_at) as date,
                    severity,
                    COUNT(*) as count,
                    SUM(CASE WHEN acknowledged_at IS NULL THEN 1 ELSE 0 END) as pending,
                    AVG(EXTRACT(EPOCH FROM (acknowledged_at - sent_at))/60) as avg_response_minutes
                FROM counselor_alerts
                WHERE sent_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
                GROUP BY DATE(sent_at), severity
                ORDER BY date DESC, severity
            """))
            
            # Quest completion rates
            db.session.execute(text("""
                CREATE OR REPLACE VIEW v_quest_completion_rates AS
                SELECT 
                    q.quest_type,
                    COUNT(*) as total_assigned,
                    SUM(CASE WHEN qp.status = 'completed' THEN 1 ELSE 0 END) as completed,
                    ROUND(100.0 * SUM(CASE WHEN qp.status = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 2) as completion_rate
                FROM quests q
                LEFT JOIN quest_progress qp ON q.id = qp.quest_id
                GROUP BY q.quest_type
            """))
            
            db.session.commit()
            print("✅ Monitoring views created")
            
        except Exception as e:
            print(f"Error creating views: {e}")
            db.session.rollback()

def generate_health_report(app):
    """Generate current health report"""
    with app.app_context():
        try:
            # Total users
            total_users = db.session.execute(
                text("SELECT COUNT(*) FROM sessions")
            ).scalar()
            
            # DAU (last 24 hours)
            dau = db.session.execute(text("""
                SELECT COUNT(DISTINCT session_id)
                FROM messages
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            """)).scalar()
            
            # WAU (last 7 days)
            wau = db.session.execute(text("""
                SELECT COUNT(DISTINCT session_id)
                FROM messages
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
            """)).scalar()
            
            # Crisis events (last 24 hours)
            crisis_count = db.session.execute(text("""
                SELECT COUNT(*)
                FROM counselor_alerts
                WHERE sent_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            """)).scalar() or 0
            
            # Pending alerts
            pending_alerts = db.session.execute(text("""
                SELECT COUNT(*)
                FROM counselor_alerts
                WHERE acknowledged_at IS NULL
            """)).scalar() or 0
            
            print("\n📊 CURRENT HEALTH REPORT:")
            print("=" * 80)
            print(f"  Total Users: {total_users}")
            print(f"  DAU (24h): {dau} ({dau/total_users*100:.1f}%)" if total_users > 0 else "  DAU: 0")
            print(f"  WAU (7d): {wau} ({wau/total_users*100:.1f}%)" if total_users > 0 else "  WAU: 0")
            print(f"  Crisis Events (24h): {crisis_count}")
            print(f"  Pending Alerts: {pending_alerts}")
            
            # Health status
            if pending_alerts > 5:
                print("\n  ⚠️  HIGH PENDING ALERTS - Check CAPS dashboard")
            elif wau/total_users < 0.3 if total_users > 0 else False:
                print("\n  ⚠️  LOW ENGAGEMENT - Investigate product issues")
            else:
                print("\n  ✅ System healthy")
                
        except Exception as e:
            print(f"Error generating health report: {e}")

def main():
    app = create_app()
    
    print("🏥 MONITORING SETUP")
    print("=" * 80)
    print()
    
    create_monitoring_views(app)
    generate_health_report(app)
    
    print("\n" + "=" * 80)
    print("✅ Monitoring setup complete")
    print("\nNext steps:")
    print("  1. Set up Render metrics dashboard")
    print("  2. Configure alert thresholds (error rate >5%, response time >5s)")
    print("  3. Set up daily health check cron job")

if __name__ == '__main__':
    main()
