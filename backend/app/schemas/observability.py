from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    metric_type: MetricType
    value: float
    labels: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=50)


class MetricCreate(MetricBase):
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    tool_id: Optional[str] = None


class MetricResponse(MetricBase):
    id: str
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    tool_id: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class LogEntryBase(BaseModel):
    level: LogLevel
    message: str = Field(..., min_length=1)
    source: Optional[str] = Field(None, max_length=255)
    function_name: Optional[str] = Field(None, max_length=255)
    line_number: Optional[int] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    exception_details: Optional[Dict[str, Any]] = None


class LogEntryCreate(LogEntryBase):
    agent_id: Optional[str] = None
    workflow_execution_id: Optional[str] = None
    tool_execution_id: Optional[str] = None


class LogEntryResponse(LogEntryBase):
    id: str
    agent_id: Optional[str] = None
    workflow_execution_id: Optional[str] = None
    tool_execution_id: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class TraceBase(BaseModel):
    trace_id: str = Field(..., min_length=1, max_length=255)
    span_id: str = Field(..., min_length=1, max_length=255)
    parent_span_id: Optional[str] = Field(None, max_length=255)
    operation_name: str = Field(..., min_length=1, max_length=255)
    service_name: str = Field(..., min_length=1, max_length=255)
    status: str = Field(default="ok", max_length=50)
    tags: Dict[str, Any] = Field(default_factory=dict)
    logs: List[Dict[str, Any]] = Field(default_factory=list)


class TraceCreate(TraceBase):
    agent_id: Optional[str] = None
    workflow_execution_id: Optional[str] = None
    tool_execution_id: Optional[str] = None


class TraceUpdate(BaseModel):
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    logs: Optional[List[Dict[str, Any]]] = None


class TraceResponse(TraceBase):
    id: str
    agent_id: Optional[str] = None
    workflow_execution_id: Optional[str] = None
    tool_execution_id: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None

    class Config:
        from_attributes = True


class AlertBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    condition: str = Field(..., min_length=1)
    threshold: Optional[float] = None
    severity: str = Field(default="medium", max_length=50)
    notification_channels: List[str] = Field(default_factory=list)


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None
    notification_channels: Optional[List[str]] = None


class AlertResponse(AlertBase):
    id: str
    is_active: bool
    is_triggered: bool
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncidentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    severity: str = Field(..., max_length=50)
    status: str = Field(default="open", max_length=50)
    context: Dict[str, Any] = Field(default_factory=dict)


class IncidentCreate(IncidentBase):
    alert_id: str


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class IncidentResponse(IncidentBase):
    id: str
    alert_id: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MetricListResponse(BaseModel):
    metrics: List[MetricResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class LogEntryListResponse(BaseModel):
    logs: List[LogEntryResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class TraceListResponse(BaseModel):
    traces: List[TraceResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class IncidentListResponse(BaseModel):
    incidents: List[IncidentResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
