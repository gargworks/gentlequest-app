"""Add performance indexes

Revision ID: 004_add_performance_indexes
Revises: 003_add_counselor_alerts
Create Date: 2026-01-17 10:03:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_add_performance_indexes'
down_revision = '003_add_counselor_alerts'
branch_labels = None
depends_on = None


def upgrade():
    # Messages table indexes (for chat history queries)
    op.create_index('idx_messages_session_timestamp', 'messages', ['session_id', 'timestamp'], 
                    postgresql_using='btree')
    op.create_index('idx_messages_timestamp', 'messages', ['timestamp'])
    
    # Mood entries indexes (for mood history and analytics)
    op.create_index('idx_mood_entries_session_timestamp', 'mood_entries', ['session_id', 'timestamp'])
    op.create_index('idx_mood_entries_timestamp', 'mood_entries', ['timestamp'])
    
    # Clinical assessments indexes (for outcome tracking)
    op.create_index('idx_clinical_assessments_session', 'clinical_assessments', ['session_id', 'timestamp'])
    op.create_index('idx_clinical_assessments_type', 'clinical_assessments', ['assessment_type', 'timestamp'])
    
    # Crisis detections indexes (for safety monitoring)
    op.create_index('idx_crisis_detections_session', 'crisis_detections', ['session_id', 'timestamp'])
    op.create_index('idx_crisis_detections_risk', 'crisis_detections', ['risk_level', 'timestamp'])
    
    # Sessions table indexes (for cleanup and analytics)
    op.create_index('idx_sessions_last_activity', 'sessions', ['last_activity'])
    op.create_index('idx_sessions_created_at', 'sessions', ['created_at'])
    
    # Analytics events indexes (for reporting)
    op.create_index('idx_analytics_events_session', 'analytics_events', ['session_id', 'timestamp'])
    op.create_index('idx_analytics_events_type', 'analytics_events', ['event_type', 'timestamp'])
    
    # Intervention outcomes indexes (for effectiveness tracking)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_intervention_outcomes_session_timestamp 
        ON intervention_outcomes(session_id, timestamp)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_intervention_outcomes_type_outcome 
        ON intervention_outcomes(exercise_type, outcome)
    """)


def downgrade():
    op.execute('DROP INDEX IF EXISTS idx_intervention_outcomes_type_outcome')
    op.execute('DROP INDEX IF EXISTS idx_intervention_outcomes_session_timestamp')
    
    op.drop_index('idx_analytics_events_type', table_name='analytics_events')
    op.drop_index('idx_analytics_events_session', table_name='analytics_events')
    
    op.drop_index('idx_sessions_created_at', table_name='sessions')
    op.drop_index('idx_sessions_last_activity', table_name='sessions')
    
    op.drop_index('idx_crisis_detections_risk', table_name='crisis_detections')
    op.drop_index('idx_crisis_detections_session', table_name='crisis_detections')
    
    op.drop_index('idx_clinical_assessments_type', table_name='clinical_assessments')
    op.drop_index('idx_clinical_assessments_session', table_name='clinical_assessments')
    
    op.drop_index('idx_mood_entries_timestamp', table_name='mood_entries')
    op.drop_index('idx_mood_entries_session_timestamp', table_name='mood_entries')
    
    op.drop_index('idx_messages_timestamp', table_name='messages')
    op.drop_index('idx_messages_session_timestamp', table_name='messages')
