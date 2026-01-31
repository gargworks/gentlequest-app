
import os
import sys

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Quest, QuestProgress
from providers.quest_generator import QuestGenerator
from sqlalchemy import text

def reseed_quests():
    print("🔄 Starting Quest Reseed...")
    
    with app.app_context():
        week, year = QuestGenerator.get_week_number()
        print(f"Targeting Week {week}, Year {year}")
        
        # 1. Check existing quests
        existing_count = Quest.query.filter_by(week_number=week, year=year).count()
        print(f"Found {existing_count} existing quests.")
        
        if existing_count > 0:
            # 2. Delete existing quests (and cascade progress if FK allows, manual otherwise)
            # Check QuestProgress first
            # We will wipe progress for this week's quests to be safe/clean for the update
            # Get IDs
            quest_ids = [q.id for q in Quest.query.filter_by(week_number=week, year=year).all()]
            
            if quest_ids:
                print(f"Deleting progress for {len(quest_ids)} quests...")
                try:
                    # In SQLite, IN clause might vary, using loop/delete query
                    QuestProgress.query.filter(QuestProgress.quest_id.in_(quest_ids)).delete(synchronize_session=False)
                    db.session.commit()
                except Exception as e:
                    print(f"Warning clearing progress: {e}")
                    db.session.rollback()
            
            print("Deleting quests...")
            Quest.query.filter_by(week_number=week, year=year).delete()
            db.session.commit()
            print("✅ Old quests deleted.")
            
        # 3. Generate New Quests
        print("Generating new quests (with targets)...")
        new_quests = QuestGenerator.generate_weekly_quests(week, year)
        
        print(f"✅ Generated {len(new_quests)} new quests.")
        for q in new_quests:
            print(f" - [{q['type']}] {q['title']} (Target: {q.get('target', 'N/A')})")

if __name__ == "__main__":
    reseed_quests()
