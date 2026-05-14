"""Add user resource prefs and push tokens

Revision ID: 008_add_user_resource_prefs_and_push_tokens
Revises: 007_add_journal_entries
Create Date: 2026-05-14 10:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '008_add_user_resource_prefs_and_push_tokens'
down_revision = '007_add_journal_entries'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_resource_prefs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('resource_id', sa.Text(), nullable=False),
        sa.Column('is_favorite', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('last_opened_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['user_sessions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'resource_id', name='uq_user_resource_prefs_session_resource'),
    )
    op.create_index('ix_user_resource_prefs_session_id', 'user_resource_prefs', ['session_id'])

    op.create_table(
        'push_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('platform', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['user_sessions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'token', name='uq_push_tokens_session_token'),
    )
    op.create_index('ix_push_tokens_session_id', 'push_tokens', ['session_id'])


def downgrade():
    op.drop_index('ix_push_tokens_session_id', table_name='push_tokens')
    op.drop_table('push_tokens')
    op.drop_index('ix_user_resource_prefs_session_id', table_name='user_resource_prefs')
    op.drop_table('user_resource_prefs')
