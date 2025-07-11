<#
.SYNOPSIS
    Health Check Script for Agent Mesh services (PowerShell version)
#>

function Check-Service($name, $url, $timeout=10) {
    Write-Host "🔍 Checking $name... " -NoNewline
    try {
        $null = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec $timeout
        Write-Host "✅ Healthy"
        return $true
    } catch {
        Write-Host "❌ Unhealthy"
        return $false
    }
}

function Check-Container($container) {
    Write-Host "🔍 Checking $container container... " -NoNewline
    $result = docker-compose ps | Select-String "$container.*Up"
    if ($result) {
        Write-Host "✅ Running"
        return $true
    } else {
        Write-Host "❌ Not running"
        return $false
    }
}

Write-Host "🏥 Running Agent Mesh Health Check..."
$allHealthy = $true

$containers = @("postgres", "redis", "backend", "observability", "frontend")
foreach ($c in $containers) {
    if (-not (Check-Container $c)) { $allHealthy = $false }
}

Write-Host ""
Write-Host "🔗 Service Health Checks:"
if (-not (Check-Service "Backend API" "http://localhost:8000/health")) { $allHealthy = $false }
if (-not (Check-Service "Observability" "http://localhost:8001/health")) { $allHealthy = $false }
if (-not (Check-Service "Frontend" "http://localhost:3000" 15)) { $allHealthy = $false }

Write-Host ""
Write-Host "📊 Detailed Service Information:"
Write-Host "🔍 Backend API Info:"
try { Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Select-Object -ExpandProperty Content } catch { Write-Host "   Unable to fetch info" }
Write-Host ""
Write-Host "🔍 Observability Info:"
try { Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing | Select-Object -ExpandProperty Content } catch { Write-Host "   Unable to fetch info" }
Write-Host ""
Write-Host "🔍 Container Status:"
docker-compose ps

if ($allHealthy) {
    Write-Host "🎉 All services are healthy!"
    Write-Host ""
    Write-Host "📊 Service URLs:"
    Write-Host "   Frontend:      http://localhost:3000"
    Write-Host "   Backend API:   http://localhost:8000"
    Write-Host "   API Docs:      http://localhost:8000/docs"
    Write-Host "   Observability: http://localhost:8001"
    Write-Host "   Metrics:       http://localhost:8001/metrics"
    exit 0
} else {
    Write-Host "❌ Some services are unhealthy!"
    Write-Host ""
    Write-Host "🔧 Troubleshooting:"
    Write-Host "   - Check logs: docker-compose logs -f [service-name]"
    Write-Host "   - Restart services: docker-compose restart [service-name]"
    Write-Host "   - Check .env file configuration"
    Write-Host "   - Ensure all required environment variables are set"
    exit 1
}
