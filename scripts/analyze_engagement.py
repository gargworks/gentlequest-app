"""Analyze user engagement patterns"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def analyze_engagement(university_id=None):
    app = create_app()
    
    with app.app_context():
        print("📈 ENGAGEMENT ANALYSIS")
        print("=" * 80)
        
        where_clause = f"WHERE university_id = {university_id}" if university_id else ""
        
        # Cohort retention
        cohorts = db.session.execute(text(f"""
            SELECT 
                DATE_TRUNC('week', created_at) as cohort_week,
                COUNT(*) as cohort_size,
                COUNT(CASE WHEN last_activity > created_at + INTERVAL '7 days' THEN 1 END) * 100.0 / COUNT(*) as week1_retention,
                COUNT(CASE WHEN last_activity > created_at + INTERVAL '28 days' THEN 1 END) * 100.0 / COUNT(*) as week4_retention
            FROM sessions
            {where_clause}
            GROUP BY DATE_TRUNC('week', created_at)
            ORDER BY cohort_week DESC
            LIMIT 12
        """)).fetchall()
        
        print("COHORT RETENTION:")
        print(f"{'Week':<12} {'Size':<8} {'Week 1':<10} {'Week 4':<10}")
        print("-" * 40)
        for cohort in cohorts:
            week, size, w1, w4 = cohort
            print(f"{str(week)[:10]:<12} {size:<8} {w1:.1f}%{' ✅' if w1 >= 60 else ' ⚠️':<8} {w4:.1f}%{' ✅' if w4 >= 40 else ' ⚠️':<8}")
        
        # Feature usage
        print("\nFEATURE USAGE:")
        features = db.session.execute(text(f"""
            SELECT 
                'Chat' as feature,
                COUNT(DISTINCT session_id) as users,
                COUNT(*) as total_uses
            FROM messages
            {where_clause.replace('university_id', 'session_id IN (SELECT id FROM sessions WHERE university_id')}
            UNION ALL
            SELECT 
                'Mood' as feature,
                COUNT(DISTINCT session_id),
                COUNT(*)
            FROM mood_entries
            UNION ALL
            SELECT 
                'Quests' as feature,
                COUNT(DISTINCT session_id),
                COUNT(*)
            FROM quest_progress
            WHERE status = 'completed'
        """)).fetchall()
        
        for feature, users, uses in features:
            print(f"  {feature:<10} {users:>6} users, {uses:>8} total uses")

if __name__ == '__main__':
    university_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    analyze_engagement(university_id)
