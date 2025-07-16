"""
Middleware for observability service
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
        
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect metrics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Collect metrics
        process_time = time.time() - start_time
        
        # Here you would typically send metrics to a metrics service
        # For now, we'll just log them
        logger.debug(f"Metrics: {request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
        
        return response


def setup_middleware(app: FastAPI) -> None:
    """Setup middleware for the application"""
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, be more restrictive
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add GZip middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add custom middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(MetricsMiddleware)
    
    logger.info("Middleware setup complete")
