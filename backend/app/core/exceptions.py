"""
Exception handlers and custom exceptions
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Any, Dict
import logging
from datetime import datetime


class AgentMeshException(Exception):
    """Base exception class for Agent Mesh"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(AgentMeshException):
    """Validation error exception"""
    pass


class AuthenticationError(AgentMeshException):
    """Authentication error exception"""
    pass


class AuthorizationError(AgentMeshException):
    """Authorization error exception"""
    pass


class NotFoundError(AgentMeshException):
    """Not found error exception"""
    pass


class ConflictError(AgentMeshException):
    """Conflict error exception"""
    pass


class ExternalServiceError(AgentMeshException):
    """External service error exception"""
    pass


class RateLimitError(AgentMeshException):
    """Rate limit error exception"""
    pass


class WorkflowError(AgentMeshException):
    """Workflow error exception"""
    pass


class AgentError(AgentMeshException):
    """Agent error exception"""
    pass


class ToolError(AgentMeshException):
    """Tool error exception"""
    pass


class DatabaseError(AgentMeshException):
    """Database error exception"""
    pass


class ConfigurationError(AgentMeshException):
    """Configuration error exception"""
    pass


class TemplateError(AgentMeshException):
    """Template error exception"""
    pass


class MasterDataError(AgentMeshException):
    """Master data error exception"""
    pass


def create_error_response(
    error: str,
    message: str,
    details: Any = None,
    error_code: str = None,
    request_id: str = None,
) -> Dict[str, Any]:
    """Create standardized error response"""
    response = {
        "error": error,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if details:
        response["details"] = details
    
    if error_code:
        response["error_code"] = error_code
    
    if request_id:
        response["request_id"] = request_id
    
    return response


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup custom exception handlers"""
    
    @app.exception_handler(AgentMeshException)
    async def agent_mesh_exception_handler(request: Request, exc: AgentMeshException):
        """Handle custom Agent Mesh exceptions"""
        logging.error(f"Agent Mesh error: {exc.message}")
        
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        if isinstance(exc, ValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, AuthenticationError):
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, AuthorizationError):
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, NotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, ConflictError):
            status_code = status.HTTP_409_CONFLICT
        elif isinstance(exc, RateLimitError):
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif isinstance(exc, ExternalServiceError):
            status_code = status.HTTP_502_BAD_GATEWAY
        
        return JSONResponse(
            status_code=status_code,
            content=create_error_response(
                error=exc.__class__.__name__,
                message=exc.message,
                error_code=exc.error_code,
                request_id=str(request.headers.get("X-Request-ID", ""))
            )
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        logging.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                error="HTTPException",
                message=exc.detail,
                request_id=str(request.headers.get("X-Request-ID", ""))
            )
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logging.warning(f"Validation error: {exc.errors()}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=create_error_response(
                error="ValidationError",
                message="Request validation failed",
                details=exc.errors(),
                request_id=str(request.headers.get("X-Request-ID", ""))
            )
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions"""
        logging.error(f"Starlette exception: {exc.status_code} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                error="StarletteHTTPException",
                message=exc.detail,
                request_id=str(request.headers.get("X-Request-ID", ""))
            )
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        logging.error(f"Unexpected error: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_response(
                error="InternalServerError",
                message="An unexpected error occurred",
                request_id=str(request.headers.get("X-Request-ID", ""))
            )
        )
