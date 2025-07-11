"""
Enhanced agent model with pgvector support for semantic search
"""

from sqlalchemy import Column, String, Text, JSON, ForeignKey, Boolean, Table, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
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


class Agent(BaseModel):
    """Enhanced Agent model with pgvector support"""
    
    __tablename__ = "agents"
    __table_args__ = {"schema": "app"}
    
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, index=True)  # 'lowcode' or 'custom'
    template = Column(String(100), nullable=True)
    
    # Configuration
    prompt = Column(Text, nullable=True)
    config = Column(JSON, nullable=True)
    
    # Input/Output Payload Specifications
    input_payload = Column(JSON, nullable=True)  # Schema and examples for input
    output_payload = Column(JSON, nullable=True)  # Schema and examples for output
    
    # LLM Settings
    llm_model = Column(String(100), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    
    # Deployment
    status = Column(String(20), default='inactive', index=True)  # 'active', 'inactive', 'deploying', 'error'
    dns = Column(String(500), nullable=True)
    health_url = Column(String(500), nullable=True)
    auth_token = Column(String(500), nullable=True)
    port = Column(Integer, nullable=True)
    
    # Metadata
    tags = Column(ARRAY(String), default=[])
    is_public = Column(Boolean, default=True, index=True)
    
    # Search vector for semantic search
    search_vector = Column(Vector(1536), nullable=True)
    
    # Relationships
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    owner = relationship("User", back_populates="agents")
    
    skills = relationship("Skill", secondary=agent_skills, back_populates="agents")
    constraints = relationship("Constraint", secondary=agent_constraints, back_populates="agents")
    tools = relationship("Tool", secondary=agent_tools, back_populates="agents")
    
    # Health and metrics
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(20), default='unknown', index=True)  # 'healthy', 'unhealthy', 'unknown'
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name}, status={self.status})>"
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'template': self.template,
            'status': self.status,
            'tags': self.tags,
            'is_public': self.is_public,
            'owner': {
                'id': str(self.owner.id),
                'name': self.owner.name,
                'avatar': self.owner.avatar
            } if self.owner else None,
            'health_status': self.health_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'llm_model': self.llm_model,
            'embedding_model': self.embedding_model,
            'dns': self.dns,
            'health_url': self.health_url,
            'port': self.port,
            'prompt': self.prompt,
            'config': self.config,
            'input_payload': self.input_payload,
            'output_payload': self.output_payload,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
        }
    
    def is_active(self) -> bool:
        """Check if agent is active"""
        return self.status == 'active'
    
    def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        return self.health_status == 'healthy'
