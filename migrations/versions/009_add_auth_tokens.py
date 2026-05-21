"""Add auth_tokens table for passwordless magic-link login

Revision ID: 009_add_auth_tokens
Revises: 008_add_user_resource_prefs_and_push_tokens
Create Date: 2026-05-21 11:00:00.000000

Schema notes:
  - token_hash is sha256 hex (64 chars). Raw token never persisted.
  - 15-minute TTL enforced in routes/auth.py — no DB-side check.
  - Single-use enforced by used_at sentinel (set on verify).
  - Indexed on (user_id) for lookups by account; (token_hash) for
    O(1) verify path.
"""
from alembic import op
import sqlalchemy as sa


revision = '009_add_auth_tokens'
down_revision = '008_add_user_resource_prefs_and_push_tokens'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'auth_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash', name='uq_auth_tokens_token_hash'),
    )
    op.create_index('ix_auth_tokens_user_id', 'auth_tokens', ['user_id'])
    op.create_index('ix_auth_tokens_token_hash', 'auth_tokens', ['token_hash'])


def downgrade():
    op.drop_index('ix_auth_tokens_token_hash', table_name='auth_tokens')
    op.drop_index('ix_auth_tokens_user_id', table_name='auth_tokens')
    op.drop_table('auth_tokens')
