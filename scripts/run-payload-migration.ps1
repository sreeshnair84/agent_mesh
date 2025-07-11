#!/usr/bin/env pwsh

<#
.SYNOPSIS
Run database migration to add agent payload specifications

.DESCRIPTION
This script runs the database migration to add input_payload and output_payload columns
to the agents table, enabling the capture of agent interface specifications.

.PARAMETER Environment
The environment to run the migration in (development, staging, production)

.PARAMETER DryRun
If specified, shows what would be done without executing the migration

.EXAMPLE
./run-payload-migration.ps1 -Environment development
#>

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "development",
    
    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "🚀 Agent Payload Migration Script" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Yellow

# Check if we're in the correct directory
if (-not (Test-Path "$ProjectRoot\database\migrations")) {
    Write-Error "❌ Database migrations directory not found. Please run from project root."
    exit 1
}

# Load environment variables
$EnvFile = "$ProjectRoot\.env"
if (Test-Path $EnvFile) {
    Write-Host "📁 Loading environment variables from .env file..." -ForegroundColor Blue
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([^#][^=]*)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# Get database connection details
$DbHost = $env:DB_HOST ?? "localhost"
$DbPort = $env:DB_PORT ?? "5432"
$DbName = $env:DB_NAME ?? "agent_mesh"
$DbUser = $env:DB_USER ?? "postgres"
$DbPassword = $env:DB_PASSWORD ?? "postgres"

$ConnectionString = "host=$DbHost port=$DbPort dbname=$DbName user=$DbUser password=$DbPassword"

Write-Host "📊 Database Connection Details:" -ForegroundColor Blue
Write-Host "  Host: $DbHost" -ForegroundColor Gray
Write-Host "  Port: $DbPort" -ForegroundColor Gray
Write-Host "  Database: $DbName" -ForegroundColor Gray
Write-Host "  User: $DbUser" -ForegroundColor Gray

# Check if psql is available
try {
    $null = Get-Command psql -ErrorAction Stop
    Write-Host "✅ PostgreSQL client (psql) found" -ForegroundColor Green
}
catch {
    Write-Error "❌ PostgreSQL client (psql) not found. Please install PostgreSQL client tools."
    exit 1
}

# Test database connection
Write-Host "🔍 Testing database connection..." -ForegroundColor Blue
try {
    $TestQuery = "SELECT version();"
    $TestResult = psql $ConnectionString -c $TestQuery -t 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database connection successful" -ForegroundColor Green
    } else {
        Write-Error "❌ Database connection failed"
        exit 1
    }
}
catch {
    Write-Error "❌ Database connection test failed: $($_.Exception.Message)"
    exit 1
}

# Check if agents table exists
Write-Host "🔍 Checking if agents table exists..." -ForegroundColor Blue
$TableCheck = psql $ConnectionString -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'agents');" -t 2>$null
if ($TableCheck -like "*t*") {
    Write-Host "✅ Agents table exists" -ForegroundColor Green
} else {
    Write-Error "❌ Agents table does not exist. Please run the initial migration first."
    exit 1
}

# Check if columns already exist
Write-Host "🔍 Checking if payload columns already exist..." -ForegroundColor Blue
$ColumnCheck = psql $ConnectionString -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'agents' AND column_name IN ('input_payload', 'output_payload');" -t 2>$null
if ($ColumnCheck -like "*input_payload*" -and $ColumnCheck -like "*output_payload*") {
    Write-Host "⚠️ Payload columns already exist. Migration may have been run before." -ForegroundColor Yellow
    $Continue = Read-Host "Continue anyway? (y/N)"
    if ($Continue -ne "y" -and $Continue -ne "Y") {
        Write-Host "❌ Migration cancelled by user" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Payload columns do not exist. Ready to migrate." -ForegroundColor Green
}

# Show migration content
$MigrationFile = "$ProjectRoot\database\migrations\003_agent_payload_specs.sql"
if (-not (Test-Path $MigrationFile)) {
    Write-Error "❌ Migration file not found: $MigrationFile"
    exit 1
}

Write-Host "📋 Migration SQL Preview:" -ForegroundColor Blue
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Gray
$MigrationContent = Get-Content $MigrationFile -Raw
Write-Host $MigrationContent -ForegroundColor Gray
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Gray

if ($DryRun) {
    Write-Host "🏃 DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host "✅ Migration validation complete" -ForegroundColor Green
    exit 0
}

# Confirm migration
Write-Host "⚠️ This will modify the database schema." -ForegroundColor Yellow
$Confirm = Read-Host "Continue with migration? (y/N)"
if ($Confirm -ne "y" -and $Confirm -ne "Y") {
    Write-Host "❌ Migration cancelled by user" -ForegroundColor Red
    exit 1
}

# Run migration
Write-Host "🚀 Running agent payload migration..." -ForegroundColor Blue
try {
    # Create a temporary SQL file with the migration
    $TempMigrationFile = "$env:TEMP\agent_payload_migration.sql"
    
    # SQL migration content
    $MigrationSQL = @"
-- Add input_payload and output_payload columns to agents table
ALTER TABLE agents ADD COLUMN IF NOT EXISTS input_payload JSONB;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS output_payload JSONB;

-- Add comments to columns
COMMENT ON COLUMN agents.input_payload IS 'JSON schema for agent input payload specification';
COMMENT ON COLUMN agents.output_payload IS 'JSON schema for agent output payload specification';

-- Create indexes for JSON queries
CREATE INDEX IF NOT EXISTS ix_agents_input_payload_name ON agents USING btree ((input_payload->>'name'));
CREATE INDEX IF NOT EXISTS ix_agents_output_payload_name ON agents USING btree ((output_payload->>'name'));

-- Update existing agents with sample payload schemas (only if they don't have them)
UPDATE agents 
SET input_payload = '{
    "name": "DefaultInput",
    "description": "Default input schema for agent",
    "properties": {
        "query": {
            "type": "string",
            "description": "The input query or prompt for the agent",
            "example": "What is the weather like today?"
        },
        "context": {
            "type": "object",
            "description": "Optional context information",
            "example": {"location": "New York", "user_id": "123"}
        }
    },
    "required": ["query"],
    "examples": [
        {
            "query": "What is the weather like today?",
            "context": {"location": "New York"}
        }
    ]
}'::jsonb,
output_payload = '{
    "name": "DefaultOutput",
    "description": "Default output schema for agent",
    "properties": {
        "response": {
            "type": "string",
            "description": "The agent response",
            "example": "The weather in New York is sunny with a temperature of 75°F."
        },
        "confidence": {
            "type": "number",
            "description": "Confidence score for the response",
            "example": 0.95
        },
        "metadata": {
            "type": "object",
            "description": "Additional metadata about the response",
            "example": {"source": "weather_api", "timestamp": "2024-01-20T12:00:00Z"}
        }
    },
    "required": ["response"],
    "examples": [
        {
            "response": "The weather in New York is sunny with a temperature of 75°F.",
            "confidence": 0.95,
            "metadata": {"source": "weather_api", "timestamp": "2024-01-20T12:00:00Z"}
        }
    ]
}'::jsonb
WHERE input_payload IS NULL AND output_payload IS NULL;

-- Show results
SELECT 
    'Migration completed successfully' AS status,
    COUNT(*) AS total_agents,
    COUNT(input_payload) AS agents_with_input_payload,
    COUNT(output_payload) AS agents_with_output_payload
FROM agents;
"@

    # Write migration to temp file
    $MigrationSQL | Out-File -FilePath $TempMigrationFile -Encoding UTF8
    
    # Execute migration
    $Result = psql $ConnectionString -f $TempMigrationFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Migration completed successfully!" -ForegroundColor Green
        Write-Host "📊 Migration Results:" -ForegroundColor Blue
        Write-Host $Result -ForegroundColor Gray
        
        # Clean up temp file
        Remove-Item $TempMigrationFile -ErrorAction SilentlyContinue
        
        Write-Host "🎉 Agent payload specifications are now ready!" -ForegroundColor Green
        Write-Host "   - input_payload column added to agents table" -ForegroundColor Gray
        Write-Host "   - output_payload column added to agents table" -ForegroundColor Gray
        Write-Host "   - JSON indexes created for efficient queries" -ForegroundColor Gray
        Write-Host "   - Sample payload schemas added to existing agents" -ForegroundColor Gray
        Write-Host "" -ForegroundColor Gray
        Write-Host "🚀 Next steps:" -ForegroundColor Blue
        Write-Host "   1. Update your frontend forms to capture payload specifications" -ForegroundColor Gray
        Write-Host "   2. Test the new payload validation endpoints" -ForegroundColor Gray
        Write-Host "   3. Update agent creation/edit workflows" -ForegroundColor Gray
        
    } else {
        Write-Error "❌ Migration failed with exit code: $LASTEXITCODE"
        exit 1
    }
}
catch {
    Write-Error "❌ Migration failed: $($_.Exception.Message)"
    exit 1
}

Write-Host "🎯 Migration complete! Edit and screen interfaces can now capture agent input/output payload specifications." -ForegroundColor Green
