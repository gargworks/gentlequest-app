"""Verify all features are working"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def verify_features():
    app = create_app()
    
    print("✅ FEATURE VERIFICATION")
    print("=" * 80)
    
    with app.app_context():
        features = {
            "Sessions table": "SELECT COUNT(*) FROM sessions",
            "Messages table": "SELECT COUNT(*) FROM messages",
            "Mood entries": "SELECT COUNT(*) FROM mood_entries",
            "Assessments": "SELECT COUNT(*) FROM clinical_assessments",
            "Quests": "SELECT COUNT(*) FROM quests",
            "Resources": "SELECT COUNT(*) FROM resources",
            "Counselor alerts": "SELECT COUNT(*) FROM counselor_alerts",
            "User profiles": "SELECT COUNT(*) FROM user_profiles",
        }
        
        for feature, query in features.items():
            try:
                count = db.session.execute(text(query)).scalar()
                print(f"✅ {feature:25s} {count:>6d} records")
            except Exception as e:
                print(f"❌ {feature:25s} Error: {str(e)[:50]}")
        
        print()
        print("=" * 80)

if __name__ == '__main__':
    verify_features()
