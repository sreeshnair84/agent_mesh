"""
Integration interfaces for Team A (Core Framework) and Team B (Agent Management)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import asyncio
import json
from dataclasses import dataclass

from .services.metrics import MetricsCollector, Metric
from .services.alerting import AlertingService


@dataclass
class AgentMetadata:
    """Agent metadata structure"""
    id: str
    name: str
    type: str
    version: str
    capabilities: List[str]
    created_at: datetime
    updated_at: datetime
    status: str
    configuration: Dict[str, Any]


@dataclass
class DeploymentInfo:
    """Deployment information structure"""
    deployment_id: str
    agent_id: str
    environment: str
    resources: Dict[str, Any]
    status: str
    deployed_at: datetime
    health_check_url: Optional[str] = None
    logs_path: Optional[str] = None


class CoreFrameworkIntegration:
    """Integration interface for Team A - Core Framework"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    async def record_message_processing_time(self, agent_id: str, processing_time: float):
        """Record message processing time from core framework"""
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name="message_processing_time",
            value=processing_time,
            timestamp=datetime.utcnow(),
            labels={"source": "core_framework"},
            unit="seconds"
        ))
    
    async def record_message_count(self, agent_id: str, message_count: int, message_type: str):
        """Record message count from core framework"""
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name="message_count",
            value=float(message_count),
            timestamp=datetime.utcnow(),
            labels={"source": "core_framework", "message_type": message_type},
            unit="count"
        ))
    
    async def record_broker_metrics(self, broker_metrics: Dict[str, Any]):
        """Record message broker metrics"""
        for metric_name, value in broker_metrics.items():
            await self.metrics_collector.record_metric(Metric(
                agent_id="system",
                metric_name=f"broker_{metric_name}",
                value=float(value),
                timestamp=datetime.utcnow(),
                labels={"source": "message_broker"},
                unit="count" if "count" in metric_name else "seconds"
            ))
    
    async def record_workflow_execution(self, workflow_id: str, execution_time: float, 
                                       status: str, agent_id: str):
        """Record workflow execution metrics"""
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name="workflow_execution_time",
            value=execution_time,
            timestamp=datetime.utcnow(),
            labels={"workflow_id": workflow_id, "status": status, "source": "core_framework"},
            unit="seconds"
        ))
        
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name="workflow_execution_count",
            value=1.0,
            timestamp=datetime.utcnow(),
            labels={"workflow_id": workflow_id, "status": status, "source": "core_framework"},
            unit="count"
        ))
    
    async def record_error_metrics(self, agent_id: str, error_type: str, error_message: str):
        """Record error metrics from core framework"""
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name="error_count",
            value=1.0,
            timestamp=datetime.utcnow(),
            labels={
                "error_type": error_type,
                "error_message": error_message[:100],  # Truncate long messages
                "source": "core_framework"
            },
            unit="count"
        ))


