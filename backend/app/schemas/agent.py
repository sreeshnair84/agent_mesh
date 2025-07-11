"""
Agent schemas
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    """Agent status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPLOYING = "deploying"
    STOPPED = "stopped"


class AgentBase(BaseModel):
    """Base agent schema"""
    name: str = Field(..., min_length=2, max_length=100)
    display_name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    category_id: Optional[str] = None
    template_id: Optional[str] = None
    model_id: Optional[str] = None
    system_prompt: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Name must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()


class AgentCreate(AgentBase):
    """Agent creation schema"""
    pass


class AgentUpdate(BaseModel):
    """Agent update schema"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    display_name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    status: Optional[AgentStatus] = None
    category_id: Optional[str] = None
    template_id: Optional[str] = None
    model_id: Optional[str] = None
    system_prompt: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None


class AgentResponse(AgentBase):
    """Agent response schema"""
    id: str
    status: AgentStatus
    version: str = "1.0.0"
    deployment_config: Optional[Dict[str, Any]] = None
    health_check_url: Optional[str] = None
    last_health_check: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    
    class Config:
        from_attributes = True


class AgentList(BaseModel):
    """Agent list response schema"""
    agents: List[AgentResponse]
    total: int
    page: int = 1
    per_page: int = 50
    pages: int = 1


class AgentCategoryBase(BaseModel):
    """Base agent category schema"""
    name: str = Field(..., min_length=2, max_length=100)
    display_name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: str = "#3B82F6"
    sort_order: int = 0
    is_active: bool = True


class AgentCategoryCreate(AgentCategoryBase):
    """Agent category creation schema"""
    pass


class AgentCategoryUpdate(BaseModel):
    """Agent category update schema"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    display_name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class AgentCategoryResponse(AgentCategoryBase):
    """Agent category response schema"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AgentTemplateBase(BaseModel):
    """Base agent template schema"""
    name: str = Field(..., min_length=2, max_length=100)
    display_name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    template_type: str = Field(..., min_length=2, max_length=50)
    category_id: Optional[str] = None
    template_code: str = Field(..., min_length=10)
    config_schema: Optional[Dict[str, Any]] = None
    default_config: Optional[Dict[str, Any]] = None
    required_tools: Optional[List[str]] = None
    supported_models: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    version: str = "1.0.0"
    is_active: bool = True


class AgentTemplateCreate(AgentTemplateBase):
    """Agent template creation schema"""
    pass


class AgentTemplateUpdate(BaseModel):
    """Agent template update schema"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    display_name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    template_type: Optional[str] = Field(None, min_length=2, max_length=50)
    category_id: Optional[str] = None
    template_code: Optional[str] = Field(None, min_length=10)
    config_schema: Optional[Dict[str, Any]] = None
    default_config: Optional[Dict[str, Any]] = None
    required_tools: Optional[List[str]] = None
    supported_models: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None


class AgentTemplateResponse(AgentTemplateBase):
    """Agent template response schema"""
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AgentVersionBase(BaseModel):
    """Base agent version schema"""
    version: str = Field(..., min_length=1, max_length=20)
    configuration: Dict[str, Any] = Field(...)
    system_prompt: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    changelog: Optional[str] = None
    is_active: bool = False


class AgentVersionCreate(AgentVersionBase):
    """Agent version creation schema"""
    pass


class AgentVersionResponse(AgentVersionBase):
    """Agent version response schema"""
    id: str
    agent_id: str
    created_by: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentMetricBase(BaseModel):
    """Base agent metric schema"""
    metric_name: str = Field(..., min_length=1, max_length=100)
    metric_value: float = Field(...)
    metric_type: str = Field(..., min_length=1, max_length=50)
    tags: Optional[Dict[str, Any]] = None
    period: str = "instant"


class AgentMetricCreate(AgentMetricBase):
    """Agent metric creation schema"""
    pass


class AgentMetricResponse(AgentMetricBase):
    """Agent metric response schema"""
    id: str
    agent_id: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AgentDeploymentConfig(BaseModel):
    """Agent deployment configuration schema"""
    replicas: int = Field(default=1, ge=1, le=10)
    resources: Optional[Dict[str, Any]] = None
    environment: Optional[Dict[str, str]] = None
    ports: Optional[List[int]] = None
    health_check: Optional[Dict[str, Any]] = None
    auto_scaling: Optional[Dict[str, Any]] = None


class AgentDeploymentRequest(BaseModel):
    """Agent deployment request schema"""
    agent_id: str
    config: Optional[AgentDeploymentConfig] = None
    force: bool = False


class AgentDeploymentResponse(BaseModel):
    """Agent deployment response schema"""
    deployment_id: str
    agent_id: str
    status: str
    started_at: datetime
    config: Optional[AgentDeploymentConfig] = None
    
    class Config:
        from_attributes = True


class AgentHealthCheck(BaseModel):
    """Agent health check schema"""
    agent_id: str
    status: str
    last_check: datetime
    error_count: int
    uptime: Optional[str] = None
    response_time: Optional[float] = None
    
    class Config:
        from_attributes = True


class AgentChatMessage(BaseModel):
    """Agent chat message schema"""
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class AgentChatResponse(BaseModel):
    """Agent chat response schema"""
    agent_id: str
    message: str
    response: str
    conversation_id: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class AgentStats(BaseModel):
    """Agent statistics schema"""
    total_agents: int
    active_agents: int
    inactive_agents: int
    error_agents: int
    deploying_agents: int
    stopped_agents: int
    total_requests: int
    average_response_time: float
    success_rate: float
