"""
Template model for agent templates
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class TemplateStatus(str, enum.Enum):
    """Template status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    DEPRECATED = "deprecated"


class TemplateType(str, enum.Enum):
    """Template type enumeration"""
    AGENT = "agent"
    WORKFLOW = "workflow"
    TOOL = "tool"
    INTEGRATION = "integration"


class Template(Base):
    """Template model for storing agent templates"""
    
    __tablename__ = "templates"
    __table_args__ = {"schema": "app"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(50), nullable=False, index=True)
    category = Column(String(100), index=True)
    definition = Column(JSONB)  # Template definition/configuration
    json_schema = Column(JSONB)  # JSON schema for validation
    parameters = Column(JSONB)  # Default parameters
    template_metadata = Column(JSONB)  # Additional metadata
    tags = Column(ARRAY(String), default=[], index=True)
    version = Column(String(20), default="1.0.0")
    is_public = Column(Boolean, default=False, index=True)
    status = Column(String(20), default="active", index=True)
    
    # Relationships
    created_by = Column(UUID(as_uuid=True), ForeignKey("app.users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=True)  # Organization reference (no FK until organizations table exists)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Template versions
    versions = relationship("TemplateVersion", back_populates="template", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Template(id={self.id}, name={self.name}, type={self.template_type})>"


class TemplateVersion(Base):
    """Template version model for versioning templates"""
    
    __tablename__ = "template_versions"
    __table_args__ = {"schema": "app"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("app.templates.id"), nullable=False)
    version = Column(String(20), nullable=False)
    definition = Column(JSONB, nullable=False)  # Version-specific definition
    changelog = Column(Text)  # Change description
    is_current = Column(Boolean, default=False, index=True)
    is_published = Column(Boolean, default=False, index=True)
    
    # Relationships
    template = relationship("Template", back_populates="versions")
    created_by = Column(UUID(as_uuid=True), ForeignKey("app.users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<TemplateVersion(id={self.id}, template_id={self.template_id}, version={self.version})>"
