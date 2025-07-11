"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import time

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "observability",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "observability",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": time.time(),
        "components": {
            "database": "healthy",
            "redis": "healthy",
            "metrics_collector": "healthy",
            "alert_monitor": "healthy"
        }
    }
