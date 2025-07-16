"""
Agent Creation Service
Handles the creation of agents from templates, custom specifications, and cloning
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid
import yaml
import json
from pathlib import Path

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.agent import Agent, AgentTemplate, AgentStatus
from app.schemas.agent import AgentCreate, AgentResponse
from app.core.exceptions import ValidationError, NotFoundError


@dataclass
class ResourceRequirements:
    """Resource requirements for agent deployment"""
    memory_mb: int = 512
    cpu_cores: float = 0.5
    storage_gb: int = 1
    max_replicas: int = 5
    min_replicas: int = 1


@dataclass
class AgentSpec:
    """Agent specification for custom agent creation"""
    name: str
    type: str
    capabilities: List[str]
    configuration: Dict
    resources: ResourceRequirements
    skills: List[str]
    display_name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_model: Optional[str] = "gpt-4"
    embedding_model: Optional[str] = "text-embedding-ada-002"
    tags: List[str] = None
    is_public: bool = True


@dataclass
class ValidationResult:
    """Result of agent configuration validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class AgentCreationService:
    """Service for creating and managing agents"""
    
    def __init__(self, db: Session):
        self.db = db
        self.template_path = Path("agent-templates")
    
    async def create_agent_from_template(self, template_id: str, config: Dict, created_by: str) -> str:
        """Create an agent from a template"""
        try:
            # Load template
            template = self._load_template(template_id)
            if not template:
                raise NotFoundError(f"Template {template_id} not found")
            
            # Merge template with custom config
            merged_config = self._merge_template_config(template, config)
            
            # Validate configuration
            validation_result = await self.validate_agent_config(merged_config)
            if not validation_result.is_valid:
                raise ValidationError(f"Invalid configuration: {validation_result.errors}")
            
            # Create agent
            agent = Agent(
                id=uuid.uuid4(),
                name=merged_config["agent"]["name"],
                display_name=merged_config["agent"]["display_name"],
                description=merged_config["agent"]["description"],
                type=merged_config["agent"]["type"],
                template_id=template_id,
                llm_model=merged_config.get("model", {}).get("llm_model"),
                embedding_model=merged_config.get("model", {}).get("embedding_model"),
                system_prompt=merged_config.get("prompts", {}).get("system_prompt"),
                configuration=merged_config,
                capabilities=merged_config.get("capabilities", []),
                tools=merged_config.get("tools", []),
                tags=merged_config.get("agent", {}).get("tags", []),
                is_public=merged_config.get("agent", {}).get("is_public", True),
                status=AgentStatus.INACTIVE,
                created_by=created_by,
                input_payload=merged_config.get("input_payload"),
                output_payload=merged_config.get("output_payload")
            )
            
            self.db.add(agent)
            self.db.commit()
            self.db.refresh(agent)
            
            return str(agent.id)
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def create_custom_agent(self, specification: AgentSpec, created_by: str) -> str:
        """Create a custom agent from specification"""
        try:
            # Convert specification to configuration
            config = self._spec_to_config(specification)
            
            # Validate configuration
            validation_result = await self.validate_agent_config(config)
            if not validation_result.is_valid:
                raise ValidationError(f"Invalid specification: {validation_result.errors}")
            
            # Create agent
            agent = Agent(
                id=uuid.uuid4(),
                name=specification.name,
                display_name=specification.display_name or specification.name,
                description=specification.description,
                type=specification.type,
                llm_model=specification.llm_model,
                embedding_model=specification.embedding_model,
                system_prompt=specification.system_prompt,
                configuration=specification.configuration,
                capabilities=specification.capabilities,
                tags=specification.tags or [],
                is_public=specification.is_public,
                status=AgentStatus.INACTIVE,
                created_by=created_by
            )
            
            self.db.add(agent)
            self.db.commit()
            self.db.refresh(agent)
            
            return str(agent.id)
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def clone_agent(self, source_agent_id: str, modifications: Dict, created_by: str) -> str:
        """Clone an existing agent with modifications"""
        try:
            # Get source agent
            source_agent = self.db.query(Agent).filter(Agent.id == source_agent_id).first()
            if not source_agent:
                raise NotFoundError(f"Agent {source_agent_id} not found")
            
            # Create modified configuration
            config = source_agent.configuration.copy()
            config.update(modifications)
            
            # Validate configuration
            validation_result = await self.validate_agent_config(config)
            if not validation_result.is_valid:
                raise ValidationError(f"Invalid modifications: {validation_result.errors}")
            
            # Create cloned agent
            cloned_agent = Agent(
                id=uuid.uuid4(),
                name=modifications.get("name", f"{source_agent.name}-clone"),
                display_name=modifications.get("display_name", f"{source_agent.display_name} (Clone)"),
                description=modifications.get("description", source_agent.description),
                type=source_agent.type,
                template_id=source_agent.template_id,
                llm_model=modifications.get("llm_model", source_agent.llm_model),
                embedding_model=modifications.get("embedding_model", source_agent.embedding_model),
                system_prompt=modifications.get("system_prompt", source_agent.system_prompt),
                configuration=config,
                capabilities=modifications.get("capabilities", source_agent.capabilities),
                tools=modifications.get("tools", source_agent.tools),
                tags=modifications.get("tags", source_agent.tags),
                is_public=modifications.get("is_public", source_agent.is_public),
                status=AgentStatus.INACTIVE,
                created_by=created_by,
                input_payload=modifications.get("input_payload", source_agent.input_payload),
                output_payload=modifications.get("output_payload", source_agent.output_payload)
            )
            
            self.db.add(cloned_agent)
            self.db.commit()
            self.db.refresh(cloned_agent)
            
            return str(cloned_agent.id)
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def validate_agent_config(self, config: Dict) -> ValidationResult:
        """Validate agent configuration"""
        errors = []
        warnings = []
        suggestions = []
        
        # Required fields validation
        if not config.get("agent", {}).get("name"):
            errors.append("Agent name is required")
        
        if not config.get("agent", {}).get("display_name"):
            errors.append("Agent display name is required")
        
        if not config.get("agent", {}).get("type"):
            errors.append("Agent type is required")
        elif config["agent"]["type"] not in ["lowcode", "custom"]:
            errors.append("Agent type must be 'lowcode' or 'custom'")
        
        # Model validation
        if not config.get("model", {}).get("llm_model"):
            warnings.append("No LLM model specified, using default")
        
        # Prompt validation
        if not config.get("prompts", {}).get("system_prompt"):
            warnings.append("No system prompt specified")
        
        # Capabilities validation
        capabilities = config.get("capabilities", [])
        if not capabilities:
            suggestions.append("Consider adding capabilities to better define agent functionality")
        
        # Tools validation
        tools = config.get("tools", [])
        for tool in tools:
            if not tool.get("name"):
                errors.append("Tool name is required")
            if not tool.get("description"):
                warnings.append(f"Tool '{tool.get('name', 'unnamed')}' has no description")
        
        # Deployment validation
        deployment = config.get("deployment", {})
        replicas = deployment.get("replicas", 1)
        if replicas < 1:
            errors.append("Deployment replicas must be at least 1")
        
        # Memory validation
        memory = config.get("memory", {})
        if memory.get("max_messages", 0) > 100:
            warnings.append("High message limit may impact performance")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _load_template(self, template_id: str) -> Optional[Dict]:
        """Load template from file"""
        template_file = self.template_path / f"{template_id}.yaml"
        if not template_file.exists():
            return None
        
        with open(template_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _merge_template_config(self, template: Dict, config: Dict) -> Dict:
        """Merge template with custom configuration"""
        merged = template.copy()
        
        # Deep merge configuration
        def deep_merge(base, override):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(merged, config)
        return merged
    
    def _spec_to_config(self, spec: AgentSpec) -> Dict:
        """Convert AgentSpec to configuration dictionary"""
        return {
            "agent": {
                "name": spec.name,
                "display_name": spec.display_name or spec.name,
                "description": spec.description,
                "type": spec.type,
                "tags": spec.tags or [],
                "is_public": spec.is_public
            },
            "model": {
                "llm_model": spec.llm_model,
                "embedding_model": spec.embedding_model
            },
            "prompts": {
                "system_prompt": spec.system_prompt
            },
            "capabilities": spec.capabilities,
            "configuration": spec.configuration,
            "deployment": {
                "replicas": spec.resources.min_replicas,
                "resources": {
                    "memory": f"{spec.resources.memory_mb}Mi",
                    "cpu": str(spec.resources.cpu_cores)
                },
                "auto_scaling": {
                    "min_replicas": spec.resources.min_replicas,
                    "max_replicas": spec.resources.max_replicas
                }
            }
        }
