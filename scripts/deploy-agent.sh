#!/bin/bash

# Agent Deployment Script
# This script deploys a new agent to the Agent Mesh platform

set -e

echo "🤖 Agent Deployment Script"
echo "=========================="

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -n, --name NAME         Agent name (required)"
    echo "  -t, --template TEMPLATE Agent template (crag, supervisor, plan-execute)"
    echo "  -c, --config CONFIG     Configuration file path"
    echo "  -d, --description DESC  Agent description"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --name my-agent --template crag"
    echo "  $0 --name my-agent --config ./config.yaml"
    echo ""
    exit 1
}

# Default values
AGENT_NAME=""
AGENT_TEMPLATE=""
CONFIG_FILE=""
DESCRIPTION=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--name)
            AGENT_NAME="$2"
            shift 2
            ;;
        -t|--template)
            AGENT_TEMPLATE="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -d|--description)
            DESCRIPTION="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required parameters
if [ -z "$AGENT_NAME" ]; then
    echo "❌ Error: Agent name is required"
    usage
fi

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Error: Backend API is not running"
    echo "   Please start the services first: ./scripts/startup.sh"
    exit 1
fi

echo "🚀 Deploying agent: $AGENT_NAME"

# Create deployment payload
PAYLOAD="{\"name\": \"$AGENT_NAME\""

if [ -n "$DESCRIPTION" ]; then
    PAYLOAD="$PAYLOAD, \"description\": \"$DESCRIPTION\""
fi

if [ -n "$AGENT_TEMPLATE" ]; then
    PAYLOAD="$PAYLOAD, \"template\": \"$AGENT_TEMPLATE\""
fi

if [ -n "$CONFIG_FILE" ] && [ -f "$CONFIG_FILE" ]; then
    echo "📄 Reading configuration from: $CONFIG_FILE"
    CONFIG_CONTENT=$(cat "$CONFIG_FILE")
    PAYLOAD="$PAYLOAD, \"config\": $CONFIG_CONTENT"
fi

PAYLOAD="$PAYLOAD}"

echo "📦 Deployment payload prepared"

# Deploy the agent
echo "🚀 Deploying agent..."
RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    http://localhost:8000/api/v1/agents/)

# Check if deployment was successful
if echo "$RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
    AGENT_ID=$(echo "$RESPONSE" | jq -r '.id')
    echo "✅ Agent deployed successfully!"
    echo "   Agent ID: $AGENT_ID"
    echo "   Agent Name: $AGENT_NAME"
    echo "   Agent URL: http://localhost:8000/api/v1/agents/$AGENT_ID"
    echo ""
    echo "🎉 Agent is now available in the Agent Mesh platform!"
    echo "📊 View in dashboard: http://localhost:3000/agent-marketplace"
    
    # Show agent details
    echo ""
    echo "📋 Agent Details:"
    echo "$RESPONSE" | jq '.'
    
else
    echo "❌ Agent deployment failed!"
    echo "Response: $RESPONSE"
    exit 1
fi
