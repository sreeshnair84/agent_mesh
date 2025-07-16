#!/usr/bin/env pwsh
# Clean up old migration structure after consolidation

Write-Host "Cleaning up old migration structure..." -ForegroundColor Green

# Check if migrations directory exists
if (Test-Path "database\migrations") {
    Write-Host "Removing old migrations directory..." -ForegroundColor Yellow
    Remove-Item -Path "database\migrations" -Recurse -Force
    Write-Host "✓ Old migrations directory removed" -ForegroundColor Green
} else {
    Write-Host "No migrations directory found to remove" -ForegroundColor Yellow
}

# Verify backup exists
if (Test-Path "database\backups\migrations_backup") {
    $backupFiles = Get-ChildItem "database\backups\migrations_backup" | Measure-Object
    Write-Host "✓ Migration backup contains $($backupFiles.Count) files" -ForegroundColor Green
} else {
    Write-Host "⚠ Warning: No migration backup found" -ForegroundColor Red
}

# List current init files
Write-Host "`nCurrent init files:" -ForegroundColor Cyan
Get-ChildItem "database\init" | Sort-Object Name | ForEach-Object {
    Write-Host "  $($_.Name)" -ForegroundColor White
}

Write-Host "`nCleanup completed. Database is now configured for fresh installation." -ForegroundColor Green
Write-Host "All migration history has been consolidated into init/05_create_all_tables.sql" -ForegroundColor Green
