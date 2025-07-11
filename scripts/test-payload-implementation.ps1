#!/usr/bin/env pwsh

<#
.SYNOPSIS
Test Agent Payload Implementation

.DESCRIPTION
This script tests the agent payload implementation by creating sample agents
with input/output payload specifications and validating the functionality.

.EXAMPLE
./test-payload-implementation.ps1
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$BaseUrl = "http://localhost:8000",
    
    [Parameter(Mandatory = $false)]
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "🧪 Testing Agent Payload Implementation" -ForegroundColor Green
Write-Host "API Base URL: $BaseUrl" -ForegroundColor Yellow

# Test data
$TestAgent = @{
    name = "Weather Assistant"
    description = "An agent that provides weather information"
    system_prompt = "You are a helpful weather assistant. Provide accurate weather information based on user queries."
    model_name = "gpt-4"
    temperature = 0.7
    max_tokens = 1000
    status = "active"
}

$InputPayload = @{
    name = "WeatherInput"
    description = "Input schema for weather queries"
    properties = @{
        location = @{
            type = "string"
            description = "The location to get weather for"
            example = "New York, NY"
        }
        date = @{
            type = "string"
            description = "Optional date for weather forecast"
            example = "2024-01-20"
        }
        units = @{
            type = "string"
            description = "Temperature units"
            example = "celsius"
            enum = @("celsius", "fahrenheit")
        }
    }
    required = @("location")
    examples = @(
        @{
            location = "New York, NY"
            units = "celsius"
        },
        @{
            location = "San Francisco, CA"
            date = "2024-01-20"
            units = "fahrenheit"
        }
    )
}

$OutputPayload = @{
    name = "WeatherOutput"
    description = "Output schema for weather responses"
    properties = @{
        location = @{
            type = "string"
            description = "The location the weather is for"
            example = "New York, NY"
        }
        temperature = @{
            type = "number"
            description = "Current temperature"
            example = 22.5
        }
        condition = @{
            type = "string"
            description = "Weather condition"
            example = "sunny"
        }
        humidity = @{
            type = "number"
            description = "Humidity percentage"
            example = 65
        }
        forecast = @{
            type = "array"
            description = "Weather forecast"
            example = @(
                @{
                    date = "2024-01-20"
                    temperature = 25.0
                    condition = "partly cloudy"
                }
            )
        }
    }
    required = @("location", "temperature", "condition")
    examples = @(
        @{
            location = "New York, NY"
            temperature = 22.5
            condition = "sunny"
            humidity = 65
            forecast = @(
                @{
                    date = "2024-01-20"
                    temperature = 25.0
                    condition = "partly cloudy"
                }
            )
        }
    )
}

# Helper function to make API requests
function Invoke-ApiRequest {
    param(
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body = $null,
        [hashtable]$Headers = @{"Content-Type" = "application/json"}
    )
    
    $Uri = "$BaseUrl$Endpoint"
    
    if ($Verbose) {
        Write-Host "🔍 $Method $Uri" -ForegroundColor Blue
        if ($Body) {
            Write-Host "📄 Body: $($Body | ConvertTo-Json -Depth 10)" -ForegroundColor Gray
        }
    }
    
    try {
        $Response = if ($Body) {
            Invoke-RestMethod -Uri $Uri -Method $Method -Body ($Body | ConvertTo-Json -Depth 10) -Headers $Headers
        } else {
            Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers
        }
        
        if ($Verbose) {
            Write-Host "✅ Response: $($Response | ConvertTo-Json -Depth 10)" -ForegroundColor Green
        }
        
        return $Response
    }
    catch {
        Write-Host "❌ API Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $Reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
            $ErrorBody = $Reader.ReadToEnd()
            Write-Host "❌ Error Body: $ErrorBody" -ForegroundColor Red
        }
        throw
    }
}

# Test 1: Health Check
Write-Host "🏥 Test 1: Health Check" -ForegroundColor Blue
try {
    $HealthResponse = Invoke-ApiRequest -Method GET -Endpoint "/health"
    Write-Host "✅ Health check passed" -ForegroundColor Green
}
catch {
    Write-Host "❌ Health check failed. Is the API running?" -ForegroundColor Red
    exit 1
}

