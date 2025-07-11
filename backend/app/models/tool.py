from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class ToolType(enum.Enum):
    API = "api"
    FUNCTION = "function"
    WEBHOOK = "webhook"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    EXTERNAL_SERVICE = "external_service"
    CUSTOM = "custom"


class ToolStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"


class Tool(Base):
    __tablename__ = "tools"
    __table_args__ = {"schema": "agent_mesh"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Tool classification
    tool_type = Column(Enum(ToolType), nullable=False)
    category = Column(String(100), nullable=True)
    tags = Column(JSON, default=[])
    
    # Tool configuration
    config = Column(JSON, nullable=False)
    tool_schema = Column(JSON, nullable=False)  # OpenAPI/JSON schema for the tool
    
    # Tool implementation
    implementation = Column(Text, nullable=True)  # Code or configuration
    endpoint_url = Column(String(500), nullable=True)
    
    # Authentication and security
    auth_type = Column(String(50), nullable=True)
    auth_config = Column(JSON, default={})
    
    # Status and metadata
    status = Column(Enum(ToolStatus), nullable=False, default=ToolStatus.ACTIVE)
    version = Column(String(50), default="1.0.0")
    
    # Ownership
    created_by = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage statistics
    total_invocations = Column(Integer, default=0)
    successful_invocations = Column(Integer, default=0)
    failed_invocations = Column(Integer, default=0)
    
    # Relationships
    creator = relationship("User", back_populates="tools")
    executions = relationship("ToolExecution", back_populates="tool")
    
    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}', type='{self.tool_type}')>"


class ToolExecution(Base):
    __tablename__ = "tool_executions"
    __table_args__ = {"schema": "agent_mesh"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.tools.id"), nullable=False)
    
    # Execution context
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.agents.id"), nullable=True)
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey("agent_mesh.workflow_executions.id"), nullable=True)
    
    # Execution details
    status = Column(String(50), nullable=False, default="pending")
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
