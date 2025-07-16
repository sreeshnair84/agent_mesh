"""
Agent Deployment System
Handles deployment, scaling, and rollback of agents
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid
import asyncio
import json

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.agent import Agent, AgentStatus
from app.core.exceptions import ValidationError, NotFoundError


@dataclass
class DeploymentResult:
    """Result of agent deployment"""
    success: bool
    deployment_id: str
    message: str
    details: Optional[Dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class DeploymentStatus:
    """Status of agent deployment"""
    deployment_id: str
    agent_id: str
    status: str  # "pending", "deploying", "active", "failed", "stopped"
    replicas: int
    ready_replicas: int
    message: str
    started_at: datetime
    last_updated: datetime
    health_check_url: Optional[str] = None
    endpoints: List[str] = None


class AgentDeploymentManager:
    """Service for managing agent deployments"""
    
    def __init__(self, db: Session):
        self.db = db
        self.deployments = {}  # In-memory deployment tracking
        self.container_orchestrator = ContainerOrchestrator()
    
    async def deploy_agent(self, agent_id: str, environment: str = "production") -> DeploymentResult:
        """Deploy an agent to specified environment"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise NotFoundError(f"Agent {agent_id} not found")
            
            # Generate deployment ID
            deployment_id = str(uuid.uuid4())
            
            # Validate deployment configuration
            validation_result = self._validate_deployment_config(agent)
            if not validation_result["is_valid"]:
                return DeploymentResult(
                    success=False,
                    deployment_id=deployment_id,
                    message=f"Validation failed: {validation_result['errors']}"
                )
            
            # Update agent status
            agent.status = AgentStatus.DEPLOYING
            agent.deployed_at = datetime.utcnow()
            self.db.commit()
            
            # Start deployment
            deployment_config = self._build_deployment_config(agent, environment)
            
            # Track deployment
            self.deployments[deployment_id] = DeploymentStatus(
                deployment_id=deployment_id,
                agent_id=agent_id,
                status="deploying",
                replicas=deployment_config.get("replicas", 1),
                ready_replicas=0,
                message="Deployment in progress",
                started_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            
            # Deploy to container orchestrator
            deployment_result = await self.container_orchestrator.deploy(
                agent_id=agent_id,
                config=deployment_config
            )
            
            if deployment_result.success:
                # Update agent status
                agent.status = AgentStatus.ACTIVE
                agent.dns = deployment_result.details.get("dns")
                agent.port = deployment_result.details.get("port")
                agent.health_check_url = deployment_result.details.get("health_check_url")
                
                # Update deployment tracking
                self.deployments[deployment_id].status = "active"
                self.deployments[deployment_id].ready_replicas = deployment_config.get("replicas", 1)
                self.deployments[deployment_id].message = "Deployment successful"
                self.deployments[deployment_id].health_check_url = agent.health_check_url
                self.deployments[deployment_id].endpoints = deployment_result.details.get("endpoints", [])
                
                self.db.commit()
                
                return DeploymentResult(
                    success=True,
                    deployment_id=deployment_id,
                    message="Agent deployed successfully",
                    details=deployment_result.details,
                    started_at=self.deployments[deployment_id].started_at,
                    completed_at=datetime.utcnow()
                )
            else:
                # Update agent status on failure
                agent.status = AgentStatus.ERROR
                agent.last_error = deployment_result.message
                agent.last_error_at = datetime.utcnow()
                
                # Update deployment tracking
                self.deployments[deployment_id].status = "failed"
                self.deployments[deployment_id].message = deployment_result.message
                
                self.db.commit()
                
                return DeploymentResult(
                    success=False,
                    deployment_id=deployment_id,
                    message=deployment_result.message,
                    started_at=self.deployments[deployment_id].started_at,
                    completed_at=datetime.utcnow()
                )
            
        except Exception as e:
            self.db.rollback()
            return DeploymentResult(
                success=False,
                deployment_id=deployment_id,
                message=str(e)
            )
    
    async def scale_agent(self, agent_id: str, replicas: int) -> bool:
        """Scale agent to specified number of replicas"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise NotFoundError(f"Agent {agent_id} not found")
            
            if agent.status != AgentStatus.ACTIVE:
                raise ValidationError("Agent must be active to scale")
            
            # Update deployment configuration
            deployment_config = agent.deployment_config or {}
            deployment_config["replicas"] = replicas
            agent.deployment_config = deployment_config
            
            # Scale via container orchestrator
            scale_result = await self.container_orchestrator.scale(
                agent_id=agent_id,
                replicas=replicas
            )
            
            if scale_result.success:
                # Update deployment tracking
                for deployment in self.deployments.values():
                    if deployment.agent_id == agent_id and deployment.status == "active":
                        deployment.replicas = replicas
                        deployment.last_updated = datetime.utcnow()
                
                self.db.commit()
                return True
            else:
                return False
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def rollback_agent(self, agent_id: str, version: str) -> bool:
        """Rollback agent to specified version"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise NotFoundError(f"Agent {agent_id} not found")
            
            # Get version configuration
            from app.models.agent import AgentVersion
            agent_version = self.db.query(AgentVersion).filter(
                AgentVersion.agent_id == agent_id,
                AgentVersion.version == version
            ).first()
            
            if not agent_version:
                raise NotFoundError(f"Version {version} not found for agent {agent_id}")
            
            # Update agent configuration
            agent.configuration = agent_version.configuration
            agent.system_prompt = agent_version.system_prompt
            agent.tools = agent_version.tools
            agent.version = version
            agent.updated_at = datetime.utcnow()
            
            # Redeploy with new configuration
            if agent.status == AgentStatus.ACTIVE:
                deployment_result = await self.deploy_agent(agent_id)
                if not deployment_result.success:
                    self.db.rollback()
                    return False
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def get_deployment_status(self, agent_id: str) -> Optional[DeploymentStatus]:
        """Get deployment status for an agent"""
        for deployment in self.deployments.values():
            if deployment.agent_id == agent_id:
                return deployment
        return None
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop a running agent"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise NotFoundError(f"Agent {agent_id} not found")
            
            # Stop via container orchestrator
            stop_result = await self.container_orchestrator.stop(agent_id)
            
            if stop_result.success:
                # Update agent status
                agent.status = AgentStatus.STOPPED
                
                # Update deployment tracking
                for deployment in self.deployments.values():
                    if deployment.agent_id == agent_id:
                        deployment.status = "stopped"
                        deployment.ready_replicas = 0
                        deployment.last_updated = datetime.utcnow()
                
                self.db.commit()
                return True
            else:
                return False
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def restart_agent(self, agent_id: str) -> bool:
        """Restart a stopped agent"""
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise NotFoundError(f"Agent {agent_id} not found")
            
            if agent.status not in [AgentStatus.STOPPED, AgentStatus.ERROR]:
                raise ValidationError("Agent must be stopped or in error state to restart")
            
            # Restart via deployment
            deployment_result = await self.deploy_agent(agent_id)
            return deployment_result.success
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def _validate_deployment_config(self, agent: Agent) -> Dict:
        """Validate deployment configuration"""
        errors = []
        warnings = []
        
        # Check required fields
        if not agent.name:
            errors.append("Agent name is required")
        
        if not agent.llm_model:
            errors.append("LLM model is required")
        
        if not agent.system_prompt:
            warnings.append("No system prompt configured")
        
        # Check deployment configuration
        deployment_config = agent.deployment_config or {}
        replicas = deployment_config.get("replicas", 1)
        
        if replicas < 1:
            errors.append("Replicas must be at least 1")
        elif replicas > 10:
            warnings.append("High replica count may impact performance")
        
        # Check resource requirements
        resources = deployment_config.get("resources", {})
        if not resources:
            warnings.append("No resource limits specified")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _build_deployment_config(self, agent: Agent, environment: str) -> Dict:
        """Build deployment configuration"""
        base_config = {
            "agent_id": str(agent.id),
            "name": agent.name,
            "image": f"agent-mesh/agent:{agent.version or 'latest'}",
            "replicas": 1,
            "environment": environment,
            "env_vars": {
                "AGENT_ID": str(agent.id),
                "AGENT_NAME": agent.name,
                "LLM_MODEL": agent.llm_model,
                "SYSTEM_PROMPT": agent.system_prompt,
                "CONFIGURATION": json.dumps(agent.configuration)
            },
            "resources": {
                "requests": {
                    "memory": "256Mi",
                    "cpu": "0.1"
                },
                "limits": {
                    "memory": "512Mi",
                    "cpu": "0.5"
                }
            },
            "ports": [
                {
                    "name": "http",
                    "containerPort": 8080,
                    "protocol": "TCP"
                }
            ],
            "health_check": {
                "path": "/health",
                "port": 8080,
                "initial_delay_seconds": 10,
                "period_seconds": 30
            }
        }
        
        # Merge with agent-specific deployment config
        if agent.deployment_config:
            base_config.update(agent.deployment_config)
        
        return base_config


class ContainerOrchestrator:
    """Container orchestration abstraction"""
    
    async def deploy(self, agent_id: str, config: Dict) -> DeploymentResult:
        """Deploy agent container"""
        # Simulate deployment process
        await asyncio.sleep(2)  # Simulate deployment time
        
        # Mock successful deployment
        return DeploymentResult(
            success=True,
            deployment_id=str(uuid.uuid4()),
            message="Deployment successful",
            details={
                "dns": f"{config['name']}.agents.local",
                "port": 8080,
                "health_check_url": f"http://{config['name']}.agents.local:8080/health",
                "endpoints": [f"http://{config['name']}.agents.local:8080"]
            }
        )
    
    async def scale(self, agent_id: str, replicas: int) -> DeploymentResult:
        """Scale agent replicas"""
        await asyncio.sleep(1)  # Simulate scaling time
        
        return DeploymentResult(
            success=True,
            deployment_id=str(uuid.uuid4()),
            message=f"Scaled to {replicas} replicas"
        )
    
    async def stop(self, agent_id: str) -> DeploymentResult:
        """Stop agent"""
        await asyncio.sleep(1)  # Simulate stop time
        
        return DeploymentResult(
            success=True,
            deployment_id=str(uuid.uuid4()),
            message="Agent stopped"
        )
    
    async def get_logs(self, agent_id: str, lines: int = 100) -> List[str]:
        """Get agent logs"""
        # Mock log entries
        return [
            f"[{datetime.utcnow().isoformat()}] INFO: Agent {agent_id} started",
            f"[{datetime.utcnow().isoformat()}] INFO: Health check passed",
            f"[{datetime.utcnow().isoformat()}] INFO: Processing request"
        ]
    
    async def get_metrics(self, agent_id: str) -> Dict:
        """Get agent metrics"""
        # Mock metrics
        return {
            "cpu_usage": 0.25,
            "memory_usage": 0.40,
            "request_count": 1234,
            "average_response_time": 0.150,
            "error_rate": 0.01
        }