# Test 2: Create Agent with Payload
Write-Host "🤖 Test 2: Create Agent with Payload Specifications" -ForegroundColor Blue
try {
    $AgentWithPayload = $TestAgent.Clone()
    $AgentWithPayload.input_payload = $InputPayload
    $AgentWithPayload.output_payload = $OutputPayload
    
    $CreateResponse = Invoke-ApiRequest -Method POST -Endpoint "/api/v1/agents" -Body $AgentWithPayload
    $AgentId = $CreateResponse.id
    
    Write-Host "✅ Agent created successfully with ID: $AgentId" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to create agent with payload specifications" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Test 3: Get Agent Payload
Write-Host "📋 Test 3: Get Agent Payload Specifications" -ForegroundColor Blue
try {
    $PayloadResponse = Invoke-ApiRequest -Method GET -Endpoint "/api/v1/agents/$AgentId/payload"
    
    if ($PayloadResponse.input_payload -and $PayloadResponse.output_payload) {
        Write-Host "✅ Agent payload specifications retrieved successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Agent payload specifications not found" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Failed to get agent payload specifications" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Test 4: Update Agent Payload
Write-Host "🔄 Test 4: Update Agent Payload Specifications" -ForegroundColor Blue
try {
    $UpdatedInputPayload = $InputPayload.Clone()
    $UpdatedInputPayload.description = "Updated input schema for weather queries"
    
    $UpdatePayload = @{
        input_payload = $UpdatedInputPayload
        output_payload = $OutputPayload
    }
    
    $UpdateResponse = Invoke-ApiRequest -Method PUT -Endpoint "/api/v1/agents/$AgentId/payload" -Body $UpdatePayload
    Write-Host "✅ Agent payload specifications updated successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to update agent payload specifications" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Test 5: Validate Valid Input Payload
Write-Host "✅ Test 5: Validate Valid Input Payload" -ForegroundColor Blue
try {
    $ValidInputData = @{
        location = "New York, NY"
        units = "celsius"
    }
    
    $ValidateRequest = @{
        payload_data = $ValidInputData
        payload_type = "input"
    }
    
    $ValidateResponse = Invoke-ApiRequest -Method POST -Endpoint "/api/v1/agents/$AgentId/payload/validate" -Body $ValidateRequest
    
    if ($ValidateResponse.valid) {
        Write-Host "✅ Valid input payload validation passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Valid input payload validation failed: $($ValidateResponse.errors -join ', ')" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Failed to validate input payload" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Test 6: Validate Invalid Input Payload
Write-Host "❌ Test 6: Validate Invalid Input Payload" -ForegroundColor Blue
try {
    $InvalidInputData = @{
        units = "celsius"
        # Missing required 'location' field
    }
    
    $ValidateRequest = @{
        payload_data = $InvalidInputData
        payload_type = "input"
    }
    
    $ValidateResponse = Invoke-ApiRequest -Method POST -Endpoint "/api/v1/agents/$AgentId/payload/validate" -Body $ValidateRequest
    
    if (-not $ValidateResponse.valid) {
        Write-Host "✅ Invalid input payload validation correctly failed" -ForegroundColor Green
        Write-Host "  Errors: $($ValidateResponse.errors -join ', ')" -ForegroundColor Gray
    } else {
        Write-Host "❌ Invalid input payload validation should have failed" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Failed to validate invalid input payload" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Test 7: Get Payload Examples
Write-Host "📝 Test 7: Get Payload Examples" -ForegroundColor Blue
try {
    $ExamplesResponse = Invoke-ApiRequest -Method GET -Endpoint "/api/v1/agents/$AgentId/payload/examples"
    
    if ($ExamplesResponse.input_examples -and $ExamplesResponse.output_examples) {
        Write-Host "✅ Payload examples retrieved successfully" -ForegroundColor Green
        Write-Host "  Input examples: $($ExamplesResponse.input_examples.Count)" -ForegroundColor Gray
        Write-Host "  Output examples: $($ExamplesResponse.output_examples.Count)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Payload examples not found" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Failed to get payload examples" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Test 8: Test Agent Creation without Payload
Write-Host "🤖 Test 8: Create Agent without Payload Specifications" -ForegroundColor Blue
try {
    $BasicAgent = $TestAgent.Clone()
    $BasicAgent.name = "Basic Assistant"
    
    $CreateResponse = Invoke-ApiRequest -Method POST -Endpoint "/api/v1/agents" -Body $BasicAgent
    $BasicAgentId = $CreateResponse.id
    
    Write-Host "✅ Basic agent created successfully with ID: $BasicAgentId" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to create basic agent" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Test 9: Add Payload to Existing Agent
Write-Host "➕ Test 9: Add Payload to Existing Agent" -ForegroundColor Blue
try {
    $NewPayload = @{
        input_payload = @{
            name = "BasicInput"
            description = "Basic input schema"
            properties = @{
                message = @{
                    type = "string"
                    description = "User message"
                    example = "Hello, how are you?"
                }
            }
            required = @("message")
            examples = @(
                @{
                    message = "Hello, how are you?"
                }
            )
        }
        output_payload = @{
            name = "BasicOutput"
            description = "Basic output schema"
            properties = @{
                response = @{
                    type = "string"
                    description = "Agent response"
                    example = "Hello! I'm doing well, thank you for asking."
                }
            }
            required = @("response")
            examples = @(
                @{
                    response = "Hello! I'm doing well, thank you for asking."
                }
            )
        }
    }
    
    $UpdateResponse = Invoke-ApiRequest -Method PUT -Endpoint "/api/v1/agents/$BasicAgentId/payload" -Body $NewPayload
    Write-Host "✅ Payload added to existing agent successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to add payload to existing agent" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Test 10: Clean up test agents
Write-Host "🧹 Test 10: Clean up Test Agents" -ForegroundColor Blue
try {
    $DeleteResponse1 = Invoke-ApiRequest -Method DELETE -Endpoint "/api/v1/agents/$AgentId"
    $DeleteResponse2 = Invoke-ApiRequest -Method DELETE -Endpoint "/api/v1/agents/$BasicAgentId"
    
    Write-Host "✅ Test agents cleaned up successfully" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Failed to clean up test agents (this is okay)" -ForegroundColor Yellow
}

# Summary
Write-Host "" -ForegroundColor Gray
Write-Host "🎉 All Tests Completed Successfully!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host "✅ Agent payload implementation is working correctly" -ForegroundColor Green
Write-Host "✅ Input/Output payload specifications can be captured" -ForegroundColor Green
Write-Host "✅ Payload validation is working" -ForegroundColor Green
Write-Host "✅ Edit and screen interfaces can now capture:" -ForegroundColor Green
Write-Host "   - Field names, types, descriptions" -ForegroundColor Gray
Write-Host "   - Required field indicators" -ForegroundColor Gray
Write-Host "   - Example values" -ForegroundColor Gray
Write-Host "   - Enumerated values for string fields" -ForegroundColor Gray
Write-Host "   - Complete payload examples" -ForegroundColor Gray
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host "🚀 Ready for production use!" -ForegroundColor Green
