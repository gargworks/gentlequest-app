"""Generate sample data for demo/testing"""
import sys
import os
import random
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def generate_sample_data(num_users=10):
    app = create_app()
    
    print(f"🎲 GENERATING SAMPLE DATA ({num_users} users)")
    print("=" * 80)
    
    with app.app_context():
        for i in range(num_users):
            session_id = f"demo_user_{i+1}"
            
            # Create session
            db.session.execute(text("""
                INSERT INTO sessions (id, created_at, last_activity)
                VALUES (:sid, CURRENT_TIMESTAMP - INTERVAL '7 days', CURRENT_TIMESTAMP)
                ON CONFLICT DO NOTHING
            """), {'sid': session_id})
            
            # Create messages (5-15 per user)
            num_messages = random.randint(5, 15)
            for j in range(num_messages):
                is_user = j % 2 == 0
                content = f"Sample message {j+1}" if is_user else f"Sample response {j+1}"
                
                db.session.execute(text("""
                    INSERT INTO messages (session_id, content, is_user, timestamp)
                    VALUES (:sid, :content, :is_user, CURRENT_TIMESTAMP - INTERVAL ':days days')
                """), {'sid': session_id, 'content': content, 'is_user': is_user, 'days': 7-j})
            
            # Create mood entries (3-7 per user)
            num_moods = random.randint(3, 7)
            for j in range(num_moods):
                mood_level = random.randint(2, 4)
                db.session.execute(text("""
                    INSERT INTO mood_entries (session_id, mood_level, timestamp)
                    VALUES (:sid, :mood, CURRENT_TIMESTAMP - INTERVAL ':days days')
                """), {'sid': session_id, 'mood': mood_level, 'days': 7-j})
        
        db.session.commit()
        print(f"✅ Generated data for {num_users} demo users")

if __name__ == '__main__':
    num_users = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    generate_sample_data(num_users)
