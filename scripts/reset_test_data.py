"""Reset test data for clean validation"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def reset_test_data():
    app = create_app()
    
    print("🔄 RESETTING TEST DATA")
    print("=" * 80)
    
    with app.app_context():
        # Delete test sessions
        deleted_sessions = db.session.execute(text("""
            DELETE FROM sessions WHERE id LIKE 'test%' OR id LIKE 'validation%'
            RETURNING id
        """)).rowcount
        
        # Delete test messages
        deleted_messages = db.session.execute(text("""
            DELETE FROM messages WHERE session_id LIKE 'test%' OR session_id LIKE 'validation%'
            RETURNING id
        """)).rowcount
        
        db.session.commit()
        
        print(f"Deleted:")
        print(f"  Sessions: {deleted_sessions}")
        print(f"  Messages: {deleted_messages}")
        print()
        print("✅ Test data reset complete")

if __name__ == '__main__':
    reset_test_data()
