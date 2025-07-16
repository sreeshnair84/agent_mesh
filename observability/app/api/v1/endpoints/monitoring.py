"""
Monitoring API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import Response
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.services.monitoring import MonitoringService, MonitoringWebSocketHandler, TimeRange, DashboardConfig
from app.services.metrics import MetricsCollector, MetricsQuery
from app.services.alerting import AlertingService, AlertRule, AlertSeverity
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


# Dependency injection
async def get_monitoring_service():
    """Get monitoring service instance"""
    # In a real implementation, this would be injected from the app state
    service = MonitoringService()
    await service.initialize()
    return service


async def get_metrics_collector():
    """Get metrics collector instance"""
    collector = MetricsCollector()
    await collector.initialize()
    return collector


async def get_alerting_service():
    """Get alerting service instance"""
    service = AlertingService()
    await service.initialize()
    return service


@router.get("/overview")
async def get_system_overview(
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """Get system overview"""
    try:
        overview = await monitoring_service.get_system_overview()
        return {
            "total_agents": overview.total_agents,
            "active_agents": overview.active_agents,
            "failed_agents": overview.failed_agents,
            "total_requests": overview.total_requests,
            "success_rate": overview.success_rate,
            "average_response_time": overview.average_response_time,
            "cpu_usage": overview.cpu_usage,
            "memory_usage": overview.memory_usage,
            "disk_usage": overview.disk_usage,
            "uptime": overview.uptime,
            "timestamp": overview.timestamp.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_agent_status(
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """Get agent status list"""
    try:
        topology = await monitoring_service.get_agent_network_topology()
        agents = [node for node in topology.nodes if node.get("type") == "agent"]
        return {
            "agents": agents,
            "total": len(agents),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent_details(
    agent_id: str,
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """Get agent details"""
    try:
        # Get agent metrics
        query = MetricsQuery(
            agent_ids=[agent_id],
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow()
        )
        
        metrics_result = await metrics_collector.get_metrics(query)
        
        # Get topology info
        topology = await monitoring_service.get_agent_network_topology()
        agent_node = next((node for node in topology.nodes if node.get("id") == agent_id), None)
        
        if not agent_node:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Calculate metrics
        response_times = []
        cpu_usage = 0
        memory_usage = 0
        request_count = 0
        
        for metric in metrics_result.metrics:
            if metric.metric_name == "response_time_seconds":
                response_times.append(metric.value)
            elif metric.metric_name == "cpu_usage_percent":
                cpu_usage = metric.value
            elif metric.metric_name == "memory_usage_bytes":
                memory_usage = metric.value
            elif metric.metric_name == "request_count":
                request_count += metric.value
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "id": agent_id,
            "name": agent_node.get("name"),
            "type": agent_node.get("type"),
            "status": agent_node.get("status"),
            "metrics": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "average_response_time": avg_response_time,
                "request_count": request_count
            },
            "recent_metrics": [
                {
                    "name": metric.metric_name,
                    "value": metric.value,
                    "timestamp": metric.timestamp.isoformat(),
                    "unit": metric.unit
                }
                for metric in metrics_result.metrics[-10:]  # Last 10 metrics
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def query_metrics(
    agent_ids: Optional[List[str]] = Query(None),
    metric_names: Optional[List[str]] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(1000),
    metrics_collector: MetricsCollector = Depends(get_metrics_collector)
):
    """Query metrics"""
    try:
        query = MetricsQuery(
            agent_ids=agent_ids,
            metric_names=metric_names,
            start_time=start_time or datetime.utcnow() - timedelta(hours=1),
            end_time=end_time or datetime.utcnow(),
            limit=limit
        )
        
        result = await metrics_collector.get_metrics(query)
        
        return {
            "metrics": [
                {
                    "agent_id": metric.agent_id,
                    "metric_name": metric.metric_name,
                    "value": metric.value,
                    "timestamp": metric.timestamp.isoformat(),
                    "labels": metric.labels,
                    "unit": metric.unit
                }
                for metric in result.metrics
            ],
            "total": result.total,
            "query": {
                "agent_ids": query.agent_ids,
                "metric_names": query.metric_names,
                "start_time": query.start_time.isoformat() if query.start_time else None,
                "end_time": query.end_time.isoformat() if query.end_time else None,
                "limit": query.limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/trends")
async def get_performance_trends(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """Get performance trends"""
    try:
        time_range = TimeRange(start=start_time, end=end_time)
        trends = await monitoring_service.get_performance_trends(time_range)
        
        return {
            "trends": {
                name: {
                    "timestamps": [ts.isoformat() for ts in trend.timestamps],
                    "values": trend.values,
                    "metric_name": trend.metric_name,
                    "unit": trend.unit
                }
                for name, trend in trends.items()
            },
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = Query(None),
    alerting_service: AlertingService = Depends(get_alerting_service)
):
    """List alerts"""
    try:
        alerts = await alerting_service.get_alerts()
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity.value == severity]
        
        return {
            "alerts": [
                {
                    "id": alert.id,
                    "rule_name": alert.rule_name,
                    "severity": alert.severity.value,
                    "status": alert.status.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                    "agent_id": alert.agent_id,
                    "metric_name": alert.metric_name,
                    "threshold": alert.threshold,
                    "current_value": alert.current_value,
                    "labels": alert.labels
                }
                for alert in alerts
            ],
            "total": len(alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts")
async def create_alert_rule(
    rule_data: Dict[str, Any],
    alerting_service: AlertingService = Depends(get_alerting_service)
):
    """Create alert rule"""
    try:
        # Validate and create alert rule
        rule = AlertRule(
            name=rule_data["name"],
            condition=rule_data["condition"],
            duration=rule_data["duration"],
            severity=AlertSeverity(rule_data["severity"]),
            description=rule_data["description"],
            metric_name=rule_data["metric_name"],
            threshold=float(rule_data["threshold"]),
            operator=rule_data["operator"],
            enabled=rule_data.get("enabled", True),
            actions=rule_data.get("actions", []),
            labels=rule_data.get("labels", {})
        )
        
        await alerting_service.add_alert_rule(rule)
        
        return {
            "message": "Alert rule created successfully",
            "rule_name": rule.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/alerts/{alert_id}")
async def resolve_alert(
    alert_id: str,
    alerting_service: AlertingService = Depends(get_alerting_service)
):
    """Resolve alert"""
    try:
        await alerting_service.resolve_alert(alert_id)
        return {"message": "Alert resolved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topology")
async def get_network_topology(
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """Get network topology"""
    try:
        topology = await monitoring_service.get_agent_network_topology()
        
        return {
            "nodes": topology.nodes,
            "edges": topology.edges,
            "clusters": topology.clusters,
            "metrics": topology.metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def query_logs(
    agent_id: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100)
):
    """Query logs"""
    try:
        # TODO: Implement actual log querying
        # For now, return mock data
        logs = [
            {
                "id": "log-1",
                "timestamp": datetime.utcnow().isoformat(),
                "level": "info",
                "message": "Agent request processed successfully",
                "agent_id": agent_id or "agent-1",
                "source": "agent_executor",
                "context": {"request_id": "req-123"}
            }
        ]
        
        return {
            "logs": logs,
            "total": len(logs),
            "query": {
                "agent_id": agent_id,
                "level": level,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboard")
async def create_dashboard(
    config_data: Dict[str, Any],
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
):
    """Create custom dashboard"""
    try:
        config = DashboardConfig(
            name=config_data["name"],
            layout=config_data["layout"],
            metrics=config_data["metrics"],
            filters=config_data.get("filters", {}),
            refresh_interval=config_data.get("refresh_interval", 30)
        )
        
        dashboard_id = await monitoring_service.create_custom_dashboard(config)
        
        return {
            "dashboard_id": dashboard_id,
            "message": "Dashboard created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "monitoring",
        "timestamp": datetime.utcnow().isoformat()
    }


# WebSocket endpoints
@router.websocket("/ws/metrics")
async def websocket_metrics(
    websocket: WebSocket,
    agent_ids: Optional[str] = Query(None)
):
    """WebSocket for real-time metrics"""
    await websocket.accept()
    
    monitoring_service = MonitoringService()
    await monitoring_service.initialize()
    
    handler = MonitoringWebSocketHandler(monitoring_service)
    
    try:
        if agent_ids:
            agent_id_list = agent_ids.split(",")
            await handler.stream_agent_status(websocket, agent_id_list)
        else:
            await handler.stream_system_metrics(websocket)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket for real-time alerts"""
    await websocket.accept()
    
    monitoring_service = MonitoringService()
    await monitoring_service.initialize()
    
    handler = MonitoringWebSocketHandler(monitoring_service)
    
    try:
        await handler.stream_alerts(websocket)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))


@router.websocket("/ws/topology")
async def websocket_topology(websocket: WebSocket):
    """WebSocket for real-time topology updates"""
    await websocket.accept()
    
    monitoring_service = MonitoringService()
    await monitoring_service.initialize()
    
    handler = MonitoringWebSocketHandler(monitoring_service)
    
    try:
        await handler.stream_network_topology(websocket)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))


@router.get("/prometheus")
async def get_prometheus_metrics():
    """Get Prometheus format metrics"""
    try:
        from app.services.metrics import MetricsService
        
        metrics_service = MetricsService()
        prometheus_metrics = metrics_service.get_prometheus_metrics()
        
        return Response(
            content=prometheus_metrics,
            media_type="text/plain"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
