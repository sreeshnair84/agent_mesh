"""
Enhanced Agent API endpoints following the implementation guide
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.enhanced_agent import Agent
from app.models.user import User
from app.schemas.enhanced_schemas import (
    AgentCreate, AgentUpdate, AgentResponse, AgentSearch, 
    AgentInvoke, AgentInvokeResponse, HealthCheckResponse,
    DeploymentResponse, SuccessResponse, ErrorResponse
)
from app.services.agent_service import AgentService
from app.services.search_service import SearchService
from app.services.observability_service import ObservabilityService

router = APIRouter()

# Dependency injection
def get_agent_service() -> AgentService:
    return AgentService()

def get_search_service() -> SearchService:
    return SearchService()

def get_observability_service() -> ObservabilityService:
    return ObservabilityService()


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    search: AgentSearch = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List agents with filtering and pagination"""
    try:
        query = select(Agent).options(
            selectinload(Agent.owner),
            selectinload(Agent.skills),
            selectinload(Agent.constraints),
            selectinload(Agent.tools)
        )
        
        # Apply filters
        filters = []
        if search.owner_id:
            filters.append(Agent.owner_id == search.owner_id)
        if search.type:
            filters.append(Agent.type == search.type)
        if search.status:
            filters.append(Agent.status == search.status)
        if search.tags:
            filters.append(Agent.tags.overlap(search.tags))
        
        if filters:
            query = query.where(and_(*filters))
        
        # Add text search if query provided
        if search.query:
            query = query.where(
                or_(
                    Agent.name.icontains(search.query),
                    Agent.description.icontains(search.query)
                )
            )
        
        # Apply pagination
        query = query.offset(search.offset).limit(search.limit)
        
        result = await db.execute(query)
        agents = result.scalars().all()
        
        return [AgentResponse.from_orm(agent) for agent in agents]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.post("/search/semantic", response_model=List[AgentResponse])
async def semantic_search_agents(
    search: AgentSearch,
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service),
    db: AsyncSession = Depends(get_db)
):
    """Perform semantic search on agents"""
    try:
        if not search.query:
            raise HTTPException(
                status_code=400,
                detail="Query is required for semantic search"
            )
        
        agents = await search_service.semantic_search_agents(
            query=search.query,
            filters=search.dict(exclude={'query'}),
            limit=search.limit,
            offset=search.offset
        )
        
        return [AgentResponse.from_orm(agent) for agent in agents]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}"
        )


@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Create a new agent"""
    try:
        agent = await agent_service.create_agent(
            agent_data=agent_data,
            owner_id=str(current_user.id),
            db=db
        )
        
        return AgentResponse.from_orm(agent)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific agent"""
    try:
        agent = await db.scalar(
            select(Agent)
            .options(
                selectinload(Agent.owner),
                selectinload(Agent.skills),
                selectinload(Agent.constraints),
                selectinload(Agent.tools)
            )
            .where(Agent.id == agent_id)
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return AgentResponse.from_orm(agent)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent: {str(e)}"
        )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Update an existing agent"""
    try:
        agent = await agent_service.update_agent(
            agent_id=agent_id,
            agent_data=agent_data,
            user_id=str(current_user.id),
            db=db
        )
        
        return AgentResponse.from_orm(agent)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {str(e)}"
        )


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Delete an agent"""
    try:
        await agent_service.delete_agent(
            agent_id=agent_id,
            user_id=str(current_user.id),
            db=db
        )
        
        return SuccessResponse(message="Agent deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent: {str(e)}"
        )


@router.post("/{agent_id}/deploy", response_model=DeploymentResponse)
async def deploy_agent(
    agent_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Deploy an agent"""
    try:
        deployment_info = await agent_service.deploy_agent(
            agent_id=agent_id,
            user_id=str(current_user.id),
            db=db,
            background_tasks=background_tasks
        )
        
        return DeploymentResponse(**deployment_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy agent: {str(e)}"
        )


@router.post("/{agent_id}/invoke", response_model=AgentInvokeResponse)
async def invoke_agent(
    agent_id: str,
    invoke_data: AgentInvoke,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service),
    observability_service: ObservabilityService = Depends(get_observability_service)
):
    """Invoke an agent"""
    try:
        # Generate trace ID if not provided
        trace_id = invoke_data.trace_id or str(uuid.uuid4())
        
        # Log invocation start
        await observability_service.log_transaction_start(
            trace_id=trace_id,
            session_id=invoke_data.session_id,
            entity_type="agent",
            entity_id=agent_id,
            user_id=str(current_user.id),
            input_data=invoke_data.input
        )
        
        try:
            result = await agent_service.invoke_agent(
                agent_id=agent_id,
                input_data=invoke_data.input,
                trace_id=trace_id,
                user_id=str(current_user.id),
                db=db
            )
            
            # Log successful completion
            await observability_service.log_transaction_end(
                trace_id=trace_id,
                output_data=result.output,
                llm_usage=result.llm_usage
            )
            
            return result
            
        except Exception as e:
            # Log error
            await observability_service.log_transaction_error(
                trace_id=trace_id,
                error_message=str(e)
            )
            raise
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invoke agent: {str(e)}"
        )


@router.get("/{agent_id}/health", response_model=HealthCheckResponse)
async def check_agent_health(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Check agent health"""
    try:
        health_status = await agent_service.check_agent_health(
            agent_id=agent_id,
            db=db
        )
        
        return HealthCheckResponse(**health_status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check agent health: {str(e)}"
        )


@router.get("/{agent_id}/logs")
async def get_agent_logs(
    agent_id: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    observability_service: ObservabilityService = Depends(get_observability_service)
):
    """Get agent logs"""
    try:
        logs = await observability_service.get_agent_logs(
            agent_id=agent_id,
            limit=limit
        )
        
        return {"logs": logs}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent logs: {str(e)}"
        )


@router.get("/{agent_id}/metrics")
async def get_agent_metrics(
    agent_id: str,
    period: str = Query("1h", regex="^(1h|24h|7d|30d)$"),
    current_user: User = Depends(get_current_user),
    observability_service: ObservabilityService = Depends(get_observability_service)
):
    """Get agent metrics"""
    try:
        metrics = await observability_service.get_agent_metrics(
            agent_id=agent_id,
            period=period
        )
        
        return {"metrics": metrics}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent metrics: {str(e)}"
        )


@router.get("/{agent_id}/similar", response_model=List[AgentResponse])
async def get_similar_agents(
    agent_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    search_service: SearchService = Depends(get_search_service)
):
    """Get agents similar to the specified agent"""
    try:
        similar_agents = await search_service.find_similar_agents(
            agent_id=agent_id,
            db=db,
            limit=limit
        )
        
        return [AgentResponse.from_orm(agent) for agent in similar_agents]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get similar agents: {str(e)}"
        )


@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Stop a running agent"""
    try:
        agent = await db.scalar(
            select(Agent).where(Agent.id == agent_id)
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if str(agent.owner_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to stop this agent")
        
        if agent.status != 'active':
            raise HTTPException(status_code=400, detail="Agent is not running")
        
        await agent_service._stop_agent(agent)
        await db.commit()
        
        return SuccessResponse(message="Agent stopped successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop agent: {str(e)}"
        )
