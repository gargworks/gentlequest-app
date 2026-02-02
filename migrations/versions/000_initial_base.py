"""Initial base schema

Revision ID: 000_initial_base
Revises: 
Create Date: 2026-02-02 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000_initial_base'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Inspector to check for existing tables
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. sessions
    if 'sessions' not in existing_tables:
        op.create_table(
            'sessions',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('last_active', sa.DateTime(), nullable=True),
            sa.Column('conversation_count', sa.Integer(), nullable=True),
            sa.Column('risk_level', sa.String(length=20), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # 2. universities
    if 'universities' not in existing_tables:
        op.create_table(
            'universities',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('domain', sa.String(length=100), nullable=True),
            sa.Column('caps_email', sa.String(length=255), nullable=True),
            sa.Column('caps_phone', sa.String(length=50), nullable=True),
            sa.Column('caps_hours', sa.String(length=200), nullable=True),
            sa.Column('waitlist_weeks', sa.Integer(), nullable=True),
            sa.Column('enrollment', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('logo_url', sa.String(length=500), nullable=True),
            sa.Column('primary_color', sa.String(length=7), nullable=True),
            sa.Column('secondary_color', sa.String(length=7), nullable=True),
            sa.Column('welcome_message', sa.Text(), nullable=True),
            sa.Column('sso_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=True),
            sa.Column('sso_provider', sa.String(length=50), nullable=True),
            sa.Column('sso_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('lms_integration', sa.String(length=50), nullable=True),
            sa.Column('custom_domain', sa.String(length=100), nullable=True),
            sa.Column('outreach_status', sa.String(length=50), nullable=True),
            sa.Column('contact_email', sa.String(length=255), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # 3. chat_messages
    if 'chat_messages' not in existing_tables:
         op.create_table(
            'chat_messages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(36), sa.ForeignKey("sessions.id")),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('is_user', sa.Boolean(), default=False),
            sa.Column('timestamp', sa.DateTime(), default=sa.func.now()),
            sa.Column('risk_level', sa.String(20), default="none"),
            sa.Column('resources', sa.Text()),
            sa.Column('message_type', sa.String(50), default="text"),
            sa.PrimaryKeyConstraint('id')
        )

    # 4. conversation_logs
    if 'conversation_logs' not in existing_tables:
        op.create_table(
            'conversation_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(length=36), nullable=True),
            sa.Column('user_message', sa.Text(), nullable=False),
            sa.Column('ai_response', sa.Text(), nullable=False),
            sa.Column('risk_level', sa.String(length=20), nullable=True),
            sa.Column('risk_score', sa.Float(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 5. crisis_detections
    if 'crisis_detections' not in existing_tables:
        op.create_table(
            'crisis_detections',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(length=36), nullable=True),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('risk_level', sa.String(length=50), nullable=True),
            sa.Column('risk_score', sa.Float(), nullable=True),
            sa.Column('keywords', sa.Text(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.Column('intervention_taken', sa.String(length=100), nullable=True),
            sa.Column('escalated', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 6. self_assessment_entries
    if 'self_assessment_entries' not in existing_tables:
        op.create_table(
            'self_assessment_entries',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(length=36), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('assessment_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 7. mood_entries
    if 'mood_entries' not in existing_tables:
        op.create_table(
            'mood_entries',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(length=36), nullable=True),
            sa.Column('mood_level', sa.Integer(), nullable=False),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 8. analytics_events
    if 'analytics_events' not in existing_tables:
        op.create_table(
            'analytics_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(length=36), nullable=True),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('request_id', sa.String(length=64), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 9. intervention_outcomes
    if 'intervention_outcomes' not in existing_tables:
        op.create_table(
            'intervention_outcomes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(length=255), nullable=False),
            sa.Column('intervention_id', sa.String(length=100), nullable=False),
            sa.Column('issue', sa.String(length=50), nullable=True),
            sa.Column('offer_stage', sa.Integer(), nullable=True),
            sa.Column('outcome', sa.String(length=20), nullable=True),
            sa.Column('completed', sa.Boolean(), nullable=False),
            sa.Column('effectiveness_rating', sa.Float(), nullable=True),
            sa.Column('feedback', sa.Text(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('exercise_type', sa.String(length=50), nullable=True),
            sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
            sa.Column('mood_before', sa.Integer(), nullable=True),
            sa.Column('mood_after', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 10. users
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('session_id', sa.String(length=36), nullable=True),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email')
        )

    # 11. community_posts
    if 'community_posts' not in existing_tables:
        op.create_table(
            'community_posts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('topic', sa.String(length=64), nullable=True),
            sa.Column('body_redacted', sa.Text(), nullable=False),
            sa.Column('is_curated', sa.Boolean(), nullable=True),
            sa.Column('is_hidden', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('reactions_relate', sa.Integer(), nullable=True),
            sa.Column('reactions_helped', sa.Integer(), nullable=True),
            sa.Column('reactions_strength', sa.Integer(), nullable=True),
            sa.Column('author_hash', sa.String(length=64), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # 12. clinical_assessments
    if 'clinical_assessments' not in existing_tables:
        op.create_table(
            'clinical_assessments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(length=36), nullable=False),
            sa.Column('assessment_type', sa.String(length=20), nullable=False),
            sa.Column('responses', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column('total_score', sa.Integer(), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=False),
            sa.Column('requires_follow_up', sa.Boolean(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('assessment_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # 13. brain_state
    if 'brain_state' not in existing_tables:
        op.create_table(
            'brain_state',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('state_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column('last_updated', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # 14. brain_events
    if 'brain_events' not in existing_tables:
        op.create_table(
            'brain_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.String(length=36), nullable=False),
            sa.Column('event_type', sa.String(length=100), nullable=False),
            sa.Column('emitter', sa.String(length=50), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=True),
            sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

def downgrade():
    op.drop_table('brain_events')
    op.drop_table('brain_state')
    op.drop_table('clinical_assessments')
    op.drop_table('community_posts')
    op.drop_table('users')
    op.drop_table('intervention_outcomes')
    op.drop_table('analytics_events')
    op.drop_table('mood_entries')
    op.drop_table('self_assessment_entries')
    op.drop_table('crisis_detections')
    op.drop_table('conversation_logs')
    op.drop_table('messages')
    op.drop_table('universities')
    op.drop_table('sessions')
