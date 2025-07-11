"""
Workflow Service
Handles workflow creation, execution, and management
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.workflow import Workflow, WorkflowExecution
from app.models.enhanced_agent import Agent
from app.models.user import User
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse,
    WorkflowExecutionCreate, WorkflowExecutionResponse
)
from app.services.enhanced_agent_service import AgentService
from app.services.observability_service import ObservabilityService
from app.core.exceptions import WorkflowError, ValidationError
import logging

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing workflows and their executions"""
    
    def __init__(self):
        self.agent_service = AgentService()
        self.observability_service = ObservabilityService()
    
    async def create_workflow(
        self,
        workflow_data: WorkflowCreate,
        user_id: str,
        db: AsyncSession
    ) -> WorkflowResponse:
        """Create a new workflow"""
        try:
            # Validate workflow definition
            await self._validate_workflow_definition(workflow_data.definition, db)
            
            # Create workflow
            workflow = Workflow(
                id=str(uuid.uuid4()),
                name=workflow_data.name,
                description=workflow_data.description,
                workflow_type=workflow_data.workflow_type,
                definition=workflow_data.definition,
                config=workflow_data.config,
                metadata=workflow_data.metadata,
                version=workflow_data.version,
                parent_workflow_id=workflow_data.parent_workflow_id,
                status="draft",
                created_by=user_id,
                organization_id=None  # TODO: Get from user context
            )
            
            db.add(workflow)
            await db.commit()
            await db.refresh(workflow)
            
            # Log workflow creation
            await self.observability_service.log_event(
                "workflow_created",
                {
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "workflow_type": workflow.workflow_type,
                    "created_by": user_id
                }
            )
            
            return WorkflowResponse.model_validate(workflow)
            
        except Exception as e:
            logger.error(f"Error creating workflow: {str(e)}")
            await db.rollback()
            raise WorkflowError(f"Failed to create workflow: {str(e)}")
    
    async def get_workflow(
        self,
        workflow_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[WorkflowResponse]:
        """Get workflow by ID"""
        try:
            stmt = select(Workflow).where(
                and_(
                    Workflow.id == workflow_id,
                    Workflow.created_by == user_id
                )
            ).options(selectinload(Workflow.executions))
            
            result = await db.execute(stmt)
            workflow = result.scalar_one_or_none()
            
            if not workflow:
                return None
            
            return WorkflowResponse.model_validate(workflow)
            
        except Exception as e:
            logger.error(f"Error getting workflow {workflow_id}: {str(e)}")
            raise WorkflowError(f"Failed to get workflow: {str(e)}")
    
    async def list_workflows(
        self,
        user_id: str,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        workflow_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[WorkflowResponse]:
        """List workflows with filtering"""
        try:
            stmt = select(Workflow).where(Workflow.created_by == user_id)
            
            # Apply filters
            if status:
                stmt = stmt.where(Workflow.status == status)
            
            if workflow_type:
                stmt = stmt.where(Workflow.workflow_type == workflow_type)
            
            if search:
                stmt = stmt.where(
                    or_(
                        Workflow.name.ilike(f"%{search}%"),
                        Workflow.description.ilike(f"%{search}%")
                    )
                )
            
            stmt = stmt.offset(skip).limit(limit)
            stmt = stmt.options(selectinload(Workflow.executions))
            
            result = await db.execute(stmt)
            workflows = result.scalars().all()
            
            return [WorkflowResponse.model_validate(w) for w in workflows]
            
        except Exception as e:
            logger.error(f"Error listing workflows: {str(e)}")
            raise WorkflowError(f"Failed to list workflows: {str(e)}")
    
    async def update_workflow(
        self,
        workflow_id: str,
        workflow_data: WorkflowUpdate,
        user_id: str,
        db: AsyncSession
    ) -> Optional[WorkflowResponse]:
        """Update workflow"""
        try:
            # Get existing workflow
            workflow = await self.get_workflow(workflow_id, user_id, db)
            if not workflow:
                return None
            
            # Validate definition if provided
            if workflow_data.definition:
                await self._validate_workflow_definition(workflow_data.definition, db)
            
            # Update workflow
            update_data = workflow_data.model_dump(exclude_unset=True)
            if update_data:
                stmt = update(Workflow).where(
                    and_(
                        Workflow.id == workflow_id,
                        Workflow.created_by == user_id
                    )
                ).values(**update_data)
                
                await db.execute(stmt)
                await db.commit()
            
            # Return updated workflow
            return await self.get_workflow(workflow_id, user_id, db)
            
        except Exception as e:
            logger.error(f"Error updating workflow {workflow_id}: {str(e)}")
            await db.rollback()
            raise WorkflowError(f"Failed to update workflow: {str(e)}")
    
    async def delete_workflow(
        self,
        workflow_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """Delete workflow"""
        try:
            stmt = delete(Workflow).where(
                and_(
                    Workflow.id == workflow_id,
                    Workflow.created_by == user_id
                )
            )
            
            result = await db.execute(stmt)
            await db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id}: {str(e)}")
            await db.rollback()
            raise WorkflowError(f"Failed to delete workflow: {str(e)}")
    
    async def execute_workflow(
        self,
        workflow_id: str,
        user_id: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        db: AsyncSession
    ) -> WorkflowExecutionResponse:
        """Execute workflow"""
        try:
            # Get workflow
            workflow = await self.get_workflow(workflow_id, user_id, db)
            if not workflow:
                raise WorkflowError(f"Workflow {workflow_id} not found")
            
            if workflow.status != "active":
                raise WorkflowError(f"Workflow {workflow_id} is not active")
            
            # Create execution record
            execution = WorkflowExecution(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                input_data=input_data,
                context=context,
                status="pending",
                created_by=user_id
            )
            
            db.add(execution)
            await db.commit()
            await db.refresh(execution)
            
            # Start execution in background
            asyncio.create_task(
                self._execute_workflow_async(execution.id, db)
            )
            
            return WorkflowExecutionResponse.model_validate(execution)
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
            await db.rollback()
            raise WorkflowError(f"Failed to execute workflow: {str(e)}")
    
    async def get_workflow_execution(
        self,
        execution_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[WorkflowExecutionResponse]:
        """Get workflow execution by ID"""
        try:
            stmt = select(WorkflowExecution).where(
                and_(
                    WorkflowExecution.id == execution_id,
                    WorkflowExecution.created_by == user_id
                )
            )
            
            result = await db.execute(stmt)
            execution = result.scalar_one_or_none()
            
            if not execution:
                return None
            
            return WorkflowExecutionResponse.model_validate(execution)
            
        except Exception as e:
            logger.error(f"Error getting workflow execution {execution_id}: {str(e)}")
            raise WorkflowError(f"Failed to get workflow execution: {str(e)}")
    
    async def list_workflow_executions(
        self,
        workflow_id: str,
        user_id: str,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[WorkflowExecutionResponse]:
        """List workflow executions"""
        try:
            stmt = select(WorkflowExecution).where(
                and_(
                    WorkflowExecution.workflow_id == workflow_id,
                    WorkflowExecution.created_by == user_id
                )
            )
            
            if status:
                stmt = stmt.where(WorkflowExecution.status == status)
            
            stmt = stmt.offset(skip).limit(limit).order_by(
                WorkflowExecution.created_at.desc()
            )
            
            result = await db.execute(stmt)
            executions = result.scalars().all()
            
            return [WorkflowExecutionResponse.model_validate(e) for e in executions]
            
        except Exception as e:
            logger.error(f"Error listing workflow executions: {str(e)}")
            raise WorkflowError(f"Failed to list workflow executions: {str(e)}")
    
    async def get_workflow_stats(
        self,
        workflow_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get workflow statistics"""
        try:
            # Get execution stats
            stmt = select(
                func.count(WorkflowExecution.id).label("total_executions"),
                func.count(WorkflowExecution.id).filter(
                    WorkflowExecution.status == "completed"
                ).label("successful_executions"),
                func.count(WorkflowExecution.id).filter(
                    WorkflowExecution.status == "failed"
                ).label("failed_executions"),
                func.avg(WorkflowExecution.execution_time_ms).label("avg_execution_time"),
                func.max(WorkflowExecution.created_at).label("last_execution")
            ).where(
                and_(
                    WorkflowExecution.workflow_id == workflow_id,
                    WorkflowExecution.created_by == user_id
                )
            )
            
            result = await db.execute(stmt)
            stats = result.first()
            
            return {
                "total_executions": stats.total_executions or 0,
                "successful_executions": stats.successful_executions or 0,
                "failed_executions": stats.failed_executions or 0,
                "success_rate": (
                    (stats.successful_executions / stats.total_executions * 100)
                    if stats.total_executions > 0 else 0
                ),
                "avg_execution_time": stats.avg_execution_time or 0,
                "last_execution": stats.last_execution
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow stats {workflow_id}: {str(e)}")
            raise WorkflowError(f"Failed to get workflow stats: {str(e)}")
    
    async def _validate_workflow_definition(
        self,
        definition: Dict[str, Any],
        db: AsyncSession
    ) -> None:
        """Validate workflow definition"""
        try:
            # Check required fields
            if "agents" not in definition:
                raise ValidationError("Workflow definition must include 'agents'")
            
            # Validate agents exist
            agent_ids = [agent.get("agent_id") for agent in definition["agents"]]
            if not agent_ids:
                raise ValidationError("Workflow must include at least one agent")
            
            # Check agents exist in database
            stmt = select(Agent.id).where(Agent.id.in_(agent_ids))
            result = await db.execute(stmt)
            existing_agents = {row[0] for row in result.fetchall()}
            
            missing_agents = set(agent_ids) - existing_agents
            if missing_agents:
                raise ValidationError(f"Agents not found: {missing_agents}")
            
        except Exception as e:
            logger.error(f"Error validating workflow definition: {str(e)}")
            raise ValidationError(f"Invalid workflow definition: {str(e)}")
    
    async def _execute_workflow_async(
        self,
        execution_id: str,
        db: AsyncSession
    ) -> None:
        """Execute workflow asynchronously"""
        try:
            # Get execution
            stmt = select(WorkflowExecution).where(
                WorkflowExecution.id == execution_id
            ).options(selectinload(WorkflowExecution.workflow))
            
            result = await db.execute(stmt)
            execution = result.scalar_one_or_none()
            
            if not execution:
                logger.error(f"Execution {execution_id} not found")
                return
            
            # Update status to running
            execution.status = "running"
            execution.started_at = datetime.utcnow()
            await db.commit()
            
            workflow = execution.workflow
            definition = workflow.definition
            
            # Execute based on workflow type
            if workflow.workflow_type == "sequential":
                await self._execute_sequential_workflow(execution, definition, db)
            elif workflow.workflow_type == "parallel":
                await self._execute_parallel_workflow(execution, definition, db)
            elif workflow.workflow_type == "conditional":
                await self._execute_conditional_workflow(execution, definition, db)
            else:
                raise WorkflowError(f"Unsupported workflow type: {workflow.workflow_type}")
            
        except Exception as e:
            logger.error(f"Error executing workflow {execution_id}: {str(e)}")
            # Update execution status to failed
            await self._update_execution_status(execution_id, "failed", str(e), db)
    
    async def _execute_sequential_workflow(
        self,
        execution: WorkflowExecution,
        definition: Dict[str, Any],
        db: AsyncSession
    ) -> None:
        """Execute sequential workflow"""
        try:
            output_data = {}
            current_data = execution.input_data
            
            for agent_config in definition["agents"]:
                agent_id = agent_config["agent_id"]
                agent_input = agent_config.get("input_mapping", {})
                
                # Map input data
                mapped_input = self._map_data(current_data, agent_input)
                
                # Execute agent
                result = await self.agent_service.invoke_agent(
                    agent_id,
                    mapped_input,
                    execution.context,
                    execution.created_by,
                    db
                )
                
                # Store result
                output_data[agent_id] = result
                current_data = result
            
            # Update execution as completed
            await self._update_execution_status(
                execution.id,
                "completed",
                None,
                db,
                output_data
            )
            
        except Exception as e:
            logger.error(f"Error in sequential workflow execution: {str(e)}")
            await self._update_execution_status(execution.id, "failed", str(e), db)
    
    async def _execute_parallel_workflow(
        self,
        execution: WorkflowExecution,
        definition: Dict[str, Any],
        db: AsyncSession
    ) -> None:
        """Execute parallel workflow"""
        try:
            tasks = []
            
            for agent_config in definition["agents"]:
                agent_id = agent_config["agent_id"]
                agent_input = agent_config.get("input_mapping", {})
                
                # Map input data
                mapped_input = self._map_data(execution.input_data, agent_input)
                
                # Create task
                task = asyncio.create_task(
                    self.agent_service.invoke_agent(
                        agent_id,
                        mapped_input,
                        execution.context,
                        execution.created_by,
                        db
                    )
                )
                tasks.append((agent_id, task))
            
            # Wait for all tasks
            results = {}
            for agent_id, task in tasks:
                result = await task
                results[agent_id] = result
            
            # Update execution as completed
            await self._update_execution_status(
                execution.id,
                "completed",
                None,
                db,
                results
            )
            
        except Exception as e:
            logger.error(f"Error in parallel workflow execution: {str(e)}")
            await self._update_execution_status(execution.id, "failed", str(e), db)
    
    async def _execute_conditional_workflow(
        self,
        execution: WorkflowExecution,
        definition: Dict[str, Any],
        db: AsyncSession
    ) -> None:
        """Execute conditional workflow"""
        try:
            output_data = {}
            current_data = execution.input_data
            
            for step in definition["steps"]:
                condition = step.get("condition")
                
                # Evaluate condition
                if condition and not self._evaluate_condition(condition, current_data):
                    continue
                
                agent_id = step["agent_id"]
                agent_input = step.get("input_mapping", {})
                
                # Map input data
                mapped_input = self._map_data(current_data, agent_input)
                
                # Execute agent
                result = await self.agent_service.invoke_agent(
                    agent_id,
                    mapped_input,
                    execution.context,
                    execution.created_by,
                    db
                )
                
                # Store result
                output_data[agent_id] = result
                current_data = result
            
            # Update execution as completed
            await self._update_execution_status(
                execution.id,
                "completed",
                None,
                db,
                output_data
            )
            
        except Exception as e:
            logger.error(f"Error in conditional workflow execution: {str(e)}")
            await self._update_execution_status(execution.id, "failed", str(e), db)
    
    async def _update_execution_status(
        self,
        execution_id: str,
        status: str,
        error_message: Optional[str],
        db: AsyncSession,
        output_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update execution status"""
        try:
            update_data = {
                "status": status,
                "completed_at": datetime.utcnow()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            if output_data:
                update_data["output_data"] = output_data
            
            stmt = update(WorkflowExecution).where(
                WorkflowExecution.id == execution_id
            ).values(**update_data)
            
            await db.execute(stmt)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error updating execution status: {str(e)}")
    
    def _map_data(self, data: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Map data based on mapping configuration"""
        if not mapping:
            return data
        
        mapped = {}
        for key, path in mapping.items():
            mapped[key] = self._get_nested_value(data, path)
        
        return mapped
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from data using dot notation"""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _evaluate_condition(self, condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Evaluate condition against data"""
        # Simple condition evaluation
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        if not field or not operator:
            return True
        
        data_value = self._get_nested_value(data, field)
        
        if operator == "equals":
            return data_value == value
        elif operator == "not_equals":
            return data_value != value
        elif operator == "contains":
            return value in str(data_value) if data_value else False
        elif operator == "greater_than":
            return data_value > value if data_value else False
        elif operator == "less_than":
            return data_value < value if data_value else False
        
        return True
