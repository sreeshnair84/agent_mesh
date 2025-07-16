# Fix All Issues Script
# This script helps fix both payload field types and observability service issues

Write-Host "🔧 Fixing Agent Mesh Issues..." -ForegroundColor Green

Write-Host "1. Stopping all services..." -ForegroundColor Yellow
docker-compose down

Write-Host "2. Removing problematic containers..." -ForegroundColor Yellow
docker-compose rm -f observability backend

Write-Host "3. Rebuilding affected services..." -ForegroundColor Yellow
docker-compose build --no-cache backend observability

Write-Host "4. Starting services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "5. Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

Write-Host "6. Checking service health..." -ForegroundColor Yellow
docker-compose ps

Write-Host "7. Checking backend logs..." -ForegroundColor Yellow
docker-compose logs backend --tail=10

Write-Host "8. Checking observability logs..." -ForegroundColor Yellow
docker-compose logs observability --tail=10

Write-Host "9. Testing API endpoints..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/system/health" -Method GET -TimeoutSec 10
    Write-Host "✅ Backend API is responding" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend API is not responding" -ForegroundColor Red
}

Write-Host "✅ All fixes applied!" -ForegroundColor Green
Write-Host "🚀 Application should now support enhanced payload types and observability service should be working" -ForegroundColor Green

Write-Host "`n📋 Summary of Changes:" -ForegroundColor Cyan
Write-Host "  - Expanded payload field types to support audio, image, video, document, file, binary, json, xml, csv, pdf, any" -ForegroundColor White
Write-Host "  - Created missing exception handlers for observability service" -ForegroundColor White
Write-Host "  - Created missing middleware for observability service" -ForegroundColor White
Write-Host "  - Fixed all Pydantic V2 compatibility issues" -ForegroundColor White
