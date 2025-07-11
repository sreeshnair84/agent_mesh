"""
Logging configuration and utilities
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import structlog
from loguru import logger
import json

from app.core.config import settings


def setup_logging():
    """
    Setup structured logging with loguru and structlog
    """
    
    # Remove default loguru handler
    logger.remove()
    
    # Configure log format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Add console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.LOG_LEVEL.upper(),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler if log file is specified
    if settings.LOG_FILE:
        log_file_path = Path(settings.LOG_FILE)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            settings.LOG_FILE,
            format=log_format,
            level=settings.LOG_LEVEL.upper(),
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
        )
    
    # Configure structlog
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
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    logger.info("Logging configuration initialized")


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get structured logger instance
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Mixin class to add logger to any class
    """
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger instance"""
        return get_logger(self.__class__.__name__)


def log_request(request_id: str, method: str, path: str, user_id: Optional[str] = None):
    """
    Log HTTP request
    """
    logger.info(
        "HTTP Request",
        request_id=request_id,
        method=method,
        path=path,
        user_id=user_id,
    )


def log_response(request_id: str, status_code: int, duration: float):
    """
    Log HTTP response
    """
    logger.info(
        "HTTP Response",
        request_id=request_id,
        status_code=status_code,
        duration=f"{duration:.3f}s",
    )


def log_error(error: Exception, context: Optional[dict] = None):
    """
    Log error with context
    """
    logger.error(
        "Error occurred",
        error=str(error),
        error_type=type(error).__name__,
        context=context or {},
        exc_info=True,
    )


def log_agent_action(
    agent_id: str,
    action: str,
    user_id: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """
    Log agent action
    """
    logger.info(
        "Agent Action",
        agent_id=agent_id,
        action=action,
        user_id=user_id,
        metadata=metadata or {},
    )


def log_llm_request(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration: float,
    user_id: Optional[str] = None,
):
    """
    Log LLM request
    """
    logger.info(
        "LLM Request",
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        duration=f"{duration:.3f}s",
        user_id=user_id,
    )


def log_workflow_execution(
    workflow_id: str,
    execution_id: str,
    status: str,
    duration: Optional[float] = None,
    user_id: Optional[str] = None,
):
    """
    Log workflow execution
    """
    logger.info(
        "Workflow Execution",
        workflow_id=workflow_id,
        execution_id=execution_id,
        status=status,
        duration=f"{duration:.3f}s" if duration else None,
        user_id=user_id,
    )


def log_database_operation(
    operation: str,
    table: str,
    record_id: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """
    Log database operation
    """
    logger.info(
        "Database Operation",
        operation=operation,
        table=table,
        record_id=record_id,
        user_id=user_id,
    )


def log_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None,
):
    """
    Log security event
    """
    logger.warning(
        "Security Event",
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        details=details or {},
    )


class RequestLoggingMiddleware:
    """
    Middleware for logging requests and responses
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request_id = f"req_{datetime.utcnow().timestamp()}"
            
            # Log request
            log_request(
                request_id=request_id,
                method=scope["method"],
                path=scope["path"],
            )
            
            # Track response
            start_time = datetime.utcnow()
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    log_response(
                        request_id=request_id,
                        status_code=message["status"],
                        duration=duration,
                    )
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


# Configure JSON encoder for complex objects
class LogJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for logging"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)
