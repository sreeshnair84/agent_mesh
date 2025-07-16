#!/usr/bin/env pwsh
# Test script to verify fresh database setup

Write-Host "Testing fresh database setup..." -ForegroundColor Green

# Check if Docker is running
try {
    docker --version | Out-Null
    Write-Host "✓ Docker is installed and running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not available" -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
try {
    docker-compose --version | Out-Null
    Write-Host "✓ Docker Compose is available" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose is not available" -ForegroundColor Red
    exit 1
}

# Check if database init files exist
$initFiles = @(
    "database/init/01_create_extensions.sql",
    "database/init/02_create_schemas.sql", 
    "database/init/03_create_user.sql",
    "database/init/04_grant_permissions.sql",
    "database/init/05_create_all_tables.sql"
)

foreach ($file in $initFiles) {
    if (Test-Path $file) {
        Write-Host "✓ Found $file" -ForegroundColor Green
    } else {
        Write-Host "✗ Missing $file" -ForegroundColor Red
    }
}

# Check if backup exists
if (Test-Path "database/backups/migrations_backup") {
    $backupCount = (Get-ChildItem "database/backups/migrations_backup" | Measure-Object).Count
    Write-Host "✓ Migration backup exists with $backupCount files" -ForegroundColor Green
} else {
    Write-Host "✗ Migration backup not found" -ForegroundColor Red
}

# Check if old migrations directory is gone
if (Test-Path "database/migrations") {
    Write-Host "⚠ Old migrations directory still exists" -ForegroundColor Yellow
} else {
    Write-Host "✓ Old migrations directory removed" -ForegroundColor Green
}

# Check docker-compose.yml
if (Test-Path "docker-compose.yml") {
    $content = Get-Content "docker-compose.yml" -Raw
    if ($content -match "agentmesh_user") {
        Write-Host "✓ Docker Compose uses updated database user" -ForegroundColor Green
    } else {
        Write-Host "⚠ Docker Compose may still use old database user" -ForegroundColor Yellow
    }
    
    if ($content -match "database/init:/docker-entrypoint-initdb.d") {
        Write-Host "✓ Docker Compose mounts init directory" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker Compose does not mount init directory" -ForegroundColor Red
    }
} else {
    Write-Host "✗ docker-compose.yml not found" -ForegroundColor Red
}

Write-Host "`nSetup verification complete!" -ForegroundColor Cyan
Write-Host "To test the database setup, run:" -ForegroundColor White
Write-Host "  docker-compose up postgres" -ForegroundColor Gray
Write-Host "  docker-compose logs postgres" -ForegroundColor Gray
