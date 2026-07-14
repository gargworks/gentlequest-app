"""
Database migration: Create user_feedback table
ADR-005 criterion (iii) — in-app feedback widget → backend (human voice).

Run with: python migrations/create_user_feedback.py
"""

from models import db, UserFeedback
from app import create_app


def run_migration():
    """Create user_feedback table using SQLAlchemy ORM (dialect-agnostic)."""
    app = create_app()

    with app.app_context():
        db.create_all()
        # Verify the table exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if "user_feedback" in inspector.get_table_names():
            print("user_feedback table created/verified successfully")
        else:
            print("ERROR: user_feedback table not found after create_all")
            raise RuntimeError("Table creation failed")


if __name__ == "__main__":
    run_migration()
