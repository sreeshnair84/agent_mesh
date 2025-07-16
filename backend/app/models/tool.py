from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base
from app.models.master_data import agent_tools


class ToolType(enum.Enum):
    FUNCTION = "function"
    API = "api"
    MCP = "mcp"
    BUILTIN = "builtin"


class ExecutionStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Tool(Base):
    __tablename__ = "tools"
    __table_args__ = {"schema": "app"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Tool classification
    type = Column(Enum(ToolType, name="tool_type", schema="app"), nullable=False)
    category = Column(String(100), nullable=True)
    
    # Tool configuration
    config = Column(JSON, default={})
    schema_input = Column(JSON, nullable=True)
    schema_output = Column(JSON, nullable=True)
    
    # Tool implementation
    endpoint_url = Column(String(500), nullable=True)
    authentication = Column(JSON, default={})
    rate_limits = Column(JSON, default={})
    timeout_seconds = Column(Integer, default=30)
    retries = Column(Integer, default=3)
    
    # Status and metadata
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True)
    
    # Ownership
    created_by = Column(UUID(as_uuid=True), ForeignKey("app.users.id"), nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="tools")
    executions = relationship("ToolExecution", back_populates="tool")
    agents = relationship("Agent", secondary=agent_tools, back_populates="tools_assoc")
    
    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}', type='{self.type}')>"


class ToolExecution(Base):
    __tablename__ = "tool_executions"
    __table_args__ = {"schema": "app"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("app.tools.id"), nullable=False)
    
    # Execution context
    agent_id = Column(UUID(as_uuid=True), ForeignKey("app.agents.id"), nullable=True)
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey("app.workflow_executions.id"), nullable=True)
    
    # Execution details
    status = Column(Enum(ExecutionStatus, name="execution_status", schema="app"), nullable=False, default=ExecutionStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Input/Output data
    input_data = Column(JSON, default={})
    output_data = Column(JSON, default={})
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Metrics
    execution_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    tool = relationship("Tool", back_populates="executions")
    agent = relationship("Agent", back_populates="tool_executions")
    
    def __repr__(self):
        return f"<ToolExecution(id={self.id}, tool_id={self.tool_id}, status='{self.status}')>"
