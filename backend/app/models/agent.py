"""
Agent model
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from pgvector.sqlalchemy import Vector

from app.core.database import Base
# Import association tables from master_data
from app.models.master_data import agent_skills, agent_constraints, agent_tools


class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AgentStatus(str, enum.Enum):
    """Agent status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPLOYING = "deploying"
    STOPPED = "stopped"


class AgentCategory(Base):
    """Agent category model"""
    
    __tablename__ = "agent_categories"
    __table_args__ = {"schema": "app"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    icon = Column(String(100))
    color = Column(String(7), default="#3B82F6")
    sort_order = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    templates = relationship("AgentTemplate", back_populates="category")
    agents = relationship("Agent", back_populates="category")
    
    def __repr__(self):
        return f"<AgentCategory(id={self.id}, name={self.name})>"
    
    def to_dict(self):
        """Convert category to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentTemplate(Base):
    """Agent template model"""
    
    __tablename__ = "agent_templates"
    __table_args__ = {"schema": "app"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(50), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("app.agent_categories.id"))
    template_code = Column(Text, nullable=False)
    config_schema = Column(JSONB, default=dict)
    default_config = Column(JSONB, default=dict)
    required_tools = Column(JSONB, default=list)
    supported_models = Column(JSONB, default=list)
    tags = Column(JSONB, default=list)
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("app.users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("AgentCategory", back_populates="templates")
    created_by_user = relationship("User", back_populates="created_templates")
    agents = relationship("Agent", back_populates="template")
    
    def __repr__(self):
        return f"<AgentTemplate(id={self.id}, name={self.name}, type={self.template_type})>"
    
    def to_dict(self):
        """Convert template to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "template_type": self.template_type,
            "category_id": str(self.category_id) if self.category_id else None,
            "config_schema": self.config_schema,
            "default_config": self.default_config,
            "required_tools": self.required_tools,
            "supported_models": self.supported_models,
            "tags": self.tags,
            "version": self.version,
            "is_active": self.is_active,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Agent(BaseModel):
    """Agent model"""
    
    __tablename__ = "agents"
    __table_args__ = {"schema": "app"}
    
    name = Column(String(100), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(AgentStatus, name="agent_status", schema="app"), default=AgentStatus.INACTIVE, index=True)
    
    # Categorization
    category_id = Column(UUID(as_uuid=True), ForeignKey("app.agent_categories.id"))
    template_id = Column(UUID(as_uuid=True), ForeignKey("app.agent_templates.id"))
    type = Column(String(50), nullable=True, index=True)  # 'lowcode' or 'custom'
    
    # Model configurations
    model_id = Column(UUID(as_uuid=True), ForeignKey("master.model_configurations.id"))
    llm_model = Column(String(100), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    
    # Prompt and configuration
    system_prompt = Column(Text)
    prompt = Column(Text, nullable=True)  # From enhanced model
    configuration = Column(JSONB, default=dict)
    
    # Payload specifications
    input_payload = Column(JSONB, nullable=True)  # Schema and examples for input
    output_payload = Column(JSONB, nullable=True)  # Schema and examples for output
    
    # Features and capabilities
    capabilities = Column(JSONB, default=list)
    tools = Column(JSONB, default=list)
    memory_config = Column(JSONB, default=dict)
    rate_limits = Column(JSONB, default=dict)
    tags = Column(JSONB, default=list)
    is_public = Column(Boolean, default=True, index=True)  # From enhanced model
    
    # Search support
    search_vector = Column(Vector(1536), nullable=True)  # From enhanced model
    
    # Version and deployment
    version = Column(String(20), default="1.0.0")
    deployment_config = Column(JSONB, default=dict)
    health_check_url = Column(String(500))
    dns = Column(String(500), nullable=True)  # From enhanced model
    port = Column(Integer, nullable=True)     # From enhanced model
    auth_token = Column(String(500), nullable=True)  # From enhanced model
    
    # Health monitoring
    last_health_check = Column(DateTime(timezone=True))
    health_status = Column(String(20), default='unknown', index=True)  # From enhanced model
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    last_error_at = Column(DateTime(timezone=True))
    
    # Ownership and usage
    created_by = Column(UUID(as_uuid=True), ForeignKey("app.users.id"))
    deployed_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True), index=True)
    usage_count = Column(Integer, default=0, index=True)
    
    # Relationships
    category = relationship("AgentCategory", back_populates="agents")
    template = relationship("AgentTemplate", back_populates="agents")
    creator = relationship("User", back_populates="agents", foreign_keys=[created_by])
    versions = relationship("AgentVersion", back_populates="agent", cascade="all, delete-orphan")
    metrics = relationship("AgentMetric", back_populates="agent")
    observability_metrics = relationship("Metric", back_populates="agent")
    log_entries = relationship("LogEntry", back_populates="agent")
    traces = relationship("Trace", back_populates="agent")
    tool_executions = relationship("ToolExecution", back_populates="agent")
    embeddings = relationship("AgentEmbedding", back_populates="agent", cascade="all, delete-orphan")
    
    # Enhanced model relationships
    skills = relationship("Skill", secondary=agent_skills, back_populates="agents")
    constraints = relationship("Constraint", secondary=agent_constraints, back_populates="agents")
    tools_assoc = relationship("Tool", secondary=agent_tools, back_populates="agents")
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name}, status={self.status})>"
    
    def to_dict(self):
        """Convert agent to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "status": self.status.value if hasattr(self.status, 'value') else self.status,
            "type": self.type,
            "category_id": str(self.category_id) if self.category_id else None,
            "template_id": str(self.template_id) if self.template_id else None,
            "model_id": str(self.model_id) if self.model_id else None,
            "system_prompt": self.system_prompt,
            "prompt": self.prompt,
            "configuration": self.configuration,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "memory_config": self.memory_config,
            "rate_limits": self.rate_limits,
            "tags": self.tags,
            "is_public": self.is_public,
            "version": self.version,
            "deployment_config": self.deployment_config,
            "health_check_url": self.health_check_url,
            "dns": self.dns,
            "port": self.port,
            "health_status": self.health_status,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_error_at": self.last_error_at.isoformat() if self.last_error_at else None,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "usage_count": self.usage_count,
            "input_payload": self.input_payload,
            "output_payload": self.output_payload,
        }
    
    def is_active(self) -> bool:
        """Check if agent is active"""
        return self.status == AgentStatus.ACTIVE or self.status == 'active'
    
    def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        return (self.status == AgentStatus.ACTIVE or self.status == 'active') and self.error_count < 5
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.last_used_at = func.now()


class AgentVersion(Base):
    """Agent version model for version control"""
    
    __tablename__ = "agent_versions"
    __table_args__ = {"schema": "app"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("app.agents.id"), nullable=False, index=True)
    version = Column(String(20), nullable=False, index=True)
    configuration = Column(JSONB, nullable=False)
    system_prompt = Column(Text)
    tools = Column(JSONB, default=list)
    changelog = Column(Text)
    is_active = Column(Boolean, default=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("app.users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="versions")
    
    def __repr__(self):
        return f"<AgentVersion(id={self.id}, agent_id={self.agent_id}, version={self.version})>"
    
    def to_dict(self):
        """Convert version to dictionary"""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "version": self.version,
            "configuration": self.configuration,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "changelog": self.changelog,
            "is_active": self.is_active,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AgentMetric(Base):
    """Agent metrics model"""
    
    __tablename__ = "agent_metrics"
    __table_args__ = {"schema": "app"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("app.agents.id"), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Integer, nullable=False)
    metric_type = Column(String(50), nullable=False)
    tags = Column(JSONB, default=dict)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    period = Column(String(20), default="instant", index=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="metrics")
    
    def __repr__(self):
        return f"<AgentMetric(id={self.id}, agent_id={self.agent_id}, metric={self.metric_name})>"
    
    def to_dict(self):
        """Convert metric to dictionary"""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "metric_type": self.metric_type,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "period": self.period,
        }


class AgentEmbedding(Base):
    """Agent embeddings model for semantic search"""
    
    __tablename__ = "agent_embeddings"
    __table_args__ = {"schema": "app"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("app.agents.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector)  # This would be vector type in production
    embedding_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="embeddings")
    
    def __repr__(self):
        return f"<AgentEmbedding(id={self.id}, agent_id={self.agent_id})>"
    
    def to_dict(self):
        """Convert embedding to dictionary"""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "content": self.content,
            "metadata": self.embedding_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Base Agent Framework
from abc import ABC, abstractmethod
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentCapability:
    """Agent capability data class"""
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    confidence_level: float


@dataclass
class AgentMetadata:
    """Agent metadata data class"""
    agent_id: str
    agent_type: str
    capabilities: List[AgentCapability]
    status: AgentStatus
    created_at: datetime
    performance_metrics: Dict[str, float]


class BaseAgent(ABC):
    """Core interface that all teams must implement"""
    
    @abstractmethod
    async def process_intent(self, intent: Dict, context: Dict) -> Dict:
        """Process the intent and return a response"""
        pass
    
    @abstractmethod
    def define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of the agent"""
        pass
    
    @abstractmethod
    async def get_health_status(self) -> str:
        """Get the health status of the agent"""
        pass


class MessageBroker(ABC):
    """Message broker API contract"""
    
    @abstractmethod
    async def register_agent(self, metadata: AgentMetadata) -> bool:
        """Register an agent with the broker"""
        pass
    
    @abstractmethod
    async def route_message(self, from_id: str, to_id: str, message: Dict) -> bool:
        """Route a message from one agent to another"""
        pass
    
    @abstractmethod
    async def broadcast(self, message: Dict, filter_criteria: Dict = None) -> int:
        """Broadcast a message to multiple agents"""
        pass
    
    @abstractmethod
    async def subscribe_to_events(self, agent_id: str, event_types: List[str]):
        """Subscribe to events of specific types"""
        pass
    
    @abstractmethod
    async def get_agent_registry(self) -> Dict[str, AgentMetadata]:
        """Get the registry of all agents"""
        pass
