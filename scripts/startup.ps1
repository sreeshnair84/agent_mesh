<#
.SYNOPSIS
    Agent Mesh Startup Script (PowerShell version)
#>

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ .env file created. Please edit it with your configuration."
    Write-Host "💡 Update the following variables in .env:"
    Write-Host "   - AZURE_OPENAI_API_KEY"
    Write-Host "   - AZURE_OPENAI_ENDPOINT"
    Write-Host "   - GEMINI_API_KEY"
    Write-Host "   - CLAUDE_API_KEY"
    Write-Host "   - SECRET_KEY"
    Write-Host ""
    Write-Host "🛑 Please update .env file and run this script again."
    exit 1
}

Write-Host "🔧 Setting up environment..."
New-Item -ItemType Directory -Force -Path logs,uploads,"database/backups" | Out-Null
Get-ChildItem scripts -Filter *.sh | ForEach-Object { icacls $_.FullName /grant Everyone:F | Out-Null }

Write-Host "🐳 Starting Docker containers..."
docker-compose up -d --build

Write-Host "⏳ Waiting for services to be ready..."

# Wait for PostgreSQL
Write-Host "🔍 Checking PostgreSQL connection..."
$timeout = 60
while ($timeout -gt 0) {
    $result = docker-compose exec -T postgres pg_isready -U $env:POSTGRES_USER -d $env:POSTGRES_DB
    if ($LASTEXITCODE -eq 0) { break }
    Start-Sleep -Seconds 2
    $timeout -= 2
    Write-Host "⏳ Waiting for PostgreSQL... ($timeout seconds remaining)"
}
if ($timeout -le 0) { Write-Host "❌ PostgreSQL failed to start within 60 seconds"; exit 1 }
Write-Host "✅ PostgreSQL is ready!"

# Wait for Redis
Write-Host "🔍 Checking Redis connection..."
$timeout = 30
while ($timeout -gt 0) {
    $result = docker-compose exec -T redis redis-cli ping
    if ($result -match "PONG") { break }
    Start-Sleep -Seconds 2
    $timeout -= 2
    Write-Host "⏳ Waiting for Redis... ($timeout seconds remaining)"
}
if ($timeout -le 0) { Write-Host "❌ Redis failed to start within 30 seconds"; exit 1 }
Write-Host "✅ Redis is ready!"

# Setup database
Write-Host "🗄️  Setting up database..."
.\scripts\setup-db.ps1

# Wait for Backend API
Write-Host "🔍 Checking Backend API..."
$timeout = 60
while ($timeout -gt 0) {
    try { $null = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5; break } catch {}
    Start-Sleep -Seconds 2
    $timeout -= 2
    Write-Host "⏳ Waiting for Backend API... ($timeout seconds remaining)"
}
if ($timeout -le 0) { Write-Host "❌ Backend API failed to start within 60 seconds"; exit 1 }
Write-Host "✅ Backend API is ready!"

# Wait for Observability
Write-Host "🔍 Checking Observability service..."
$timeout = 60
while ($timeout -gt 0) {
    try { $null = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing -TimeoutSec 5; break } catch {}
    Start-Sleep -Seconds 2
    $timeout -= 2
    Write-Host "⏳ Waiting for Observability service... ($timeout seconds remaining)"
}
if ($timeout -le 0) { Write-Host "❌ Observability service failed to start within 60 seconds"; exit 1 }
Write-Host "✅ Observability service is ready!"

# Wait for Frontend
Write-Host "🔍 Checking Frontend application..."
$timeout = 90
while ($timeout -gt 0) {
    try { $null = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5; break } catch {}
    Start-Sleep -Seconds 3
    $timeout -= 3
    Write-Host "⏳ Waiting for Frontend application... ($timeout seconds remaining)"
}
if ($timeout -le 0) { Write-Host "❌ Frontend application failed to start within 90 seconds"; exit 1 }
Write-Host "✅ Frontend application is ready!"

# Run health check
Write-Host "🏥 Running health check..."
.\scripts\health-check.ps1

Write-Host ""
Write-Host "🎉 Agent Mesh Application is now running!"
Write-Host ""
Write-Host "📊 Service URLs:"
Write-Host "   Frontend:      http://localhost:3000"
Write-Host "   Backend API:   http://localhost:8000"
Write-Host "   API Docs:      http://localhost:8000/docs"
Write-Host "   Observability: http://localhost:8001"
Write-Host "   Metrics:       http://localhost:8001/metrics"
Write-Host ""
Write-Host "🗄️  Database URLs:"
Write-Host "   PostgreSQL:    localhost:5432"
Write-Host "   Redis:         localhost:6379"
Write-Host ""
Write-Host "📝 Logs:"
Write-Host "   View logs: docker-compose logs -f [service-name]"
Write-Host "   All logs:  docker-compose logs -f"
Write-Host ""
Write-Host "🛑 To stop all services:"
Write-Host "   docker-compose down"
Write-Host ""
Write-Host "✨ Happy coding!"
