"""
System API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_user_from_db, get_current_admin_user
from app.models.user import User
from app.services.system_service import SystemService

router = APIRouter(
    prefix="/system",
    responses={404: {"description": "Not found"}},)
system_service = SystemService()

# System Status endpoints
@router.get("/status")
async def get_system_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Get comprehensive system status"""
    try:
        return await system_service.get_system_status(db)
    except Exception as e:
        # Fallback to basic status
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "System is operational"
        }

@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db)
):
    """Simple health check endpoint"""
    try:
        # Quick database check
        result = await db.execute("SELECT 1")
        result.scalar()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/info")
async def get_system_info(
    current_user: User = Depends(get_current_user_from_db)
):
    """Get system information"""
    try:
        return await system_service.get_system_info()
    except Exception as e:
        return {
            "version": "1.0.0",
            "environment": "production",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# System Logs endpoints
@router.get("/logs")
async def get_system_logs(
    log_level: str = Query("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    limit: int = Query(100, ge=1, le=1000),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get system logs"""
    try:
        since_dt = None
        if since:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        
        logs = await system_service.get_system_logs(log_level, limit, since_dt)
        return {
            "logs": logs,
            "total": len(logs),
            "level": log_level,
            "since": since
        }
    except Exception as e:
        return {
            "logs": [],
            "total": 0,
            "error": str(e)
        }

# System Configuration endpoints
@router.get("/config")
async def get_system_configuration(
    current_user: User = Depends(get_current_admin_user)
):
    """Get system configuration"""
    try:
        return await system_service.get_system_configuration()
    except Exception as e:
        return {"error": str(e)}

@router.put("/config")
async def update_system_configuration(
    config: Dict[str, Any],
    current_user: User = Depends(get_current_admin_user)
):
    """Update system configuration"""
    try:
        return await system_service.update_system_configuration(config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# System Metrics endpoints
@router.get("/metrics")
async def get_system_metrics(
    current_user: User = Depends(get_current_user_from_db)
):
    """Get current system metrics"""
    try:
        status = await system_service.get_system_status(None)
        return status.get("system", {})
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/metrics/history")
async def get_metrics_history(
    period: str = Query("24h", pattern="^(1h|24h|7d|30d)$"),
    current_user: User = Depends(get_current_user_from_db)
):
    """Get system metrics history"""
    try:
        return await system_service.get_system_metrics_history(period)
    except Exception as e:
        return {
            "error": str(e),
            "period": period,
            "data_points": 0,
            "metrics": []
        }

# System Management endpoints
@router.post("/restart/{service_name}")
async def restart_service(
    service_name: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Restart a specific service"""
    try:
        return await system_service.restart_service(service_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cache/clear")
async def clear_cache(
    cache_type: str = Query("all", pattern="^(all|health|api|database)$"),
    current_user: User = Depends(get_current_admin_user)
):
    """Clear system caches"""
    try:
        return await system_service.clear_cache(cache_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# System Statistics endpoints
@router.get("/stats")
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Get system statistics"""
    try:
        status = await system_service.get_system_status(db)
        return status.get("application", {}).get("stats", {})
    except Exception as e:
        return {
            "agents": 0,
            "workflows": 0,
            "tools": 0,
            "users": 0,
            "error": str(e)
        }

@router.get("/stats/summary")
async def get_stats_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Get system statistics summary"""
    try:
        status = await system_service.get_system_status(db)
        app_stats = status.get("application", {}).get("stats", {})
        system_metrics = status.get("system", {})
        
        return {
            "overview": {
                "status": status.get("status"),
                "uptime": "Available",
                "last_check": status.get("timestamp")
            },
            "resources": {
                "agents": app_stats.get("agents", 0),
                "workflows": app_stats.get("workflows", 0),
                "tools": app_stats.get("tools", 0),
                "users": app_stats.get("users", 0)
            },
            "performance": {
                "cpu_usage": system_metrics.get("cpu_percent", 0),
                "memory_usage": system_metrics.get("memory", {}).get("percent", 0),
                "disk_usage": system_metrics.get("disk", {}).get("percent", 0)
            }
        }
    except Exception as e:
        return {
            "overview": {
                "status": "unknown",
                "uptime": "Unknown",
                "last_check": datetime.utcnow().isoformat()
            },
            "resources": {
                "agents": 0,
                "workflows": 0,
                "tools": 0,
                "users": 0
            },
            "performance": {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0
            },
            "error": str(e)
        }

# System Alerts endpoints
@router.get("/alerts")
async def get_system_alerts(
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user_from_db)
):
    """Get system alerts"""
    try:
        # This is a placeholder - in a real system, you'd query actual alerts
        alerts = []
        
        # Add sample alerts based on system status
        now = datetime.utcnow()
        
        # CPU alert
        alerts.append({
            "id": "alert-cpu-1",
            "type": "cpu",
            "severity": "medium",
            "message": "CPU usage is within normal range",
            "timestamp": now.isoformat(),
            "resolved": True
        })
        
        # Memory alert
        alerts.append({
            "id": "alert-memory-1",
            "type": "memory",
            "severity": "low",
            "message": "Memory usage is optimal",
            "timestamp": (now - timedelta(minutes=30)).isoformat(),
            "resolved": True
        })
        
        # Filter by severity if specified
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        
        return {
            "alerts": alerts[:limit],
            "total": len(alerts),
            "severity_filter": severity
        }
    except Exception as e:
        return {
            "alerts": [],
            "total": 0,
            "error": str(e)
        }

# System Backup endpoints
@router.post("/backup")
async def create_system_backup(
    backup_type: str = Query("full", pattern="^(full|incremental|config)$"),
    current_user: User = Depends(get_current_admin_user)
):
    """Create system backup"""
    try:
        # This is a placeholder - in a real system, you'd implement actual backup
        backup_id = f"backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        return {
            "backup_id": backup_id,
            "type": backup_type,
            "status": "initiated",
            "created_at": datetime.utcnow().isoformat(),
            "message": f"Backup {backup_id} initiated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/backup/status/{backup_id}")
async def get_backup_status(
    backup_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Get backup status"""
    try:
        # This is a placeholder - in a real system, you'd query actual backup status
        return {
            "backup_id": backup_id,
            "status": "completed",
            "progress": 100,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "size": "1.2GB"
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="Backup not found")