class AgentLifecycleMonitor:
    """Monitor agent lifecycle events for Team B - Agent Management"""
    
    def __init__(self, metrics_collector: MetricsCollector, alerting_service: AlertingService):
        self.metrics_collector = metrics_collector
        self.alerting_service = alerting_service
    
    async def on_agent_created(self, agent_id: str, metadata: AgentMetadata):
        """Handle agent creation event"""
        # Record agent creation metric
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name="agent_lifecycle_event",
            value=1.0,
            timestamp=datetime.utcnow(),
            labels={
                "event": "created",
                "agent_type": metadata.type,
                "agent_name": metadata.name,
                "source": "agent_management"
            },
            unit="count"
        ))
        
        # Record agent metadata
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name="agent_capabilities_count",
            value=float(len(metadata.capabilities)),
            timestamp=datetime.utcnow(),
            labels={
                "agent_type": metadata.type,
                "agent_name": metadata.name,
                "source": "agent_management"
            },
            unit="count"
        ))
    
    async def on_agent_deployed(self, agent_id: str, deployment_info: DeploymentInfo):
        """Handle agent deployment event"""
        # Record deployment metric
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name="agent_lifecycle_event",
            value=1.0,
            timestamp=datetime.utcnow(),
            labels={
                "event": "deployed",
                "deployment_id": deployment_info.deployment_id,
                "environment": deployment_info.environment,
                "status": deployment_info.status,
                "source": "agent_management"
            },
            unit="count"
        ))
        
        # Record resource allocation
        if deployment_info.resources:
            for resource_type, amount in deployment_info.resources.items():
                await self.metrics_collector.record_metric(Metric(
                    agent_id=agent_id,
                    metric_name=f"resource_allocation_{resource_type}",
                    value=float(amount),
                    timestamp=datetime.utcnow(),
                    labels={
                        "deployment_id": deployment_info.deployment_id,
                        "environment": deployment_info.environment,
                        "source": "agent_management"
                    },
                    unit="units"
                ))
    
    async def on_agent_error(self, agent_id: str, error: Exception):
        """Handle agent error event"""
        # Record error metric
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name="agent_error_count",
            value=1.0,
            timestamp=datetime.utcnow(),
            labels={
                "error_type": error.__class__.__name__,
                "error_message": str(error)[:100],  # Truncate long messages
                "source": "agent_management"
            },
            unit="count"
        ))
        
        # Trigger alert for critical errors
        if isinstance(error, (ConnectionError, TimeoutError, RuntimeError)):
            # This would trigger an alert through the alerting service
            # The alerting service would handle the alert based on configured rules
            pass
    
    async def on_agent_stopped(self, agent_id: str, reason: str):
        """Handle agent stop event"""
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name="agent_lifecycle_event",
            value=1.0,
            timestamp=datetime.utcnow(),
            labels={
                "event": "stopped",
                "reason": reason,
                "source": "agent_management"
            },
            unit="count"
        ))
    
    async def on_agent_health_check(self, agent_id: str, health_status: str, 
                                   response_time: float):
        """Handle agent health check event"""
        # Record health status
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name="agent_health_status",
            value=1.0 if health_status == "healthy" else 0.0,
            timestamp=datetime.utcnow(),
            labels={
                "status": health_status,
                "source": "agent_management"
            },
            unit="boolean"
        ))
        
        # Record health check response time
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name="health_check_response_time",
            value=response_time,
            timestamp=datetime.utcnow(),
            labels={
                "status": health_status,
                "source": "agent_management"
            },
            unit="seconds"
        ))


