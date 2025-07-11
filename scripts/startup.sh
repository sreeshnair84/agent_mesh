#!/bin/bash

# Agent Mesh Startup Script
# This script initializes and starts all services for the Agent Mesh application

set -e

echo "🚀 Starting Agent Mesh Application..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your configuration."
    echo "💡 Update the following variables in .env:"
    echo "   - AZURE_OPENAI_API_KEY"
    echo "   - AZURE_OPENAI_ENDPOINT"
    echo "   - GEMINI_API_KEY"
    echo "   - CLAUDE_API_KEY"
    echo "   - SECRET_KEY"
    echo ""
    echo "🛑 Please update .env file and run this script again."
    exit 1
fi

# Load environment variables
source .env

echo "🔧 Setting up environment..."

# Create necessary directories
mkdir -p logs uploads database/backups

# Set permissions
chmod +x scripts/*.sh

echo "🐳 Starting Docker containers..."

# Build and start services
docker-compose up -d --build

echo "⏳ Waiting for services to be ready..."

# Wait for PostgreSQL to be ready
echo "🔍 Checking PostgreSQL connection..."
timeout=60
while ! docker-compose exec -T postgres pg_isready -U ${POSTGRES_USER:-user} -d ${POSTGRES_DB:-agentmesh} > /dev/null 2>&1; do
    if [ $timeout -le 0 ]; then
        echo "❌ PostgreSQL failed to start within 60 seconds"
        exit 1
    fi
    echo "⏳ Waiting for PostgreSQL... ($timeout seconds remaining)"
    sleep 2
    timeout=$((timeout - 2))
done

echo "✅ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "🔍 Checking Redis connection..."
timeout=30
while ! docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    if [ $timeout -le 0 ]; then
        echo "❌ Redis failed to start within 30 seconds"
        exit 1
    fi
    echo "⏳ Waiting for Redis... ($timeout seconds remaining)"
    sleep 2
    timeout=$((timeout - 2))
done

echo "✅ Redis is ready!"

# Setup database
echo "🗄️  Setting up database..."
./scripts/setup-db.sh

# Wait for backend to be ready
echo "🔍 Checking Backend API..."
timeout=60
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    if [ $timeout -le 0 ]; then
        echo "❌ Backend API failed to start within 60 seconds"
        exit 1
    fi
    echo "⏳ Waiting for Backend API... ($timeout seconds remaining)"
    sleep 2
    timeout=$((timeout - 2))
done

echo "✅ Backend API is ready!"

# Wait for observability service to be ready
echo "🔍 Checking Observability service..."
timeout=60
while ! curl -s http://localhost:8001/health > /dev/null 2>&1; do
    if [ $timeout -le 0 ]; then
        echo "❌ Observability service failed to start within 60 seconds"
        exit 1
    fi
    echo "⏳ Waiting for Observability service... ($timeout seconds remaining)"
    sleep 2
    timeout=$((timeout - 2))
done

echo "✅ Observability service is ready!"

# Wait for frontend to be ready
echo "🔍 Checking Frontend application..."
timeout=90
while ! curl -s http://localhost:3000 > /dev/null 2>&1; do
    if [ $timeout -le 0 ]; then
        echo "❌ Frontend application failed to start within 90 seconds"
        exit 1
    fi
    echo "⏳ Waiting for Frontend application... ($timeout seconds remaining)"
    sleep 3
    timeout=$((timeout - 3))
done

echo "✅ Frontend application is ready!"

# Run health check
echo "🏥 Running health check..."
./scripts/health-check.sh

echo ""
echo "🎉 Agent Mesh Application is now running!"
echo ""
echo "📊 Service URLs:"
echo "   Frontend:      http://localhost:3000"
echo "   Backend API:   http://localhost:8000"
echo "   API Docs:      http://localhost:8000/docs"
echo "   Observability: http://localhost:8001"
echo "   Metrics:       http://localhost:8001/metrics"
echo ""
echo "🗄️  Database URLs:"
echo "   PostgreSQL:    localhost:5432"
echo "   Redis:         localhost:6379"
echo ""
echo "📝 Logs:"
echo "   View logs: docker-compose logs -f [service-name]"
echo "   All logs:  docker-compose logs -f"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
echo ""
echo "✨ Happy coding!"
