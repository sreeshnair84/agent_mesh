# Agent Templates

This directory contains pre-built agent templates that can be used to quickly create new agents with specific capabilities.

## Primary Template

### Master Template
- **File**: `agent-template.yaml`
- **Description**: Comprehensive template with all possible configurations
- **Use Case**: Reference for creating custom agents with specific requirements

## Usage

To use these templates:

1. Copy the desired template YAML file
2. Rename it to reflect your agent's purpose
3. Customize the configuration based on your requirements
4. Deploy the agent using the Agent Mesh framework

## Template Structure

Each agent template follows a standard structure:

```yaml
agent:
  name: "agent-name"
  display_name: "Human Readable Name"
  # Other basic information
  
model:
  llm_model: "model-name"
  # Model configuration
  
prompts:
  system_prompt: "System instructions"
  # Other prompts
  
capabilities:
  # List of agent capabilities
  
tools:
  # Tools the agent can use
  
# Additional sections for deployment, memory, etc.
```

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

### 4. Customer Support Agent
- **File**: `customer-support.yaml`
- **Description**: Specialized agent for handling customer inquiries and support
- **Use Case**: Customer service, help desk, product support

### 4. Content Generation Agent
- **File**: `content-generator.yaml`
- **Description**: Agent focused on content creation and writing
- **Use Case**: Blog posts, documentation, marketing content

### 5. Research Agent
- **File**: `research-agent.yaml`
- **Description**: Agent specialized in research and information gathering
- **Use Case**: Market research, academic research, fact-checking

## Contributing

To add a new template:

1. Create a new YAML file with the template configuration
2. Update this README with the template description
3. Test the template thoroughly
4. Submit a pull request
