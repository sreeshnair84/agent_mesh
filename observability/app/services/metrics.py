"""
Metrics collection and aggregation service
"""

import asyncio
import time
import psutil
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog
import httpx
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import aioredis
import json

from ..core.config import get_settings
from ..core.database import get_db

logger = structlog.get_logger(__name__)

settings = get_settings()


@dataclass
class Metric:
    """Metric data structure"""
    agent_id: str
    metric_name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    unit: str


@dataclass
class MetricsQuery:
    """Query structure for metrics"""
    agent_ids: Optional[List[str]] = None
    metric_names: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    labels: Optional[Dict[str, str]] = None
    limit: int = 1000


@dataclass
class MetricsResult:
    """Result structure for metrics queries"""
    metrics: List[Metric]
    total: int
    query: MetricsQuery


class MetricsCollector:
    """Core metrics collector implementing the API specification"""
    
    def __init__(self):
        self.redis_client = None
        self.metrics_buffer = []
        self.buffer_size = 1000
        self.flush_interval = 10  # seconds
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            logger.info("Redis client initialized for metrics collection")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            
    async def record_metric(self, metric: Metric) -> bool:
        """Record a single metric"""
        try:
            # Add to buffer
            self.metrics_buffer.append(metric)
            
            # Flush buffer if full
            if len(self.metrics_buffer) >= self.buffer_size:
                await self._flush_buffer()
                
            # Store in Redis for real-time access
            if self.redis_client:
                metric_key = f"metric:{metric.agent_id}:{metric.metric_name}"
                metric_data = {
                    "value": metric.value,
                    "timestamp": metric.timestamp.isoformat(),
                    "labels": metric.labels,
                    "unit": metric.unit
                }
                await self.redis_client.setex(
                    metric_key,
                    300,  # 5 minutes TTL
                    json.dumps(metric_data)
                )
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
            return False
    
    async def record_batch_metrics(self, metrics: List[Metric]) -> int:
        """Record multiple metrics in batch"""
        success_count = 0
        
        for metric in metrics:
            if await self.record_metric(metric):
                success_count += 1
                
        return success_count
    
    async def get_metrics(self, query: MetricsQuery) -> MetricsResult:
        """Get metrics based on query parameters"""
        try:
            # TODO: Implement database query based on parameters
            # For now, return cached metrics from Redis
            
            if not self.redis_client:
                return MetricsResult(metrics=[], total=0, query=query)
                
            pattern = "metric:*"
            if query.agent_ids:
                pattern = f"metric:{query.agent_ids[0]}:*"
                
            keys = await self.redis_client.keys(pattern)
            metrics = []
            
            for key in keys[:query.limit]:
                try:
                    data = await self.redis_client.get(key)
                    if data:
                        metric_data = json.loads(data)
                        parts = key.split(":")
                        metric = Metric(
                            agent_id=parts[1],
                            metric_name=parts[2],
                            value=metric_data["value"],
                            timestamp=datetime.fromisoformat(metric_data["timestamp"]),
                            labels=metric_data["labels"],
                            unit=metric_data["unit"]
                        )
                        metrics.append(metric)
                except Exception as e:
                    logger.warning(f"Failed to parse metric from key {key}: {e}")
                    
            return MetricsResult(metrics=metrics, total=len(metrics), query=query)
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return MetricsResult(metrics=[], total=0, query=query)
    
    async def get_real_time_metrics(self, agent_ids: List[str]) -> AsyncIterator[Metric]:
        """Get real-time metrics stream"""
        if not self.redis_client:
            return
            
        try:
            # Subscribe to Redis key events for real-time updates
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe("__keyspace@0__:metric:*")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # Parse the key and get metric data
                        key = message['channel'].split(':')[-1]
                        if any(agent_id in key for agent_id in agent_ids):
                            data = await self.redis_client.get(key)
                            if data:
                                metric_data = json.loads(data)
                                parts = key.split(":")
                                metric = Metric(
                                    agent_id=parts[1],
                                    metric_name=parts[2],
                                    value=metric_data["value"],
                                    timestamp=datetime.fromisoformat(metric_data["timestamp"]),
                                    labels=metric_data["labels"],
                                    unit=metric_data["unit"]
                                )
                                yield metric
                    except Exception as e:
                        logger.warning(f"Failed to process real-time metric: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
    
    async def _flush_buffer(self):
        """Flush metrics buffer to database"""
        if not self.metrics_buffer:
            return
            
        try:
            # TODO: Implement database storage
            logger.info(f"Flushing {len(self.metrics_buffer)} metrics to database")
            self.metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush metrics buffer: {e}")


class MetricsService:
    """Service for collecting and aggregating metrics"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self.collectors = {}
        self.running = False
        self.metrics_collector = MetricsCollector()
        
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
            ),
            'message_queue_size': Gauge(
                'message_queue_size',
                'Message queue size',
                ['queue_name'],
                registry=self.registry
            ),
            'error_rate': Gauge(
                'error_rate',
                'Error rate percentage',
                ['service'],
                registry=self.registry
            )
        }
    
    async def start_collection(self):
        """Start metrics collection"""
        self.running = True
        await self.metrics_collector.initialize()
        logger.info("Starting metrics collection")
        
        # Start collection tasks
        await asyncio.gather(
            self._collect_system_metrics(),
            self._collect_agent_metrics(),
            self._collect_database_metrics(),
            self._flush_metrics_periodically()
        )
    
    async def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
        logger.info("Stopping metrics collection")
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        while self.running:
            try:
                # Import here to avoid startup errors
                import psutil
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.collectors['cpu_usage'].labels(service='observability').set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.collectors['memory_usage'].labels(service='observability').set(memory.used)
                
                # Record metrics
                await self.metrics_collector.record_metric(Metric(
                    agent_id='system',
                    metric_name='cpu_usage_percent',
                    value=cpu_percent,
                    timestamp=datetime.utcnow(),
                    labels={'service': 'observability'},
                    unit='percent'
                ))
                
                await self.metrics_collector.record_metric(Metric(
                    agent_id='system',
                    metric_name='memory_usage_bytes',
                    value=memory.used,
                    timestamp=datetime.utcnow(),
                    labels={'service': 'observability'},
                    unit='bytes'
                ))
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(10)
    
    async def _collect_agent_metrics(self):
        """Collect agent-specific metrics"""
        while self.running:
            try:
                # TODO: Fetch agent metrics from backend service
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.get(f"{settings.BACKEND_URL}/api/v1/agents/metrics")
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Update active agents gauge
                            self.collectors['active_agents'].set(data.get('active_count', 0))
                            
                            # Record detailed metrics
                            for agent_data in data.get('agents', []):
                                agent_id = agent_data.get('id')
                                
                                # Record agent metrics
                                await self.metrics_collector.record_metric(Metric(
                                    agent_id=agent_id,
                                    metric_name='response_time_seconds',
                                    value=agent_data.get('avg_response_time', 0),
                                    timestamp=datetime.utcnow(),
                                    labels={'agent_type': agent_data.get('type', 'unknown')},
                                    unit='seconds'
                                ))
                                
                                await self.metrics_collector.record_metric(Metric(
                                    agent_id=agent_id,
                                    metric_name='success_rate',
                                    value=agent_data.get('success_rate', 0),
                                    timestamp=datetime.utcnow(),
                                    labels={'agent_type': agent_data.get('type', 'unknown')},
                                    unit='percent'
                                ))
                                
                    except httpx.RequestError as e:
                        logger.warning(f"Failed to fetch agent metrics: {e}")
                
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"Error collecting agent metrics: {e}")
                await asyncio.sleep(30)
    
    async def _collect_database_metrics(self):
        """Collect database metrics"""
        while self.running:
            try:
                # TODO: Implement database connection pool metrics
                # For now, simulate database metrics
                
                await self.metrics_collector.record_metric(Metric(
                    agent_id='system',
                    metric_name='database_connections_active',
                    value=5,  # Placeholder
                    timestamp=datetime.utcnow(),
                    labels={'database': 'postgresql'},
                    unit='connections'
                ))
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logger.error(f"Error collecting database metrics: {e}")
                await asyncio.sleep(10)
    
    async def _flush_metrics_periodically(self):
        """Periodically flush metrics buffer"""
        while self.running:
            try:
                await self.metrics_collector._flush_buffer()
                await asyncio.sleep(self.metrics_collector.flush_interval)
                
            except Exception as e:
                logger.error(f"Error flushing metrics: {e}")
                await asyncio.sleep(5)
    
    async def record_agent_request(self, agent_id: str, status: str, response_time: float):
        """Record agent request metrics"""
        self.collectors['agent_requests_total'].labels(agent_id=agent_id, status=status).inc()
        self.collectors['agent_response_time'].labels(agent_id=agent_id).observe(response_time)
        
        # Record to collector
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name='request_count',
            value=1,
            timestamp=datetime.utcnow(),
            labels={'status': status},
            unit='count'
        ))
        
        await self.metrics_collector.record_metric(Metric(
            agent_id=agent_id,
            metric_name='response_time_seconds',
            value=response_time,
            timestamp=datetime.utcnow(),
            labels={'status': status},
            unit='seconds'
        ))
    
    async def record_workflow_execution(self, workflow_id: str, status: str, execution_time: float):
        """Record workflow execution metrics"""
        self.collectors['workflow_executions_total'].labels(workflow_id=workflow_id, status=status).inc()
        self.collectors['workflow_execution_time'].labels(workflow_id=workflow_id).observe(execution_time)
        
        # Record to collector
        await self.metrics_collector.record_metric(Metric(
            agent_id='system',
            metric_name='workflow_execution_count',
            value=1,
            timestamp=datetime.utcnow(),
            labels={'workflow_id': workflow_id, 'status': status},
            unit='count'
        ))
        
        await self.metrics_collector.record_metric(Metric(
            agent_id='system',
            metric_name='workflow_execution_time_seconds',
            value=execution_time,
            timestamp=datetime.utcnow(),
            labels={'workflow_id': workflow_id, 'status': status},
            unit='seconds'
        ))
    
    async def record_tool_invocation(self, tool_id: str, status: str, execution_time: float):
        """Record tool invocation metrics"""
        self.collectors['tool_invocations_total'].labels(tool_id=tool_id, status=status).inc()
        self.collectors['tool_execution_time'].labels(tool_id=tool_id).observe(execution_time)
        
        # Record to collector
        await self.metrics_collector.record_metric(Metric(
            agent_id='system',
            metric_name='tool_invocation_count',
            value=1,
            timestamp=datetime.utcnow(),
            labels={'tool_id': tool_id, 'status': status},
            unit='count'
        ))
        
        await self.metrics_collector.record_metric(Metric(
            agent_id='system',
            metric_name='tool_execution_time_seconds',
            value=execution_time,
            timestamp=datetime.utcnow(),
            labels={'tool_id': tool_id, 'status': status},
            unit='seconds'
        ))
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus format metrics"""
        return generate_latest(self.registry)
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        try:
            # Get recent metrics from collector
            query = MetricsQuery(
                start_time=datetime.utcnow() - timedelta(hours=1),
                end_time=datetime.utcnow(),
                limit=1000
            )
            
            result = await self.metrics_collector.get_metrics(query)
            
            # Aggregate metrics
            summary = {
                'total_metrics': result.total,
                'active_agents': 0,
                'total_requests': 0,
                'average_response_time': 0,
                'error_rate': 0,
                'system_health': {
                    'cpu_usage': 0,
                    'memory_usage': 0,
                    'disk_usage': 0
                }
            }
            
            # Process metrics
            response_times = []
            error_count = 0
            
            for metric in result.metrics:
                if metric.metric_name == 'response_time_seconds':
                    response_times.append(metric.value)
                elif metric.metric_name == 'request_count' and metric.labels.get('status') == 'error':
                    error_count += metric.value
                elif metric.metric_name == 'cpu_usage_percent':
                    summary['system_health']['cpu_usage'] = metric.value
                elif metric.metric_name == 'memory_usage_bytes':
                    summary['system_health']['memory_usage'] = metric.value
            
            if response_times:
                summary['average_response_time'] = sum(response_times) / len(response_times)
            
            if result.total > 0:
                summary['error_rate'] = (error_count / result.total) * 100
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {
                'total_metrics': 0,
                'active_agents': 0,
                'total_requests': 0,
                'average_response_time': 0,
                'error_rate': 0,
                'system_health': {
                    'cpu_usage': 0,
                    'memory_usage': 0,
                    'disk_usage': 0
                }
            }
