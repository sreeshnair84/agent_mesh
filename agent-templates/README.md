# Agent Templates

This directory contains pre-built agent templates that can be used to quickly create new agents with specific capabilities.

## Available Templates

### 1. Basic Assistant Agent
- **File**: `basic-assistant.yaml`
- **Description**: A general-purpose assistant agent with basic conversational capabilities
- **Use Case**: Customer support, general Q&A

### 2. Data Analysis Agent
- **File**: `data-analyst.yaml`
- **Description**: Specialized agent for data analysis tasks
- **Use Case**: Data exploration, statistical analysis, reporting

### 3. Code Review Agent
- **File**: `code-reviewer.yaml`
- **Description**: Agent specialized in code review and analysis
- **Use Case**: Code quality checks, security reviews, best practices

### 4. Content Generation Agent
- **File**: `content-generator.yaml`
- **Description**: Agent focused on content creation and writing
- **Use Case**: Blog posts, documentation, marketing content

### 5. Research Agent
- **File**: `research-agent.yaml`
- **Description**: Agent specialized in research and information gathering
- **Use Case**: Market research, academic research, fact-checking

## Template Structure

Each template follows this structure:

```yaml
name: "Template Name"
version: "1.0.0"
description: "Template description"
category: "category"
tags: ["tag1", "tag2"]
capabilities:
  - capability1
  - capability2
tools:
  - tool1
  - tool2
system_prompt: |
  System prompt for the agent
default_config:
  key: value
schema:
  type: object
  properties:
    config_item:
      type: string
      description: "Description"
```

## Usage

1. Choose a template that matches your use case
2. Copy the template file to your agent configuration
3. Customize the configuration as needed
4. Deploy the agent through the Agent Mesh interface

## Contributing

To add a new template:

1. Create a new YAML file with the template configuration
2. Update this README with the template description
3. Test the template thoroughly
4. Submit a pull request
