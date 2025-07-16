"""
API v1 router
"""

from fastapi import APIRouter
from .endpoints import health, monitoring

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])

# Add WebSocket route for real-time monitoring
@api_router.websocket("/ws/monitoring")
async def websocket_monitoring_endpoint(websocket):
    """WebSocket endpoint for real-time monitoring data"""
    await websocket.accept()
    # WebSocket handling logic is in the monitoring router
    await monitoring.handle_websocket(websocket)
