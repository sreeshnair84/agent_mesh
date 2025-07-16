# Creating Agents with Templates

This guide explains how to create new agents using the provided templates in the Agent Mesh framework.

## Quick Start

### 1. Choose a Template

Select an appropriate template based on your use case:
- `agent-template.yaml`: Complete reference template with all options
- `basic-assistant.yaml`: Simple conversational agent
- `data-analyst.yaml`: Data analysis specialist
- `customer-support.yaml`: Customer service representative

### 2. Create Your Agent Configuration

Create a new YAML file for your agent:

```bash
# Copy an existing template
cp agent-templates/basic-assistant.yaml my-new-agent.yaml
```

### 3. Customize Your Agent

Edit your new YAML file to customize:

- Basic information (name, description)
- System prompt and instructions
- Tools and capabilities
- Input/output specifications
- Deployment settings

### 4. Deploy Your Agent

Deploy your agent using the Agent Mesh framework:

```bash
# Using the CLI tool
agentmesh deploy --config my-new-agent.yaml

# Or via the API
curl -X POST http://localhost:8000/api/v1/agents/deploy \
  -H "Content-Type: application/yaml" \
  -d @my-new-agent.yaml
```

## Template Structure

### Required Fields

Every agent configuration must include:

1. **Basic Information**
   ```yaml
   agent:
     name: "unique-agent-name"
     display_name: "Human Readable Name"
     description: "Detailed description of the agent's purpose"
     type: "lowcode" # or "custom"
   ```

2. **Model Configuration**
   ```yaml
   model:
     llm_model: "gpt-4" # or other supported model
   ```

3. **System Prompt**
   ```yaml
   prompts:
     system_prompt: "Instructions for the agent..."
   ```

### Optional Sections

Depending on your requirements:

1. **Capabilities and Tools**
   ```yaml
   capabilities:
     - name: "capability_name"
       description: "What the agent can do"
   
   tools:
     - name: "tool_name"
       description: "Tool description"
       config:
         # Tool-specific configuration
   ```

2. **Input/Output Specifications**
   ```yaml
   input_payload:
     # Input schema definition
   
   output_payload:
     # Output schema definition
   ```

3. **Deployment Settings**
   ```yaml
   deployment:
     replicas: 1
     # Other deployment options
   ```

## Best Practices

1. **Clear Instructions**: Provide detailed system prompts with specific guidelines
2. **Appropriate Tools**: Include only tools relevant to the agent's purpose
3. **Version Control**: Track changes to your agent configurations
4. **Testing**: Test your agent thoroughly before deployment
5. **Monitoring**: Set up proper monitoring to track performance

## Example: Creating a Specialized Agent

Here's how you might create a specialized product recommendation agent:

1. Start with the basic assistant template
2. Customize the system prompt for product recommendations
3. Add product catalog and recommendation tools
4. Define specific input/output schemas for product attributes
5. Deploy and test with various customer scenarios
