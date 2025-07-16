"""
Integration Service
Provides integration between different services and external systems
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
import json
import aiohttp
from urllib.parse import urljoin

from app.services.agent_creation import AgentCreationService
from app.services.workflow_service import WorkflowService
from app.services.tool_service import ToolService
from app.services.observability_service import ObservabilityService
from app.services.master_data_service import MasterDataService
from app.services.template_service import TemplateService
from app.services.system_service import SystemService

logger = logging.getLogger(__name__)

class IntegrationService:
    """Service for integrating different components and external systems"""
    
    def __init__(self):
        self.agent_creation_service = None  # Will be initialized with db session
        self.workflow_service = WorkflowService()
        self.tool_service = ToolService()
        self.observability_service = ObservabilityService()
        self.master_data_service = MasterDataService()
        self.template_service = TemplateService()
        self.system_service = SystemService()
    
    async def create_agent_from_template(self, 
                                       template_id: str,
                                       agent_data: Dict[str, Any],
                                       user_id: str,
                                       db: AsyncSession) -> Dict[str, Any]:
        """Create an agent from a template"""
        try:
            # Get template
            template = await self.template_service.get_template(template_id, user_id, db)
            if not template:
                raise ValueError("Template not found")
            
            # Instantiate template with agent data
            instantiated_template = await self.template_service.instantiate_template(
                template_id, agent_data, user_id, db
            )
            
            # Create agent using instantiated template
            agent_config = json.loads(instantiated_template.get("content", "{}"))
            
            # Merge with additional agent data
            agent_config.update(agent_data)
            
            # Create agent using creation service
            if not self.agent_creation_service:
                self.agent_creation_service = AgentCreationService(db)
            
            from app.services.agent_creation import AgentSpec, ResourceRequirements
            agent_spec = AgentSpec(
                name=agent_config.get('name', 'Template Agent'),
                description=agent_config.get('description', ''),
                category=agent_config.get('category', 'General'),
                configuration=agent_config,
                instructions=agent_config.get('prompt', ''),
                model=agent_config.get('llm_model', 'gpt-4'),
                resource_requirements=ResourceRequirements(),
                metadata=agent_config
            )
            
            agent = await self.agent_creation_service.create_agent_from_spec(agent_spec, user_id)
            
            # Log integration event
            await self.observability_service.log_event(
                "agent_created_from_template",
                "integration",
                {
                    "template_id": template_id,
                    "agent_id": agent.get("id"),
                    "user_id": user_id
                }
            )
            
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent from template: {e}")
            raise
    
    async def deploy_agent_workflow(self, 
                                  agent_id: str,
                                  workflow_config: Dict[str, Any],
                                  user_id: str,
                                  db: AsyncSession) -> Dict[str, Any]:
        """Deploy an agent with a workflow"""
        try:
            # Get agent
            # TODO: Replace with proper agent retrieval
            # agent = await self.agent_service.get_agent(agent_id, user_id, db)
            agent = None  # Temporarily disabled
            if not agent:
                raise ValueError("Agent not found")
            
            # Create workflow
            workflow_config["agent_id"] = agent_id
            workflow = await self.workflow_service.create_workflow(workflow_config, user_id, db)
            
            # Deploy agent
            # TODO: Replace with proper agent deployment
            # deployment = await self.agent_service.deploy_agent(agent_id, {}, user_id, db)
            deployment = {"status": "success", "message": "Deployment disabled temporarily"}
            
            # Start workflow
            execution = await self.workflow_service.execute_workflow(
                workflow.get("id"), {}, user_id, db
            )
            
            # Log integration event
            await self.observability_service.log_event(
                "agent_workflow_deployed",
                "integration",
                {
                    "agent_id": agent_id,
                    "workflow_id": workflow.get("id"),
                    "execution_id": execution.get("id"),
                    "user_id": user_id
                }
            )
            
            return {
                "agent": agent,
                "workflow": workflow,
                "deployment": deployment,
                "execution": execution
            }
            
        except Exception as e:
            logger.error(f"Error deploying agent workflow: {e}")
            raise
    
    async def integrate_external_tool(self, 
                                    tool_config: Dict[str, Any],
                                    user_id: str,
                                    db: AsyncSession) -> Dict[str, Any]:
        """Integrate an external tool"""
        try:
            # Validate tool configuration
            validation = await self.tool_service.validate_tool_config(tool_config)
            if not validation.get("valid"):
                raise ValueError("Invalid tool configuration")
            
            # Create tool
            tool = await self.tool_service.create_tool(tool_config, user_id, db)
            
            # Test tool integration
            test_result = await self.tool_service.test_tool(tool.get("id"), {}, user_id, db)
            
            # Deploy tool if test passes
            if test_result.get("test_passed"):
                deployment = await self.tool_service.deploy_tool(tool.get("id"), {}, user_id, db)
            else:
                deployment = {"status": "test_failed", "message": "Tool test failed"}
            
            # Log integration event
            await self.observability_service.log_event(
                "external_tool_integrated",
                "integration",
                {
                    "tool_id": tool.get("id"),
                    "tool_type": tool_config.get("tool_type"),
                    "test_passed": test_result.get("test_passed"),
                    "user_id": user_id
                }
            )
            
            return {
                "tool": tool,
                "test_result": test_result,
                "deployment": deployment
            }
            
        except Exception as e:
            logger.error(f"Error integrating external tool: {e}")
            raise
    
    async def sync_master_data(self, 
                             source: str,
                             sync_config: Dict[str, Any],
                             user_id: str,
                             db: AsyncSession) -> Dict[str, Any]:
        """Sync master data from external source"""
        try:
            sync_results = {
                "skills": [],
                "constraints": [],
                "prompts": [],
                "models": [],
                "secrets": []
            }
            
            # Sync skills
            if sync_config.get("sync_skills"):
                skills = await self._sync_skills_from_source(source, sync_config)
                for skill in skills:
                    created_skill = await self.master_data_service.create_skill(skill, user_id, db)
                    sync_results["skills"].append(created_skill)
            
            # Sync constraints
            if sync_config.get("sync_constraints"):
                constraints = await self._sync_constraints_from_source(source, sync_config)
                for constraint in constraints:
                    created_constraint = await self.master_data_service.create_constraint(
                        constraint, user_id, db
                    )
                    sync_results["constraints"].append(created_constraint)
            
            # Sync prompts
            if sync_config.get("sync_prompts"):
                prompts = await self._sync_prompts_from_source(source, sync_config)
                for prompt in prompts:
                    created_prompt = await self.master_data_service.create_prompt(prompt, user_id, db)
                    sync_results["prompts"].append(created_prompt)
            
            # Sync models
            if sync_config.get("sync_models"):
                models = await self._sync_models_from_source(source, sync_config)
                for model in models:
                    created_model = await self.master_data_service.create_model(model, user_id, db)
                    sync_results["models"].append(created_model)
            
            # Log sync event
            await self.observability_service.log_event(
                "master_data_sync",
                "integration",
                {
                    "source": source,
                    "synced_counts": {k: len(v) for k, v in sync_results.items()},
                    "user_id": user_id
                }
            )
            
            return {
                "source": source,
                "sync_results": sync_results,
                "total_synced": sum(len(v) for v in sync_results.values()),
                "synced_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing master data: {e}")
            raise
    
    async def _sync_skills_from_source(self, source: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sync skills from external source"""
        # This is a placeholder - implement actual sync logic based on source
        return [
            {
                "name": "web_search",
                "description": "Web search capability",
                "category": "search",
                "skill_type": "api"
            },
            {
                "name": "data_analysis", 
                "description": "Data analysis capability",
                "category": "analysis",
                "skill_type": "function"
            }
        ]
    
    async def _sync_constraints_from_source(self, source: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sync constraints from external source"""
        # This is a placeholder - implement actual sync logic based on source
        return [
            {
                "name": "rate_limit",
                "description": "Rate limiting constraint",
                "constraint_type": "rate_limit",
                "value": "100/hour"
            },
            {
                "name": "memory_limit",
                "description": "Memory usage limit",
                "constraint_type": "resource",
                "value": "1GB"
            }
        ]
    
    async def _sync_prompts_from_source(self, source: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sync prompts from external source"""
        # This is a placeholder - implement actual sync logic based on source
        return [
            {
                "name": "assistant_prompt",
                "description": "General assistant prompt",
                "prompt_type": "system",
                "content": "You are a helpful AI assistant."
            },
            {
                "name": "analysis_prompt",
                "description": "Data analysis prompt",
                "prompt_type": "user",
                "content": "Please analyze the following data:"
            }
        ]
    
    async def _sync_models_from_source(self, source: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sync models from external source"""
        # This is a placeholder - implement actual sync logic based on source
        return [
            {
                "name": "gpt-4",
                "description": "OpenAI GPT-4 model",
                "model_type": "llm",
                "provider": "openai",
                "version": "gpt-4"
            },
            {
                "name": "claude-3",
                "description": "Anthropic Claude 3 model",
                "model_type": "llm",
                "provider": "anthropic",
                "version": "claude-3-sonnet"
            }
        ]
    
    async def export_system_data(self, 
                               export_config: Dict[str, Any],
                               user_id: str,
                               db: AsyncSession) -> Dict[str, Any]:
        """Export system data"""
        try:
            export_data = {}
            
            # Export agents
            if export_config.get("include_agents"):
                agents = await self.agent_service.list_agents(user_id, db)
                export_data["agents"] = agents
            
            # Export workflows
            if export_config.get("include_workflows"):
                workflows = await self.workflow_service.list_workflows(user_id, db)
                export_data["workflows"] = workflows
            
            # Export tools
            if export_config.get("include_tools"):
                tools = await self.tool_service.list_tools(user_id, db)
                export_data["tools"] = tools
            
            # Export templates
            if export_config.get("include_templates"):
                templates = await self.template_service.list_templates(user_id, db)
                export_data["templates"] = templates
            
            # Export master data
            if export_config.get("include_master_data"):
                master_data = {}
                master_data["skills"] = await self.master_data_service.list_skills(user_id, db)
                master_data["constraints"] = await self.master_data_service.list_constraints(user_id, db)
                master_data["prompts"] = await self.master_data_service.list_prompts(user_id, db)
                master_data["models"] = await self.master_data_service.list_models(user_id, db)
                export_data["master_data"] = master_data
            
            # Add metadata
            export_data["metadata"] = {
                "exported_at": datetime.utcnow().isoformat(),
                "exported_by": user_id,
                "export_config": export_config,
                "version": "1.0.0"
            }
            
            # Log export event
            await self.observability_service.log_event(
                "system_data_export",
                "integration",
                {
                    "user_id": user_id,
                    "export_config": export_config,
                    "total_items": sum(len(v) for v in export_data.values() if isinstance(v, list))
                }
            )
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting system data: {e}")
            raise
    
    async def import_system_data(self, 
                               import_data: Dict[str, Any],
                               import_config: Dict[str, Any],
                               user_id: str,
                               db: AsyncSession) -> Dict[str, Any]:
        """Import system data"""
        try:
            import_results = {
                "agents": [],
                "workflows": [],
                "tools": [],
                "templates": [],
                "master_data": {
                    "skills": [],
                    "constraints": [],
                    "prompts": [],
                    "models": []
                }
            }
            
            # Import agents
            if import_config.get("import_agents") and "agents" in import_data:
                for agent_data in import_data["agents"]:
                    try:
                        agent = await self.agent_service.create_agent(agent_data, user_id, db)
                        import_results["agents"].append(agent)
                    except Exception as e:
                        logger.error(f"Error importing agent: {e}")
            
            # Import workflows
            if import_config.get("import_workflows") and "workflows" in import_data:
                for workflow_data in import_data["workflows"]:
                    try:
                        workflow = await self.workflow_service.create_workflow(workflow_data, user_id, db)
                        import_results["workflows"].append(workflow)
                    except Exception as e:
                        logger.error(f"Error importing workflow: {e}")
            
            # Import tools
            if import_config.get("import_tools") and "tools" in import_data:
                for tool_data in import_data["tools"]:
                    try:
                        tool = await self.tool_service.create_tool(tool_data, user_id, db)
                        import_results["tools"].append(tool)
                    except Exception as e:
                        logger.error(f"Error importing tool: {e}")
            
            # Import templates
            if import_config.get("import_templates") and "templates" in import_data:
                for template_data in import_data["templates"]:
                    try:
                        template = await self.template_service.create_template(template_data, user_id, db)
                        import_results["templates"].append(template)
                    except Exception as e:
                        logger.error(f"Error importing template: {e}")
            
            # Import master data
            if import_config.get("import_master_data") and "master_data" in import_data:
                master_data = import_data["master_data"]
                
                # Import skills
                for skill_data in master_data.get("skills", []):
                    try:
                        skill = await self.master_data_service.create_skill(skill_data, user_id, db)
                        import_results["master_data"]["skills"].append(skill)
                    except Exception as e:
                        logger.error(f"Error importing skill: {e}")
                
                # Import constraints
                for constraint_data in master_data.get("constraints", []):
                    try:
                        constraint = await self.master_data_service.create_constraint(
                            constraint_data, user_id, db
                        )
                        import_results["master_data"]["constraints"].append(constraint)
                    except Exception as e:
                        logger.error(f"Error importing constraint: {e}")
                
                # Import prompts
                for prompt_data in master_data.get("prompts", []):
                    try:
                        prompt = await self.master_data_service.create_prompt(prompt_data, user_id, db)
                        import_results["master_data"]["prompts"].append(prompt)
                    except Exception as e:
                        logger.error(f"Error importing prompt: {e}")
                
                # Import models
                for model_data in master_data.get("models", []):
                    try:
                        model = await self.master_data_service.create_model(model_data, user_id, db)
                        import_results["master_data"]["models"].append(model)
                    except Exception as e:
                        logger.error(f"Error importing model: {e}")
            
            # Log import event
            await self.observability_service.log_event(
                "system_data_import",
                "integration",
                {
                    "user_id": user_id,
                    "import_config": import_config,
                    "import_results": {k: len(v) if isinstance(v, list) else 
                                     sum(len(vv) for vv in v.values()) if isinstance(v, dict) else 0 
                                     for k, v in import_results.items()}
                }
            )
            
            return {
                "import_results": import_results,
                "imported_at": datetime.utcnow().isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error importing system data: {e}")
            raise
    
    async def get_integration_status(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Get integration status"""
        try:
            # Get service statistics
            agent_stats = await self.agent_service.get_agent_stats(user_id, db)
            workflow_stats = await self.workflow_service.get_workflow_stats(user_id, db)
            tool_stats = await self.tool_service.get_tool_stats(user_id, db)
            
            # Get system status
            system_status = await self.system_service.get_system_status(db)
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "agents": agent_stats,
                    "workflows": workflow_stats,
                    "tools": tool_stats,
                    "system": system_status
                },
                "integrations": {
                    "external_tools": 0,
                    "data_sources": 0,
                    "webhooks": 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting integration status: {e}")
            return {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
