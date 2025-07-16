"""
Observability Service Main Application
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, Counter, Histogram, Gauge
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
import structlog
import uvicorn

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import setup_middleware
from app.api.v1.api import api_router
from app.services.metrics import MetricsService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('observability_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('observability_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('observability_active_connections', 'Active connections')

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Agent Mesh Observability Service")
    
    # Initialize tracing (disabled for now)
    pass
    
    # Initialize services
    app.state.metrics_service = MetricsService()
    
    # Start background tasks
    asyncio.create_task(app.state.metrics_service.start_collection())
    
    logger.info("Observability service started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Observability service")
    await app.state.metrics_service.stop_collection()


# Create FastAPI app
app = FastAPI(
    title="Agent Mesh Observability Service",
    description="Observability, monitoring, and alerting service for Agent Mesh",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Setup middleware
setup_middleware(app)

# Setup exception handlers
setup_exception_handlers(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
if settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Instrument FastAPI for tracing
if settings.TRACING_ENABLED:
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect metrics"""
    start_time = time.time()
    
    # Increment active connections
    ACTIVE_CONNECTIONS.inc()
    
    try:
        response = await call_next(request)
        
        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path
        ).inc()
        
        REQUEST_DURATION.observe(time.time() - start_time)
        
        return response
    
    finally:
        # Decrement active connections
        ACTIVE_CONNECTIONS.dec()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "observability",
        "version": "1.0.0",
        "timestamp": time.time()
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agent Mesh Observability Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


if __name__ == "__main__":
    import time
    from fastapi import Response
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=settings.DEBUG,
        log_level="info"
    )
