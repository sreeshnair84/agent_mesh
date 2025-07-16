#!/usr/bin/env pwsh
# Clean PostgreSQL setup script
# This script will stop containers, remove volumes, and start fresh

Write-Host "Starting fresh PostgreSQL setup..." -ForegroundColor Green

# Stop all containers
Write-Host "Stopping all containers..." -ForegroundColor Yellow
docker-compose down

# Remove PostgreSQL volume to ensure fresh start
Write-Host "Removing PostgreSQL volume..." -ForegroundColor Yellow
docker volume rm agent_mesh_postgres_data 2>$null
docker volume rm agentmesh_postgres_data 2>$null

# Remove any existing containers
Write-Host "Removing existing containers..." -ForegroundColor Yellow
docker-compose rm -f

# Start only PostgreSQL to initialize database
Write-Host "Starting PostgreSQL container..." -ForegroundColor Yellow
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
Write-Host "Waiting for PostgreSQL to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if PostgreSQL is ready
$maxAttempts = 30
$attempt = 0
$isReady = $false

while ($attempt -lt $maxAttempts -and -not $isReady) {
    try {
        $result = docker-compose exec postgres pg_isready -U agentmesh_user -d agentmesh
        if ($result -match "accepting connections") {
            $isReady = $true
            Write-Host "✓ PostgreSQL is ready!" -ForegroundColor Green
        }
    } catch {
        # Continue waiting
    }
    
    if (-not $isReady) {
        $attempt++
        Write-Host "Waiting... ($attempt/$maxAttempts)" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if (-not $isReady) {
    Write-Host "✗ PostgreSQL failed to start within timeout" -ForegroundColor Red
    Write-Host "Checking logs..." -ForegroundColor Yellow
    docker-compose logs postgres
    exit 1
}

# Show initialization logs
Write-Host "`nDatabase initialization logs:" -ForegroundColor Cyan
docker-compose logs postgres | Select-String -Pattern "CREATE|INSERT|GRANT|Database initialized"

# Verify database setup
Write-Host "`nVerifying database setup..." -ForegroundColor Cyan
docker-compose exec postgres psql -U agentmesh_user -d agentmesh -c "SELECT 'Database setup verified' as status, (SELECT COUNT(*) FROM app.users) as users, (SELECT COUNT(*) FROM app.skills) as skills, (SELECT COUNT(*) FROM app.agent_categories) as categories;"

Write-Host "`n✓ Fresh PostgreSQL setup completed successfully!" -ForegroundColor Green
Write-Host "You can now start all services with: docker-compose up" -ForegroundColor White
