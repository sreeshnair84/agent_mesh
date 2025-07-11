<#
.SYNOPSIS
    Database Setup Script for Agent Mesh (PowerShell version)
#>

# Load environment variables from .env if present
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Variable -Name $name -Value $value -Scope Script
        }
    }
}

$DB_HOST = $env:POSTGRES_HOST ? $env:POSTGRES_HOST : "localhost"
$DB_PORT = $env:POSTGRES_PORT ? $env:POSTGRES_PORT : "5432"
$DB_USER = $env:POSTGRES_USER ? $env:POSTGRES_USER : "user"
$DB_PASSWORD = $env:POSTGRES_PASSWORD ? $env:POSTGRES_PASSWORD : "password"
$DB_NAME = $env:POSTGRES_DB ? $env:POSTGRES_DB : "agentmesh"

Write-Host "🗄️  Setting up Agent Mesh database..."

# Check if running in Docker
$inDocker = docker-compose ps | Select-String "postgres"
if ($inDocker) {
    Write-Host "🐳 Running database setup in Docker environment..."
    Get-ChildItem "database/init/*.sql" | ForEach-Object {
        Write-Host "📜 Executing $($_.Name)..."
        docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -f "/docker-entrypoint-initdb.d/$($_.Name)"
    }
    Get-ChildItem "database/migrations/*.sql" | ForEach-Object {
        Write-Host "🔄 Running migration $($_.Name)..."
        docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -f "/docker-entrypoint-initdb.d/../migrations/$($_.Name)"
    }
} else {
    Write-Host "🖥️  Running database setup in local environment..."
    $ready = & pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ PostgreSQL is not running or not accessible"
        Write-Host "   Host: $DB_HOST"
        Write-Host "   Port: $DB_PORT"
        Write-Host "   User: $DB_USER"
        exit 1
    }
    Get-ChildItem "database/init/*.sql" | ForEach-Object {
        Write-Host "📜 Executing $($_.Name)..."
        $env:PGPASSWORD = $DB_PASSWORD
        & psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $_.FullName
    }
    Get-ChildItem "database/migrations/*.sql" | ForEach-Object {
        Write-Host "🔄 Running migration $($_.Name)..."
        $env:PGPASSWORD = $DB_PASSWORD
        & psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $_.FullName
    }
}

Write-Host "✅ Database setup completed!"
Write-Host "🔍 Verifying database setup..."

# Check if pgvector extension is installed
if ($inDocker) {
    $pgvector = docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -t -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" 2>$null
} else {
    $env:PGPASSWORD = $DB_PASSWORD
    $pgvector = & psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" 2>$null
}
if ($pgvector -match "1") {
    Write-Host "✅ pgvector extension is installed"
} else {
    Write-Host "⚠️  pgvector extension is not installed"
}

Write-Host ""
Write-Host "🎉 Database setup completed successfully!"
Write-Host ""
Write-Host "📊 Database Information:"
Write-Host "   Host: $DB_HOST"
Write-Host "   Port: $DB_PORT"
Write-Host "   Database: $DB_NAME"
Write-Host "   User: $DB_USER"
Write-Host ""
Write-Host "🔗 Connection String:"
Write-Host "   postgresql://$DB_USER:****@$DB_HOST:$DB_PORT/$DB_NAME"
