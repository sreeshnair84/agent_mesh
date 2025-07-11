#!/bin/bash

# Database Setup Script
# This script sets up the PostgreSQL database with extensions and initial schema

set -e

echo "🗄️  Setting up Agent Mesh database..."

# Load environment variables
if [ -f ".env" ]; then
    source .env
fi

# Database connection parameters
DB_HOST=${POSTGRES_HOST:-localhost}
DB_PORT=${POSTGRES_PORT:-5432}
DB_USER=${POSTGRES_USER:-user}
DB_PASSWORD=${POSTGRES_PASSWORD:-password}
DB_NAME=${POSTGRES_DB:-agentmesh}

# Check if running in Docker
if docker-compose ps | grep -q postgres; then
    echo "🐳 Running database setup in Docker environment..."
    
    # Execute SQL files in Docker container
    for sql_file in database/init/*.sql; do
        if [ -f "$sql_file" ]; then
            echo "📜 Executing $(basename "$sql_file")..."
            docker-compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" -f "/docker-entrypoint-initdb.d/$(basename "$sql_file")"
        fi
    done
    
    # Execute migration files
    for migration_file in database/migrations/*.sql; do
        if [ -f "$migration_file" ]; then
            echo "🔄 Running migration $(basename "$migration_file")..."
            docker-compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" -f "/docker-entrypoint-initdb.d/../migrations/$(basename "$migration_file")" || true
        fi
    done
    
else
    echo "🖥️  Running database setup in local environment..."
    
    # Check if PostgreSQL is running
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
        echo "❌ PostgreSQL is not running or not accessible"
        echo "   Host: $DB_HOST"
        echo "   Port: $DB_PORT"
        echo "   User: $DB_USER"
        exit 1
    fi
    
    # Execute SQL files
    for sql_file in database/init/*.sql; do
        if [ -f "$sql_file" ]; then
            echo "📜 Executing $(basename "$sql_file")..."
            PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$sql_file"
        fi
    done
    
    # Execute migration files
    for migration_file in database/migrations/*.sql; do
        if [ -f "$migration_file" ]; then
            echo "🔄 Running migration $(basename "$migration_file")..."
            PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration_file" || true
        fi
    done
fi

echo "✅ Database setup completed!"

# Verify setup
echo "🔍 Verifying database setup..."

# Check if pgvector extension is installed
if docker-compose ps | grep -q postgres; then
    PGVECTOR_CHECK=$(docker-compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" 2>/dev/null | xargs || echo "0")
else
    PGVECTOR_CHECK=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" 2>/dev/null | xargs || echo "0")
fi

if [ "$PGVECTOR_CHECK" = "1" ]; then
    echo "✅ pgvector extension is installed"
else
    echo "⚠️  pgvector extension is not installed"
fi

echo ""
echo "🎉 Database setup completed successfully!"
echo ""
echo "📊 Database Information:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo ""
echo "🔗 Connection String:"
echo "   postgresql://$DB_USER:****@$DB_HOST:$DB_PORT/$DB_NAME"
