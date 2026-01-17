"""Export pilot data for analysis"""
import sys
import os
import csv
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def export_pilot_data(university_id, output_file):
    app = create_app()
    
    with app.app_context():
        # Get all sessions for university
        sessions = db.session.execute(
            text("SELECT id, created_at FROM sessions WHERE university_id = :uid"),
            {'uid': university_id}
        ).fetchall()
        
        data = []
        for session_id, created_at in sessions:
            # Message count
            msg_count = db.session.execute(
                text("SELECT COUNT(*) FROM messages WHERE session_id = :sid"),
                {'sid': session_id}
            ).scalar()
            
            # Mood entries
            mood_count = db.session.execute(
                text("SELECT COUNT(*) FROM mood_entries WHERE session_id = :sid"),
                {'sid': session_id}
            ).scalar()
            
            # Assessments
            phq9_scores = db.session.execute(
                text("""
                    SELECT total_score FROM clinical_assessments
                    WHERE session_id = :sid AND assessment_type = 'phq9'
                    ORDER BY timestamp
                """),
                {'sid': session_id}
            ).fetchall()
            
            # Quest completion
            quests_completed = db.session.execute(
                text("""
                    SELECT COUNT(*) FROM quest_progress
                    WHERE session_id = :sid AND status = 'completed'
                """),
                {'sid': session_id}
            ).scalar()
            
            data.append({
                'session_id': session_id,
                'created_at': created_at,
                'messages': msg_count,
                'mood_entries': mood_count,
                'phq9_baseline': phq9_scores[0][0] if phq9_scores else None,
                'phq9_final': phq9_scores[-1][0] if len(phq9_scores) > 1 else None,
                'quests_completed': quests_completed
            })
        
        # Write CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        print(f"✅ Exported {len(data)} student records to {output_file}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python scripts/export_pilot_data.py <university_id> <output_file>")
        sys.exit(1)
    
    export_pilot_data(int(sys.argv[1]), sys.argv[2])
