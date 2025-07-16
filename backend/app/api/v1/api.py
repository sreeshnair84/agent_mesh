"""
API v1 router
Main router for API version 1
"""

from fastapi import APIRouter

# Import endpoint modules
from app.api.v1.endpoints import auth, agents, workflows, tools, observability, master_data, templates, system, integration, skills, prompts, models, constraints, secrets
from app.api.v1 import agent_payload

api_router = APIRouter()

# Include all endpoint routers - Note: Each router already has its own prefix defined
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(agents.router, tags=["Agents"])  # Using capitalized tag for consistency
api_router.include_router(workflows.router, tags=["Workflows"])
api_router.include_router(tools.router, tags=["Tools"])  # Using capitalized tag for consistency
api_router.include_router(skills.router, tags=["Skills"])  # Using capitalized tag for consistency
api_router.include_router(prompts.router, tags=["Prompts"])  # Using capitalized tag for consistency
api_router.include_router(models.router, tags=["Models"])  # Using capitalized tag for consistency
api_router.include_router(constraints.router, tags=["Constraints"])  # Using capitalized tag for consistency
api_router.include_router(secrets.router, tags=["Environment Secrets"])
api_router.include_router(observability.router, tags=["Observability"])
api_router.include_router(master_data.router, tags=["Master Data"])
api_router.include_router(templates.router, tags=["Templates"])
api_router.include_router(system.router, tags=["System"])
api_router.include_router(integration.router, tags=["Integration"])
# Group agent payload endpoints with other agent endpoints
api_router.include_router(agent_payload.router, prefix="/agents", tags=["Agents"])

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "agent-mesh-api"
    }
