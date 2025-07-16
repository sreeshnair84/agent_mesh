"""
Agent Service - Core business logic for agent management
Delegates to specialized services for specific operations
"""

import asyncio
import httpx
import os
import socket
import subprocess
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime
import uuid

from app.models.agent import Agent
from app.models.master_data import Skill, Constraint, Tool
from app.schemas.agent import AgentCreate, AgentUpdate, AgentInvoke, AgentInvokeResponse
from app.core.config import settings
from app.services.llm_service import LLMService
from app.services.search_service import SearchService
from app.services.agent_creation import AgentCreationService
from app.services.agent_deployment import AgentDeploymentManager
from app.services.agent_configuration import AgentConfigurationManager


class AgentService:
    """Service for managing agents - delegates to specialized services"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.search_service = SearchService()
        # Initialize specialized services
        self.creation_service = None  # Will be initialized with db session
        self.deployment_manager = None  # Will be initialized with db session
        self.config_manager = None  # Will be initialized with db session
        
    def _init_services(self, db: AsyncSession):
        """Initialize services that need database session"""
        if not self.creation_service:
            self.creation_service = AgentCreationService(db)
        if not self.deployment_manager:
            self.deployment_manager = AgentDeploymentManager(db)
        if not self.config_manager:
            self.config_manager = AgentConfigurationManager(db)
    
    async def create_agent(
        self,
        agent_data: AgentCreate,
        owner_id: str,
        db: AsyncSession
    ) -> Agent:
        """Create a new agent using specialized creation service"""
        self._init_services(db)
        
        # Convert to AgentSpec format expected by creation service
        from app.services.agent_creation import AgentSpec, ResourceRequirements
        
        agent_spec = AgentSpec(
            name=agent_data.name,
            description=agent_data.description,
            category=getattr(agent_data, 'category', 'General'),
            configuration=getattr(agent_data, 'config', {}),
            instructions=getattr(agent_data, 'prompt', ''),
            model=getattr(agent_data, 'llm_model', 'gpt-4'),
            resource_requirements=ResourceRequirements(),
            metadata={
                'type': getattr(agent_data, 'type', 'assistant'),
                'template': getattr(agent_data, 'template', 'basic'),
                'embedding_model': getattr(agent_data, 'embedding_model', 'text-embedding-ada-002'),
                'dns': getattr(agent_data, 'dns', ''),
                'health_url': getattr(agent_data, 'health_url', ''),
                'tags': getattr(agent_data, 'tags', []),
                'is_public': getattr(agent_data, 'is_public', False),
            }
        )
        
        return await self.creation_service.create_agent_from_spec(agent_spec, owner_id)
    
    async def update_agent(
        self,
        agent_id: str,
        agent_data: AgentUpdate,
        user_id: str,
        db: AsyncSession
    ) -> Agent:
        """Update an existing agent"""
        agent = await db.scalar(
            select(Agent)
            .options(
                selectinload(Agent.skills),
                selectinload(Agent.constraints),
                selectinload(Agent.tools)
            )
            .where(Agent.id == agent_id)
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if str(agent.owner_id) != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this agent")
        
        # Update fields
        update_data = agent_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field.endswith('_ids'):
                continue  # Handle relationships separately
            setattr(agent, field, value)
        
        # Update relationships
        if agent_data.skill_ids is not None:
            agent.skills.clear()
            if agent_data.skill_ids:
                skills = await db.scalars(
                    select(Skill).where(Skill.id.in_(agent_data.skill_ids))
                )
                agent.skills.extend(skills.all())
        
        if agent_data.constraint_ids is not None:
            agent.constraints.clear()
            if agent_data.constraint_ids:
                constraints = await db.scalars(
                    select(Constraint).where(Constraint.id.in_(agent_data.constraint_ids))
                )
                agent.constraints.extend(constraints.all())
        
        if agent_data.tool_ids is not None:
            agent.tools.clear()
            if agent_data.tool_ids:
                tools = await db.scalars(
                    select(Tool).where(Tool.id.in_(agent_data.tool_ids))
                )
                agent.tools.extend(tools.all())
        
        # Update search vector if description changed
        if agent_data.description:
            search_vector = await self.search_service.generate_embedding(
                f"{agent.name} {agent.description}"
            )
            agent.search_vector = search_vector
        
        await db.commit()
        await db.refresh(agent)
        
        return agent
    
    async def delete_agent(
        self,
        agent_id: str,
        user_id: str,
        db: AsyncSession
    ) -> None:
        """Delete an agent"""
        agent = await db.scalar(
            select(Agent).where(Agent.id == agent_id)
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if str(agent.owner_id) != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this agent")
        
        # Stop agent if it's running
        if agent.status == 'active':
            await self._stop_agent(agent)
        
        await db.delete(agent)
        await db.commit()
    
    async def deploy_agent(
        self,
        agent_id: str,
        user_id: str,
        db: AsyncSession,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Deploy an agent"""
        agent = await db.scalar(
            select(Agent).where(Agent.id == agent_id)
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if str(agent.owner_id) != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to deploy this agent")
        
        # Set status to deploying
        agent.status = 'deploying'
        await db.commit()
        
        # Schedule background deployment
        background_tasks.add_task(self._deploy_agent_background, agent_id, db)
        
        return {
            "message": "Agent deployment started",
            "agent_id": agent_id,
            "status": "deploying"
        }
    
    async def _deploy_agent_background(self, agent_id: str, db: AsyncSession):
        """Background task for agent deployment"""
        try:
            agent = await db.scalar(select(Agent).where(Agent.id == agent_id))
            
            if agent.type == 'lowcode':
                port = await self._get_available_port()
                
                # Generate agent code from template
                agent_code = await self._generate_agent_code(agent)
                
                # Deploy using script
                await self._deploy_agent_script(agent, agent_code, port)
                
                # Update agent with deployment info
                agent.port = port
                agent.dns = f"http://localhost:{port}"
                agent.health_url = f"http://localhost:{port}/health"
                agent.status = 'active'
                
            elif agent.type == 'custom':
                # For custom agents, just validate the provided DNS
                if agent.dns and agent.health_url:
                    health_check = await self._check_health(agent.health_url)
                    if health_check:
                        agent.status = 'active'
                        agent.health_status = 'healthy'
                    else:
                        agent.status = 'error'
                        agent.health_status = 'unhealthy'
                else:
                    raise Exception("Custom agent requires DNS and health URL")
            
            await db.commit()
            
        except Exception as e:
            # Update agent status to error
            agent.status = 'error'
            await db.commit()
            print(f"Agent deployment failed: {e}")
    
    async def invoke_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        trace_id: str,
        user_id: str,
        db: AsyncSession
    ) -> AgentInvokeResponse:
        """Invoke an agent"""
        agent = await db.scalar(
            select(Agent)
            .options(selectinload(Agent.tools))
            .where(Agent.id == agent_id)
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent.status != 'active':
            raise HTTPException(status_code=400, detail="Agent is not active")
        
        # Invoke agent based on type
        if agent.type == 'lowcode':
            result = await self._invoke_lowcode_agent(agent, input_data, trace_id)
        else:
            result = await self._invoke_custom_agent(agent, input_data, trace_id)
        
        return AgentInvokeResponse(**result)
    
    async def _invoke_lowcode_agent(
        self, 
        agent: Agent, 
        input_data: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        """Invoke low-code agent using LangChain"""
        # Simplified implementation - would use LangChain in production
        start_time = asyncio.get_event_loop().time()
        
        # Simulate processing
        await asyncio.sleep(0.1)
        
        # Mock response
        result = {
            "response": f"Agent {agent.name} processed your request: {input_data.get('message', 'No message')}"
        }
        
        end_time = asyncio.get_event_loop().time()
        execution_time_ms = int((end_time - start_time) * 1000)
        
        return {
            "output": result,
            "trace_id": trace_id,
            "execution_time_ms": execution_time_ms,
            "llm_usage": {
                "model": agent.llm_model or "gpt-3.5-turbo",
                "tokens": 50,
                "cost": 0.001
            }
        }
    
    async def _invoke_custom_agent(
        self, 
        agent: Agent, 
        input_data: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        """Invoke custom agent via HTTP"""
        if not agent.dns:
            raise HTTPException(status_code=400, detail="Agent DNS not configured")
        
        headers = {}
        if agent.auth_token:
            headers["Authorization"] = f"Bearer {agent.auth_token}"
        
        headers["X-Trace-ID"] = trace_id
        
        async with httpx.AsyncClient() as client:
            start_time = asyncio.get_event_loop().time()
            
            try:
                response = await client.post(
                    f"{agent.dns}/invoke",
                    json=input_data,
                    headers=headers,
                    timeout=30.0
                )
                
                end_time = asyncio.get_event_loop().time()
                execution_time_ms = int((end_time - start_time) * 1000)
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Agent invocation failed: {response.text}"
                    )
                
                result = response.json()
                
                return {
                    "output": result,
                    "trace_id": trace_id,
                    "execution_time_ms": execution_time_ms
                }
                
            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=408,
                    detail="Agent invocation timed out"
                )
    
    async def check_agent_health(
        self,
        agent_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Check agent health"""
        agent = await db.scalar(select(Agent).where(Agent.id == agent_id))
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if not agent.health_url:
            return {
                "agent_id": agent_id,
                "status": "unknown",
                "message": "No health URL configured"
            }
        
        health_status = await self._check_health(agent.health_url)
        
        # Update agent health status
        agent.health_status = 'healthy' if health_status else 'unhealthy'
        agent.last_health_check = datetime.utcnow()
        await db.commit()
        
        return {
            "agent_id": agent_id,
            "status": agent.health_status,
            "last_check": agent.last_health_check,
            "url": agent.health_url
        }
    
    async def _check_health(self, health_url: str) -> bool:
        """Check if agent is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(health_url, timeout=5.0)
                return response.status_code == 200
        except:
            return False
    
    async def _get_available_port(self) -> int:
        """Find available port for agent deployment"""
        for port in range(settings.AGENT_BASE_PORT, settings.AGENT_BASE_PORT + settings.MAX_AGENT_PORTS):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('localhost', port))
                sock.close()
                return port
            except OSError:
                continue
        
        raise Exception("No available ports for agent deployment")
    
    async def _generate_agent_code(self, agent: Agent) -> str:
        """Generate agent code from template"""
        # Load template based on agent.template
        template_path = f"agent-templates/{agent.template}/template.py"
        
        if not os.path.exists(template_path):
            raise Exception(f"Template {agent.template} not found")
        
        with open(template_path, 'r') as f:
            template_code = f.read()
        
        # Replace placeholders with agent configuration
        agent_code = template_code.replace(
            "{{AGENT_NAME}}", agent.name
        ).replace(
            "{{AGENT_PROMPT}}", agent.prompt or ""
        ).replace(
            "{{LLM_MODEL}}", agent.llm_model or "gpt-3.5-turbo"
        )
        
        return agent_code
    
    async def _deploy_agent_script(self, agent: Agent, agent_code: str, port: int):
        """Deploy agent using deployment script"""
        # Write agent code to file
        agent_dir = f"/tmp/agents/{agent.id}"
        os.makedirs(agent_dir, exist_ok=True)
        
        with open(f"{agent_dir}/agent.py", 'w') as f:
            f.write(agent_code)
        
        # Run deployment script
        script_path = "./scripts/deploy-agent.sh"
        if os.name == 'nt':  # Windows
            script_path = ".\\scripts\\deploy-agent.ps1"
        
        result = subprocess.run([
            script_path,
            str(agent.id),
            str(port),
            agent_dir
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Agent deployment failed: {result.stderr}")
    
    async def _stop_agent(self, agent: Agent):
        """Stop a running agent"""
        if agent.port:
            # Kill process on port
            if os.name == 'nt':  # Windows
                subprocess.run(f"netstat -ano | findstr :{agent.port}", shell=True)
            else:  # Unix
                subprocess.run(f"lsof -ti:{agent.port} | xargs kill -9", shell=True)
        
        agent.status = 'inactive'
        agent.health_status = 'unknown'
