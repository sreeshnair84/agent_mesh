# Fix Database Schema Issues Script (PowerShell)
# This script helps fix database schema issues by rebuilding containers

Write-Host "🔧 Fixing Agent Mesh Database Schema Issues..." -ForegroundColor Green

Write-Host "1. Stopping all services..." -ForegroundColor Yellow
docker-compose down

Write-Host "2. Removing database volume to start fresh..." -ForegroundColor Yellow
docker volume rm agent_mesh_postgres_data 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Volume already removed or doesn't exist" -ForegroundColor Gray
}

Write-Host "3. Rebuilding and starting services..." -ForegroundColor Yellow
docker-compose up -d --build

Write-Host "4. Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "5. Checking database status..." -ForegroundColor Yellow
docker-compose exec postgres pg_isready -U user -d agentmesh

Write-Host "6. Checking schemas..." -ForegroundColor Yellow
docker-compose exec postgres psql -U user -d agentmesh -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('app', 'agent_mesh', 'observability', 'vectors', 'audit', 'master');"

Write-Host "✅ Database schema fix completed!" -ForegroundColor Green
Write-Host "🚀 You can now test the application" -ForegroundColor Cyan
