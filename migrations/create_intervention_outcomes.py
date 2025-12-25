"""
Database migration: Create intervention_outcomes table
Supports agentic variety tracking (issue, offer_stage, outcome)

Run with: python migrations/create_intervention_outcomes.py
"""

from sqlalchemy import text
from models import db
from app import create_app

def run_migration():
    """Create/update intervention_outcomes table"""
    app = create_app()
    
    with app.app_context():
        # Create table with all columns
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS intervention_outcomes (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                intervention_id VARCHAR(100) NOT NULL,
                issue VARCHAR(50),
                offer_stage INTEGER DEFAULT 1,
                outcome VARCHAR(20) DEFAULT 'offered',
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                effectiveness_rating FLOAT,
                feedback TEXT,
                timestamp TIMESTAMP NOT NULL,
                
                CONSTRAINT effectiveness_rating_check CHECK (effectiveness_rating IS NULL OR (effectiveness_rating >= 0 AND effectiveness_rating <= 1)),
                CONSTRAINT outcome_check CHECK (outcome IN ('offered', 'started', 'completed', 'skipped'))
            )
        """))
        
        # Add columns if they don't exist (for existing tables)
        try:
            db.session.execute(text("ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS issue VARCHAR(50)"))
            db.session.execute(text("ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS offer_stage INTEGER DEFAULT 1"))
            db.session.execute(text("ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS outcome VARCHAR(20) DEFAULT 'offered'"))
        except Exception as e:
            print(f"Note: {e}")  # Columns may already exist
        
        # Create indexes for common queries
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_intervention_outcomes_session 
            ON intervention_outcomes(session_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_intervention_outcomes_intervention 
            ON intervention_outcomes(intervention_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_intervention_outcomes_issue 
            ON intervention_outcomes(session_id, issue)
        """))
        
        db.session.commit()
        print("✅ intervention_outcomes table created/updated successfully")

if __name__ == '__main__':
    run_migration()
