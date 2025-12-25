"""
Database migration: Create intervention_outcomes table

Run with: python migrations/create_intervention_outcomes.py
"""

from sqlalchemy import text
from models import db
from app import create_app

def run_migration():
    """Create intervention_outcomes table"""
    app = create_app()
    
    with app.app_context():
        # Create table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS intervention_outcomes (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                intervention_id VARCHAR(100) NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                effectiveness_rating FLOAT,
                feedback TEXT,
                timestamp TIMESTAMP NOT NULL,
                
                CONSTRAINT effectiveness_rating_check CHECK (effectiveness_rating IS NULL OR (effectiveness_rating >= 0 AND effectiveness_rating <= 1))
            )
        """))
        
        # Create indexes for common queries
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_intervention_outcomes_session 
            ON intervention_outcomes(session_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_intervention_outcomes_intervention 
            ON intervention_outcomes(intervention_id)
        """))
        
        db.session.commit()
        print("✅ intervention_outcomes table created successfully")

if __name__ == '__main__':
    run_migration()
