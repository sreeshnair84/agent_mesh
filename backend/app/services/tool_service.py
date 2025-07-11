"""
Tool Service
Handles tool registration, management, and execution
"""

import asyncio
import json
import uuid
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.tool import Tool, ToolExecution
from app.models.enhanced_agent import Agent
from app.models.user import User
from app.schemas.tool import (
    ToolCreate, ToolUpdate, ToolResponse,
    ToolExecutionCreate, ToolExecutionResponse
)
from app.services.observability_service import ObservabilityService
from app.core.exceptions import ToolError, ValidationError
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class ToolService:
    """Service for managing tools and their executions"""
    
    def __init__(self):
        self.observability_service = ObservabilityService()
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def create_tool(
        self,
        tool_data: ToolCreate,
        user_id: str,
        db: AsyncSession
    ) -> ToolResponse:
        """Create a new tool"""
        try:
            # Validate tool configuration
            await self._validate_tool_config(tool_data)
            
            # Create tool
            tool = Tool(
                id=str(uuid.uuid4()),
                name=tool_data.name,
                display_name=tool_data.display_name,
                description=tool_data.description,
                tool_type=tool_data.tool_type,
                category=tool_data.category,
                tags=tool_data.tags,
                config=tool_data.config,
                tool_schema=tool_data.tool_schema,
                implementation=tool_data.implementation,
                endpoint_url=tool_data.endpoint_url,
                auth_type=tool_data.auth_type,
                auth_config=tool_data.auth_config,
                status="draft",
                version=tool_data.version,
                created_by=user_id,
                organization_id=None  # TODO: Get from user context
            )
            
            db.add(tool)
            await db.commit()
            await db.refresh(tool)
            
            # Log tool creation
            await self.observability_service.log_event(
                "tool_created",
                {
                    "tool_id": tool.id,
                    "tool_name": tool.name,
                    "tool_type": tool.tool_type,
                    "created_by": user_id
                }
            )
            
            return ToolResponse.model_validate(tool)
            
        except Exception as e:
            logger.error(f"Error creating tool: {str(e)}")
            await db.rollback()
            raise ToolError(f"Failed to create tool: {str(e)}")
    
    async def get_tool(
        self,
        tool_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[ToolResponse]:
        """Get tool by ID"""
        try:
            stmt = select(Tool).where(Tool.id == tool_id)
            result = await db.execute(stmt)
            tool = result.scalar_one_or_none()
            
            if not tool:
                return None
            
            return ToolResponse.model_validate(tool)
            
        except Exception as e:
            logger.error(f"Error getting tool {tool_id}: {str(e)}")
            raise ToolError(f"Failed to get tool: {str(e)}")
    
    async def list_tools(
        self,
        user_id: str,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        tool_type: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[ToolResponse]:
        """List tools with filtering"""
        try:
            stmt = select(Tool)
            
            # Apply filters
            if tool_type:
                stmt = stmt.where(Tool.tool_type == tool_type)
            
            if category:
                stmt = stmt.where(Tool.category == category)
            
            if status:
                stmt = stmt.where(Tool.status == status)
            
            if search:
                stmt = stmt.where(
                    or_(
                        Tool.name.ilike(f"%{search}%"),
                        Tool.display_name.ilike(f"%{search}%"),
                        Tool.description.ilike(f"%{search}%")
                    )
                )
            
            stmt = stmt.offset(skip).limit(limit)
            
            result = await db.execute(stmt)
            tools = result.scalars().all()
            
            return [ToolResponse.model_validate(t) for t in tools]
            
        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}")
            raise ToolError(f"Failed to list tools: {str(e)}")
    
    async def update_tool(
        self,
        tool_id: str,
        tool_data: ToolUpdate,
        user_id: str,
        db: AsyncSession
    ) -> Optional[ToolResponse]:
        """Update tool"""
        try:
            # Get existing tool
            tool = await self.get_tool(tool_id, user_id, db)
            if not tool:
                return None
            
            # Validate configuration if provided
            if tool_data.config:
                await self._validate_tool_config(tool_data)
            
            # Update tool
            update_data = tool_data.model_dump(exclude_unset=True)
            if update_data:
                stmt = update(Tool).where(Tool.id == tool_id).values(**update_data)
                await db.execute(stmt)
                await db.commit()
            
            # Return updated tool
            return await self.get_tool(tool_id, user_id, db)
            
        except Exception as e:
            logger.error(f"Error updating tool {tool_id}: {str(e)}")
            await db.rollback()
            raise ToolError(f"Failed to update tool: {str(e)}")
    
    async def delete_tool(
        self,
        tool_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """Delete tool"""
        try:
            stmt = delete(Tool).where(Tool.id == tool_id)
            result = await db.execute(stmt)
            await db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error deleting tool {tool_id}: {str(e)}")
            await db.rollback()
            raise ToolError(f"Failed to delete tool: {str(e)}")
    
    async def deploy_tool(
        self,
        tool_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Deploy tool to active status"""
        try:
            # Get tool
            tool = await self.get_tool(tool_id, user_id, db)
            if not tool:
                raise ToolError(f"Tool {tool_id} not found")
            
            # Validate tool before deployment
            await self._validate_tool_deployment(tool)
            
            # Update tool status
            stmt = update(Tool).where(Tool.id == tool_id).values(
                status="active",
                updated_at=datetime.utcnow()
            )
            await db.execute(stmt)
            await db.commit()
            
            # Log deployment
            await self.observability_service.log_event(
                "tool_deployed",
                {
                    "tool_id": tool_id,
                    "tool_name": tool.name,
                    "deployed_by": user_id
                }
            )
            
            return {
                "tool_id": tool_id,
                "status": "active",
                "deployed_at": datetime.utcnow().isoformat(),
                "message": "Tool deployed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deploying tool {tool_id}: {str(e)}")
            await db.rollback()
            raise ToolError(f"Failed to deploy tool: {str(e)}")
    
    async def test_tool(
        self,
        tool_id: str,
        test_data: Dict[str, Any],
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Test tool functionality"""
        try:
            # Get tool
            tool = await self.get_tool(tool_id, user_id, db)
            if not tool:
                raise ToolError(f"Tool {tool_id} not found")
            
            # Execute tool test
            start_time = datetime.utcnow()
            
            try:
                result = await self._execute_tool_test(tool, test_data)
                status = "passed"
                error_message = None
            except Exception as e:
                result = None
                status = "failed"
                error_message = str(e)
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            # Log test execution
            await self.observability_service.log_event(
                "tool_tested",
                {
                    "tool_id": tool_id,
                    "tool_name": tool.name,
                    "test_status": status,
                    "execution_time_ms": execution_time,
                    "tested_by": user_id
                }
            )
            
            return {
                "tool_id": tool_id,
                "test_id": f"test-{uuid.uuid4()}",
                "status": status,
                "result": result,
                "error_message": error_message,
                "execution_time_ms": execution_time,
                "timestamp": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error testing tool {tool_id}: {str(e)}")
            raise ToolError(f"Failed to test tool: {str(e)}")
    
    async def execute_tool(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        user_id: str,
        db: AsyncSession,
        agent_id: Optional[str] = None,
        workflow_execution_id: Optional[str] = None
    ) -> ToolExecutionResponse:
        """Execute tool"""
        try:
            # Get tool
            tool = await self.get_tool(tool_id, user_id, db)
            if not tool:
                raise ToolError(f"Tool {tool_id} not found")
            
            if tool.status != "active":
                raise ToolError(f"Tool {tool_id} is not active")
            
            # Create execution record
            execution = ToolExecution(
                id=str(uuid.uuid4()),
                tool_id=tool_id,
                agent_id=agent_id,
                workflow_execution_id=workflow_execution_id,
                input_data=input_data,
                status="pending",
                created_by=user_id
            )
            
            db.add(execution)
            await db.commit()
            await db.refresh(execution)
            
            # Execute tool
            start_time = datetime.utcnow()
            
            try:
                execution.status = "running"
                execution.started_at = start_time
                await db.commit()
                
                # Execute based on tool type
                if tool.tool_type == "api":
                    result = await self._execute_api_tool(tool, input_data, context)
                elif tool.tool_type == "function":
                    result = await self._execute_function_tool(tool, input_data, context)
                elif tool.tool_type == "mcp":
                    result = await self._execute_mcp_tool(tool, input_data, context)
                else:
                    raise ToolError(f"Unsupported tool type: {tool.tool_type}")
                
                end_time = datetime.utcnow()
                execution_time = (end_time - start_time).total_seconds() * 1000
                
                # Update execution as completed
                execution.status = "completed"
                execution.completed_at = end_time
                execution.output_data = result
                execution.execution_time_ms = int(execution_time)
                
                # Update tool statistics
                await self._update_tool_stats(tool_id, "success", execution_time, db)
                
            except Exception as e:
                end_time = datetime.utcnow()
                execution_time = (end_time - start_time).total_seconds() * 1000
                
                # Update execution as failed
                execution.status = "failed"
                execution.completed_at = end_time
                execution.error_message = str(e)
                execution.execution_time_ms = int(execution_time)
                
                # Update tool statistics
                await self._update_tool_stats(tool_id, "error", execution_time, db)
                
                raise
            
            finally:
                await db.commit()
            
            return ToolExecutionResponse.model_validate(execution)
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_id}: {str(e)}")
            raise ToolError(f"Failed to execute tool: {str(e)}")
    
    async def get_tool_execution(
        self,
        execution_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[ToolExecutionResponse]:
        """Get tool execution by ID"""
        try:
            stmt = select(ToolExecution).where(
                and_(
                    ToolExecution.id == execution_id,
                    ToolExecution.created_by == user_id
                )
            )
            
            result = await db.execute(stmt)
            execution = result.scalar_one_or_none()
            
            if not execution:
                return None
            
            return ToolExecutionResponse.model_validate(execution)
            
        except Exception as e:
            logger.error(f"Error getting tool execution {execution_id}: {str(e)}")
            raise ToolError(f"Failed to get tool execution: {str(e)}")
    
    async def list_tool_executions(
        self,
        tool_id: str,
        user_id: str,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[ToolExecutionResponse]:
        """List tool executions"""
        try:
            stmt = select(ToolExecution).where(ToolExecution.tool_id == tool_id)
            
            if status:
                stmt = stmt.where(ToolExecution.status == status)
            
            stmt = stmt.offset(skip).limit(limit).order_by(
                ToolExecution.created_at.desc()
            )
            
            result = await db.execute(stmt)
            executions = result.scalars().all()
            
            return [ToolExecutionResponse.model_validate(e) for e in executions]
            
        except Exception as e:
            logger.error(f"Error listing tool executions: {str(e)}")
            raise ToolError(f"Failed to list tool executions: {str(e)}")
    
    async def get_tool_stats(
        self,
        tool_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get tool statistics"""
        try:
            # Get execution stats
            stmt = select(
                func.count(ToolExecution.id).label("total_invocations"),
                func.count(ToolExecution.id).filter(
                    ToolExecution.status == "completed"
                ).label("successful_invocations"),
                func.count(ToolExecution.id).filter(
                    ToolExecution.status == "failed"
                ).label("failed_invocations"),
                func.avg(ToolExecution.execution_time_ms).label("avg_execution_time"),
                func.max(ToolExecution.created_at).label("last_execution")
            ).where(ToolExecution.tool_id == tool_id)
            
            result = await db.execute(stmt)
            stats = result.first()
            
            return {
                "total_invocations": stats.total_invocations or 0,
                "successful_invocations": stats.successful_invocations or 0,
                "failed_invocations": stats.failed_invocations or 0,
                "success_rate": (
                    (stats.successful_invocations / stats.total_invocations * 100)
                    if stats.total_invocations > 0 else 0
                ),
                "avg_execution_time": stats.avg_execution_time or 0,
                "last_execution": stats.last_execution
            }
            
        except Exception as e:
            logger.error(f"Error getting tool stats {tool_id}: {str(e)}")
            raise ToolError(f"Failed to get tool stats: {str(e)}")
    
    async def get_tool_categories(self, db: AsyncSession) -> List[str]:
        """Get available tool categories"""
        try:
            stmt = select(Tool.category).distinct().where(Tool.category.isnot(None))
            result = await db.execute(stmt)
            categories = [row[0] for row in result.fetchall()]
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"Error getting tool categories: {str(e)}")
            raise ToolError(f"Failed to get tool categories: {str(e)}")
    
    async def _validate_tool_config(self, tool_data: Union[ToolCreate, ToolUpdate]) -> None:
        """Validate tool configuration"""
        try:
            if tool_data.tool_type == "api":
                if not tool_data.endpoint_url:
                    raise ValidationError("API tools require endpoint_url")
                
                # Validate URL format
                if not tool_data.endpoint_url.startswith(("http://", "https://")):
                    raise ValidationError("Invalid endpoint URL format")
            
            elif tool_data.tool_type == "function":
                if not tool_data.implementation:
                    raise ValidationError("Function tools require implementation code")
            
            elif tool_data.tool_type == "mcp":
                if not tool_data.config or "server" not in tool_data.config:
                    raise ValidationError("MCP tools require server configuration")
            
            # Validate tool schema if provided
            if tool_data.tool_schema:
                await self._validate_tool_schema(tool_data.tool_schema)
                
        except Exception as e:
            logger.error(f"Error validating tool config: {str(e)}")
            raise ValidationError(f"Invalid tool configuration: {str(e)}")
    
    async def _validate_tool_schema(self, schema: Dict[str, Any]) -> None:
        """Validate tool schema"""
        try:
            # Check required fields
            required_fields = ["name", "description", "parameters"]
            for field in required_fields:
                if field not in schema:
                    raise ValidationError(f"Tool schema missing required field: {field}")
            
            # Validate parameters
            if "properties" in schema["parameters"]:
                for param_name, param_def in schema["parameters"]["properties"].items():
                    if "type" not in param_def:
                        raise ValidationError(f"Parameter {param_name} missing type")
                        
        except Exception as e:
            logger.error(f"Error validating tool schema: {str(e)}")
            raise ValidationError(f"Invalid tool schema: {str(e)}")
    
    async def _validate_tool_deployment(self, tool: ToolResponse) -> None:
        """Validate tool before deployment"""
        try:
            if tool.tool_type == "api":
                # Test API endpoint
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(tool.endpoint_url, timeout=10.0)
                        if response.status_code >= 400:
                            raise ValidationError(f"API endpoint returned status {response.status_code}")
                except httpx.RequestError as e:
                    raise ValidationError(f"API endpoint not reachable: {str(e)}")
            
            elif tool.tool_type == "function":
                # Validate function implementation
                if not tool.implementation:
                    raise ValidationError("Function tool missing implementation")
                
                # Basic syntax check
                try:
                    compile(tool.implementation, "<string>", "exec")
                except SyntaxError as e:
                    raise ValidationError(f"Function implementation syntax error: {str(e)}")
            
            elif tool.tool_type == "mcp":
                # Validate MCP configuration
                if not tool.config or "server" not in tool.config:
                    raise ValidationError("MCP tool missing server configuration")
                    
        except Exception as e:
            logger.error(f"Error validating tool deployment: {str(e)}")
            raise ValidationError(f"Tool deployment validation failed: {str(e)}")
    
    async def _execute_tool_test(
        self,
        tool: ToolResponse,
        test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool test"""
        try:
            if tool.tool_type == "api":
                return await self._execute_api_tool(tool, test_data, {})
            elif tool.tool_type == "function":
                return await self._execute_function_tool(tool, test_data, {})
            elif tool.tool_type == "mcp":
                return await self._execute_mcp_tool(tool, test_data, {})
            else:
                raise ToolError(f"Unsupported tool type: {tool.tool_type}")
                
        except Exception as e:
            logger.error(f"Error executing tool test: {str(e)}")
            raise ToolError(f"Tool test execution failed: {str(e)}")
    
    async def _execute_api_tool(
        self,
        tool: ToolResponse,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute API tool"""
        try:
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            
            # Handle authentication
            if tool.auth_type == "api-key" and tool.auth_config:
                api_key = tool.auth_config.get("api_key")
                key_header = tool.auth_config.get("header", "X-API-Key")
                if api_key:
                    headers[key_header] = api_key
            
            elif tool.auth_type == "bearer" and tool.auth_config:
                token = tool.auth_config.get("token")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    tool.endpoint_url,
                    json=input_data,
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                
                return {
                    "status": response.status_code,
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    "headers": dict(response.headers)
                }
                
        except Exception as e:
            logger.error(f"Error executing API tool: {str(e)}")
            raise ToolError(f"API tool execution failed: {str(e)}")
    
    async def _execute_function_tool(
        self,
        tool: ToolResponse,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute function tool"""
        try:
            # Create execution environment
            globals_dict = {
                "__builtins__": __builtins__,
                "input_data": input_data,
                "context": context,
                "result": None
            }
            
            # Execute function
            exec(tool.implementation, globals_dict)
            
            return {
                "result": globals_dict.get("result"),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error executing function tool: {str(e)}")
            raise ToolError(f"Function tool execution failed: {str(e)}")
    
    async def _execute_mcp_tool(
        self,
        tool: ToolResponse,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute MCP tool"""
        try:
            # TODO: Implement MCP tool execution
            # This would involve communicating with the MCP server
            # For now, return a placeholder
            
            return {
                "message": "MCP tool execution not yet implemented",
                "tool_id": tool.id,
                "input_data": input_data,
                "status": "placeholder"
            }
            
        except Exception as e:
            logger.error(f"Error executing MCP tool: {str(e)}")
            raise ToolError(f"MCP tool execution failed: {str(e)}")
    
    async def _update_tool_stats(
        self,
        tool_id: str,
        status: str,
        execution_time: float,
        db: AsyncSession
    ) -> None:
        """Update tool statistics"""
        try:
            if status == "success":
                stmt = update(Tool).where(Tool.id == tool_id).values(
                    total_invocations=Tool.total_invocations + 1,
                    successful_invocations=Tool.successful_invocations + 1,
                    updated_at=datetime.utcnow()
                )
            else:
                stmt = update(Tool).where(Tool.id == tool_id).values(
                    total_invocations=Tool.total_invocations + 1,
                    failed_invocations=Tool.failed_invocations + 1,
                    updated_at=datetime.utcnow()
                )
            
            await db.execute(stmt)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error updating tool stats: {str(e)}")
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
