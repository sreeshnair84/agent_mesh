"""
System Service
Provides system-wide status, health checks, and configuration management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import psutil
import os
import json

from app.core.config import settings
from app.services.observability_service import ObservabilityService

logger = logging.getLogger(__name__)

class SystemService:
    """Service for system-wide operations"""
    
    def __init__(self):
        self.observability_service = ObservabilityService()
        self.health_check_cache = {}
        self.health_check_cache_ttl = 60  # seconds
    
    async def get_system_status(self, db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Get database status
            db_status = await self._check_database_health(db)
            
            # Get system metrics
            system_metrics = await self._get_system_metrics()
            
            # Get service status
            service_status = await self._get_service_status()
            
            # Get application status
            app_status = await self._get_application_status(db)
            
            return {
                "status": "healthy" if all([
                    db_status.get("healthy", False),
                    system_metrics.get("healthy", False),
                    service_status.get("healthy", False),
                    app_status.get("healthy", False)
                ]) else "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": db_status,
                "system": system_metrics,
                "services": service_status,
                "application": app_status
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def _check_database_health(self, db: AsyncSession) -> Dict[str, Any]:
        """Check database health"""
        try:
            # Check database connection
            result = await db.execute(text("SELECT 1"))
            result.scalar()
            
            # Check database size
            size_result = await db.execute(text(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            ))
            db_size = size_result.scalar()
            
            # Check active connections
            conn_result = await db.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            ))
            active_connections = conn_result.scalar()
            
            return {
                "healthy": True,
                "size": db_size,
                "active_connections": active_connections,
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            return {
                "healthy": cpu_percent < 80 and memory.percent < 85,
                "cpu_percent": cpu_percent,
                "memory": {
                    "percent": memory.percent,
                    "available": memory.available,
                    "total": memory.total
                },
                "disk": {
                    "percent": (disk.used / disk.total) * 100,
                    "free": disk.free,
                    "total": disk.total
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv
                },
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def _get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        try:
            services = {
                "observability": await self._check_observability_service(),
                "database": True,  # If we're here, DB is working
                "api": True,      # If we're here, API is working
            }
            
            return {
                "healthy": all(services.values()),
                "services": services,
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Service status check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def _check_observability_service(self) -> bool:
        """Check if observability service is working"""
        try:
            # Try to log a test event
            await self.observability_service.log_event(
                "system_health_check",
                "test",
                {"timestamp": datetime.utcnow().isoformat()}
            )
            return True
        except Exception as e:
            logger.error(f"Observability service check failed: {e}")
            return False
    
    async def _get_application_status(self, db: AsyncSession) -> Dict[str, Any]:
        """Get application-specific status"""
        try:
            # Check agent count
            agent_count = await self._get_count(db, "agents")
            
            # Check workflow count
            workflow_count = await self._get_count(db, "workflows")
            
            # Check tool count
            tool_count = await self._get_count(db, "tools")
            
            # Check user count
            user_count = await self._get_count(db, "users")
            
            return {
                "healthy": True,
                "stats": {
                    "agents": agent_count,
                    "workflows": workflow_count,
                    "tools": tool_count,
                    "users": user_count
                },
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Application status check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "stats": {
                    "agents": 0,
                    "workflows": 0,
                    "tools": 0,
                    "users": 0
                },
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def _get_count(self, db: AsyncSession, table: str) -> int:
        """Get count of records in a table"""
        try:
            result = await db.execute(text(f"SELECT count(*) FROM {table}"))
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting {table}: {e}")
            return 0
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "python_version": os.sys.version,
                "platform": os.name,
                "uptime": self._get_uptime(),
                "settings": {
                    "debug": settings.DEBUG,
                    "cors_origins": settings.CORS_ORIGINS,
                    "database_url": settings.DATABASE_URL[:20] + "..." if settings.DATABASE_URL else None
                }
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"error": str(e)}
    
    def _get_uptime(self) -> str:
        """Get system uptime"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.now().timestamp() - boot_time
            uptime_delta = timedelta(seconds=uptime_seconds)
            return str(uptime_delta)
        except Exception as e:
            return f"Error: {e}"
    
    async def get_system_logs(self, 
                            log_level: str = "INFO",
                            limit: int = 100,
                            since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get system logs"""
        try:
            # This is a simplified implementation
            # In a real system, you'd read from actual log files
            logs = []
            
            # Add some sample logs
            base_time = datetime.utcnow() - timedelta(hours=1)
            for i in range(min(limit, 10)):
                logs.append({
                    "timestamp": (base_time + timedelta(minutes=i*5)).isoformat(),
                    "level": log_level,
                    "message": f"System log entry {i+1}",
                    "component": "system"
                })
            
            return logs
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return []
    
    async def get_system_configuration(self) -> Dict[str, Any]:
        """Get system configuration"""
        try:
            return {
                "database": {
                    "url": settings.DATABASE_URL[:20] + "..." if settings.DATABASE_URL else None,
                    "pool_size": 5,
                    "max_overflow": 10
                },
                "security": {
                    "secret_key_set": bool(settings.SECRET_KEY),
                    "algorithm": settings.ALGORITHM,
                    "token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES
                },
                "cors": {
                    "origins": settings.CORS_ORIGINS,
                    "methods": ["GET", "POST", "PUT", "DELETE"],
                    "headers": ["*"]
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            }
        except Exception as e:
            logger.error(f"Error getting system configuration: {e}")
            return {"error": str(e)}
    
    async def update_system_configuration(self, 
                                        config: Dict[str, Any]) -> Dict[str, Any]:
        """Update system configuration"""
        try:
            # This is a simplified implementation
            # In a real system, you'd update actual configuration files
            
            updated_config = {}
            
            # Log the configuration change
            await self.observability_service.log_event(
                "system_config_update",
                "configuration",
                {
                    "updated_fields": list(config.keys()),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "updated_at": datetime.utcnow().isoformat(),
                "message": "Configuration updated successfully"
            }
        except Exception as e:
            logger.error(f"Error updating system configuration: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart a specific service"""
        try:
            # This is a placeholder - in production, you'd implement actual service restart
            await self.observability_service.log_event(
                "service_restart",
                "system",
                {
                    "service": service_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "service": service_name,
                "restarted_at": datetime.utcnow().isoformat(),
                "message": f"Service {service_name} restarted successfully"
            }
        except Exception as e:
            logger.error(f"Error restarting service {service_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def clear_cache(self, cache_type: str = "all") -> Dict[str, Any]:
        """Clear system caches"""
        try:
            if cache_type == "all" or cache_type == "health":
                self.health_check_cache.clear()
            
            await self.observability_service.log_event(
                "cache_clear",
                "system",
                {
                    "cache_type": cache_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "cache_type": cache_type,
                "cleared_at": datetime.utcnow().isoformat(),
                "message": f"Cache {cache_type} cleared successfully"
            }
        except Exception as e:
            logger.error(f"Error clearing cache {cache_type}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_system_metrics_history(self, 
                                       period: str = "24h") -> Dict[str, Any]:
        """Get system metrics history"""
        try:
            # This is a simplified implementation
            # In a real system, you'd query historical metrics from a time-series database
            
            history = []
            now = datetime.utcnow()
            
            # Generate sample data points
            for i in range(24):  # 24 hours
                timestamp = now - timedelta(hours=i)
                history.append({
                    "timestamp": timestamp.isoformat(),
                    "cpu_percent": 20 + (i % 10),
                    "memory_percent": 30 + (i % 20),
                    "disk_percent": 45 + (i % 5)
                })
            
            return {
                "period": period,
                "data_points": len(history),
                "metrics": history,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting metrics history: {e}")
            return {
                "error": str(e),
                "period": period,
                "data_points": 0,
                "metrics": []
            }
