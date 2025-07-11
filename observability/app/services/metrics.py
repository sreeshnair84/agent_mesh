"""
Metrics collection and aggregation service
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog
import httpx
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest

from ..core.config import get_settings
from ..core.database import get_db

logger = structlog.get_logger(__name__)

settings = get_settings()


class MetricsService:
    """Service for collecting and aggregating metrics"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self.collectors = {}
        self.running = False
        
        # Initialize metrics
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize Prometheus metrics"""
        self.collectors = {
            'agent_requests_total': Counter(
                'agent_requests_total',
                'Total agent requests',
                ['agent_id', 'status'],
                registry=self.registry
            ),
            'agent_response_time': Histogram(
                'agent_response_time_seconds',
                'Agent response time',
                ['agent_id'],
                registry=self.registry
            ),
            'workflow_executions_total': Counter(
                'workflow_executions_total',
                'Total workflow executions',
                ['workflow_id', 'status'],
                registry=self.registry
            ),
            'workflow_execution_time': Histogram(
                'workflow_execution_time_seconds',
                'Workflow execution time',
                ['workflow_id'],
                registry=self.registry
            ),
            'tool_invocations_total': Counter(
                'tool_invocations_total',
                'Total tool invocations',
                ['tool_id', 'status'],
                registry=self.registry
            ),
            'tool_execution_time': Histogram(
                'tool_execution_time_seconds',
                'Tool execution time',
                ['tool_id'],
                registry=self.registry
            ),
            'active_agents': Gauge(
                'active_agents',
                'Number of active agents',
                registry=self.registry
            ),
            'memory_usage': Gauge(
                'memory_usage_bytes',
                'Memory usage in bytes',
                ['service'],
                registry=self.registry
            ),
            'cpu_usage': Gauge(
                'cpu_usage_percent',
                'CPU usage percentage',
                ['service'],
                registry=self.registry
            ),
            'database_connections': Gauge(
                'database_connections',
                'Database connections',
                ['status'],
                registry=self.registry
            )
        }
    
    async def start_collection(self):
        """Start metrics collection"""
        self.running = True
        logger.info("Starting metrics collection")
        
        while self.running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(settings.METRICS_COLLECTION_INTERVAL)
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(5)
    
    async def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
        logger.info("Stopping metrics collection")
    
    async def _collect_metrics(self):
        """Collect metrics from various sources"""
        try:
            # Collect agent metrics
            await self._collect_agent_metrics()
            
            # Collect workflow metrics
            await self._collect_workflow_metrics()
            
            # Collect tool metrics
            await self._collect_tool_metrics()
            
            # Collect system metrics
            await self._collect_system_metrics()
            
        except Exception as e:
            logger.error(f"Error in metrics collection: {e}")
    
    async def _collect_agent_metrics(self):
        """Collect agent-related metrics"""
        try:
            async with httpx.AsyncClient() as client:
                # Get agent statistics from backend
                response = await client.get(f"{settings.BACKEND_URL}/api/v1/agents/stats")
                if response.status_code == 200:
                    stats = response.json()
                    
                    # Update active agents gauge
                    self.collectors['active_agents'].set(stats.get('active_count', 0))
                    
                    # Update agent-specific metrics
                    for agent_stat in stats.get('agents', []):
                        agent_id = agent_stat['id']
                        
                        # Request counts
                        self.collectors['agent_requests_total'].labels(
                            agent_id=agent_id,
                            status='success'
                        ).inc(agent_stat.get('successful_requests', 0))
                        
                        self.collectors['agent_requests_total'].labels(
                            agent_id=agent_id,
                            status='error'
                        ).inc(agent_stat.get('failed_requests', 0))
                        
                        # Response times
                        if 'avg_response_time' in agent_stat:
                            self.collectors['agent_response_time'].labels(
                                agent_id=agent_id
                            ).observe(agent_stat['avg_response_time'])
                
        except Exception as e:
            logger.error(f"Error collecting agent metrics: {e}")
    
    async def _collect_workflow_metrics(self):
        """Collect workflow-related metrics"""
        try:
            async with httpx.AsyncClient() as client:
                # Get workflow statistics from backend
                response = await client.get(f"{settings.BACKEND_URL}/api/v1/workflows/stats")
                if response.status_code == 200:
                    stats = response.json()
                    
                    # Update workflow-specific metrics
                    for workflow_stat in stats.get('workflows', []):
                        workflow_id = workflow_stat['id']
                        
                        # Execution counts
                        self.collectors['workflow_executions_total'].labels(
                            workflow_id=workflow_id,
                            status='completed'
                        ).inc(workflow_stat.get('completed_executions', 0))
                        
                        self.collectors['workflow_executions_total'].labels(
                            workflow_id=workflow_id,
                            status='failed'
                        ).inc(workflow_stat.get('failed_executions', 0))
                        
                        # Execution times
                        if 'avg_execution_time' in workflow_stat:
                            self.collectors['workflow_execution_time'].labels(
                                workflow_id=workflow_id
                            ).observe(workflow_stat['avg_execution_time'])
                
        except Exception as e:
            logger.error(f"Error collecting workflow metrics: {e}")
    
    async def _collect_tool_metrics(self):
        """Collect tool-related metrics"""
        try:
            async with httpx.AsyncClient() as client:
                # Get tool statistics from backend
                response = await client.get(f"{settings.BACKEND_URL}/api/v1/tools/stats")
                if response.status_code == 200:
                    stats = response.json()
                    
                    # Update tool-specific metrics
                    for tool_stat in stats.get('tools', []):
                        tool_id = tool_stat['id']
                        
                        # Invocation counts
                        self.collectors['tool_invocations_total'].labels(
                            tool_id=tool_id,
                            status='success'
                        ).inc(tool_stat.get('successful_invocations', 0))
                        
                        self.collectors['tool_invocations_total'].labels(
                            tool_id=tool_id,
                            status='error'
                        ).inc(tool_stat.get('failed_invocations', 0))
                        
                        # Execution times
                        if 'avg_execution_time' in tool_stat:
                            self.collectors['tool_execution_time'].labels(
                                tool_id=tool_id
                            ).observe(tool_stat['avg_execution_time'])
                
        except Exception as e:
            logger.error(f"Error collecting tool metrics: {e}")
    
    async def _collect_system_metrics(self):
        """Collect system-related metrics"""
        try:
            import psutil
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.collectors['memory_usage'].labels(service='observability').set(memory.used)
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.collectors['cpu_usage'].labels(service='observability').set(cpu_percent)
            
            # Database connections (mock data for now)
            self.collectors['database_connections'].labels(status='active').set(5)
            self.collectors['database_connections'].labels(status='idle').set(10)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        return generate_latest(self.registry)
    
    async def record_custom_metric(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Record a custom metric"""
        try:
            if metric_name in self.collectors:
                collector = self.collectors[metric_name]
                
                if labels:
                    if hasattr(collector, 'labels'):
                        collector.labels(**labels).inc(value)
                    else:
                        collector.set(value)
                else:
                    if hasattr(collector, 'inc'):
                        collector.inc(value)
                    else:
                        collector.set(value)
            
        except Exception as e:
            logger.error(f"Error recording custom metric {metric_name}: {e}")
    
    async def get_metric_history(self, metric_name: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Get metric history for a time range"""
        # This would typically query a time-series database
        # For now, return mock data
        return [
            {
                "timestamp": start_time.isoformat(),
                "value": 10.5,
                "labels": {"service": "backend"}
            },
            {
                "timestamp": end_time.isoformat(),
                "value": 12.3,
                "labels": {"service": "backend"}
            }
        ]
