"""Enhanced agent mesh models with pgvector support

Revision ID: 003_enhanced_models
Revises: 002_agents
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003_enhanced_models'
down_revision = '002_agents'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create pgvector extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create skills table
    op.create_table('skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='app'
    )
    op.create_index('ix_skills_name', 'skills', ['name'], unique=True, schema='app')
    op.create_index('ix_skills_category', 'skills', ['category'], schema='app')
    
    # Create constraints table
    op.create_table('constraints',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='app'
    )
    op.create_index('ix_constraints_name', 'constraints', ['name'], unique=True, schema='app')
    op.create_index('ix_constraints_type', 'constraints', ['type'], schema='app')
    
    # Create prompts table
    op.create_table('prompts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['app.users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='app'
    )
    op.create_index('ix_prompts_name', 'prompts', ['name'], schema='app')
    
    # Create models table
    op.create_table('models',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model_id', sa.String(100), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['app.users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='app'
    )
    op.create_index('ix_models_name', 'models', ['name'], schema='app')
    op.create_index('ix_models_provider', 'models', ['provider'], schema='app')
    op.create_index('ix_models_is_active', 'models', ['is_active'], schema='app')
    
    # Create environment_secrets table
    op.create_table('environment_secrets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('environment', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['app.users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='app'
    )
    op.create_index('ix_environment_secrets_key', 'environment_secrets', ['key'], schema='app')
    op.create_index('ix_environment_secrets_environment', 'environment_secrets', ['environment'], schema='app')
    
    # Create association tables for many-to-many relationships
    op.create_table('agent_skills',
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['app.agents.id'], ),
        sa.ForeignKeyConstraint(['skill_id'], ['app.skills.id'], ),
        schema='app'
    )
    
    op.create_table('agent_constraints',
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('constraint_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['app.agents.id'], ),
        sa.ForeignKeyConstraint(['constraint_id'], ['app.constraints.id'], ),
        schema='app'
    )
    
    op.create_table('agent_tools',
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['app.agents.id'], ),
        sa.ForeignKeyConstraint(['tool_id'], ['app.tools.id'], ),
        schema='app'
    )
    
    # Add pgvector column to agents table if not exists
    try:
        op.add_column('agents', sa.Column('search_vector', postgresql.ARRAY(sa.Float), nullable=True), schema='app')
    except:
        # Column might already exist
        pass
    
    # Add new columns to existing agents table
    try:
        op.add_column('agents', sa.Column('llm_model', sa.String(100), nullable=True), schema='app')
        op.add_column('agents', sa.Column('embedding_model', sa.String(100), nullable=True), schema='app')
        op.add_column('agents', sa.Column('auth_token', sa.String(500), nullable=True), schema='app')
        op.add_column('agents', sa.Column('port', sa.Integer(), nullable=True), schema='app')
        op.add_column('agents', sa.Column('dns', sa.String(500), nullable=True), schema='app')
        op.add_column('agents', sa.Column('health_url', sa.String(500), nullable=True), schema='app')
        op.add_column('agents', sa.Column('health_status', sa.String(20), nullable=True), schema='app')
        op.add_column('agents', sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True), schema='app')
        op.add_column('agents', sa.Column('is_public', sa.Boolean(), nullable=True), schema='app')
        op.add_column('agents', sa.Column('prompt', sa.Text(), nullable=True), schema='app')
        op.add_column('agents', sa.Column('config', sa.JSON(), nullable=True), schema='app')
        op.add_column('agents', sa.Column('input_payload', sa.JSON(), nullable=True), schema='app')
        op.add_column('agents', sa.Column('output_payload', sa.JSON(), nullable=True), schema='app')
        op.add_column('agents', sa.Column('type', sa.String(50), nullable=True), schema='app')
        op.add_column('agents', sa.Column('template', sa.String(100), nullable=True), schema='app')
    except:
        # Columns might already exist
        pass
    
    # Add indexes for new columns
    try:
        op.create_index('ix_agents_status', 'agents', ['status'], schema='app')
        op.create_index('ix_agents_type', 'agents', ['type'], schema='app')
        op.create_index('ix_agents_is_public', 'agents', ['is_public'], schema='app')
        op.create_index('ix_agents_health_status', 'agents', ['health_status'], schema='app')
    except:
        # Indexes might already exist
        pass
    
    # Add relationships to users table
    try:
        op.add_column('users', sa.Column('prompts', sa.String(), nullable=True), schema='app')
        op.add_column('users', sa.Column('models', sa.String(), nullable=True), schema='app')
        op.add_column('users', sa.Column('environment_secrets', sa.String(), nullable=True), schema='app')
    except:
        # Columns might already exist or not needed
        pass


def downgrade() -> None:
    # Remove new columns from agents table
    try:
        op.drop_column('agents', 'search_vector', schema='app')
        op.drop_column('agents', 'llm_model', schema='app')
        op.drop_column('agents', 'embedding_model', schema='app')
        op.drop_column('agents', 'auth_token', schema='app')
        op.drop_column('agents', 'port', schema='app')
        op.drop_column('agents', 'dns', schema='app')
        op.drop_column('agents', 'health_url', schema='app')
        op.drop_column('agents', 'health_status', schema='app')
        op.drop_column('agents', 'last_health_check', schema='app')
        op.drop_column('agents', 'is_public', schema='app')
        op.drop_column('agents', 'prompt', schema='app')
        op.drop_column('agents', 'config', schema='app')
        op.drop_column('agents', 'input_payload', schema='app')
        op.drop_column('agents', 'output_payload', schema='app')
        op.drop_column('agents', 'type', schema='app')
        op.drop_column('agents', 'template', schema='app')
    except:
        pass
    
    # Drop association tables
    op.drop_table('agent_tools', schema='app')
    op.drop_table('agent_constraints', schema='app')
    op.drop_table('agent_skills', schema='app')
    
    # Drop new tables
    op.drop_table('environment_secrets', schema='app')
    op.drop_table('models', schema='app')
    op.drop_table('prompts', schema='app')
    op.drop_table('constraints', schema='app')
    op.drop_table('skills', schema='app')
