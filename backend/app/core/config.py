"""
Core configuration module
Handles application settings and environment variables
"""

from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings
from typing import List, Optional, Any, Dict
from functools import lru_cache
import os
import secrets
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings
    """
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Agent Mesh Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    TEST_DATABASE_URL: Optional[str] = Field(default=None, env="TEST_DATABASE_URL")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    # LLM Providers
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION: str = Field(default="2023-12-01-preview", env="AZURE_OPENAI_API_VERSION")
    
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    
    CLAUDE_API_KEY: Optional[str] = Field(default=None, env="CLAUDE_API_KEY")
    
    # Observability
    OBSERVABILITY_URL: str = Field(default="http://localhost:8001", env="OBSERVABILITY_URL")
    
    # Deployment
    AGENT_BASE_PORT: int = Field(default=9000, env="AGENT_BASE_PORT")
    MAX_AGENT_PORTS: int = Field(default=1000, env="MAX_AGENT_PORTS")
    
    # Additional settings for backward compatibility
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "https://localhost:3000"],
        env="CORS_ORIGINS"
    )
    
    # API Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    UPLOAD_DIR: str = Field(default="./uploads", env="UPLOAD_DIR")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Vector database settings
    VECTOR_DB_URL: Optional[str] = Field(default=None, env="VECTOR_DB_URL")
    VECTOR_DIMENSIONS: int = Field(default=1536, env="VECTOR_DIMENSIONS")
    
    # External service URLs
    FRONTEND_URL: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    BACKEND_URL: str = Field(default="http://localhost:8000", env="BACKEND_URL")
    
    # Celery settings (for background tasks)
    CELERY_BROKER_URL: Optional[str] = Field(default=None, env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None, env="CELERY_RESULT_BACKEND")
    
    # Monitoring settings
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=8080, env="METRICS_PORT")
    
    # Default User Settings (for development/testing)
    USE_DEFAULT_USER: bool = Field(default=True, env="USE_DEFAULT_USER")
    DEFAULT_USER_ID: str = Field(default="550e8400-e29b-41d4-a716-446655440000", env="DEFAULT_USER_ID")
    DEFAULT_USER_EMAIL: str = Field(default="default@agentmesh.dev", env="DEFAULT_USER_EMAIL")
    DEFAULT_USER_USERNAME: str = Field(default="defaultuser", env="DEFAULT_USER_USERNAME")
    DEFAULT_USER_FULL_NAME: str = Field(default="Default User", env="DEFAULT_USER_FULL_NAME")
    DEFAULT_USER_ROLE: str = Field(default="developer", env="DEFAULT_USER_ROLE")
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in the .env file
    )
        
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str):
            import json
            return json.loads(v)
        return v
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        """Validate database URL"""
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v
    
    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def assemble_secret_key(cls, v: Optional[str]) -> str:
        """Validate secret key"""
        if not v:
            raise ValueError("SECRET_KEY is required")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def database_url_async(self) -> str:
        """Get async database URL"""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL
    
    @property
    def redis_url_parsed(self) -> Optional[Dict[str, Any]]:
        """Parse Redis URL into components"""
        if not self.REDIS_URL:
            return None
        
        from urllib.parse import urlparse
        parsed = urlparse(self.REDIS_URL)
        
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 6379,
            "password": parsed.password,
            "db": int(parsed.path.lstrip("/")) if parsed.path else 0,
        }
    
    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        """Get LLM provider configuration"""
        configs = {
            "azure_openai": {
                "api_key": self.AZURE_OPENAI_API_KEY,
                "endpoint": self.AZURE_OPENAI_ENDPOINT,
                "api_version": self.AZURE_OPENAI_API_VERSION,
            },
            "openai": {
                "api_key": self.OPENAI_API_KEY,
            },
            "anthropic": {
                "api_key": self.ANTHROPIC_API_KEY or self.CLAUDE_API_KEY,
            },
            "google": {
                "api_key": self.GOOGLE_API_KEY or self.GEMINI_API_KEY,
            },
        }
        
        return configs.get(provider, {})


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings
    """
    return Settings()


# Global settings instance
settings = get_settings()

# Create upload directory if it doesn't exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
