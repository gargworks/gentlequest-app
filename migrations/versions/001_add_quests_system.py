"""Add quests system

Revision ID: 001_add_quests_system
Revises: 
Create Date: 2026-01-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_quests_system'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create quest_type enum
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'questtype') THEN CREATE TYPE questtype AS ENUM ('task', 'tip', 'check_in', 'progress'); END IF; END $$;")
    
    # Create quest_status enum
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'queststatus') THEN CREATE TYPE queststatus AS ENUM ('available', 'in_progress', 'completed', 'expired'); END IF; END $$;")
    
    # Create quests table
    op.create_table(
        'quests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('quest_type', postgresql.ENUM('task', 'tip', 'check_in', 'progress', name='questtype'), nullable=False),
        sa.Column('xp_reward', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('difficulty', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_quests_week', 'quests', ['week_number', 'year'])
    
    # Create quest_progress table
    op.create_table(
        'quest_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('quest_id', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('available', 'in_progress', 'completed', 'expired', name='queststatus'), nullable=False, server_default='available'),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['session_id'], ['user_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quest_id'], ['quests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_quest_progress_session', 'quest_progress', ['session_id'])
    op.create_index('idx_quest_progress_quest', 'quest_progress', ['quest_id'])
    op.create_index('idx_quest_progress_status', 'quest_progress', ['session_id', 'status'])
    
    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('xp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('streak_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_activity_date', sa.DateTime()),
        sa.Column('badges', sa.String(500), server_default=''),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['session_id'], ['user_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index('idx_user_profiles_session', 'user_profiles', ['session_id'])


def downgrade():
    op.drop_index('idx_user_profiles_session', table_name='user_profiles')
    op.drop_table('user_profiles')
    
    op.drop_index('idx_quest_progress_status', table_name='quest_progress')
    op.drop_index('idx_quest_progress_quest', table_name='quest_progress')
    op.drop_index('idx_quest_progress_session', table_name='quest_progress')
    op.drop_table('quest_progress')
    
    op.drop_index('idx_quests_week', table_name='quests')
    op.drop_table('quests')
    
    op.execute('DROP TYPE IF EXISTS queststatus')
    op.execute('DROP TYPE IF EXISTS questtype')
