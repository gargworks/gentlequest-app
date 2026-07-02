"""Add feedback_submissions table for in-app FeedbackDialog

Revision ID: 010_add_feedback_submissions
Revises: 009_add_auth_tokens
Create Date: 2026-07-02 00:00:00.000000

Schema notes:
  - Anonymous — session_id FK only, no user_id/auth.
  - rating is required (1-5); feedback_text/app_version/platform optional.
  - Length caps enforced app-side in routes/feedback.py, not via DB CHECK.
"""
from alembic import op
import sqlalchemy as sa


revision = '010_add_feedback_submissions'
down_revision = '009_add_auth_tokens'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'feedback_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('app_version', sa.String(length=40), nullable=True),
        sa.Column('platform', sa.String(length=20), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['session_id'], ['user_sessions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_feedback_submissions_session_id', 'feedback_submissions', ['session_id'])


def downgrade():
    op.drop_index('ix_feedback_submissions_session_id', table_name='feedback_submissions')
    op.drop_table('feedback_submissions')
