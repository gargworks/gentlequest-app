"""Add performance indexes

Revision ID: 004_add_performance_indexes
Revises: 003_add_counselor_alerts
Create Date: 2026-01-17 10:03:00.000000

"""
from alembic import context, op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_add_performance_indexes'
down_revision = '003_add_counselor_alerts'
branch_labels = None
depends_on = None


def upgrade():
    if context.get_context().dialect.name == 'postgresql':
        op.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_session_timestamp ON chat_messages USING btree (session_id, timestamp)")
    else:
        op.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_session_timestamp ON chat_messages (session_id, timestamp)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages (timestamp)")
    
    # Mood entries indexes (for mood history and analytics)
    op.execute("CREATE INDEX IF NOT EXISTS idx_mood_entries_session_timestamp ON mood_entries (session_id, timestamp)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_mood_entries_timestamp ON mood_entries (timestamp)")
    
    # Clinical assessments indexes (for outcome tracking)
    # Wrap these in if exists table check because they are new tables in this sprint
    if context.is_offline_mode():
        existing_tables = {
            'clinical_assessments',
            'crisis_detections',
            'analytics_events',
            'intervention_outcomes',
        }
    else:
        conn = op.get_bind()
        existing_tables = set(sa.inspect(conn).get_table_names())

    if 'clinical_assessments' in existing_tables:
        op.execute("CREATE INDEX IF NOT EXISTS idx_clinical_assessments_session ON clinical_assessments (session_id, timestamp)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_clinical_assessments_type ON clinical_assessments (assessment_type, timestamp)")
    
    # Crisis detections indexes (for safety monitoring)
    if 'crisis_detections' in existing_tables:
        op.execute("CREATE INDEX IF NOT EXISTS idx_crisis_detections_session ON crisis_detections (session_id, timestamp)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_crisis_detections_risk ON crisis_detections (risk_level, timestamp)")
    
    # Sessions table indexes (for cleanup and analytics)
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_last_active ON sessions (last_active)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions (created_at)")
    
    # Analytics events indexes (for reporting)
    if 'analytics_events' in existing_tables:
        op.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_session ON analytics_events (session_id, timestamp)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events (event_type, timestamp)")
    
    # Intervention outcomes indexes (for effectiveness tracking)
    if 'intervention_outcomes' in existing_tables:
        op.execute("CREATE INDEX IF NOT EXISTS idx_intervention_outcomes_session_timestamp ON intervention_outcomes(session_id, timestamp)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_intervention_outcomes_type_outcome ON intervention_outcomes(exercise_type, outcome)")


def downgrade():
    op.execute('DROP INDEX IF EXISTS idx_intervention_outcomes_type_outcome')
    op.execute('DROP INDEX IF EXISTS idx_intervention_outcomes_session_timestamp')
    
    op.drop_index('idx_analytics_events_type', table_name='analytics_events')
    op.drop_index('idx_analytics_events_session', table_name='analytics_events')
    
    op.drop_index('idx_sessions_created_at', table_name='sessions')
    op.drop_index('idx_sessions_last_active', table_name='sessions')
    
    op.drop_index('idx_crisis_detections_risk', table_name='crisis_detections')
    op.drop_index('idx_crisis_detections_session', table_name='crisis_detections')
    
    op.drop_index('idx_clinical_assessments_type', table_name='clinical_assessments')
    op.drop_index('idx_clinical_assessments_session', table_name='clinical_assessments')
    
    op.drop_index('idx_mood_entries_timestamp', table_name='mood_entries')
    op.drop_index('idx_mood_entries_session_timestamp', table_name='mood_entries')
    
    op.drop_index('idx_chat_messages_timestamp', table_name='chat_messages')
    op.drop_index('idx_chat_messages_session_timestamp', table_name='chat_messages')
