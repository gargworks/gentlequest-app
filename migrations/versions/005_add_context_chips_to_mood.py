"""Add context_chips column to mood_entries

Revision ID: 005_add_context_chips_to_mood
Revises: 004_add_performance_indexes
Create Date: 2026-05-13 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '005_add_context_chips_to_mood'
down_revision = '004_add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'mood_entries',
        sa.Column(
            'context_chips',
            sa.JSON().with_variant(JSONB(), "postgresql"),
            nullable=False,
            server_default='[]',
        ),
    )


def downgrade():
    op.drop_column('mood_entries', 'context_chips')
