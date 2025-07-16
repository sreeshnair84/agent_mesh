# Agent Mesh Database Setup

This directory contains the database initialization scripts for the Agent Mesh application.

## Fresh Installation

For a fresh PostgreSQL installation, the database will be initialized automatically using the scripts in the `init/` directory. These scripts are executed in order:

1. **01_create_extensions.sql** - Creates required PostgreSQL extensions (pgvector, uuid-ossp, etc.)
2. **02_create_schemas.sql** - Creates database schemas and types
3. **03_create_user.sql** - Creates database user with basic permissions
4. **04_grant_permissions.sql** - Grants schema-specific permissions
5. **05_create_all_tables.sql** - Creates all tables, indexes, and inserts default data

## Migration History

The `migrations/` directory has been deprecated in favor of the consolidated approach. All migration scripts have been combined into `init/05_create_all_tables.sql`.

### Previous Migrations (Backed up)

The original migration files have been backed up to `backups/migrations_backup/`:

- `001_initial.sql` - Initial database setup with core tables
- `002_agents.sql` - Agent-related tables and relationships
- `003_agent_payload_specs.sql` - Agent payload specifications (Python/Alembic)
- `004_update_skills_table.sql` - Skills table updates
- `005_insert_default_agent_categories.sql` - Default agent categories
- `006_add_tags_to_skills.py` - Skills table tags column (Python/Alembic)

## Database Structure

The database uses the following schemas:

- `app` - Main application data (users, agents, skills, etc.)
- `master` - Master data (LLM providers, model configurations)
- `vectors` - Vector embeddings for semantic search
- `audit` - Audit trails and data changes
- `observability` - Monitoring and logging data
- `agent_mesh` - Alternative schema for some models

## Key Features

- **Vector Search**: Uses pgvector for semantic similarity search
- **Audit Trails**: Comprehensive audit logging for all data changes
- **Multi-schema Design**: Organized data structure with proper schema separation
- **JSON Support**: Extensive use of JSONB for flexible configuration storage
- **Performance**: Optimized indexes including GIN indexes for JSONB columns
- **Default Data**: Includes default users, agent categories, skills, and LLM providers

## Default Users

The system creates two default users:

1. **Admin User**
   - Email: admin@agentmesh.com
   - Username: admin
   - Password: admin123
   - Role: admin

2. **Regular User**
   - Email: user@agentmesh.com
   - Username: user
   - Password: user123
   - Role: developer

## Docker Compose Integration

The database initialization works seamlessly with Docker Compose. The scripts in the `init/` directory are automatically executed when the PostgreSQL container starts for the first time.

## Manual Setup

If you need to manually set up the database:

```bash
# Connect to PostgreSQL as superuser
psql -U postgres -d agentmesh

# Execute scripts in order
\i database/init/01_create_extensions.sql
\i database/init/02_create_schemas.sql
\i database/init/03_create_user.sql
\i database/init/04_grant_permissions.sql
\i database/init/05_create_all_tables.sql
```

## Troubleshooting

If you encounter issues:

1. **Extension not found**: Ensure pgvector extension is installed
2. **Permission denied**: Check user permissions and schema grants
3. **Migration conflicts**: This setup is designed for fresh installations only

## Notes

- The consolidated approach eliminates the need for sequential migrations
- All tables, indexes, and default data are created in a single transaction
- The system uses UUID primary keys throughout for better scalability
- Vector embeddings are configured for 1536 dimensions (compatible with OpenAI embeddings)
