<#
.SYNOPSIS
    Agent Deployment Script for Agent Mesh platform (PowerShell version)
#>

param(
    [Parameter(Mandatory=$true)][string]$Name,
    [string]$Template,
    [string]$Config,
    [string]$Description
)

function Show-Usage {
    Write-Host "Usage: .\deploy-agent.ps1 -Name <AgentName> [-Template <Template>] [-Config <ConfigFile>] [-Description <Description>]"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\deploy-agent.ps1 -Name my-agent -Template crag"
    Write-Host "  .\deploy-agent.ps1 -Name my-agent -Config .\config.yaml"
    exit 1
}

if (-not $Name) { Show-Usage }

# Check if backend is running
try {
    $null = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
} catch {
    Write-Host "❌ Error: Backend API is not running"
    Write-Host "   Please start the services first: .\startup.ps1"
    exit 1
}

Write-Host "🚀 Deploying agent: $Name"

# Build payload
$payload = @{ name = $Name }
if ($Description) { $payload.description = $Description }
if ($Template) { $payload.template = $Template }
if ($Config -and (Test-Path $Config)) {
    Write-Host "📄 Reading configuration from: $Config"
    $configContent = Get-Content $Config -Raw
    $payload.config = $configContent
}
$jsonPayload = $payload | ConvertTo-Json -Depth 10

# Deploy the agent
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/agents/" -Method Post -ContentType "application/json" -Body $jsonPayload

if ($response.id) {
    Write-Host "✅ Agent deployed successfully!"
    Write-Host "   Agent ID: $($response.id)"
    Write-Host "   Agent Name: $Name"
    Write-Host "   Agent URL: http://localhost:8000/api/v1/agents/$($response.id)"
    Write-Host ""
    Write-Host "🎉 Agent is now available in the Agent Mesh platform!"
    Write-Host "📊 View in dashboard: http://localhost:3000/agent-marketplace"
    Write-Host ""
    Write-Host "📋 Agent Details:"
    $response | ConvertTo-Json -Depth 10
} else {
    Write-Host "❌ Agent deployment failed!"
    Write-Host "Response: $($response | ConvertTo-Json -Depth 10)"
    exit 1
}
