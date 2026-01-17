"""Test database connection and basic queries"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def test_connection():
    app = create_app()
    
    print("🔌 DATABASE CONNECTION TEST")
    print("=" * 80)
    
    with app.app_context():
        try:
            # Test connection
            result = db.session.execute(text("SELECT 1")).scalar()
            print("✅ Connection successful")
            
            # Test tables exist
            tables = db.session.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)).fetchall()
            
            print(f"\nTables ({len(tables)}):")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Test data exists
            print("\nData Counts:")
            for table_name in ['sessions', 'messages', 'quests', 'resources']:
                try:
                    count = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                    print(f"  {table_name:20s} {count:>8d} rows")
                except:
                    print(f"  {table_name:20s} (table not found)")
            
            print()
            print("=" * 80)
            print("✅ Database is healthy")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    
    return True

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
