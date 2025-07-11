# Agent Input/Output Payload Specifications

This document describes the implementation of agent input/output payload specifications that can be captured in edit and screen interfaces.

## Overview

The Agent Mesh now supports capturing detailed specifications for agent input and output payloads, including:
- Field names, types, and descriptions
- Required field indicators
- Example values for each field
- Enumerated values for string fields
- Complete payload examples
- JSON schema validation

## Database Schema

### New Columns Added to `agents` Table

```sql
-- JSON column for input payload specification
input_payload JSONB,

-- JSON column for output payload specification  
output_payload JSONB
```

### Payload Schema Structure

Each payload (input/output) follows this JSON schema:

```json
{
  "name": "string",           // Schema name
  "description": "string",    // Schema description
  "properties": {             // Field definitions
    "field_name": {
      "type": "string|number|boolean|array|object",
      "description": "string",
      "example": "any",       // Example value
      "enum": ["val1", "val2"] // Optional for string types
    }
  },
  "required": ["field1"],     // Required field names
  "examples": []              // Complete payload examples
}
```

## API Endpoints

### Get Agent Payload Specifications

```http
GET /api/v1/agents/{agent_id}/payload
```

**Response:**
```json
{
  "agent_id": "string",
  "input_payload": { /* PayloadSchema */ },
  "output_payload": { /* PayloadSchema */ }
}
```

### Update Agent Payload Specifications

```http
PUT /api/v1/agents/{agent_id}/payload
```

**Request Body:**
```json
{
  "input_payload": { /* PayloadSchema */ },
  "output_payload": { /* PayloadSchema */ }
}
```

### Validate Data Against Payload Schema

```http
POST /api/v1/agents/{agent_id}/payload/validate
```

**Request Body:**
```json
{
  "payload_data": { /* Data to validate */ },
  "payload_type": "input" | "output"
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "payload_type": "input",
  "agent_id": "string"
}
```

### Get Payload Examples

```http
GET /api/v1/agents/{agent_id}/payload/examples
```

**Response:**
```json
{
  "input_examples": [{ /* Example payloads */ }],
  "output_examples": [{ /* Example payloads */ }]
}
```

## Frontend Components

### AgentPayloadForm

A comprehensive React component for editing payload specifications:

```tsx
import AgentPayloadForm from '@/components/agents/AgentPayloadForm';

<AgentPayloadForm
  inputPayload={inputPayload}
  outputPayload={outputPayload}
  onPayloadChange={handlePayloadChange}
/>
```

**Features:**
- Tab-based interface for input/output payloads
- Field management (add, edit, remove)
- Type selection (string, number, boolean, array, object)
- Required field indicators
- Example value capture
- Enumerated value support for strings
- Example payload generation
- JSON schema preview

### AgentEditForm

Enhanced agent edit form with payload specifications:

```tsx
import AgentEditForm from '@/components/agents/AgentEditForm';

<AgentEditForm
  agent={agent}
  onSave={handleSave}
  onCancel={handleCancel}
  loading={loading}
/>
```

**Features:**
- Multi-tab interface (Basic, Configuration, Input/Output, Testing)
- Integrated payload editing
- Payload validation testing
- Example generation
- JSON validation

## Service Layer

### payloadService

Utility service for payload management:

```typescript
import payloadService from '@/lib/services/payload-service';

// Get agent payload specifications
const payload = await payloadService.getAgentPayload(agentId);

// Update payload specifications
await payloadService.updateAgentPayload(agentId, {
  input_payload: inputPayload,
  output_payload: outputPayload
});

// Validate payload data
const result = await payloadService.validatePayload(agentId, data, 'input');

// Get examples
const examples = await payloadService.getPayloadExamples(agentId);
```

## Example Usage

### Creating an Agent with Payload Specifications

```typescript
const agent = {
  name: "Weather Assistant",
  description: "Provides weather information",
  system_prompt: "You are a helpful weather assistant...",
  model_name: "gpt-4",
  input_payload: {
    name: "WeatherInput",
    description: "Input schema for weather queries",
    properties: {
      location: {
        type: "string",
        description: "The location to get weather for",
        example: "New York, NY"
      },
      units: {
        type: "string",
        description: "Temperature units",
        example: "celsius",
        enum: ["celsius", "fahrenheit"]
      }
    },
    required: ["location"],
    examples: [
      {
        location: "New York, NY",
        units: "celsius"
      }
    ]
  },
  output_payload: {
    name: "WeatherOutput",
    description: "Output schema for weather responses",
    properties: {
      temperature: {
        type: "number",
        description: "Current temperature",
        example: 22.5
      },
      condition: {
        type: "string",
        description: "Weather condition",
        example: "sunny"
      }
    },
    required: ["temperature", "condition"],
    examples: [
      {
        temperature: 22.5,
        condition: "sunny"
      }
    ]
  }
};
```

### Validating Input Data

