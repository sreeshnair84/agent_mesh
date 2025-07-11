"""
Master data models for skills, constraints, prompts, models, and secrets
"""

from sqlalchemy import Column, String, Text, JSON, ForeignKey, Boolean, Table, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
from app.core.database import Base


# Association tables for many-to-many relationships
agent_skills = Table(
    'agent_skills',
    Base.metadata,
    Column('agent_id', UUID(as_uuid=True), ForeignKey('agents.id')),
    Column('skill_id', UUID(as_uuid=True), ForeignKey('skills.id')),
    schema='app'
)

agent_constraints = Table(
    'agent_constraints',
    Base.metadata,
    Column('agent_id', UUID(as_uuid=True), ForeignKey('agents.id')),
    Column('constraint_id', UUID(as_uuid=True), ForeignKey('constraints.id')),
    schema='app'
)

agent_tools = Table(
    'agent_tools',
    Base.metadata,
    Column('agent_id', UUID(as_uuid=True), ForeignKey('agents.id')),
    Column('tool_id', UUID(as_uuid=True), ForeignKey('tools.id')),
    schema='app'
)


class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Skill(BaseModel):
    """Skills that can be associated with agents"""
    
    __tablename__ = "skills"
    __table_args__ = {"schema": "app"}
    
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)
    config = Column(JSON, nullable=True)
    
    # Relationships
    agents = relationship("Agent", secondary=agent_skills, back_populates="skills")
    
    def __repr__(self):
        return f"<Skill(id={self.id}, name={self.name})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Constraint(BaseModel):
    """Constraints that can be applied to agents"""
    
    __tablename__ = "constraints"
    __table_args__ = {"schema": "app"}
    
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=False)
    type = Column(String(50), nullable=False, index=True)  # 'validation', 'security', 'performance'
    
    # Relationships
    agents = relationship("Agent", secondary=agent_constraints, back_populates="constraints")
    
    def __repr__(self):
        return f"<Constraint(id={self.id}, name={self.name}, type={self.type})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "type": self.type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Prompt(BaseModel):
    """Reusable prompt templates"""
    
    __tablename__ = "prompts"
    __table_args__ = {"schema": "app"}
    
    name = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    version = Column(String(20), default="1.0")
    description = Column(Text, nullable=True)
    tags = Column(ARRAY(String), default=[])
    
    # Relationships
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    owner = relationship("User", back_populates="prompts")
    
    def __repr__(self):
        return f"<Prompt(id={self.id}, name={self.name}, version={self.version})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "content": self.content,
            "version": self.version,
            "description": self.description,
            "tags": self.tags,
            "owner_id": str(self.owner_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Model(BaseModel):
    """LLM model configurations"""
    
    __tablename__ = "models"
    __table_args__ = {"schema": "app"}
    
    name = Column(String(100), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)  # 'azure_openai', 'gemini', 'claude'
    model_id = Column(String(100), nullable=False)
    config = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    owner = relationship("User", back_populates="models")
    
    def __repr__(self):
        return f"<Model(id={self.id}, name={self.name}, provider={self.provider})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "provider": self.provider,
            "model_id": self.model_id,
            "config": self.config,
            "is_active": self.is_active,
            "owner_id": str(self.owner_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EnvironmentSecret(BaseModel):
    """Encrypted environment secrets"""
    
    __tablename__ = "environment_secrets"
    __table_args__ = {"schema": "app"}
    
    key = Column(String(100), nullable=False, index=True)
    value = Column(Text, nullable=False)  # Encrypted
    environment = Column(String(20), nullable=False, index=True)  # 'dev', 'staging', 'prod'
    description = Column(Text, nullable=True)
    
    # Relationships
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    owner = relationship("User", back_populates="environment_secrets")
    
    def __repr__(self):
        return f"<EnvironmentSecret(id={self.id}, key={self.key}, env={self.environment})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "key": self.key,
            "environment": self.environment,
            "description": self.description,
            "owner_id": str(self.owner_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
