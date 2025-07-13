#!/bin/bash
# Quick fix script for Agent Mesh common issues

echo "Agent Mesh Quick Fix Script"
echo "This script will help resolve common setup issues."
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file. Please update it with your actual values."
else
    echo "✓ .env file already exists."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "✗ Docker is not running. Please start Docker."
    exit 1
fi
echo "✓ Docker is running."

echo ""
echo "Fixing common issues..."

# Stop any existing containers and remove them
echo "- Stopping and removing existing containers..."
docker-compose down --remove-orphans 2>/dev/null

# Clean up volumes if requested
echo "The database initialization scripts have been fixed."
echo "To apply the fixes, we need to recreate the database."
echo "Do you want to recreate the database? This will delete all data. (Y/n)"
read -r cleanVolumes
if [[ $cleanVolumes != "n" && $cleanVolumes != "N" ]]; then
    echo "- Cleaning up database volumes..."
    docker-compose down -v --remove-orphans 2>/dev/null
    docker volume prune -f 2>/dev/null
    echo "✓ Database volumes cleaned up."
fi

# Remove old images to ensure fresh build
echo "- Removing old images to ensure fresh build..."
docker images --filter "reference=*frontend*" -q | xargs -r docker rmi -f 2>/dev/null
docker images --filter "reference=*backend*" -q | xargs -r docker rmi -f 2>/dev/null
docker images --filter "reference=*observability*" -q | xargs -r docker rmi -f 2>/dev/null

# Rebuild containers with no cache
echo "- Rebuilding containers with no cache..."
docker-compose build --no-cache --parallel

# Start services
echo "- Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 15

# Check service status
echo "Checking service status..."
services=("postgres" "redis" "backend" "observability" "frontend")

for service in "${services[@]}"; do
    if docker-compose ps --services --filter "status=running" | grep -q "^$service$"; then
        echo "✓ $service is running"
    else
        echo "✗ $service is not running"
        echo "  Checking logs for $service..."
        docker-compose logs --tail=10 $service
    fi
done

echo ""
echo "Setup complete!"
echo "Services should be available at:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- Observability: http://localhost:8001"
echo ""
echo "If services are not running, check the logs with:"
echo "  docker-compose logs -f [service-name]"
echo ""
echo "For development mode (hot reloading):"
echo "  ./run-docker.sh dev"
