from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
import uuid


class ToolType(str, Enum):
    API = "api"
    FUNCTION = "function"
    WEBHOOK = "webhook"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    EXTERNAL_SERVICE = "external_service"
    CUSTOM = "custom"


class ToolStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"


class ToolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tool_type: ToolType
    category: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(..., description="Tool configuration")
    tool_schema: Dict[str, Any] = Field(..., description="Tool schema definition")
    implementation: Optional[str] = None
    endpoint_url: Optional[str] = Field(None, max_length=500)
    auth_type: Optional[str] = Field(None, max_length=50)
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"


class ToolCreate(ToolBase):
    pass


class ToolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tool_type: Optional[ToolType] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    tool_schema: Optional[Dict[str, Any]] = None
    implementation: Optional[str] = None
    endpoint_url: Optional[str] = Field(None, max_length=500)
    auth_type: Optional[str] = Field(None, max_length=50)
    auth_config: Optional[Dict[str, Any]] = None
    status: Optional[ToolStatus] = None
    version: Optional[str] = None


class ToolResponse(ToolBase):
    id: str
    status: ToolStatus
    created_by: str
    organization_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    total_invocations: int = 0
    successful_invocations: int = 0
    failed_invocations: int = 0

    model_config = ConfigDict(from_attributes=True)


class ToolExecutionBase(BaseModel):
    input_data: Dict[str, Any] = Field(default_factory=dict)


class ToolExecutionCreate(ToolExecutionBase):
    tool_id: str
    agent_id: Optional[str] = None
    workflow_execution_id: Optional[str] = None


class ToolExecutionUpdate(BaseModel):
    status: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class ToolExecutionResponse(ToolExecutionBase):
    id: str
    tool_id: str
    agent_id: Optional[str] = None
    workflow_execution_id: Optional[str] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ToolListResponse(BaseModel):
    tools: List[ToolResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class ToolExecutionListResponse(BaseModel):
    executions: List[ToolExecutionResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class ToolInvocationRequest(BaseModel):
    tool_id: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class ToolInvocationResponse(BaseModel):
    execution_id: str
    output_data: Dict[str, Any]
    status: str
    execution_time_ms: Optional[int] = None
