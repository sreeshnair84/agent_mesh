#!/usr/bin/env pwsh
# Quick fix script for Agent Mesh common issues

Write-Host "Agent Mesh Quick Fix Script" -ForegroundColor Green
Write-Host "This script will help resolve common setup issues." -ForegroundColor Green
Write-Host ""

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file. Please update it with your actual values." -ForegroundColor Green
} else {
    Write-Host "✓ .env file already exists." -ForegroundColor Green
}

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running." -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Fixing common issues..." -ForegroundColor Yellow

# Stop any existing containers and remove them
Write-Host "- Stopping and removing existing containers..." -ForegroundColor Yellow
docker-compose down --remove-orphans 2>$null

# Clean up volumes if requested
Write-Host "The database initialization scripts have been fixed." -ForegroundColor Yellow
Write-Host "To apply the fixes, we need to recreate the database." -ForegroundColor Yellow
$cleanVolumes = Read-Host "Do you want to recreate the database? This will delete all data. (Y/n)"
if ($cleanVolumes -ne "n" -and $cleanVolumes -ne "N") {
    Write-Host "- Cleaning up database volumes..." -ForegroundColor Yellow
    docker-compose down -v --remove-orphans 2>$null
    docker volume prune -f 2>$null
    Write-Host "✓ Database volumes cleaned up." -ForegroundColor Green
}

# Remove old images to ensure fresh build
Write-Host "- Removing old images to ensure fresh build..." -ForegroundColor Yellow
docker images --filter "reference=*frontend*" -q | ForEach-Object { docker rmi $_ -f 2>$null }
docker images --filter "reference=*backend*" -q | ForEach-Object { docker rmi $_ -f 2>$null }
docker images --filter "reference=*observability*" -q | ForEach-Object { docker rmi $_ -f 2>$null }

# Rebuild containers with no cache
Write-Host "- Rebuilding containers with no cache..." -ForegroundColor Yellow
docker-compose build --no-cache --parallel

# Start services
Write-Host "- Starting services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check service status
Write-Host "Checking service status..." -ForegroundColor Yellow
$services = @("postgres", "redis", "backend", "observability", "frontend")

foreach ($service in $services) {
    $status = docker-compose ps --services --filter "status=running" | Where-Object { $_ -eq $service }
    if ($status) {
        Write-Host "✓ $service is running" -ForegroundColor Green
    } else {
        Write-Host "✗ $service is not running" -ForegroundColor Red
        Write-Host "  Checking logs for $service..." -ForegroundColor Yellow
        docker-compose logs --tail=10 $service
    }
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "Services should be available at:" -ForegroundColor Cyan
Write-Host "- Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "- Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "- API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "- Observability: http://localhost:8001" -ForegroundColor Cyan
Write-Host ""
Write-Host "If services are not running, check the logs with:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f [service-name]" -ForegroundColor Yellow
Write-Host ""
Write-Host "For development mode (hot reloading):" -ForegroundColor Yellow
Write-Host "  .\run-docker.ps1 dev" -ForegroundColor Yellow
