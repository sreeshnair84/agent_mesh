# Tool Templates

This directory contains pre-built tool templates that can be used to quickly create new tools for agents.

## Available Templates

### 1. Web Search Tool
- **File**: `web-search.yaml`
- **Description**: Tool for searching the web and retrieving information
- **Use Case**: Research, fact-checking, current information

### 2. Database Query Tool
- **File**: `database-query.yaml`
- **Description**: Tool for executing database queries
- **Use Case**: Data retrieval, reporting, analysis

### 3. Email Sender Tool
- **File**: `email-sender.yaml`
- **Description**: Tool for sending emails
- **Use Case**: Notifications, communications, alerts

### 4. File Processor Tool
- **File**: `file-processor.yaml`
- **Description**: Tool for processing various file types
- **Use Case**: Document processing, data extraction, file conversion

### 5. API Client Tool
- **File**: `api-client.yaml`
- **Description**: Generic API client tool
- **Use Case**: External service integration, data fetching

### 6. Code Executor Tool
- **File**: `code-executor.yaml`
- **Description**: Tool for executing code in various languages
- **Use Case**: Data analysis, automation, calculations

## Template Structure

Each tool template follows this structure:

```yaml
name: "Tool Name"
version: "1.0.0"
description: "Tool description"
type: "tool_type"
category: "category"
tags: ["tag1", "tag2"]
schema:
  input_schema:
    type: object
    properties: {}
  output_schema:
    type: object
    properties: {}
implementation:
  type: "implementation_type"
  config: {}
authentication:
  type: "auth_type"
  config: {}
```

## Usage

1. Choose a tool template that matches your requirements
2. Copy the template file to your tool configuration
3. Customize the implementation and configuration
4. Test the tool thoroughly
5. Deploy the tool through the Agent Mesh interface

## Contributing

To add a new tool template:

1. Create a new YAML file with the tool configuration
2. Update this README with the tool description
3. Test the tool template thoroughly
4. Submit a pull request
