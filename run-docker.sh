#!/bin/bash
# Agent Mesh Docker Management Script

ACTION=""
SERVICE=""

# Function to display help
show_help() {
    echo "Usage: $0 [dev|prod|stop|clean|logs] [service-name]"
    echo ""
    echo "Commands:"
    echo "  dev     Start in development mode (hot-reloading)"
    echo "  prod    Start in production mode (optimized build)"
    echo "  stop    Stop all services"
    echo "  clean   Remove all containers, images, and volumes"
    echo "  logs    Show logs (optional: specify service name)"
    echo ""
    echo "Examples:"
    echo "  $0 dev"
    echo "  $0 logs frontend"
    echo "  $0 prod"
}

# Parse arguments
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

ACTION=$1
SERVICE=$2

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not available. Please install docker-compose."
    exit 1
fi

case $ACTION in
    "dev")
        echo "Starting Agent Mesh in Development Mode..."
        echo "This will:"
        echo "- Use hot-reloading for frontend and backend"
        echo "- Mount source code volumes"
        echo "- Run in development configuration"
        echo ""
        
        # Stop any existing containers
        docker-compose down
        
        # Build and start in development mode
        docker-compose up --build -d
        
        echo "Agent Mesh is starting in development mode..."
        echo "Frontend: http://localhost:3000"
        echo "Backend API: http://localhost:8000"
        echo "Observability: http://localhost:8001"
        echo ""
        echo "Use './run-docker.sh logs' to view logs"
        ;;
    
    "prod")
        echo "Starting Agent Mesh in Production Mode..."
        echo "This will:"
        echo "- Build optimized production images"
        echo "- Use production configuration"
        echo "- No source code volumes"
        echo ""
        
        # Stop any existing containers
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
        
        # Build and start in production mode
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
        
        echo "Agent Mesh is starting in production mode..."
        echo "Frontend: http://localhost:3000"
        echo "Backend API: http://localhost:8000"
        echo "Observability: http://localhost:8001"
        echo ""
        echo "Use './run-docker.sh logs' to view logs"
        ;;
    
    "stop")
        echo "Stopping Agent Mesh..."
        docker-compose down
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
        echo "Agent Mesh stopped."
        ;;
    
    "clean")
        echo "This will remove all containers, images, and volumes for Agent Mesh."
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Cleaning up Agent Mesh..."
            docker-compose down -v --remove-orphans
            docker-compose -f docker-compose.yml -f docker-compose.prod.yml down -v --remove-orphans
            
            # Remove images
            docker images --filter "reference=agent_mesh*" -q | xargs -r docker rmi -f
            
            echo "Cleanup completed."
        else
            echo "Cleanup cancelled."
        fi
        ;;
    
    "logs")
        if [ -n "$SERVICE" ]; then
            echo "Showing logs for service: $SERVICE"
            docker-compose logs -f $SERVICE
        else
            echo "Showing logs for all services (Ctrl+C to exit)"
            docker-compose logs -f
        fi
        ;;
    
    *)
        echo "Error: Unknown action '$ACTION'"
        show_help
        exit 1
        ;;
esac
