"""
API v1 router
"""

from fastapi import APIRouter
from .endpoints import metrics, tracing, alerts, health

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(tracing.router, prefix="/tracing", tags=["tracing"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
