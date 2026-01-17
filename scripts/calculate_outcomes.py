"""Calculate pilot outcomes (symptom reduction, engagement)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def calculate_outcomes(university_id):
    app = create_app()
    
    with app.app_context():
        print(f"📊 PILOT OUTCOMES - University {university_id}")
        print("=" * 80)
        
        # Total signups
        total = db.session.execute(
            text("SELECT COUNT(*) FROM sessions WHERE university_id = :uid"),
            {'uid': university_id}
        ).scalar()
        
        # Weekly active users
        wau = db.session.execute(text("""
            SELECT COUNT(DISTINCT session_id) FROM messages
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
        """)).scalar() or 0
        
        # PHQ-9 reduction
        phq9_data = db.session.execute(text("""
            WITH first_last AS (
                SELECT 
                    session_id,
                    FIRST_VALUE(total_score) OVER (PARTITION BY session_id ORDER BY timestamp) as baseline,
                    LAST_VALUE(total_score) OVER (PARTITION BY session_id ORDER BY timestamp 
                        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as final
                FROM clinical_assessments
                WHERE assessment_type = 'phq9'
            )
            SELECT AVG((baseline - final) * 100.0 / NULLIF(baseline, 0))
            FROM first_last
            WHERE baseline > 0 AND final IS NOT NULL
        """)).scalar() or 0
        
        # GAD-7 reduction
        gad7_data = db.session.execute(text("""
            WITH first_last AS (
                SELECT 
                    session_id,
                    FIRST_VALUE(total_score) OVER (PARTITION BY session_id ORDER BY timestamp) as baseline,
                    LAST_VALUE(total_score) OVER (PARTITION BY session_id ORDER BY timestamp 
                        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as final
                FROM clinical_assessments
                WHERE assessment_type = 'gad7'
            )
            SELECT AVG((baseline - final) * 100.0 / NULLIF(baseline, 0))
            FROM first_last
            WHERE baseline > 0 AND final IS NOT NULL
        """)).scalar() or 0
        
        # Crisis events
        crisis_count = db.session.execute(text("""
            SELECT COUNT(*) FROM counselor_alerts WHERE university_id = :uid
        """), {'uid': university_id}).scalar() or 0
        
        print(f"Total Students: {total}")
        print(f"Weekly Active: {wau} ({wau/total*100:.1f}%)" if total > 0 else "Weekly Active: 0")
        print(f"PHQ-9 Reduction: {phq9_data:.1f}%")
        print(f"GAD-7 Reduction: {gad7_data:.1f}%")
        print(f"Crisis Events: {crisis_count}")
        print()
        
        # Assessment
        if wau/total >= 0.40 if total > 0 else False:
            print("✅ Engagement target met (40%+)")
        else:
            print("⚠️  Engagement below target (<40%)")
        
        if phq9_data >= 20 or gad7_data >= 20:
            print("✅ Outcome target met (20%+ reduction)")
        else:
            print("⚠️  Outcomes below target (<20%)")
        
        print()
        print("=" * 80)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/calculate_outcomes.py <university_id>")
        sys.exit(1)
    
    calculate_outcomes(int(sys.argv[1]))