class PerformanceAnalyticsEngine:
    """Performance analytics engine for analyzing collected metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    async def calculate_agent_performance_score(self, agent_id: str, 
                                               time_window: int = 3600) -> float:
        """Calculate performance score for an agent"""
        from .services.metrics import MetricsQuery
        
        # Get metrics for the last hour
        query = MetricsQuery(
            agent_ids=[agent_id],
            start_time=datetime.utcnow() - timedelta(seconds=time_window),
            end_time=datetime.utcnow()
        )
        
        result = await self.metrics_collector.get_metrics(query)
        
        # Calculate performance metrics
        response_times = []
        error_count = 0
        success_count = 0
        cpu_usage = 0
        memory_usage = 0
        
        for metric in result.metrics:
            if metric.metric_name == "response_time_seconds":
                response_times.append(metric.value)
            elif metric.metric_name == "error_count":
                error_count += metric.value
            elif metric.metric_name == "success_count":
                success_count += metric.value
            elif metric.metric_name == "cpu_usage_percent":
                cpu_usage = max(cpu_usage, metric.value)
            elif metric.metric_name == "memory_usage_percent":
                memory_usage = max(memory_usage, metric.value)
        
        # Calculate score components
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        total_requests = error_count + success_count
        success_rate = (success_count / total_requests) if total_requests > 0 else 1.0
        
        # Calculate performance score (0-100)
        response_time_score = max(0, 100 - (avg_response_time * 50))  # Penalty for slow responses
        success_rate_score = success_rate * 100
        resource_score = max(0, 100 - cpu_usage - memory_usage)  # Penalty for high resource usage
        
        # Weighted average
        performance_score = (
            response_time_score * 0.3 +
            success_rate_score * 0.5 +
            resource_score * 0.2
        )
        
        return min(100, max(0, performance_score))
    
    async def generate_performance_report(self, agent_id: str) -> Dict[str, Any]:
        """Generate comprehensive performance report for an agent"""
        from .services.metrics import MetricsQuery
        
        # Get metrics for the last 24 hours
        query = MetricsQuery(
            agent_ids=[agent_id],
            start_time=datetime.utcnow() - timedelta(hours=24),
            end_time=datetime.utcnow()
        )
        
        result = await self.metrics_collector.get_metrics(query)
        
        # Analyze metrics
        metrics_by_hour = {}
        total_requests = 0
        total_errors = 0
        response_times = []
        
        for metric in result.metrics:
            hour = metric.timestamp.hour
            if hour not in metrics_by_hour:
                metrics_by_hour[hour] = {"requests": 0, "errors": 0, "response_times": []}
            
            if metric.metric_name == "request_count":
                metrics_by_hour[hour]["requests"] += metric.value
                total_requests += metric.value
            elif metric.metric_name == "error_count":
                metrics_by_hour[hour]["errors"] += metric.value
                total_errors += metric.value
            elif metric.metric_name == "response_time_seconds":
                metrics_by_hour[hour]["response_times"].append(metric.value)
                response_times.append(metric.value)
        
        # Calculate summary statistics
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        success_rate = ((total_requests - total_errors) / total_requests) if total_requests > 0 else 1.0
        performance_score = await self.calculate_agent_performance_score(agent_id)
        
        # Generate hourly breakdown
        hourly_breakdown = []
        for hour in sorted(metrics_by_hour.keys()):
            hour_data = metrics_by_hour[hour]
            hour_avg_response = sum(hour_data["response_times"]) / len(hour_data["response_times"]) if hour_data["response_times"] else 0
            hour_success_rate = ((hour_data["requests"] - hour_data["errors"]) / hour_data["requests"]) if hour_data["requests"] > 0 else 1.0
            
            hourly_breakdown.append({
                "hour": hour,
                "requests": hour_data["requests"],
                "errors": hour_data["errors"],
                "average_response_time": hour_avg_response,
                "success_rate": hour_success_rate
            })
        
        return {
            "agent_id": agent_id,
            "report_period": "24 hours",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "success_rate": success_rate,
                "average_response_time": avg_response_time,
                "performance_score": performance_score
            },
            "hourly_breakdown": hourly_breakdown,
            "recommendations": self._generate_recommendations(performance_score, success_rate, avg_response_time)
        }
    
    def _generate_recommendations(self, performance_score: float, success_rate: float, 
                                 avg_response_time: float) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        if performance_score < 70:
            recommendations.append("Overall performance is below acceptable threshold. Consider scaling resources.")
        
        if success_rate < 0.95:
            recommendations.append("Success rate is low. Investigate error patterns and improve error handling.")
        
        if avg_response_time > 1.0:
            recommendations.append("Average response time is high. Consider optimizing algorithms or scaling resources.")
        
        if not recommendations:
            recommendations.append("Agent performance is within acceptable parameters.")
        
        return recommendations


# Example usage functions for integration
async def integrate_with_core_framework(metrics_collector: MetricsCollector):
    """Example integration with core framework"""
    integration = CoreFrameworkIntegration(metrics_collector)
    
    # Example: Record message processing time
    await integration.record_message_processing_time("agent-1", 0.5)
    
    # Example: Record message count
    await integration.record_message_count("agent-1", 10, "user_request")
    
    # Example: Record broker metrics
    await integration.record_broker_metrics({
        "messages_processed": 150,
        "queue_size": 25,
        "processing_time": 0.1
    })


async def integrate_with_agent_management(metrics_collector: MetricsCollector, 
                                        alerting_service: AlertingService):
    """Example integration with agent management"""
    monitor = AgentLifecycleMonitor(metrics_collector, alerting_service)
    
    # Example: Handle agent creation
    metadata = AgentMetadata(
        id="agent-1",
        name="Customer Support Agent",
        type="support",
        version="1.0.0",
        capabilities=["text_processing", "sentiment_analysis"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        status="active",
        configuration={"max_concurrent_requests": 10}
    )
    
    await monitor.on_agent_created("agent-1", metadata)
    
    # Example: Handle agent deployment
    deployment_info = DeploymentInfo(
        deployment_id="deploy-1",
        agent_id="agent-1",
        environment="production",
        resources={"cpu": 2, "memory": 4096, "storage": 10240},
        status="deployed",
        deployed_at=datetime.utcnow(),
        health_check_url="http://agent-1:8080/health"
    )
    
    await monitor.on_agent_deployed("agent-1", deployment_info)
