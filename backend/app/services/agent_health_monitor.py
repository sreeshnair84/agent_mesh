"""
Agent Health Monitor
Monitors agent health, performance, and availability
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.agent import Agent, AgentStatus, AgentMetric
from app.core.exceptions import NotFoundError


@dataclass
class HealthCheckResult:
    """Result of health check"""
    agent_id: str
    status: str  # "healthy", "unhealthy", "unknown"
    response_time: float
    error_message: Optional[str] = None
    timestamp: datetime = None
    details: Optional[Dict] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for an agent"""
    agent_id: str
    cpu_usage: float
    memory_usage: float
    request_count: int
    average_response_time: float
    error_rate: float
    uptime: float
    timestamp: datetime


class AgentHealthMonitor:
    """Service for monitoring agent health and performance"""
    
    def __init__(self, db: Session):
        self.db = db
        self.health_check_interval = 30  # seconds
        self.performance_check_interval = 60  # seconds
        self.monitoring_active = False
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        self.monitoring_active = True
        
        # Start health check loop
        asyncio.create_task(self._health_check_loop())
        
        # Start performance metrics loop
        asyncio.create_task(self._performance_metrics_loop())
    
    async def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
    
    async def check_agent_health(self, agent_id: str) -> HealthCheckResult:
        """Check health of a specific agent"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise NotFoundError(f"Agent {agent_id} not found")
            
            if agent.status != AgentStatus.ACTIVE:
                return HealthCheckResult(
                    agent_id=agent_id,
                    status="unhealthy",
                    response_time=0.0,
                    error_message="Agent is not active",
                    timestamp=datetime.utcnow()
                )
            
            if not agent.health_check_url:
                return HealthCheckResult(
                    agent_id=agent_id,
                    status="unknown",
                    response_time=0.0,
                    error_message="No health check URL configured",
                    timestamp=datetime.utcnow()
                )
            
            # Perform HTTP health check
            start_time = datetime.utcnow()
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        agent.health_check_url,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        end_time = datetime.utcnow()
                        response_time = (end_time - start_time).total_seconds()
                        
                        if response.status == 200:
                            response_data = await response.json()
                            
                            # Update agent health status
                            agent.health_status = "healthy"
                            agent.last_health_check = datetime.utcnow()
                            agent.error_count = 0
                            self.db.commit()
                            
                            return HealthCheckResult(
                                agent_id=agent_id,
                                status="healthy",
                                response_time=response_time,
                                timestamp=datetime.utcnow(),
                                details=response_data
                            )
                        else:
                            # Update agent health status
                            agent.health_status = "unhealthy"
                            agent.last_health_check = datetime.utcnow()
                            agent.error_count += 1
                            agent.last_error = f"Health check failed with status {response.status}"
                            agent.last_error_at = datetime.utcnow()
                            self.db.commit()
                            
                            return HealthCheckResult(
                                agent_id=agent_id,
                                status="unhealthy",
                                response_time=response_time,
                                error_message=f"Health check failed with status {response.status}",
                                timestamp=datetime.utcnow()
                            )
                
                except asyncio.TimeoutError:
                    agent.health_status = "unhealthy"
                    agent.last_health_check = datetime.utcnow()
                    agent.error_count += 1
                    agent.last_error = "Health check timeout"
                    agent.last_error_at = datetime.utcnow()
                    self.db.commit()
                    
                    return HealthCheckResult(
                        agent_id=agent_id,
                        status="unhealthy",
                        response_time=10.0,
                        error_message="Health check timeout",
                        timestamp=datetime.utcnow()
                    )
                
                except Exception as e:
                    agent.health_status = "unhealthy"
                    agent.last_health_check = datetime.utcnow()
                    agent.error_count += 1
                    agent.last_error = str(e)
                    agent.last_error_at = datetime.utcnow()
                    self.db.commit()
                    
                    return HealthCheckResult(
                        agent_id=agent_id,
                        status="unhealthy",
                        response_time=0.0,
                        error_message=str(e),
                        timestamp=datetime.utcnow()
                    )
        
        except Exception as e:
            return HealthCheckResult(
                agent_id=agent_id,
                status="unknown",
                response_time=0.0,
                error_message=str(e),
                timestamp=datetime.utcnow()
            )
    
    async def get_agent_metrics(self, agent_id: str) -> PerformanceMetrics:
        """Get performance metrics for an agent"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise NotFoundError(f"Agent {agent_id} not found")
            
            # Get metrics from container orchestrator or metrics endpoint
            metrics_data = await self._fetch_performance_metrics(agent_id)
            
            return PerformanceMetrics(
                agent_id=agent_id,
                cpu_usage=metrics_data.get("cpu_usage", 0.0),
                memory_usage=metrics_data.get("memory_usage", 0.0),
                request_count=metrics_data.get("request_count", 0),
                average_response_time=metrics_data.get("average_response_time", 0.0),
                error_rate=metrics_data.get("error_rate", 0.0),
                uptime=metrics_data.get("uptime", 0.0),
                timestamp=datetime.utcnow()
            )
        
        except Exception as e:
            return PerformanceMetrics(
                agent_id=agent_id,
                cpu_usage=0.0,
                memory_usage=0.0,
                request_count=0,
                average_response_time=0.0,
                error_rate=1.0,
                uptime=0.0,
                timestamp=datetime.utcnow()
            )
    
    async def get_agent_logs(self, agent_id: str, lines: int = 100, since: Optional[datetime] = None) -> List[str]:
        """Get recent logs for an agent"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise NotFoundError(f"Agent {agent_id} not found")
            
            # Get logs from container orchestrator
            from app.services.agent_deployment import ContainerOrchestrator
            orchestrator = ContainerOrchestrator()
            logs = await orchestrator.get_logs(agent_id, lines)
            
            return logs
        
        except Exception as e:
            return [f"Error fetching logs: {str(e)}"]
    
    async def get_health_history(self, agent_id: str, hours: int = 24) -> List[HealthCheckResult]:
        """Get health check history for an agent"""
        # In a real implementation, this would fetch from a time-series database
        # For now, we'll simulate some historical data
        history = []
        current_time = datetime.utcnow()
        
        for i in range(hours):
            timestamp = current_time - timedelta(hours=i)
            
            # Simulate health check results
            if i < 2:  # Recent checks
                status = "healthy"
                response_time = 0.15
                error_message = None
            elif i < 5:  # Some issues
                status = "unhealthy"
                response_time = 2.0
                error_message = "High response time"
            else:  # Normal operation
                status = "healthy"
                response_time = 0.12
                error_message = None
            
            history.append(HealthCheckResult(
                agent_id=agent_id,
                status=status,
                response_time=response_time,
                error_message=error_message,
                timestamp=timestamp
            ))
        
        return history
    
    async def get_performance_history(self, agent_id: str, hours: int = 24) -> List[PerformanceMetrics]:
        """Get performance metrics history for an agent"""
        # Query metrics from database
        since = datetime.utcnow() - timedelta(hours=hours)
        
        metrics = self.db.query(AgentMetric).filter(
            AgentMetric.agent_id == agent_id,
            AgentMetric.timestamp >= since
        ).order_by(AgentMetric.timestamp.desc()).all()
        
        # Convert to PerformanceMetrics objects
        performance_history = []
        for metric in metrics:
            performance_history.append(PerformanceMetrics(
                agent_id=agent_id,
                cpu_usage=metric.tags.get("cpu_usage", 0.0),
                memory_usage=metric.tags.get("memory_usage", 0.0),
                request_count=metric.metric_value if metric.metric_name == "request_count" else 0,
                average_response_time=metric.tags.get("response_time", 0.0),
                error_rate=metric.tags.get("error_rate", 0.0),
                uptime=metric.tags.get("uptime", 0.0),
                timestamp=metric.timestamp
            ))
        
        return performance_history
    
    async def trigger_alert(self, agent_id: str, alert_type: str, message: str):
        """Trigger an alert for an agent"""
        # This would integrate with alerting systems like PagerDuty, Slack, etc.
        alert_data = {
            "agent_id": agent_id,
            "alert_type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": self._get_alert_severity(alert_type)
        }
        
        # Log the alert
        print(f"ALERT: {alert_data}")
        
        # In a real implementation, send to alerting system
        # await self.alerting_service.send_alert(alert_data)
    
    async def _health_check_loop(self):
        """Continuous health check loop"""
        while self.monitoring_active:
            try:
                # Get all active agents
                active_agents = self.db.query(Agent).filter(
                    Agent.status == AgentStatus.ACTIVE
                ).all()
                
                # Check health of each agent
                for agent in active_agents:
                    health_result = await self.check_agent_health(str(agent.id))
                    
                    # Trigger alerts if needed
                    if health_result.status == "unhealthy":
                        await self.trigger_alert(
                            str(agent.id),
                            "health_check_failed",
                            f"Agent {agent.name} health check failed: {health_result.error_message}"
                        )
                    
                    # Auto-restart if too many failures
                    if agent.error_count >= 5:
                        await self.trigger_alert(
                            str(agent.id),
                            "agent_failure",
                            f"Agent {agent.name} has failed {agent.error_count} times"
                        )
                        
                        # Auto-restart logic could go here
                        # await self.deployment_manager.restart_agent(str(agent.id))
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                print(f"Error in health check loop: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _performance_metrics_loop(self):
        """Continuous performance metrics collection loop"""
        while self.monitoring_active:
            try:
                # Get all active agents
                active_agents = self.db.query(Agent).filter(
                    Agent.status == AgentStatus.ACTIVE
                ).all()
                
                # Collect metrics for each agent
                for agent in active_agents:
                    metrics = await self.get_agent_metrics(str(agent.id))
                    
                    # Store metrics in database
                    await self._store_metrics(metrics)
                    
                    # Check for performance issues
                    if metrics.cpu_usage > 0.8:
                        await self.trigger_alert(
                            str(agent.id),
                            "high_cpu_usage",
                            f"Agent {agent.name} CPU usage is {metrics.cpu_usage:.2%}"
                        )
                    
                    if metrics.memory_usage > 0.8:
                        await self.trigger_alert(
                            str(agent.id),
                            "high_memory_usage",
                            f"Agent {agent.name} memory usage is {metrics.memory_usage:.2%}"
                        )
                    
                    if metrics.error_rate > 0.05:
                        await self.trigger_alert(
                            str(agent.id),
                            "high_error_rate",
                            f"Agent {agent.name} error rate is {metrics.error_rate:.2%}"
                        )
                
                await asyncio.sleep(self.performance_check_interval)
                
            except Exception as e:
                print(f"Error in performance metrics loop: {e}")
                await asyncio.sleep(self.performance_check_interval)
    
    async def _fetch_performance_metrics(self, agent_id: str) -> Dict:
        """Fetch performance metrics from container orchestrator"""
        from app.services.agent_deployment import ContainerOrchestrator
        orchestrator = ContainerOrchestrator()
        return await orchestrator.get_metrics(agent_id)
    
    async def _store_metrics(self, metrics: PerformanceMetrics):
        """Store performance metrics in database"""
        try:
            # Store individual metrics
            metric_records = [
                AgentMetric(
                    agent_id=metrics.agent_id,
                    metric_name="cpu_usage",
                    metric_value=int(metrics.cpu_usage * 100),
                    metric_type="gauge",
                    tags={"unit": "percent"},
                    timestamp=metrics.timestamp
                ),
                AgentMetric(
                    agent_id=metrics.agent_id,
                    metric_name="memory_usage",
                    metric_value=int(metrics.memory_usage * 100),
                    metric_type="gauge",
                    tags={"unit": "percent"},
                    timestamp=metrics.timestamp
                ),
                AgentMetric(
                    agent_id=metrics.agent_id,
                    metric_name="request_count",
                    metric_value=metrics.request_count,
                    metric_type="counter",
                    tags={"unit": "count"},
                    timestamp=metrics.timestamp
                ),
                AgentMetric(
                    agent_id=metrics.agent_id,
                    metric_name="response_time",
                    metric_value=int(metrics.average_response_time * 1000),
                    metric_type="gauge",
                    tags={"unit": "milliseconds"},
                    timestamp=metrics.timestamp
                ),
                AgentMetric(
                    agent_id=metrics.agent_id,
                    metric_name="error_rate",
                    metric_value=int(metrics.error_rate * 100),
                    metric_type="gauge",
                    tags={"unit": "percent"},
                    timestamp=metrics.timestamp
                )
            ]
            
            for metric in metric_records:
                self.db.add(metric)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            print(f"Error storing metrics: {e}")
    
    def _get_alert_severity(self, alert_type: str) -> str:
        """Get alert severity based on type"""
        severity_map = {
            "health_check_failed": "warning",
            "agent_failure": "critical",
            "high_cpu_usage": "warning",
            "high_memory_usage": "warning",
            "high_error_rate": "critical"
        }
        return severity_map.get(alert_type, "info")
