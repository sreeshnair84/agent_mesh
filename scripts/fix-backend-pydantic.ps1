# Fix Backend Pydantic Issues Script
# This script helps fix backend Pydantic issues and restart services

Write-Host "🔧 Fixing Agent Mesh Backend Pydantic Issues..." -ForegroundColor Green

Write-Host "1. Stopping all services..." -ForegroundColor Yellow
docker-compose down

Write-Host "2. Rebuilding backend with fixes..." -ForegroundColor Yellow
docker-compose build backend

Write-Host "3. Starting services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "4. Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host "5. Checking backend logs..." -ForegroundColor Yellow
docker-compose logs backend --tail=20

Write-Host "6. Checking service health..." -ForegroundColor Yellow
docker-compose ps

Write-Host "✅ Backend Pydantic fix completed!" -ForegroundColor Green
Write-Host "🚀 You can now test the application" -ForegroundColor Green
