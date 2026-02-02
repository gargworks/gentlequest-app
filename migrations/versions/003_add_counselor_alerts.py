"""Add counselor alerts system

Revision ID: 003_add_counselor_alerts
Revises: 002_add_resources_system
Create Date: 2026-01-17 10:02:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_counselor_alerts'
down_revision = '002_add_resources_system'
branch_labels = None
depends_on = None


def upgrade():
    # Create alert_severity enum
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alertseverity') THEN CREATE TYPE alertseverity AS ENUM ('low', 'medium', 'high', 'critical'); END IF; END $$;")
    
    # Create university_counselors table
    op.create_table(
        'university_counselors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('university_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50)),
        sa.Column('role', sa.String(100)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('receives_alerts', sa.Boolean(), server_default='true'),
        sa.Column('alert_methods', sa.String(100), server_default='email'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_counselors_university', 'university_counselors', ['university_id'])
    op.create_index('idx_counselors_active', 'university_counselors', ['is_active', 'receives_alerts'])
    
    # Create counselor_alerts table
    op.create_table(
        'counselor_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('university_id', sa.Integer()),
        sa.Column('severity', postgresql.ENUM('low', 'medium', 'high', 'critical', name='alertseverity'), nullable=False),
        sa.Column('trigger_message', sa.Text(), nullable=False),
        sa.Column('conversation_excerpt', sa.Text()),
        sa.Column('risk_keywords', sa.String(500)),
        sa.Column('sent_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('acknowledged_at', sa.DateTime()),
        sa.Column('acknowledged_by', sa.String(255)),
        sa.Column('email_sent', sa.Boolean(), server_default='false'),
        sa.Column('sms_sent', sa.Boolean(), server_default='false'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alerts_session', 'counselor_alerts', ['session_id'])
    op.create_index('idx_alerts_severity', 'counselor_alerts', ['severity', 'sent_at'])
    op.create_index('idx_alerts_acknowledged', 'counselor_alerts', ['acknowledged_at'])
    op.create_index('idx_alerts_university', 'counselor_alerts', ['university_id', 'acknowledged_at'])
    op.create_index('idx_alerts_pending', 'counselor_alerts', ['university_id', 'severity'], 
                    postgresql_where=sa.text('acknowledged_at IS NULL'))
    
    # Create alert_acknowledgments table
    op.create_table(
        'alert_acknowledgments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('counselor_id', sa.String(255), nullable=False),
        sa.Column('response_notes', sa.Text()),
        sa.Column('action_taken', sa.String(500)),
        sa.Column('responded_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['alert_id'], ['counselor_alerts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_acknowledgments_alert', 'alert_acknowledgments', ['alert_id'])
    op.create_index('idx_acknowledgments_counselor', 'alert_acknowledgments', ['counselor_id'])


def downgrade():
    op.drop_index('idx_acknowledgments_counselor', table_name='alert_acknowledgments')
    op.drop_index('idx_acknowledgments_alert', table_name='alert_acknowledgments')
    op.drop_table('alert_acknowledgments')
    
    op.drop_index('idx_alerts_pending', table_name='counselor_alerts')
    op.drop_index('idx_alerts_university', table_name='counselor_alerts')
    op.drop_index('idx_alerts_acknowledged', table_name='counselor_alerts')
    op.drop_index('idx_alerts_severity', table_name='counselor_alerts')
    op.drop_index('idx_alerts_session', table_name='counselor_alerts')
    op.drop_table('counselor_alerts')
    
    op.drop_index('idx_counselors_active', table_name='university_counselors')
    op.drop_index('idx_counselors_university', table_name='university_counselors')
    op.drop_table('university_counselors')
    
    op.execute('DROP TYPE IF EXISTS alertseverity')
