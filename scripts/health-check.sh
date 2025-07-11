#!/bin/bash

# Health Check Script
# This script checks the health of all Agent Mesh services

set -e

echo "🏥 Running Agent Mesh Health Check..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Health check function
check_service() {
    local service_name="$1"
    local url="$2"
    local timeout="${3:-10}"
    
    echo -n "🔍 Checking $service_name... "
    
    if curl -s --max-time "$timeout" "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Unhealthy${NC}"
        return 1
    fi
}

# Check database connection
check_database() {
    echo -n "🔍 Checking PostgreSQL... "
    
    if docker-compose exec -T postgres pg_isready -U ${POSTGRES_USER:-user} -d ${POSTGRES_DB:-agentmesh} > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Unhealthy${NC}"
        return 1
    fi
}

# Check Redis connection
check_redis() {
    echo -n "🔍 Checking Redis... "
    
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Unhealthy${NC}"
        return 1
    fi
}

# Check Docker containers
check_containers() {
    echo "🐳 Checking Docker containers..."
    
    local containers=("postgres" "redis" "backend" "observability" "frontend")
    local all_healthy=true
    
    for container in "${containers[@]}"; do
        echo -n "🔍 Checking $container container... "
        
        if docker-compose ps | grep -q "${container}.*Up"; then
            echo -e "${GREEN}✅ Running${NC}"
        else
            echo -e "${RED}❌ Not running${NC}"
            all_healthy=false
        fi
    done
    
    return $all_healthy
}

# Main health check
main() {
    local all_healthy=true
    
    echo "🏥 Agent Mesh Health Check Report"
    echo "=================================="
    echo ""
    
    # Check containers
    if ! check_containers; then
        all_healthy=false
    fi
    
    echo ""
    echo "🔗 Service Health Checks:"
    echo "-------------------------"
    
    # Check database
    if ! check_database; then
        all_healthy=false
    fi
    
    # Check Redis
    if ! check_redis; then
        all_healthy=false
    fi
    
    # Check backend API
    if ! check_service "Backend API" "http://localhost:8000/health"; then
        all_healthy=false
    fi
    
    # Check observability service
    if ! check_service "Observability" "http://localhost:8001/health"; then
        all_healthy=false
    fi
    
    # Check frontend
    if ! check_service "Frontend" "http://localhost:3000" 15; then
        all_healthy=false
    fi
    
    echo ""
    echo "📊 Detailed Service Information:"
    echo "-------------------------------"
    
    # Get service versions and info
    echo "🔍 Backend API Info:"
    curl -s http://localhost:8000/health 2>/dev/null | jq '.' 2>/dev/null || echo "   Unable to fetch info"
    
    echo ""
    echo "🔍 Observability Info:"
    curl -s http://localhost:8001/health 2>/dev/null | jq '.' 2>/dev/null || echo "   Unable to fetch info"
    
    echo ""
    echo "🔍 Container Status:"
    docker-compose ps
    
    echo ""
    
    if [ "$all_healthy" = true ]; then
        echo -e "${GREEN}🎉 All services are healthy!${NC}"
        echo ""
        echo "📊 Service URLs:"
        echo "   Frontend:      http://localhost:3000"
        echo "   Backend API:   http://localhost:8000"
        echo "   API Docs:      http://localhost:8000/docs"
        echo "   Observability: http://localhost:8001"
        echo "   Metrics:       http://localhost:8001/metrics"
        exit 0
    else
        echo -e "${RED}❌ Some services are unhealthy!${NC}"
        echo ""
        echo "🔧 Troubleshooting:"
        echo "   - Check logs: docker-compose logs -f [service-name]"
        echo "   - Restart services: docker-compose restart [service-name]"
        echo "   - Check .env file configuration"
        echo "   - Ensure all required environment variables are set"
        exit 1
    fi
}

# Run main function
main "$@"
