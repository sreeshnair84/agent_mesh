"""
Monitoring service for real-time system monitoring
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog
from fastapi import WebSocket
import aioredis

from ..core.config import get_settings
from .metrics import MetricsCollector, Metric, MetricsQuery

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass
class SystemOverview:
    """System overview data structure"""
    total_agents: int
    active_agents: int
    failed_agents: int
    total_requests: int
    success_rate: float
    average_response_time: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime: str
    timestamp: datetime


@dataclass
class NetworkTopology:
    """Network topology data structure"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    clusters: List[Dict[str, Any]]
    metrics: Dict[str, Any]


@dataclass
class TimeRange:
    """Time range for queries"""
    start: datetime
    end: datetime


@dataclass
class TrendData:
    """Trend data structure"""
    timestamps: List[datetime]
    values: List[float]
    metric_name: str
    unit: str


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    name: str
    severity: str
    message: str
    timestamp: datetime
    resolved: bool
    agent_id: Optional[str] = None
    metric_name: Optional[str] = None
    threshold: Optional[float] = None
    current_value: Optional[float] = None


@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    name: str
    layout: Dict[str, Any]
    metrics: List[str]
    filters: Dict[str, Any]
    refresh_interval: int


class MonitoringService:
    """Core monitoring service implementing the API specification"""
    
    def __init__(self):
        self.redis_client = None
        self.metrics_collector = MetricsCollector()
        self.active_websockets: List[WebSocket] = []
        self.running = False
        
    async def initialize(self):
        """Initialize the monitoring service"""
        try:
            self.redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            await self.metrics_collector.initialize()
            logger.info("Monitoring service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize monitoring service: {e}")
    
    async def start_monitoring(self):
        """Start monitoring background tasks"""
        self.running = True
        logger.info("Starting monitoring service")
        
        # Start monitoring tasks
        await asyncio.gather(
            self._monitor_system_health(),
            self._monitor_agents(),
            self._monitor_network_topology(),
            self._broadcast_updates()
        )
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        logger.info("Stopping monitoring service")
    
    async def get_system_overview(self) -> SystemOverview:
        """Get system overview"""
        try:
            # Get recent metrics
            query = MetricsQuery(
                start_time=datetime.utcnow() - timedelta(minutes=5),
                end_time=datetime.utcnow()
            )
            
            result = await self.metrics_collector.get_metrics(query)
            
            # Aggregate metrics
            total_agents = 0
            active_agents = 0
            failed_agents = 0
            total_requests = 0
            response_times = []
            success_count = 0
            error_count = 0
            cpu_usage = 0
            memory_usage = 0
            
            for metric in result.metrics:
                if metric.metric_name == 'active_agents':
                    active_agents = int(metric.value)
                elif metric.metric_name == 'request_count':
                    total_requests += int(metric.value)
                    if metric.labels.get('status') == 'success':
                        success_count += int(metric.value)
                    else:
                        error_count += int(metric.value)
                elif metric.metric_name == 'response_time_seconds':
                    response_times.append(metric.value)
                elif metric.metric_name == 'cpu_usage_percent':
                    cpu_usage = metric.value
                elif metric.metric_name == 'memory_usage_bytes':
                    memory_usage = metric.value
            
            # Calculate averages
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            success_rate = (success_count / (success_count + error_count)) * 100 if (success_count + error_count) > 0 else 0
            
            # Get system uptime (placeholder)
            uptime = "2d 14h 32m"  # TODO: Calculate actual uptime
            
            return SystemOverview(
                total_agents=total_agents,
                active_agents=active_agents,
                failed_agents=failed_agents,
                total_requests=total_requests,
                success_rate=success_rate,
                average_response_time=avg_response_time,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage / (1024 * 1024 * 1024),  # Convert to GB
                disk_usage=0,  # TODO: Implement disk usage
                uptime=uptime,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return SystemOverview(
                total_agents=0,
                active_agents=0,
                failed_agents=0,
                total_requests=0,
                success_rate=0,
                average_response_time=0,
                cpu_usage=0,
                memory_usage=0,
                disk_usage=0,
                uptime="0s",
                timestamp=datetime.utcnow()
            )
    
    async def get_agent_network_topology(self) -> NetworkTopology:
        """Get agent network topology"""
        try:
            # TODO: Implement actual topology discovery
            nodes = [
                {
                    "id": "agent-1",
                    "name": "Customer Support Agent",
                    "type": "agent",
                    "status": "active",
                    "metrics": {
                        "cpu_usage": 25.5,
                        "memory_usage": 128.5,
                        "request_count": 150
                    }
                },
                {
                    "id": "agent-2",
                    "name": "Data Analysis Agent",
                    "type": "agent",
                    "status": "active",
                    "metrics": {
                        "cpu_usage": 45.2,
                        "memory_usage": 256.8,
                        "request_count": 89
                    }
                },
                {
                    "id": "workflow-1",
                    "name": "Data Processing Workflow",
                    "type": "workflow",
                    "status": "running",
                    "metrics": {
                        "execution_time": 2.5,
                        "success_rate": 95.2
                    }
                }
            ]
            
            edges = [
                {
                    "source": "agent-1",
                    "target": "workflow-1",
                    "type": "triggers",
                    "metrics": {
                        "message_count": 25,
                        "avg_latency": 0.15
                    }
                },
                {
                    "source": "agent-2",
                    "target": "workflow-1",
                    "type": "provides_data",
                    "metrics": {
                        "data_volume": 1024,
                        "avg_processing_time": 0.85
                    }
                }
            ]
            
            clusters = [
                {
                    "id": "customer-service",
                    "name": "Customer Service Cluster",
                    "nodes": ["agent-1"],
                    "status": "healthy"
                },
                {
                    "id": "data-processing",
                    "name": "Data Processing Cluster",
                    "nodes": ["agent-2", "workflow-1"],
                    "status": "healthy"
                }
            ]
            
            return NetworkTopology(
                nodes=nodes,
                edges=edges,
                clusters=clusters,
                metrics={
                    "total_nodes": len(nodes),
                    "active_connections": len(edges),
                    "cluster_health": "healthy"
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting network topology: {e}")
            return NetworkTopology(
                nodes=[],
                edges=[],
                clusters=[],
                metrics={}
            )
    
    async def get_performance_trends(self, time_range: TimeRange) -> Dict[str, TrendData]:
        """Get performance trends over time"""
        try:
            query = MetricsQuery(
                start_time=time_range.start,
                end_time=time_range.end,
                limit=10000
            )
            
            result = await self.metrics_collector.get_metrics(query)
            
            # Group metrics by name
            trends = {}
            
            for metric in result.metrics:
                if metric.metric_name not in trends:
                    trends[metric.metric_name] = {
                        'timestamps': [],
                        'values': [],
                        'unit': metric.unit
                    }
                
                trends[metric.metric_name]['timestamps'].append(metric.timestamp)
                trends[metric.metric_name]['values'].append(metric.value)
            
            # Convert to TrendData objects
            trend_data = {}
            for name, data in trends.items():
                trend_data[name] = TrendData(
                    timestamps=data['timestamps'],
                    values=data['values'],
                    metric_name=name,
                    unit=data['unit']
                )
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {}
    
    async def get_alerts(self, severity: str = None) -> List[Alert]:
        """Get system alerts"""
        try:
            # TODO: Implement alert storage and retrieval
            alerts = [
                Alert(
                    id="alert-1",
                    name="High CPU Usage",
                    severity="warning",
                    message="CPU usage is above 80%",
                    timestamp=datetime.utcnow() - timedelta(minutes=5),
                    resolved=False,
                    agent_id="agent-1",
                    metric_name="cpu_usage_percent",
                    threshold=80.0,
                    current_value=85.5
                ),
                Alert(
                    id="alert-2",
                    name="Agent Failure",
                    severity="critical",
                    message="Agent has failed to respond",
                    timestamp=datetime.utcnow() - timedelta(minutes=10),
                    resolved=False,
                    agent_id="agent-3"
                )
            ]
            
            if severity:
                alerts = [alert for alert in alerts if alert.severity == severity]
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
    
    async def create_custom_dashboard(self, config: DashboardConfig) -> str:
        """Create custom dashboard"""
        try:
            dashboard_id = f"dashboard-{datetime.utcnow().timestamp()}"
            
            # Store dashboard configuration
            if self.redis_client:
                await self.redis_client.setex(
                    f"dashboard:{dashboard_id}",
                    3600,  # 1 hour TTL
                    json.dumps({
                        "name": config.name,
                        "layout": config.layout,
                        "metrics": config.metrics,
                        "filters": config.filters,
                        "refresh_interval": config.refresh_interval,
                        "created_at": datetime.utcnow().isoformat()
                    })
                )
            
            logger.info(f"Created custom dashboard: {dashboard_id}")
            return dashboard_id
            
        except Exception as e:
            logger.error(f"Error creating custom dashboard: {e}")
            raise
    
    async def _monitor_system_health(self):
        """Monitor system health"""
        while self.running:
            try:
                # Get system metrics
                overview = await self.get_system_overview()
                
                # Check for alerts
                if overview.cpu_usage > 80:
                    await self._create_alert(
                        "high_cpu_usage",
                        "warning",
                        f"CPU usage is {overview.cpu_usage:.1f}%",
                        "cpu_usage_percent",
                        80.0,
                        overview.cpu_usage
                    )
                
                if overview.memory_usage > 80:
                    await self._create_alert(
                        "high_memory_usage",
                        "warning",
                        f"Memory usage is {overview.memory_usage:.1f}GB",
                        "memory_usage_bytes",
                        80.0,
                        overview.memory_usage
                    )
                
                if overview.success_rate < 95:
                    await self._create_alert(
                        "low_success_rate",
                        "critical",
                        f"Success rate is {overview.success_rate:.1f}%",
                        "success_rate",
                        95.0,
                        overview.success_rate
                    )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring system health: {e}")
                await asyncio.sleep(10)
    
    async def _monitor_agents(self):
        """Monitor agent status"""
        while self.running:
            try:
                # TODO: Implement agent monitoring
                # Check agent heartbeats, response times, etc.
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error monitoring agents: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_network_topology(self):
        """Monitor network topology changes"""
        while self.running:
            try:
                # TODO: Implement topology change detection
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error monitoring network topology: {e}")
                await asyncio.sleep(60)
    
    async def _broadcast_updates(self):
        """Broadcast real-time updates to WebSocket clients"""
        while self.running:
            try:
                if self.active_websockets:
                    overview = await self.get_system_overview()
                    
                    message = {
                        "type": "system_overview",
                        "data": {
                            "total_agents": overview.total_agents,
                            "active_agents": overview.active_agents,
                            "cpu_usage": overview.cpu_usage,
                            "memory_usage": overview.memory_usage,
                            "success_rate": overview.success_rate,
                            "timestamp": overview.timestamp.isoformat()
                        }
                    }
                    
                    # Send to all connected clients
                    disconnected = []
                    for websocket in self.active_websockets:
                        try:
                            await websocket.send_text(json.dumps(message))
                        except Exception:
                            disconnected.append(websocket)
                    
                    # Remove disconnected clients
                    for websocket in disconnected:
                        self.active_websockets.remove(websocket)
                
                await asyncio.sleep(10)  # Broadcast every 10 seconds
                
            except Exception as e:
                logger.error(f"Error broadcasting updates: {e}")
                await asyncio.sleep(5)
    
    async def _create_alert(self, name: str, severity: str, message: str, 
                           metric_name: str = None, threshold: float = None, 
                           current_value: float = None):
        """Create a new alert"""
        try:
            alert = Alert(
                id=f"alert-{datetime.utcnow().timestamp()}",
                name=name,
                severity=severity,
                message=message,
                timestamp=datetime.utcnow(),
                resolved=False,
                metric_name=metric_name,
                threshold=threshold,
                current_value=current_value
            )
            
            # Store alert in Redis
            if self.redis_client:
                await self.redis_client.setex(
                    f"alert:{alert.id}",
                    3600,  # 1 hour TTL
                    json.dumps({
                        "name": alert.name,
                        "severity": alert.severity,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "metric_name": alert.metric_name,
                        "threshold": alert.threshold,
                        "current_value": alert.current_value
                    })
                )
            
            logger.warning(f"Alert created: {alert.name} - {alert.message}")
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    def add_websocket(self, websocket: WebSocket):
        """Add WebSocket connection"""
        self.active_websockets.append(websocket)
    
    def remove_websocket(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_websockets:
            self.active_websockets.remove(websocket)


class MonitoringWebSocketHandler:
    """WebSocket handler for real-time monitoring data"""
    
    def __init__(self, monitoring_service: MonitoringService):
        self.monitoring_service = monitoring_service
    
    async def stream_system_metrics(self, websocket: WebSocket):
        """Stream system metrics"""
        try:
            self.monitoring_service.add_websocket(websocket)
            
            while True:
                await websocket.receive_text()  # Keep connection alive
                
        except Exception as e:
            logger.info(f"WebSocket disconnected: {e}")
        finally:
            self.monitoring_service.remove_websocket(websocket)
    
    async def stream_agent_status(self, websocket: WebSocket, agent_ids: List[str]):
        """Stream agent status updates"""
        try:
            self.monitoring_service.add_websocket(websocket)
            
            # Stream agent-specific metrics
            async for metric in self.monitoring_service.metrics_collector.get_real_time_metrics(agent_ids):
                message = {
                    "type": "agent_metric",
                    "data": {
                        "agent_id": metric.agent_id,
                        "metric_name": metric.metric_name,
                        "value": metric.value,
                        "timestamp": metric.timestamp.isoformat(),
                        "labels": metric.labels
                    }
                }
                
                await websocket.send_text(json.dumps(message))
                
        except Exception as e:
            logger.info(f"WebSocket disconnected: {e}")
        finally:
            self.monitoring_service.remove_websocket(websocket)
    
    async def stream_alerts(self, websocket: WebSocket):
        """Stream alerts"""
        try:
            self.monitoring_service.add_websocket(websocket)
            
            while True:
                alerts = await self.monitoring_service.get_alerts()
                
                message = {
                    "type": "alerts",
                    "data": [
                        {
                            "id": alert.id,
                            "name": alert.name,
                            "severity": alert.severity,
                            "message": alert.message,
                            "timestamp": alert.timestamp.isoformat(),
                            "resolved": alert.resolved
                        }
                        for alert in alerts
                    ]
                }
                
                await websocket.send_text(json.dumps(message))
                await asyncio.sleep(30)  # Send every 30 seconds
                
        except Exception as e:
            logger.info(f"WebSocket disconnected: {e}")
        finally:
            self.monitoring_service.remove_websocket(websocket)
    
    async def stream_network_topology(self, websocket: WebSocket):
        """Stream network topology updates"""
        try:
            self.monitoring_service.add_websocket(websocket)
            
            while True:
                topology = await self.monitoring_service.get_agent_network_topology()
                
                message = {
                    "type": "network_topology",
                    "data": {
                        "nodes": topology.nodes,
                        "edges": topology.edges,
                        "clusters": topology.clusters,
                        "metrics": topology.metrics
                    }
                }
                
                await websocket.send_text(json.dumps(message))
                await asyncio.sleep(60)  # Send every minute
                
        except Exception as e:
            logger.info(f"WebSocket disconnected: {e}")
        finally:
            self.monitoring_service.remove_websocket(websocket)
