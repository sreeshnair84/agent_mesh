"""
Exception handlers for observability service
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup exception handlers for the application"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions"""
        logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "message": exc.detail,
                    "status_code": exc.status_code
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle validation errors"""
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "validation_error",
                    "message": "Validation failed",
                    "details": exc.errors()
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle general exceptions"""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "message": "Internal server error",
                    "details": str(exc) if logger.level == logging.DEBUG else None
                }
            }
        )


class ObservabilityException(Exception):
    """Base exception for observability service"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class MetricsException(ObservabilityException):
    """Exception for metrics-related errors"""
    pass


class IntegrationException(ObservabilityException):
    """Exception for integration-related errors"""
    pass
