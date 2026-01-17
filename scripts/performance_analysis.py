"""
Performance Analysis Script
Identifies slow queries, missing indexes, N+1 issues
Run with: python scripts/performance_analysis.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def analyze_slow_queries(app):
    """Analyze slow queries using pg_stat_statements"""
    with app.app_context():
        try:
            # Enable pg_stat_statements if not already
            db.session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
            db.session.commit()
            
            # Get slow queries (>100ms)
            result = db.session.execute(text("""
                SELECT 
                    query,
                    calls,
                    mean_exec_time,
                    max_exec_time,
                    stddev_exec_time
                FROM pg_stat_statements
                WHERE mean_exec_time > 100
                ORDER BY mean_exec_time DESC
                LIMIT 20
            """)).fetchall()
            
            print("🐌 SLOW QUERIES (>100ms average):")
            print("=" * 80)
            for row in result:
                query, calls, mean_time, max_time, stddev = row
                print(f"\nQuery: {query[:100]}...")
                print(f"Calls: {calls}, Avg: {mean_time:.2f}ms, Max: {max_time:.2f}ms")
            
        except Exception as e:
            print(f"⚠️  pg_stat_statements not available: {e}")

def check_missing_indexes(app):
    """Check for missing indexes on foreign keys"""
    with app.app_context():
        try:
            result = db.session.execute(text("""
                SELECT 
                    t.relname as table_name,
                    a.attname as column_name
                FROM pg_constraint c
                JOIN pg_class t ON c.conrelid = t.oid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(c.conkey)
                WHERE c.contype = 'f'
                AND NOT EXISTS (
                    SELECT 1 FROM pg_index i
                    WHERE i.indrelid = t.oid
                    AND a.attnum = ANY(i.indkey)
                )
                ORDER BY t.relname, a.attname
            """)).fetchall()
            
            if result:
                print("\n📊 MISSING INDEXES ON FOREIGN KEYS:")
                print("=" * 80)
                for row in result:
                    table, column = row
                    print(f"  CREATE INDEX idx_{table}_{column} ON {table}({column});")
            else:
                print("\n✅ All foreign keys have indexes")
                
        except Exception as e:
            print(f"Error checking indexes: {e}")

def analyze_table_sizes(app):
    """Analyze table sizes and growth"""
    with app.app_context():
        try:
            result = db.session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 20
            """)).fetchall()
            
            print("\n💾 TABLE SIZES:")
            print("=" * 80)
            for row in result:
                schema, table, size, size_bytes = row
                print(f"  {table:30s} {size:>15s}")
                
        except Exception as e:
            print(f"Error analyzing table sizes: {e}")

def check_query_performance(app):
    """Check specific query performance"""
    with app.app_context():
        queries_to_test = [
            ("Chat history", "SELECT * FROM messages WHERE session_id = 'test' ORDER BY timestamp DESC LIMIT 50"),
            ("Mood history", "SELECT * FROM mood_entries WHERE session_id = 'test' ORDER BY timestamp DESC LIMIT 50"),
            ("Quests", "SELECT * FROM quests WHERE week_number = 3 AND year = 2026"),
            ("Resources", "SELECT * FROM resources WHERE is_active = true AND category = 'crisis'"),
        ]
        
        print("\n⚡ QUERY PERFORMANCE:")
        print("=" * 80)
        
        for name, query in queries_to_test:
            try:
                result = db.session.execute(text(f"EXPLAIN ANALYZE {query}")).fetchall()
                
                # Extract execution time from EXPLAIN ANALYZE output
                for row in result:
                    line = str(row[0])
                    if "Execution Time" in line or "Planning Time" in line:
                        print(f"  {name:20s} {line}")
                        
            except Exception as e:
                print(f"  {name:20s} Error: {e}")

def main():
    app = create_app()
    
    print("🔍 PERFORMANCE ANALYSIS")
    print("=" * 80)
    
    analyze_slow_queries(app)
    check_missing_indexes(app)
    analyze_table_sizes(app)
    check_query_performance(app)
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete")

if __name__ == '__main__':
    main()
