"""Add quests system

Revision ID: 001_add_quests_system
Revises: 
Create Date: 2026-01-17 10:00:00.000000

"""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_quests_system'
down_revision = '000_initial_base'
branch_labels = None
depends_on = None

def upgrade():
    dialect_name = context.get_context().dialect.name
    is_postgresql = dialect_name == 'postgresql'
    quest_type = (
        postgresql.ENUM('task', 'tip', 'check_in', 'progress', name='questtype', create_type=False)
        if is_postgresql
        else sa.String(length=20)
    )
    quest_status = (
        postgresql.ENUM('available', 'in_progress', 'completed', 'expired', name='queststatus', create_type=False)
        if is_postgresql
        else sa.String(length=20)
    )
    if is_postgresql:
        op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'questtype') THEN CREATE TYPE questtype AS ENUM ('task', 'tip', 'check_in', 'progress'); END IF; END $$;")
        op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'queststatus') THEN CREATE TYPE queststatus AS ENUM ('available', 'in_progress', 'completed', 'expired'); END IF; END $$;")
    if context.is_offline_mode():
        existing_tables = set()
    else:
        conn = op.get_bind()
        existing_tables = set(sa.inspect(conn).get_table_names())

    # Create quests table
    if 'quests' not in existing_tables:
        op.create_table(
            'quests',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('description', sa.String(500), nullable=False),
            sa.Column('quest_type', quest_type, nullable=False),
            sa.Column('xp_reward', sa.Integer(), nullable=False, server_default='10'),
            sa.Column('difficulty', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('week_number', sa.Integer(), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_quests_week', 'quests', ['week_number', 'year'])
    
    # Create quest_progress table
    if 'quest_progress' not in existing_tables:
        op.create_table(
            'quest_progress',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(255), nullable=False),
            sa.Column('quest_id', sa.Integer(), nullable=False),
            sa.Column('status', quest_status, nullable=False, server_default='available'),
            sa.Column('started_at', sa.DateTime()),
            sa.Column('completed_at', sa.DateTime()),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['quest_id'], ['quests.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_quest_progress_session', 'quest_progress', ['session_id'])
        op.create_index('idx_quest_progress_quest', 'quest_progress', ['quest_id'])
        op.create_index('idx_quest_progress_status', 'quest_progress', ['session_id', 'status'])
    
    # Create user_profiles table
    if 'user_profiles' not in existing_tables:
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
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('session_id')
        )
        op.create_index('idx_user_profiles_session', 'user_profiles', ['session_id'])


def downgrade():
    dialect_name = context.get_context().dialect.name
    op.drop_index('idx_user_profiles_session', table_name='user_profiles')
    op.drop_table('user_profiles')
    
    op.drop_index('idx_quest_progress_status', table_name='quest_progress')
    op.drop_index('idx_quest_progress_quest', table_name='quest_progress')
    op.drop_index('idx_quest_progress_session', table_name='quest_progress')
    op.drop_table('quest_progress')
    
    op.drop_index('idx_quests_week', table_name='quests')
    op.drop_table('quests')
    
    if dialect_name == 'postgresql':
        op.execute('DROP TYPE IF EXISTS queststatus')
        op.execute('DROP TYPE IF EXISTS questtype')
