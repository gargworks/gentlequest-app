"""Add settings fields to users

Revision ID: 006_add_user_settings_fields
Revises: 005_add_context_chips_to_mood
Create Date: 2026-05-14 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '006_add_user_settings_fields'
down_revision = '005_add_context_chips_to_mood'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('anonymity_mode', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.add_column(
        'users',
        sa.Column('notification_prefs', JSONB, nullable=False, server_default='{}'),
    )
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'notification_prefs')
    op.drop_column('users', 'anonymity_mode')
