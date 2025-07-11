"""
Distributed tracing service
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog
import httpx
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource

from ..core.config import get_settings
from ..core.database import get_db

logger = structlog.get_logger(__name__)

settings = get_settings()


class TracingService:
    """Service for distributed tracing"""
    
    def __init__(self):
        self.tracer = None
        self.running = False
        self._init_tracer()
    
    def _init_tracer(self):
        """Initialize OpenTelemetry tracer"""
        if settings.TRACING_ENABLED:
            # Create resource
            resource = Resource.create({
                "service.name": "agent-mesh-observability",
                "service.version": "1.0.0"
            })
            
            # Set tracer provider
            trace.set_tracer_provider(TracerProvider(resource=resource))
            
            # Configure Jaeger exporter if enabled
            if settings.JAEGER_ENDPOINT:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=settings.JAEGER_HOST,
                    agent_port=settings.JAEGER_PORT,
                )
                span_processor = BatchSpanProcessor(jaeger_exporter)
                trace.get_tracer_provider().add_span_processor(span_processor)
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__)
    
    async def start_trace(self, operation_name: str, parent_context: Optional[Any] = None) -> Any:
        """Start a new trace span"""
        if not self.tracer:
            return None
        
        try:
            span = self.tracer.start_span(
                operation_name,
                context=parent_context
            )
            
            # Add common attributes
            span.set_attribute("service.name", "agent-mesh-observability")
            span.set_attribute("timestamp", time.time())
            
            return span
            
        except Exception as e:
            logger.error(f"Error starting trace: {e}")
            return None
    
    async def end_trace(self, span: Any, status: str = "ok", error: Optional[str] = None):
        """End a trace span"""
        if not span:
            return
        
        try:
            # Set status
            span.set_attribute("status", status)
            
            # Add error details if present
            if error:
                span.set_attribute("error", True)
                span.set_attribute("error.message", error)
                span.record_exception(Exception(error))
            
            # End span
            span.end()
            
        except Exception as e:
            logger.error(f"Error ending trace: {e}")
    
    async def add_trace_event(self, span: Any, event_name: str, attributes: Dict[str, Any] = None):
        """Add an event to a trace span"""
        if not span:
            return
        
        try:
            span.add_event(event_name, attributes or {})
            
        except Exception as e:
            logger.error(f"Error adding trace event: {e}")
    
    async def get_trace_by_id(self, trace_id: str) -> Optional[Dict]:
        """Get trace by ID"""
        try:
            # This would typically query Jaeger or another tracing backend
            # For now, return mock data
            return {
                "trace_id": trace_id,
                "spans": [
                    {
                        "span_id": "span-123",
                        "operation_name": "agent.execute",
                        "start_time": datetime.utcnow().isoformat(),
                        "duration": 150.5,
                        "tags": {
                            "agent.id": "agent-123",
                            "status": "success"
                        }
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting trace {trace_id}: {e}")
            return None
    
    async def search_traces(self, filters: Dict[str, Any], limit: int = 100) -> List[Dict]:
        """Search traces with filters"""
        try:
            # This would typically query Jaeger or another tracing backend
            # For now, return mock data
            return [
                {
                    "trace_id": "trace-123",
                    "root_span": {
                        "operation_name": "workflow.execute",
                        "start_time": datetime.utcnow().isoformat(),
                        "duration": 2500.0,
                        "tags": {
                            "workflow.id": "workflow-123",
                            "status": "success"
                        }
                    },
                    "span_count": 5,
                    "error_count": 0
                }
            ]
            
        except Exception as e:
            logger.error(f"Error searching traces: {e}")
            return []
    
    async def get_service_map(self) -> Dict[str, Any]:
        """Get service dependency map"""
        try:
            # This would typically analyze trace data to build service map
            # For now, return mock data
            return {
                "services": [
                    {
                        "name": "agent-mesh-backend",
                        "type": "service",
                        "metrics": {
                            "request_rate": 150.0,
                            "error_rate": 0.02,
                            "avg_response_time": 45.5
                        }
                    },
                    {
                        "name": "agent-mesh-observability",
                        "type": "service",
                        "metrics": {
                            "request_rate": 50.0,
                            "error_rate": 0.01,
                            "avg_response_time": 25.0
                        }
                    }
                ],
                "dependencies": [
                    {
                        "source": "agent-mesh-backend",
                        "target": "postgresql",
                        "type": "database",
                        "request_rate": 200.0
                    },
                    {
                        "source": "agent-mesh-backend",
                        "target": "redis",
                        "type": "cache",
                        "request_rate": 100.0
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting service map: {e}")
            return {}
    
    async def get_trace_analytics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get trace analytics for a time range"""
        try:
            # This would typically analyze trace data
            # For now, return mock data
            return {
                "total_traces": 1250,
                "error_traces": 25,
                "error_rate": 0.02,
                "avg_trace_duration": 125.5,
                "p95_trace_duration": 450.0,
                "p99_trace_duration": 1200.0,
                "top_operations": [
                    {
                        "operation": "agent.execute",
                        "count": 800,
                        "avg_duration": 95.0,
                        "error_rate": 0.015
                    },
                    {
                        "operation": "workflow.execute",
                        "count": 300,
                        "avg_duration": 250.0,
                        "error_rate": 0.03
                    }
                ],
                "top_errors": [
                    {
                        "error": "ConnectionTimeoutError",
                        "count": 15,
                        "percentage": 0.6
                    },
                    {
                        "error": "ValidationError",
                        "count": 10,
                        "percentage": 0.4
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting trace analytics: {e}")
            return {}
    
    async def instrument_request(self, request_info: Dict[str, Any]) -> Any:
        """Instrument an HTTP request"""
        if not self.tracer:
            return None
        
        try:
            span = self.tracer.start_span(f"HTTP {request_info.get('method', 'GET')}")
            
            # Add request attributes
            span.set_attribute("http.method", request_info.get('method', 'GET'))
            span.set_attribute("http.url", request_info.get('url', ''))
            span.set_attribute("http.user_agent", request_info.get('user_agent', ''))
            
            return span
            
        except Exception as e:
            logger.error(f"Error instrumenting request: {e}")
            return None
    
    async def record_database_operation(self, operation: str, table: str, duration: float, error: Optional[str] = None):
        """Record a database operation trace"""
        if not self.tracer:
            return
        
        try:
            with self.tracer.start_as_current_span(f"db.{operation}") as span:
                span.set_attribute("db.statement", operation)
                span.set_attribute("db.table", table)
                span.set_attribute("db.duration", duration)
                
                if error:
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", error)
                    span.record_exception(Exception(error))
                
        except Exception as e:
            logger.error(f"Error recording database operation: {e}")
    
    async def create_trace_context(self, trace_id: str, span_id: str, parent_span_id: Optional[str] = None) -> Dict[str, str]:
        """Create trace context for propagation"""
        return {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id or "",
            "flags": "01"  # Sampled
        }
