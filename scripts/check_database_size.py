"""Check database size and growth trends"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def check_database_size():
    app = create_app()
    
    with app.app_context():
        print("💾 DATABASE SIZE ANALYSIS")
        print("=" * 80)
        
        # Total database size
        total_size = db.session.execute(text("""
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """)).scalar()
        print(f"Total Database Size: {total_size}")
        print()
        
        # Table sizes
        print("TABLE SIZES:")
        tables = db.session.execute(text("""
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size('public.'||tablename)) as size,
                pg_total_relation_size('public.'||tablename) as size_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size('public.'||tablename) DESC
            LIMIT 20
        """)).fetchall()
        
        for table, size, size_bytes in tables:
            print(f"  {table:30s} {size:>15s}")
        
        print()
        print("=" * 80)

if __name__ == '__main__':
    check_database_size()
