"""
API v1 router
Main router for API version 1
"""

from fastapi import APIRouter

# Import endpoint modules
from app.api.v1.endpoints import auth, agents, workflows, tools, observability, master_data, templates, system, integration
from app.api.v1 import agent_payload

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
api_router.include_router(tools.router, prefix="/tools", tags=["Tools"])
api_router.include_router(observability.router, prefix="/observability", tags=["Observability"])
api_router.include_router(master_data.router, prefix="/master-data", tags=["Master Data"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
api_router.include_router(integration.router, prefix="/integration", tags=["Integration"])
api_router.include_router(agent_payload.router, prefix="/agents", tags=["Agent Payload"])

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "agent-mesh-api"
    }
