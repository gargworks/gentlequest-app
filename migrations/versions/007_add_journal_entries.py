"""Add journal entries

Revision ID: 007_add_journal_entries
Revises: 006_add_user_settings_fields
Create Date: 2026-05-14 04:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '007_add_journal_entries'
down_revision = '006_add_user_settings_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'journal_entries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('mood_tag', sa.String(length=40), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['user_sessions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_journal_entries_session_id', 'journal_entries', ['session_id'])


def downgrade():
    op.drop_index('ix_journal_entries_session_id', table_name='journal_entries')
    op.drop_table('journal_entries')
