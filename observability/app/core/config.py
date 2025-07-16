"""
Observability Service Configuration
"""

import os
from typing import List, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Basic settings
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/agent_mesh"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security settings
    ALLOWED_ORIGINS: List[str] = ["*"]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Tracing settings
    TRACING_ENABLED: bool = True
    JAEGER_ENDPOINT: Optional[str] = None
    JAEGER_HOST: str = "localhost"
    JAEGER_PORT: int = 14268
    
    # Metrics settings
    METRICS_ENABLED: bool = True
    METRICS_COLLECTION_INTERVAL: int = 30  # seconds
    METRICS_BUFFER_SIZE: int = 1000
    METRICS_FLUSH_INTERVAL: int = 10  # seconds
    
    # Alerting settings
    ALERTING_ENABLED: bool = True
    ALERT_CHECK_INTERVAL: int = 60  # seconds
    
    # External service URLs
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Notification settings
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    # Email settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_TO: Optional[str] = None
    SMTP_TLS: bool = True
    
    # Webhook settings
    WEBHOOK_URL: Optional[str] = None
    
    # Performance settings
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT: int = 30
    
    # Storage settings
    METRICS_RETENTION_DAYS: int = 30
    LOGS_RETENTION_DAYS: int = 7
    ALERTS_RETENTION_DAYS: int = 30
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


_settings = None


def get_settings() -> Settings:
    """Get application settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
