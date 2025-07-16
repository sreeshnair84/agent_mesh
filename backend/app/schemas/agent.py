"""
Agent schemas - merged with enhanced schemas
"""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(BaseSchema):
    """Schema with timestamp fields"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class AgentStatus(str, Enum):
    """Agent status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPLOYING = "deploying"
    STOPPED = "stopped"


class AgentBase(BaseModel):
    """Base agent schema - merged from original and enhanced versions"""
    model_config = ConfigDict(protected_namespaces=())
    
    name: str = Field(..., min_length=2, max_length=100)
    display_name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    category_id: Optional[str] = None
    template_id: Optional[str] = None
    model_id: Optional[str] = None
    type: Optional[str] = Field(None, pattern="^(lowcode|custom)$")
    system_prompt: Optional[str] = None
    prompt: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    is_public: bool = True
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    dns: Optional[str] = None
    health_url: Optional[str] = None
    port: Optional[int] = None
    input_payload: Optional[Dict[str, Any]] = None
    output_payload: Optional[Dict[str, Any]] = None
    
    @validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Name must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()


class AgentCreate(AgentBase):
    """Agent creation schema"""
    config: Optional[Dict[str, Any]] = None
    skill_ids: Optional[List[str]] = Field(default_factory=list)
    constraint_ids: Optional[List[str]] = Field(default_factory=list)
    tool_ids: Optional[List[str]] = Field(default_factory=list)
    
    @validator('system_prompt')
    @classmethod
    def validate_system_prompt_for_lowcode(cls, v, values):
        """Validate system prompt is required for low-code agents"""
        if values.get('type') == 'lowcode' and not v:
            raise ValueError('System prompt is required for low-code agents')
        return v
    
    @validator('model_id')
    @classmethod
    def validate_model_for_lowcode(cls, v, values):
        """Validate model is required for low-code agents"""
        if values.get('type') == 'lowcode' and not v and not values.get('llm_model'):
            raise ValueError('Model is required for low-code agents')
        return v
    
    @validator('tool_ids')
    @classmethod
    def validate_tools_for_lowcode(cls, v, values):
        """Validate tools are required for low-code agents"""
        if values.get('type') == 'lowcode' and (not v or len(v) == 0):
            raise ValueError('At least one tool is required for low-code agents')
        return v


class AgentUpdate(BaseModel):
    """Agent update schema"""
    model_config = ConfigDict(protected_namespaces=())
    
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    display_name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    status: Optional[AgentStatus] = None
    category_id: Optional[str] = None
    template_id: Optional[str] = None
    model_id: Optional[str] = None
    type: Optional[str] = Field(None, pattern="^(lowcode|custom)$")
    system_prompt: Optional[str] = None
    prompt: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    dns: Optional[str] = None
    health_url: Optional[str] = None
    port: Optional[int] = None
    input_payload: Optional[Dict[str, Any]] = None
    output_payload: Optional[Dict[str, Any]] = None
    skill_ids: Optional[List[str]] = None
    constraint_ids: Optional[List[str]] = None
    tool_ids: Optional[List[str]] = None


class AgentResponse(AgentBase):
    """Agent response schema"""
    id: str
    status: AgentStatus
    version: str = "1.0.0"
    deployment_config: Optional[Dict[str, Any]] = None
    health_check_url: Optional[str] = None
    health_status: str = "unknown"
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
    owner: Optional[Dict[str, Any]] = None
    skills: List[Dict[str, Any]] = Field(default_factory=list)
    constraints: List[Dict[str, Any]] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


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


# Additional schemas from enhanced_schemas.py

class AgentSearch(BaseModel):
    """Schema for agent search queries"""
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    owner_id: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(20, le=100)
    offset: int = Field(0, ge=0)


class AgentInvoke(BaseModel):
    """Schema for agent invocation"""
    input: Dict[str, Any]
    session_id: Optional[str] = None
    trace_id: Optional[str] = None


class AgentInvokeResponse(BaseModel):
    """Schema for agent invocation response"""
    output: Dict[str, Any]
    trace_id: str
    execution_time_ms: int
    llm_usage: Optional[Dict[str, Any]] = None


# Skill Schemas
class SkillBase(BaseModel):
    """Base skill schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    status: Optional[str] = Field("active", pattern="^(active|inactive|draft)$")
    dependencies: Optional[List[str]] = Field(default_factory=list)
    examples: Optional[List[str]] = Field(default_factory=list)
    usage_count: Optional[int] = Field(default=0)


class SkillCreate(SkillBase):
    """Schema for creating skills"""
    pass


class SkillUpdate(BaseModel):
    """Schema for updating skills"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|draft)$")
    dependencies: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    usage_count: Optional[int] = None