```typescript
const inputData = {
  location: "New York, NY",
  units: "celsius"
};

const validation = await payloadService.validatePayload(
  agentId, 
  inputData, 
  'input'
);

if (!validation.valid) {
  console.log('Validation errors:', validation.errors);
}
```

## Migration

### Running the Migration

```powershell
# Run the migration script
./scripts/run-payload-migration.ps1 -Environment development

# Or with dry run to see what would be done
./scripts/run-payload-migration.ps1 -Environment development -DryRun
```

The migration will:
1. Add `input_payload` and `output_payload` JSONB columns to `agents` table
2. Create indexes for efficient JSON queries
3. Add sample payload schemas to existing agents
4. Add column comments for documentation

### Sample Payload Schemas

All existing agents will be updated with default payload schemas:

**Default Input Schema:**
```json
{
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
}
```

**Default Output Schema:**
```json
{
  "name": "DefaultOutput",
  "description": "Default output schema for agent",
  "properties": {
    "response": {
      "type": "string",
      "description": "The agent's response",
      "example": "The weather in New York is sunny with a temperature of 75°F."
    },
    "confidence": {
      "type": "number",
      "description": "Confidence score for the response",
      "example": 0.95
    }
  },
  "required": ["response"],
  "examples": [
    {
      "response": "The weather in New York is sunny with a temperature of 75°F.",
      "confidence": 0.95
    }
  ]
}
```

## Testing

### Run Tests

```powershell
# Test the payload implementation
./scripts/test-payload-implementation.ps1

# With verbose output
./scripts/test-payload-implementation.ps1 -Verbose
```

The test script validates:
1. Agent creation with payload specifications
2. Payload retrieval
3. Payload updates
4. Payload validation (valid and invalid data)
5. Example retrieval
6. Adding payloads to existing agents

## Field Types

### Supported Field Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | Text value | `"Hello World"` |
| `number` | Numeric value | `42.5` |
| `boolean` | True/false value | `true` |
| `array` | List of values | `[1, 2, 3]` |
| `object` | Nested object | `{"key": "value"}` |

### String Field Enumerations

For string fields, you can specify allowed values:

```json
{
  "units": {
    "type": "string",
    "description": "Temperature units",
    "enum": ["celsius", "fahrenheit", "kelvin"]
  }
}
```

### Required Fields

Fields marked as required will be validated during payload validation:

```json
{
  "required": ["location", "query"]
}
```

## Best Practices

### 1. Descriptive Field Names
Use clear, descriptive field names that indicate their purpose:
```json
{
  "user_location": "string",  // Good
  "loc": "string"            // Avoid
}
```

### 2. Comprehensive Descriptions
Provide detailed descriptions for each field:
```json
{
  "temperature": {
    "type": "number",
    "description": "Current temperature in the specified units (celsius/fahrenheit)"
  }
}
```

### 3. Realistic Examples
Use realistic example values that help users understand the expected format:
```json
{
  "email": {
    "type": "string",
    "description": "User email address",
    "example": "user@example.com"
  }
}
```

### 4. Schema Validation
Always validate payload schemas before saving:
```typescript
const validation = payloadService.validatePayloadStructure(payload);
if (!validation.valid) {
  console.log('Schema errors:', validation.errors);
}
```

### 5. Version Management
Consider versioning your payload schemas for backward compatibility:
```json
{
  "name": "WeatherInput_v1.0",
  "description": "Weather input schema version 1.0"
}
```

## Troubleshooting

### Common Issues

1. **Invalid JSON in payload data**
   - Ensure all JSON is properly formatted
   - Use JSON validators to check syntax

2. **Missing required fields**
   - Check that all required fields are present in validation data
   - Verify field names match exactly

3. **Type mismatches**
   - Ensure data types match the schema definitions
   - Check for proper type conversion

4. **Migration failures**
   - Verify database connection
   - Check that agents table exists
   - Ensure proper permissions

### Debug Mode

Enable verbose logging in the test script:
```powershell
./scripts/test-payload-implementation.ps1 -Verbose
```

## Future Enhancements

1. **Advanced Validation Rules**
   - Min/max length for strings
   - Min/max values for numbers
   - Pattern matching with regex

2. **Nested Object Schemas**
   - Support for complex nested object validation
   - Recursive schema definitions

3. **Schema Inheritance**
   - Base schemas that can be extended
   - Template payload schemas

4. **Real-time Validation**
   - Live validation in the UI
   - Instant feedback on payload editing

5. **Schema Documentation**
   - Auto-generated documentation from schemas
   - Interactive schema explorers

---

## Summary

The Agent Mesh now fully supports capturing agent input/output payload specifications through:

- ✅ Enhanced database schema with JSONB columns
- ✅ Comprehensive API endpoints for payload management
- ✅ Rich frontend components for payload editing
- ✅ Validation and testing capabilities
- ✅ Migration scripts and testing tools
- ✅ Complete documentation and examples

Edit and screen interfaces can now capture detailed payload specifications including field names, types, descriptions, examples, and validation rules, enabling robust agent interface definition and validation.
