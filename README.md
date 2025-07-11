# Agent Mesh Application

A comprehensive Agent mesh application enabling creation, management, and orchestration of AI agents with full observability and workflow capabilities.

## Technology Stack
- **Frontend**: React + Next.js (Latest)
- **Backend**: FastAPI
- **Observability**: FastAPI
- **Database**: PostgreSQL + pgvector, Redis
- **Agent Framework**: LangChain + LangGraph
- **LLM**: Azure OpenAI, Gemini, Claude
- **Vector DB**: PGVector
- **Deployment**: Docker Compose + Scripts

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+

### Setup Commands

```bash
# Clone and setup
git clone <repository>
cd agent-mesh

# Copy environment file
cp .env.example .env

# Edit .env with your configurations
nano .env

# Start all services
./scripts/startup.sh

# Setup database
./scripts/setup-db.sh
```

### Development Workflow

1. **Frontend Development**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **Backend Development**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```

3. **Observability Development**
   ```bash
   cd observability
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8001
   ```

## Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Observability**: http://localhost:8001
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Team Assignments

| Team | Component | Port | Responsibility |
|------|-----------|------|---------------|
| Frontend | React/Next.js | 3000 | UI/UX, Components |
| Backend | FastAPI | 8000 | Business Logic, APIs |
| Observability | FastAPI | 8001 | Logging, Metrics |
| DevOps | Scripts/Docker | - | Deployment, Infrastructure |
| Agent Templates | Python | - | Reusable Agent Frameworks |
| Tool Templates | Python | - | Tool Templates & MCP |

## Development Standards

### Code Quality
- Use TypeScript for frontend
- Use Python type hints for backend
- Follow PEP 8 for Python
- Use ESLint/Prettier for JavaScript/TypeScript
- Minimum 80% test coverage

### API Standards
- RESTful API design
- OpenAPI/Swagger documentation
- Consistent error handling
- Request/Response validation
- Rate limiting

### Database Standards
- Use migrations for schema changes
- Proper indexing strategy
- Data validation at DB level
- Connection pooling
- Backup strategy

### Security Standards
- JWT authentication
- API key management
- Input validation
- SQL injection prevention
- CORS configuration

## Documentation

- [API Documentation](./docs/api/)
- [Deployment Guide](./docs/deployment/)
- [Development Guide](./docs/development/)
- [User Guide](./docs/user-guide/)