class SkillResponse(TimestampedSchema, SkillBase):
    """Schema for skill responses"""
    pass


# Constraint Schemas
class ConstraintBase(BaseModel):
    """Base constraint schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    config: Dict[str, Any]
    type: str = Field(..., pattern="^(validation|security|performance)$")


class ConstraintCreate(ConstraintBase):
    """Schema for creating constraints"""
    pass


class ConstraintUpdate(BaseModel):
    """Schema for updating constraints"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    type: Optional[str] = Field(None, pattern="^(validation|security|performance)$")


class ConstraintResponse(TimestampedSchema, ConstraintBase):
    """Schema for constraint responses"""
    pass


# Prompt Schemas
class PromptBase(BaseModel):
    """Base prompt schema"""
    name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    version: str = Field(default="1.0")
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class PromptCreate(PromptBase):
    """Schema for creating prompts"""
    pass


class PromptUpdate(BaseModel):
    """Schema for updating prompts"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1)
    version: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class PromptResponse(TimestampedSchema, PromptBase):
    """Schema for prompt responses"""
    owner_id: str


# Model Schemas
class ModelBase(BaseModel):
    """Base model schema"""
    model_config = ConfigDict(protected_namespaces=())
    
    name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., pattern="^(azure_openai|gemini|claude)$")
    model_id: str = Field(..., min_length=1, max_length=100)
    config: Dict[str, Any]
    is_active: bool = True


class ModelCreate(ModelBase):
    """Schema for creating models"""
    pass


class ModelUpdate(BaseModel):
    """Schema for updating models"""
    model_config = ConfigDict(protected_namespaces=())
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider: Optional[str] = Field(None, pattern="^(azure_openai|gemini|claude)$")
    model_id: Optional[str] = Field(None, min_length=1, max_length=100)
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ModelResponse(TimestampedSchema, ModelBase):
    """Schema for model responses"""
    owner_id: str


# Health Check Schemas
class HealthCheckResponse(BaseModel):
    """Schema for health check responses"""
    agent_id: str
    status: str
    last_check: Optional[datetime] = None
    url: Optional[str] = None
    message: Optional[str] = None


# Input/Output Payload Schemas
class PayloadField(BaseModel):
    """Schema for payload field definition"""
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern="^(string|number|boolean|object|array|text|audio|image|video|document|file|binary|json|xml|csv|pdf|any)$")
    description: Optional[str] = None
    required: bool = True
    example: Optional[Any] = None
    enum: Optional[List[str]] = None
    properties: Optional[Dict[str, 'PayloadField']] = None  # For object type
    items: Optional['PayloadField'] = None  # For array type


class PayloadSchema(BaseModel):
    """Schema for input/output payload specification"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    type: str = Field(default="object", pattern="^(object|array|text|audio|image|video|document|file|binary|json|xml|csv|pdf|any)$")
    properties: Dict[str, PayloadField] = {}
    required: List[str] = []
    examples: List[Dict[str, Any]] = []


class AgentPayloadUpdate(BaseModel):
    """Schema for updating agent payload specifications"""
    input_payload: Optional[PayloadSchema] = None
    output_payload: Optional[PayloadSchema] = None


# Update PayloadField to support recursive definition
PayloadField.model_rebuild()

# Base Agent Framework Schemas
class AgentCapabilitySchema(BaseModel):
    """Agent capability schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    input_types: List[str]
    output_types: List[str]
    confidence_level: float = Field(..., ge=0.0, le=1.0)


class AgentMetadataSchema(BaseModel):
    """Agent metadata schema"""
    agent_id: str
    agent_type: str
    capabilities: List[AgentCapabilitySchema]
    status: AgentStatus
    created_at: datetime
    performance_metrics: Dict[str, float]


class MessageBrokerRegisterRequest(BaseModel):
    """Message broker register request schema"""
    metadata: AgentMetadataSchema


class MessageBrokerRouteRequest(BaseModel):
    """Message broker route request schema"""
    from_id: str
    to_id: str
    message: Dict[str, Any]


class MessageBrokerBroadcastRequest(BaseModel):
    """Message broker broadcast request schema"""
    message: Dict[str, Any]
    filter_criteria: Optional[Dict[str, Any]] = None


class MessageBrokerSubscribeRequest(BaseModel):
    """Message broker subscribe request schema"""
    agent_id: str
    event_types: List[str]


class MessageBrokerResponse(BaseModel):
    """Message broker response schema"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
