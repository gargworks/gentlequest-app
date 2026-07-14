"""
Startup auto-migrations: idempotent ALTER TABLE statements for legacy columns.
Extracted from app.py monolith.
"""

from flask import Flask
from sqlalchemy import inspect, text as sql_text

from models import db

MIGRATION_STATEMENTS = [
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) DEFAULT 'none'",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS resources TEXT",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS message_type VARCHAR(50) DEFAULT 'text'",
    "ALTER TABLE quests ADD COLUMN IF NOT EXISTS target INTEGER DEFAULT 1",
    "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS exercise_type VARCHAR(50)",
    "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS time_spent_seconds INTEGER",
    "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS mood_before INTEGER",
    "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS mood_after INTEGER",
    "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS offer_stage INTEGER DEFAULT 1",
    "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS effectiveness_rating FLOAT",
    "ALTER TABLE intervention_outcomes ADD COLUMN IF NOT EXISTS feedback TEXT",
    "ALTER TABLE mood_entries ADD COLUMN IF NOT EXISTS context_chips JSONB NOT NULL DEFAULT '[]'::jsonb",
    # Phase H: triage state machine
    "ALTER TABLE counselor_alerts ADD COLUMN IF NOT EXISTS triage_state VARCHAR(20) DEFAULT 'new'",
    # Phase I: crisis escalation events
    (
        "CREATE TABLE IF NOT EXISTS crisis_escalations ("
        "  id SERIAL PRIMARY KEY,"
        "  session_id VARCHAR(255) NOT NULL,"
        "  country_code VARCHAR(5),"
        "  channel VARCHAR(20) NOT NULL,"
        "  status VARCHAR(20) NOT NULL DEFAULT 'initiated',"
        "  details TEXT,"
        "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  check_in_at TIMESTAMP,"
        "  check_in_sent BOOLEAN DEFAULT FALSE"
        ")"
    ),
    # ADR-005 criterion (iii): in-app feedback widget → backend
    # (Postgres syntax — SQLite uses db.create_all() via the model)
    (
        "CREATE TABLE IF NOT EXISTS user_feedback ("
        "  id SERIAL PRIMARY KEY,"
        "  session_id VARCHAR(36),"
        "  rating INTEGER NOT NULL,"
        "  feedback_text TEXT,"
        "  \"trigger\" VARCHAR(50) DEFAULT 'after_3rd_checkin',"
        "  country VARCHAR(10),"
        "  app_version VARCHAR(50),"
        "  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
        ")"
    ),
]


def run_auto_migrations(app: Flask) -> None:
    """Apply idempotent ALTER TABLE statements for the Agentic Wellness feature set."""
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            table_names = set(inspector.get_table_names())
            if "sessions" in table_names and "user_sessions" not in table_names:
                try:
                    statement = "ALTER TABLE sessions RENAME TO user_sessions"
                    db.session.execute(sql_text(statement))
                    db.session.commit()
                    app.logger.info(f"Migration successful: {statement}")
                except Exception as e:
                    db.session.rollback()
                    app.logger.warning(f"Migration error for '{statement}': {e}")
            for statement in MIGRATION_STATEMENTS:
                try:
                    db.session.execute(sql_text(statement))
                    db.session.commit()
                    app.logger.info(f"Migration successful: {statement}")
                except Exception as e:
                    db.session.rollback()
                    msg = str(e).lower()
                    if "already exists" in msg or "duplicate column" in msg:
                        app.logger.info(
                            f"Migration column already exists (ignored): {statement}"
                        )
                    else:
                        app.logger.warning(f"Migration error for '{statement}': {e}")
    except Exception as e:
        app.logger.error(f"Failed to initialize auto-migrations: {e}")
