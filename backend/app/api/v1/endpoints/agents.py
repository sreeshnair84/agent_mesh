"""
Agent Management API Endpoints
REST API for agent lifecycle management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime

from app.core.database import get_db
from app.models.agent import Agent, AgentStatus, AgentCategory
from app.schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentList,
    AgentDeploymentRequest, AgentDeploymentResponse,
    AgentHealthCheck, AgentChatMessage, AgentChatResponse,
    AgentCategoryResponse
)
from app.services.agent_creation import AgentCreationService, AgentSpec, ResourceRequirements
from app.services.agent_configuration import AgentConfigurationManager
from app.services.agent_deployment import AgentDeploymentManager
from app.services.agent_health_monitor import AgentHealthMonitor
from app.core.exceptions import NotFoundError, ValidationError
from app.api.deps import get_current_user_from_db

router = APIRouter(
    prefix="/agents",
    responses={404: {"description": "Not found"}},
)

# Categories
@router.get("/categories", response_model=List[AgentCategoryResponse])
async def get_agent_categories(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
    include_inactive: bool = Query(False, description="Include inactive categories")
):
    """
    Get all agent categories
    
    Returns a list of categories that can be used for organizing agents.
    """
    try:
        query = db.query(AgentCategory)
        
        if not include_inactive:
            query = query.filter(AgentCategory.is_active == True)
            
        categories = query.order_by(AgentCategory.sort_order.asc()).all()
        
        return [
            AgentCategoryResponse(
                id=str(cat.id),
                name=cat.name,
                display_name=cat.display_name,
                description=cat.description,
                icon=cat.icon,
                color=cat.color,
                sort_order=cat.sort_order,
                is_active=cat.is_active,
                created_at=cat.created_at
            ) for cat in categories
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Core CRUD Operations

@router.get("/", response_model=List[AgentResponse])
async def get_agents(
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(get_current_user_from_db),  # Temporarily disabled for testing
    skip: int = Query(0, ge=0, description="Number of agents to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of agents to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search agents"),
    show_all: bool = Query(False, description="Show all agents or just user's agents"),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
    is_private: Optional[bool] = Query(None, description="Filter by private status"),
    version: Optional[str] = Query(None, description="Filter by version")
):
    """
    Get list of agents with filtering and pagination
    """
    try:
        # Apply filters
        query = db.query(Agent)
        
        # User filter - temporarily disabled
        # if not show_all:
        #     query = query.filter(Agent.user_id == current_user.id)
        
        # Category filter
        if category:
            query = query.filter(Agent.category == category)
            
        # Status filter
        if status:
            query = query.filter(Agent.status == status)
            
        # Published filter
        if is_published is not None:
            query = query.filter(Agent.is_published == is_published)
            
        # Private filter
        if is_private is not None:
            query = query.filter(Agent.is_private == is_private)
        
        # Version filter
        if version:
            query = query.filter(Agent.version == version)
        
        # Search filter
        if search:
            query = query.filter(
                db.or_(
                    Agent.name.contains(search),
                    Agent.description.contains(search)
                )
            )
        
        # Pagination
        agents = query.offset(skip).limit(limit).all()
        return agents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_create: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Create a new agent
    """
    try:
        # Create agent using the creation service
        creation_service = AgentCreationService(db)
        
        # Convert AgentCreate to AgentSpec
        agent_spec = AgentSpec(
            name=agent_create.name,
            description=agent_create.description,
            category=agent_create.category,
            configuration=agent_create.configuration,
            instructions=agent_create.instructions,
            model=agent_create.model,
            resource_requirements=ResourceRequirements(),
            metadata=agent_create.metadata or {}
        )
        
        # Create the agent
        agent = await creation_service.create_agent_from_spec(
            agent_spec=agent_spec,
            user_id=current_user.id
        )
        
        return agent
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int = Path(..., description="The ID of the agent to get"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Get agent by ID
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.is_private and agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_update: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Update an existing agent
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update agent fields
        for field, value in agent_update.dict(exclude_unset=True).items():
            setattr(agent, field, value)
        
        db.commit()
        db.refresh(agent)
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Delete an agent
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        db.delete(agent)
        db.commit()
        
        return {"message": "Agent deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Agent Deployment Operations

@router.post("/{agent_id}/deploy", response_model=AgentDeploymentResponse)
async def deploy_agent(
    agent_id: int,
    deployment_request: AgentDeploymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Deploy an agent to a runtime environment
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Deploy agent using deployment service
        deployment_service = AgentDeploymentManager(db)
        deployment_result = await deployment_service.deploy_agent(
            agent_id=agent_id,
            environment=deployment_request.environment,
            replicas=deployment_request.replicas,
            resource_limits=deployment_request.resource_limits
        )
        
        return deployment_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Stop a running agent
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Stop agent using deployment service
        deployment_service = AgentDeploymentManager(db)
        await deployment_service.stop_agent(agent_id)
        
        return {"message": "Agent stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/restart")
async def restart_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Restart a running agent
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Restart agent using deployment service
        deployment_service = AgentDeploymentManager(db)
        await deployment_service.restart_agent(agent_id)
        
        return {"message": "Agent restarted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/scale")
async def scale_agent(
    agent_id: int,
    replicas: int = Body(..., description="Number of replicas"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Scale an agent deployment
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Scale agent using deployment service
        deployment_service = AgentDeploymentManager(db)
        await deployment_service.scale_agent(agent_id, replicas)
        
        return {"message": f"Agent scaled to {replicas} replicas"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/rollback")
async def rollback_agent(
    agent_id: int,
    version: str = Body(..., description="Version to rollback to"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Rollback agent to a previous version
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Rollback agent using deployment service
        deployment_service = AgentDeploymentManager(db)
        await deployment_service.rollback_agent(agent_id, version)
        
        return {"message": f"Agent rolled back to version {version}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/logs")
async def get_agent_logs(
    agent_id: int,
    lines: int = Query(100, ge=1, le=10000, description="Number of log lines to retrieve"),
    since: Optional[datetime] = Query(None, description="Get logs since this timestamp"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Get agent logs
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get logs using deployment service
        deployment_service = AgentDeploymentManager(db)
        logs = await deployment_service.get_agent_logs(agent_id, lines, since)
        
        return {"logs": logs}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Agent Health & Monitoring

@router.get("/{agent_id}/health", response_model=AgentHealthCheck)
async def get_agent_health(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Get agent health status
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.is_private and agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get health status using health monitor
        health_monitor = AgentHealthMonitor(db)
        health_status = await health_monitor.check_agent_health(agent_id)
        
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/metrics")
async def get_agent_metrics(
    agent_id: int,
    hours: int = Query(24, ge=1, le=168, description="Hours of metrics to retrieve"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Get agent performance metrics
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get metrics using health monitor
        health_monitor = AgentHealthMonitor(db)
        metrics = await health_monitor.get_agent_metrics(agent_id, hours)
        
        return {"metrics": metrics}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Agent Configuration Management

@router.get("/{agent_id}/config")
async def get_agent_config(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Get agent configuration
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get configuration using configuration manager
        config_manager = AgentConfigurationManager(db)
        config = await config_manager.get_agent_configuration(agent_id)
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agent_id}/config")
async def update_agent_config(
    agent_id: int,
    config_data: Dict[str, Any] = Body(..., description="Configuration data"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Update agent configuration
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update configuration using configuration manager
        config_manager = AgentConfigurationManager(db)
        updated_config = await config_manager.update_agent_configuration(
            agent_id, config_data
        )
        
        return updated_config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/config/versions")
async def get_agent_config_versions(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Get agent configuration version history
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get version history using configuration manager
        config_manager = AgentConfigurationManager(db)
        versions = await config_manager.get_configuration_versions(agent_id)
        
        return {"versions": versions}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Agent Template & Creation Operations

@router.post("/from-template")
async def create_agent_from_template(
    template_name: str = Body(..., description="Template name"),
    customizations: Dict[str, Any] = Body(default={}, description="Template customizations"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Create agent from template
    """
    try:
        # Create agent using creation service
        creation_service = AgentCreationService(db)
        agent = await creation_service.create_agent_from_template(
            template_name=template_name,
            customizations=customizations,
            user_id=current_user.id
        )
        
        return agent
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/clone")
async def clone_agent(
    agent_id: int,
    clone_name: str = Body(..., description="Name for the cloned agent"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Clone an existing agent
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.is_private and agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Clone agent using creation service
        creation_service = AgentCreationService(db)
        cloned_agent = await creation_service.clone_agent(
            source_agent_id=agent_id,
            new_name=clone_name,
            user_id=current_user.id
        )
        
        return cloned_agent
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Agent Chat Operations

@router.post("/{agent_id}/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    agent_id: int,
    message: AgentChatMessage,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Chat with an agent
    """
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Check permissions
        if agent.is_private and agent.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if agent is running
        if agent.status != AgentStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Agent is not running")
        
        # Process chat message (implement chat logic here)
        # This would integrate with your chat system
        response = {
            "response": f"Hello! I'm {agent.name}. How can I help you?",
            "timestamp": datetime.utcnow(),
            "agent_id": agent_id
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# System Information

@router.get("/categories/")
async def get_agent_categories(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Get available agent categories
    """
    return [
        {"name": "Assistant", "description": "General purpose assistants"},
        {"name": "Analysis", "description": "Data analysis and reporting"},
        {"name": "Customer Support", "description": "Customer service agents"},
        {"name": "Research", "description": "Research and information gathering"},
        {"name": "Creative", "description": "Creative content generation"},
        {"name": "Technical", "description": "Technical support and coding"},
        {"name": "Education", "description": "Educational and tutoring"},
        {"name": "Sales", "description": "Sales and marketing support"},
    ]


@router.get("/templates/")
async def get_agent_templates(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db),
):
    """
    Get available agent templates
    """
    return [
        {
            "id": "basic-assistant",
            "name": "Basic Assistant",
            "description": "A general purpose assistant template",
            "category": "Assistant",
            "configuration": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        },
        {
            "id": "customer-support",
            "name": "Customer Support",
            "description": "Customer service agent template",
            "category": "Customer Support",
            "configuration": {
                "model": "gpt-4",
                "temperature": 0.3,
                "max_tokens": 1500
            }
        },
        {
            "id": "data-analyst",
            "name": "Data Analyst",
            "description": "Data analysis and reporting template",
            "category": "Analysis",
            "configuration": {
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 3000
            }
        }
    ]
