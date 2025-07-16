#!/bin/bash

# Fix Database Schema Issues Script
# This script helps fix database schema issues by rebuilding containers

echo "🔧 Fixing Agent Mesh Database Schema Issues..."

echo "1. Stopping all services..."
docker-compose down

echo "2. Removing database volume to start fresh..."
docker volume rm agent_mesh_postgres_data 2>/dev/null || echo "Volume already removed or doesn't exist"

echo "3. Rebuilding and starting services..."
docker-compose up -d --build

echo "4. Waiting for database to be ready..."
sleep 10

echo "5. Checking database status..."
docker-compose exec postgres pg_isready -U user -d agentmesh

echo "6. Checking schemas..."
docker-compose exec postgres psql -U user -d agentmesh -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('app', 'agent_mesh', 'observability', 'vectors', 'audit', 'master');"

echo "✅ Database schema fix completed!"
echo "🚀 You can now test the application"
