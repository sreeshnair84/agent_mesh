from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
import enum

from app.core.database import Base


class WorkflowStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowType(enum.Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    CUSTOM = "custom"


class Workflow(Base):
    __tablename__ = "workflows"
    __table_args__ = {"schema": "app"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    workflow_type = Column(Enum(WorkflowType), nullable=False, default=WorkflowType.SEQUENTIAL)
    status = Column(Enum(WorkflowStatus, name="workflow_status", schema="app"), nullable=False, default=WorkflowStatus.DRAFT)
    
    # Workflow definition as JSON
    definition = Column(JSON, nullable=False)
    
    # Configuration and metadata
    config = Column(JSON, default={})
    workflow_metadata = Column(JSON, default={})
    
    # Ownership and permissions
    created_by = Column(UUID(as_uuid=True), ForeignKey("app.users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Versioning
    version = Column(String(50), default="1.0.0")
    parent_workflow_id = Column(UUID(as_uuid=True), ForeignKey("app.workflows.id"), nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Execution statistics
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    
    # Relationships
    creator = relationship("User", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow")
    parent_workflow = relationship("Workflow", remote_side=[id])
    
    def __repr__(self):
        return f"<Workflow(id={self.id}, name='{self.name}', status='{self.status}')>"


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    __table_args__ = {"schema": "app"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("app.workflows.id"), nullable=False)
    
    # Execution details
    status = Column(Enum(ExecutionStatus, name="execution_status", schema="app"), nullable=False, default=ExecutionStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Input/Output data
    input_data = Column(JSON, default={})
    output_data = Column(JSON, default={})
    
    # Execution context
    context = Column(JSON, default={})
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Metrics
    execution_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    steps = relationship("WorkflowStepExecution", back_populates="execution")
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status='{self.status}')>"


class WorkflowStepExecution(Base):
    __tablename__ = "workflow_step_executions"
    __table_args__ = {"schema": "app"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("app.workflow_executions.id"), nullable=False)
    
    # Step details
    step_name = Column(String(255), nullable=False)
    step_type = Column(String(100), nullable=False)
    step_config = Column(JSON, default={})
    
    # Execution details
    status = Column(Enum(ExecutionStatus, name="execution_status", schema="app"), nullable=False, default=ExecutionStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Step data
    input_data = Column(JSON, default={})
    output_data = Column(JSON, default={})
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Metrics
    execution_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    execution = relationship("WorkflowExecution", back_populates="steps")
    
    def __repr__(self):
        return f"<WorkflowStepExecution(id={self.id}, step_name='{self.step_name}', status='{self.status}')>"
