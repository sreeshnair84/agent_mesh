# Quick Start Guide

Get Agent Mesh up and running in under 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- Git (for cloning the repository)
- 4GB+ RAM available
- Port 3000, 8000, 8002, 8003, 5432, 6379 available

## Step 1: Clone the Repository

```bash
git clone https://github.com/agent-mesh/agent-mesh.git
cd agent-mesh
```

## Step 2: Environment Setup

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit the `.env` file with your preferred settings. The defaults work for local development.

## Step 3: Start the Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

This will start:
- PostgreSQL database with pgvector extension
- Redis cache
- Backend API (FastAPI)
- Frontend UI (Next.js)
- Observability service
- Pipeline service

## Step 4: Initialize the Database

```bash
# Run database initialization
./scripts/setup-db.sh

# Verify database setup
docker-compose exec backend python -c "from app.core.database import engine; print('Database connected!')"
```

## Step 5: Access the Application

Once all services are running:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Observability**: http://localhost:8002
- **Pipeline API**: http://localhost:8003

## Step 6: Create Your First Agent

### Option A: Using the Web UI

1. Navigate to http://localhost:3000
2. Click "Create Agent"
3. Choose "Basic Assistant" template
4. Configure your agent settings
5. Deploy the agent

### Option B: Using the API

```bash
# Create a basic agent
curl -X POST "http://localhost:8000/api/v1/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-first-agent",
    "display_name": "My First Agent",
    "description": "A basic assistant agent",
    "system_prompt": "You are a helpful assistant.",
    "configuration": {
      "model": "gpt-4o-mini",
      "temperature": 0.7
    }
  }'
```

## Step 7: Test Your Agent

### Using the Web UI

1. Go to the Agents page
2. Click on your agent
3. Use the chat interface to test

### Using the API

```bash
# Chat with your agent
curl -X POST "http://localhost:8000/api/v1/agents/{agent_id}/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "session_id": "test-session"
  }'
```

## Step 8: Monitor Your Agent

Visit the observability dashboard at http://localhost:8002 to:
- View real-time metrics
- Monitor agent performance
- Check system health
- View logs and traces

## What's Next?

Now that you have Agent Mesh running:

1. **[Create More Agents](./guides/creating-agents.md)** - Build specialized agents
2. **[Set Up Workflows](./guides/workflows.md)** - Orchestrate multi-agent workflows
3. **[Add Tools](./guides/tools.md)** - Integrate external tools and APIs
4. **[Configure Monitoring](./guides/monitoring.md)** - Set up alerts and monitoring
5. **[Deploy to Production](./operations/deployment.md)** - Production deployment guide

## Common Issues

### Services Won't Start

```bash
# Check Docker resources
docker system df

# Check port availability
netstat -tuln | grep -E '(3000|8000|8002|8003|5432|6379)'

# View logs
docker-compose logs -f
```

### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready -U postgres

# Check database tables
docker-compose exec postgres psql -U postgres -d agent_mesh -c "\dt"
```

### Agent Not Responding

1. Check if the agent is deployed and active
2. Verify API keys are configured correctly
3. Check the observability dashboard for errors
4. Review agent logs

## Getting Help

- **Documentation**: Continue reading the guides
- **API Reference**: Check the API documentation
- **Issues**: Report bugs on GitHub
- **Community**: Join our Discord server

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  Observability  │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (FastAPI)     │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8002    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Pipeline      │    │   PostgreSQL    │    │      Redis      │
│   (FastAPI)     │◄──►│   + pgvector    │◄──►│     Cache       │
│   Port: 8003    │    │   Port: 5432    │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

Congratulations! You now have Agent Mesh running and your first agent created. 🎉
