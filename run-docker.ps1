#!/usr/bin/env pwsh
# Agent Mesh Docker Management Script

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "prod", "stop", "clean", "logs")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [string]$Service = ""
)

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

# Check if Docker is running
try {
    docker info | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker is not running. Please start Docker Desktop."
        exit 1
    }
} catch {
    Write-Error "Docker is not available. Please install Docker Desktop."
    exit 1
}

# Check if docker-compose is available
try {
    docker-compose --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "docker-compose is not available. Please install docker-compose."
        exit 1
    }
} catch {
    Write-Error "docker-compose is not available. Please install docker-compose."
    exit 1
}

switch ($Action) {
    "dev" {
        Write-Info "Starting Agent Mesh in Development Mode..."
        Write-Info "This will:"
        Write-Info "- Use hot-reloading for frontend and backend"
        Write-Info "- Mount source code volumes"
        Write-Info "- Run in development configuration"
        Write-Info ""
        
        # Stop any existing containers
        docker-compose down
        
        # Build and start in development mode
        docker-compose up --build -d
        
        Write-Info "Agent Mesh is starting in development mode..."
        Write-Info "Frontend: http://localhost:3000"
        Write-Info "Backend API: http://localhost:8000"
        Write-Info "Observability: http://localhost:8001"
        Write-Info ""
        Write-Info "Use 'pwsh run-docker.ps1 logs' to view logs"
    }
    
    "prod" {
        Write-Info "Starting Agent Mesh in Production Mode..."
        Write-Info "This will:"
        Write-Info "- Build optimized production images"
        Write-Info "- Use production configuration"
        Write-Info "- No source code volumes"
        Write-Info ""
        
        # Stop any existing containers
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
        
        # Build and start in production mode
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
        
        Write-Info "Agent Mesh is starting in production mode..."
        Write-Info "Frontend: http://localhost:3000"
        Write-Info "Backend API: http://localhost:8000"
        Write-Info "Observability: http://localhost:8001"
        Write-Info ""
        Write-Info "Use 'pwsh run-docker.ps1 logs' to view logs"
    }
    
    "stop" {
        Write-Info "Stopping Agent Mesh..."
        docker-compose down
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
        Write-Info "Agent Mesh stopped."
    }
    
    "clean" {
        Write-Warning "This will remove all containers, images, and volumes for Agent Mesh."
        $confirm = Read-Host "Are you sure? (y/N)"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            Write-Info "Cleaning up Agent Mesh..."
            docker-compose down -v --remove-orphans
            docker-compose -f docker-compose.yml -f docker-compose.prod.yml down -v --remove-orphans
            
            # Remove images
            docker images --filter "reference=agent_mesh*" -q | ForEach-Object { docker rmi $_ -f }
            
            Write-Info "Cleanup completed."
        } else {
            Write-Info "Cleanup cancelled."
        }
    }
    
    "logs" {
        if ($Service) {
            Write-Info "Showing logs for service: $Service"
            docker-compose logs -f $Service
        } else {
            Write-Info "Showing logs for all services (Ctrl+C to exit)"
            docker-compose logs -f
        }
    }
}
