from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import uuid


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowType(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    CUSTOM = "custom"


class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    workflow_type: WorkflowType = WorkflowType.SEQUENTIAL
    definition: Dict[str, Any] = Field(..., description="Workflow definition as JSON")
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"
    parent_workflow_id: Optional[str] = None


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    workflow_type: Optional[WorkflowType] = None
    definition: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[WorkflowStatus] = None
    version: Optional[str] = None


class WorkflowResponse(WorkflowBase):
    id: str
    status: WorkflowStatus
    created_by: str
    organization_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0

    class Config:
        from_attributes = True


class WorkflowExecutionBase(BaseModel):
    input_data: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionCreate(WorkflowExecutionBase):
    workflow_id: str


class WorkflowExecutionUpdate(BaseModel):
    status: Optional[WorkflowStatus] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class WorkflowExecutionResponse(WorkflowExecutionBase):
    id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None

    class Config:
        from_attributes = True


class WorkflowStepExecutionBase(BaseModel):
    step_name: str = Field(..., min_length=1, max_length=255)
    step_type: str = Field(..., min_length=1, max_length=100)
    step_config: Dict[str, Any] = Field(default_factory=dict)
    input_data: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStepExecutionCreate(WorkflowStepExecutionBase):
    execution_id: str


class WorkflowStepExecutionUpdate(BaseModel):
    status: Optional[WorkflowStatus] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class WorkflowStepExecutionResponse(WorkflowStepExecutionBase):
    id: str
    execution_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class WorkflowExecutionListResponse(BaseModel):
    executions: List[WorkflowExecutionResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
