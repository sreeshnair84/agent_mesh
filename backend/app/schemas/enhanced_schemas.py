"""
Enhanced Pydantic schemas for the Agent Mesh API
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(BaseSchema):
    """Schema with timestamp fields"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# Agent Schemas
class AgentBase(BaseModel):
    """Base agent schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    type: str = Field(..., pattern="^(lowcode|custom)$")
    template: Optional[str] = None
    prompt: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    dns: Optional[str] = None
    health_url: Optional[str] = None
    tags: List[str] = []
    is_public: bool = True
    input_payload: Optional[Dict[str, Any]] = None
    output_payload: Optional[Dict[str, Any]] = None


class AgentCreate(AgentBase):
    """Schema for creating agents"""
    config: Optional[Dict[str, Any]] = None
    skill_ids: List[str] = []
    constraint_ids: List[str] = []
    tool_ids: List[str] = []


class AgentUpdate(BaseModel):
    """Schema for updating agents"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    prompt: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    dns: Optional[str] = None
    health_url: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    input_payload: Optional[Dict[str, Any]] = None
    output_payload: Optional[Dict[str, Any]] = None
    skill_ids: Optional[List[str]] = None
    constraint_ids: Optional[List[str]] = None
    tool_ids: Optional[List[str]] = None


class AgentResponse(TimestampedSchema, AgentBase):
    """Schema for agent responses"""
    status: str
    health_status: str
    port: Optional[int] = None
    owner: Optional[Dict[str, Any]] = None
    skills: List[Dict[str, Any]] = []
    constraints: List[Dict[str, Any]] = []
    tools: List[Dict[str, Any]] = []
    last_health_check: Optional[datetime] = None
    config: Optional[Dict[str, Any]] = None


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


class SkillCreate(SkillBase):
    """Schema for creating skills"""
    pass


class SkillUpdate(BaseModel):
    """Schema for updating skills"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


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
    tags: List[str] = []


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
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider: Optional[str] = Field(None, pattern="^(azure_openai|gemini|claude)$")
    model_id: Optional[str] = Field(None, min_length=1, max_length=100)
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ModelResponse(TimestampedSchema, ModelBase):
    """Schema for model responses"""
    owner_id: str


# Environment Secret Schemas
class EnvironmentSecretBase(BaseModel):
    """Base environment secret schema"""
    key: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1)
    environment: str = Field(..., pattern="^(dev|staging|prod)$")
    description: Optional[str] = None


class EnvironmentSecretCreate(EnvironmentSecretBase):
    """Schema for creating environment secrets"""
    pass


class EnvironmentSecretUpdate(BaseModel):
    """Schema for updating environment secrets"""
    key: Optional[str] = Field(None, min_length=1, max_length=100)
    value: Optional[str] = Field(None, min_length=1)
    environment: Optional[str] = Field(None, pattern="^(dev|staging|prod)$")
    description: Optional[str] = None


class EnvironmentSecretResponse(TimestampedSchema):
    """Schema for environment secret responses (value hidden)"""
    key: str
    environment: str
    description: Optional[str] = None
    owner_id: str


# Health Check Schemas
class HealthCheckResponse(BaseModel):
    """Schema for health check responses"""
    agent_id: str
    status: str
    last_check: Optional[datetime] = None
    url: Optional[str] = None
    message: Optional[str] = None


# Deployment Schemas
class DeploymentResponse(BaseModel):
    """Schema for deployment responses"""
    message: str
    agent_id: str
    status: str
    deployment_id: Optional[str] = None


# Error Schemas
class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Success Schemas
class SuccessResponse(BaseModel):
    """Schema for success responses"""
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Input/Output Payload Schemas
class PayloadField(BaseModel):
    """Schema for payload field definition"""
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., regex="^(string|number|boolean|object|array)$")
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
    type: str = Field(default="object", regex="^(object|array)$")
    properties: Dict[str, PayloadField] = {}
    required: List[str] = []
    examples: List[Dict[str, Any]] = []


class AgentPayloadUpdate(BaseModel):
    """Schema for updating agent payload specifications"""
    input_payload: Optional[PayloadSchema] = None
    output_payload: Optional[PayloadSchema] = None


# Update PayloadField to support recursive definition
PayloadField.model_rebuild()
