"""Add resources system

Revision ID: 002_add_resources_system
Revises: 001_add_quests_system
Create Date: 2026-01-17 10:01:00.000000

"""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_resources_system'
down_revision = '001_add_quests_system'
branch_labels = None
depends_on = None


def upgrade():
    dialect_name = context.get_context().dialect.name
    is_postgresql = dialect_name == 'postgresql'
    resource_category = (
        postgresql.ENUM('crisis', 'self_help', 'university', 'external', name='resourcecategory', create_type=False)
        if is_postgresql
        else sa.String(length=20)
    )
    if is_postgresql:
        op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'resourcecategory') THEN CREATE TYPE resourcecategory AS ENUM ('crisis', 'self_help', 'university', 'external'); END IF; END $$;")
    if context.is_offline_mode():
        existing_tables = set()
    else:
        conn = op.get_bind()
        existing_tables = set(sa.inspect(conn).get_table_names())

    # Create resources table
    if 'resources' not in existing_tables:
        op.create_table(
            'resources',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('description', sa.String(1000), nullable=False),
            sa.Column('url', sa.String(500)),
            sa.Column('category', resource_category, nullable=False),
            sa.Column('country', sa.String(10)),
            sa.Column('university_id', sa.Integer()),
            sa.Column('tags', sa.String(500)),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('is_active', sa.Boolean(), server_default='true'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_resources_category', 'resources', ['category'])
        op.create_index('idx_resources_country', 'resources', ['country'])
        op.create_index('idx_resources_active', 'resources', ['is_active'])
        
        if is_postgresql:
            op.execute("""
                CREATE INDEX idx_resources_search ON resources 
                USING GIN(to_tsvector('english', title || ' ' || description || ' ' || COALESCE(tags, '')))
            """)
    
    # Create user_resource_interactions table
    if 'user_resource_interactions' not in existing_tables:
        op.create_table(
            'user_resource_interactions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(255), nullable=False),
            sa.Column('resource_id', sa.Integer(), nullable=False),
            sa.Column('viewed_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_interactions_session', 'user_resource_interactions', ['session_id'])
        op.create_index('idx_interactions_resource', 'user_resource_interactions', ['resource_id'])
        op.create_index('idx_interactions_viewed_at', 'user_resource_interactions', ['viewed_at'])


def downgrade():
    dialect_name = context.get_context().dialect.name
    op.drop_index('idx_interactions_viewed_at', table_name='user_resource_interactions')
    op.drop_index('idx_interactions_resource', table_name='user_resource_interactions')
    op.drop_index('idx_interactions_session', table_name='user_resource_interactions')
    op.drop_table('user_resource_interactions')
    
    if dialect_name == 'postgresql':
        op.execute('DROP INDEX IF EXISTS idx_resources_search')
    op.drop_index('idx_resources_active', table_name='resources')
    op.drop_index('idx_resources_country', table_name='resources')
    op.drop_index('idx_resources_category', table_name='resources')
    op.drop_table('resources')
    
    if dialect_name == 'postgresql':
        op.execute('DROP TYPE IF EXISTS resourcecategory')
