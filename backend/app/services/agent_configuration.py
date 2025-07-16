"""
Agent Configuration Manager
Handles configuration updates, validation, and version management
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.agent import Agent, AgentVersion
from app.core.exceptions import ValidationError, NotFoundError


class AgentConfigurationManager:
    """Service for managing agent configurations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def update_agent_config(self, agent_id: str, config_updates: Dict, user_id: str) -> bool:
        """Update agent configuration"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise NotFoundError(f"Agent {agent_id} not found")
            
            # Create new version before updating
            await self._create_config_version(agent, user_id, "Configuration update")
            
            # Update configuration
            if "system_prompt" in config_updates:
                agent.system_prompt = config_updates["system_prompt"]
            
            if "configuration" in config_updates:
                agent.configuration.update(config_updates["configuration"])
            
            if "capabilities" in config_updates:
                agent.capabilities = config_updates["capabilities"]
            
            if "tools" in config_updates:
                agent.tools = config_updates["tools"]
            
            if "tags" in config_updates:
                agent.tags = config_updates["tags"]
            
            if "llm_model" in config_updates:
                agent.llm_model = config_updates["llm_model"]
            
            if "embedding_model" in config_updates:
                agent.embedding_model = config_updates["embedding_model"]
            
            # Update metadata
            agent.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def get_agent_config(self, agent_id: str) -> Dict:
        """Get complete agent configuration"""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        return {
            "agent": {
                "id": str(agent.id),
                "name": agent.name,
                "display_name": agent.display_name,
                "description": agent.description,
                "type": agent.type,
                "status": agent.status.value if hasattr(agent.status, 'value') else agent.status,
                "tags": agent.tags,
                "is_public": agent.is_public
            },
            "model": {
                "llm_model": agent.llm_model,
                "embedding_model": agent.embedding_model
            },
            "prompts": {
                "system_prompt": agent.system_prompt
            },
            "capabilities": agent.capabilities,
            "tools": agent.tools,
            "configuration": agent.configuration,
            "input_payload": agent.input_payload,
            "output_payload": agent.output_payload,
            "deployment": {
                "health_check_url": agent.health_check_url,
                "dns": agent.dns,
                "port": agent.port
            },
            "metadata": {
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
                "created_by": str(agent.created_by) if agent.created_by else None,
                "version": agent.version
            }
        }
    
    async def create_config_version(self, agent_id: str, user_id: str, changelog: str) -> str:
        """Create a new configuration version"""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        return await self._create_config_version(agent, user_id, changelog)
    
    async def revert_to_version(self, agent_id: str, version_id: str, user_id: str) -> bool:
        """Revert agent to a specific version"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise NotFoundError(f"Agent {agent_id} not found")
            
            version = self.db.query(AgentVersion).filter(
                AgentVersion.id == version_id,
                AgentVersion.agent_id == agent_id
            ).first()
            
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            # Create backup of current state
            await self._create_config_version(agent, user_id, f"Backup before reverting to version {version.version}")
            
            # Revert to version
            agent.configuration = version.configuration
            agent.system_prompt = version.system_prompt
            agent.tools = version.tools
            agent.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def get_version_history(self, agent_id: str) -> List[Dict]:
        """Get version history for an agent"""
        versions = self.db.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id
        ).order_by(AgentVersion.created_at.desc()).all()
        
        return [
            {
                "id": str(version.id),
                "version": version.version,
                "changelog": version.changelog,
                "is_active": version.is_active,
                "created_at": version.created_at.isoformat() if version.created_at else None,
                "created_by": str(version.created_by) if version.created_by else None
            }
            for version in versions
        ]
    
    async def validate_configuration_update(self, agent_id: str, config_updates: Dict) -> Dict:
        """Validate configuration updates"""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")
        
        errors = []
        warnings = []
        
        # Validate system prompt
        if "system_prompt" in config_updates:
            if not config_updates["system_prompt"]:
                errors.append("System prompt cannot be empty")
            elif len(config_updates["system_prompt"]) > 10000:
                warnings.append("System prompt is very long, may impact performance")
        
        # Validate capabilities
        if "capabilities" in config_updates:
            capabilities = config_updates["capabilities"]
            if not isinstance(capabilities, list):
                errors.append("Capabilities must be a list")
            elif len(capabilities) > 20:
                warnings.append("Too many capabilities may impact performance")
        
        # Validate tools
        if "tools" in config_updates:
            tools = config_updates["tools"]
            if not isinstance(tools, list):
                errors.append("Tools must be a list")
            else:
                for tool in tools:
                    if not tool.get("name"):
                        errors.append("Tool name is required")
                    if not tool.get("description"):
                        warnings.append(f"Tool '{tool.get('name', 'unnamed')}' has no description")
        
        # Validate model updates
        if "llm_model" in config_updates:
            supported_models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "gemini-pro"]
            if config_updates["llm_model"] not in supported_models:
                warnings.append(f"Model {config_updates['llm_model']} may not be supported")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def export_agent_config(self, agent_id: str, format: str = "yaml") -> str:
        """Export agent configuration"""
        config = await self.get_agent_config(agent_id)
        
        if format.lower() == "yaml":
            import yaml
            return yaml.dump(config, default_flow_style=False)
        elif format.lower() == "json":
            return json.dumps(config, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def import_agent_config(self, agent_id: str, config_data: str, format: str = "yaml", user_id: str = None) -> bool:
        """Import agent configuration"""
        try:
            if format.lower() == "yaml":
                import yaml
                config = yaml.safe_load(config_data)
            elif format.lower() == "json":
                config = json.loads(config_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Validate imported configuration
            validation_result = await self.validate_configuration_update(agent_id, config)
            if not validation_result["is_valid"]:
                raise ValidationError(f"Invalid configuration: {validation_result['errors']}")
            
            # Apply configuration
            return await self.update_agent_config(agent_id, config, user_id)
            
        except Exception as e:
            raise e
    
    async def _create_config_version(self, agent: Agent, user_id: str, changelog: str) -> str:
        """Create a new configuration version"""
        # Get current version number
        latest_version = self.db.query(AgentVersion).filter(
            AgentVersion.agent_id == agent.id
        ).order_by(AgentVersion.created_at.desc()).first()
        
        if latest_version:
            version_parts = latest_version.version.split(".")
            version_num = f"{version_parts[0]}.{version_parts[1]}.{int(version_parts[2]) + 1}"
        else:
            version_num = "1.0.0"
        
        # Create version record
        version = AgentVersion(
            id=uuid.uuid4(),
            agent_id=agent.id,
            version=version_num,
            configuration=agent.configuration,
            system_prompt=agent.system_prompt,
            tools=agent.tools,
            changelog=changelog,
            is_active=False,
            created_by=user_id
        )
        
        self.db.add(version)
        self.db.commit()
        
        return str(version.id)
    
    async def get_configuration_diff(self, agent_id: str, version1_id: str, version2_id: str) -> Dict:
        """Get differences between two configuration versions"""
        version1 = self.db.query(AgentVersion).filter(AgentVersion.id == version1_id).first()
        version2 = self.db.query(AgentVersion).filter(AgentVersion.id == version2_id).first()
        
        if not version1 or not version2:
            raise NotFoundError("One or both versions not found")
        
        def deep_diff(dict1, dict2, path=""):
            """Compare two dictionaries recursively"""
            changes = []
            
            all_keys = set(dict1.keys()) | set(dict2.keys())
            
            for key in all_keys:
                current_path = f"{path}.{key}" if path else key
                
                if key not in dict1:
                    changes.append({"type": "added", "path": current_path, "value": dict2[key]})
                elif key not in dict2:
                    changes.append({"type": "removed", "path": current_path, "value": dict1[key]})
                elif dict1[key] != dict2[key]:
                    if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                        changes.extend(deep_diff(dict1[key], dict2[key], current_path))
                    else:
                        changes.append({
                            "type": "modified",
                            "path": current_path,
                            "old_value": dict1[key],
                            "new_value": dict2[key]
                        })
            
            return changes
        
        return {
            "version1": {
                "id": str(version1.id),
                "version": version1.version,
                "created_at": version1.created_at.isoformat()
            },
            "version2": {
                "id": str(version2.id),
                "version": version2.version,
                "created_at": version2.created_at.isoformat()
            },
            "changes": deep_diff(version1.configuration, version2.configuration)
        }
