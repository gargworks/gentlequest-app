
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models but need to init db with OUR app, not the one in models.py if possible?
# Actually models.py does `db = SQLAlchemy()`. We can import that instance and init it.
from models import db, Quest, QuestProgress
from providers.quest_generator import QuestGenerator

def reseed_standalone():
    # 1. Setup Minimal App
    app = Flask(__name__)
    
    # Get DB URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'instance', 'mental_health.db')
        db_url = f"sqlite:///{db_path}"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize DB (bind to this app)
    db.init_app(app)
    
    print(f"🔄 Starting Connect to {db_url}...")
    
    with app.app_context():
        week, year = QuestGenerator.get_week_number()
        print(f"Targeting Week {week}, Year {year}")
        
        # 1. Check existing quests
        try:
            existing_count = Quest.query.filter_by(week_number=week, year=year).count()
            print(f"Found {existing_count} existing quests.")
            
            if existing_count > 0:
                quest_ids = [q.id for q in Quest.query.filter_by(week_number=week, year=year).all()]
                
                if quest_ids:
                    print(f"Deleting progress for {len(quest_ids)} quests...")
                    try:
                        QuestProgress.query.filter(QuestProgress.quest_id.in_(quest_ids)).delete(synchronize_session=False)
                        db.session.commit()
                    except Exception as e:
                        print(f"Warning clearing progress: {e}")
                        db.session.rollback()
                
                print("Deleting quests...")
                Quest.query.filter_by(week_number=week, year=year).delete()
                db.session.commit()
                print("✅ Old quests deleted.")
                
            # 2. Generate New Quests
            print("Generating new quests (with targets)...")
            new_quests = QuestGenerator.generate_weekly_quests(week, year)
            
            print(f"✅ Generated {len(new_quests)} new quests.")
            for q in new_quests:
                print(f" - [{q['type']}] {q['title']} (Target: {q.get('target', 'N/A')})")
                
        except Exception as e:
            print(f"❌ Error during reseed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    reseed_standalone()
