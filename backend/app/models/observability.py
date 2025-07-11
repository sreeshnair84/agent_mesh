from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Enum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class MetricType(enum.Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Metric(Base):
    __tablename__ = "metrics"
    __table_args__ = {"schema": "agent_mesh"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    metric_type = Column(Enum(MetricType), nullable=False)
    value = Column(Float, nullable=False)
    
    # Context
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.agents.id"), nullable=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.workflows.id"), nullable=True)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.tools.id"), nullable=True)
    
    # Labels and tags
    labels = Column(JSON, default={})
    tags = Column(JSON, default=[])
    
    # Metadata
    description = Column(Text)
    unit = Column(String(50))
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", back_populates="metrics")
    
    def __repr__(self):
        return f"<Metric(id={self.id}, name='{self.name}', value={self.value})>"


class LogEntry(Base):
    __tablename__ = "log_entries"
    __table_args__ = {"schema": "agent_mesh"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(Enum(LogLevel), nullable=False)
    message = Column(Text, nullable=False)
    
    # Context
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.agents.id"), nullable=True)
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.workflow_executions.id"), nullable=True)
    tool_execution_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.tool_executions.id"), nullable=True)
    
    # Source information
    source = Column(String(255))
    function_name = Column(String(255))
    line_number = Column(Integer)
    
    # Additional data
    context = Column(JSON, default={})
    exception_details = Column(JSON, nullable=True)
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent = relationship("Agent", back_populates="log_entries")
    
    def __repr__(self):
        return f"<LogEntry(id={self.id}, level='{self.level}', message='{self.message[:50]}...')>"


class Trace(Base):
    __tablename__ = "traces"
    __table_args__ = {"schema": "agent_mesh"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(255), nullable=False, unique=True)
    span_id = Column(String(255), nullable=False)
    parent_span_id = Column(String(255), nullable=True)
    
    # Trace details
    operation_name = Column(String(255), nullable=False)
    service_name = Column(String(255), nullable=False)
    
    # Context
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.agents.id"), nullable=True)
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.workflow_executions.id"), nullable=True)
    tool_execution_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.tool_executions.id"), nullable=True)
    
    # Timing
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(50), default="ok")
    
    # Tags and metadata
    tags = Column(JSON, default={})
    logs = Column(JSON, default=[])
    
    # Relationships
    agent = relationship("Agent", back_populates="traces")
    
    def __repr__(self):
        return f"<Trace(id={self.id}, trace_id='{self.trace_id}', operation='{self.operation_name}')>"


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {"schema": "agent_mesh"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Alert configuration
    condition = Column(Text, nullable=False)  # Alert condition query/expression
    threshold = Column(Float, nullable=True)
    severity = Column(String(50), nullable=False, default="medium")
    
    # Status
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered_at = Column(DateTime, nullable=True)
    
    # Notification settings
    notification_channels = Column(JSON, default=[])
    
    # Relationships
    incidents = relationship("Incident", back_populates="alert")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, name='{self.name}', severity='{self.severity}')>"


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = {"schema": "agent_mesh"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.alerts.id"), nullable=False)
    
    # Incident details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    severity = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="open")
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Context
    context = Column(JSON, default={})
    
    # Relationships
    alert = relationship("Alert", back_populates="incidents")
    
    def __repr__(self):
        return f"<Incident(id={self.id}, title='{self.title}', status='{self.status}')>"
