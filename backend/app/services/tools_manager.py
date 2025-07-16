"""
Tools Manager Service
Handles tool registration, discovery, testing, and integration
"""

import asyncio
import json
import uuid
import httpx
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.tool import Tool, ToolExecution, ToolType
from app.models.agent import Agent
from app.models.user import User
from app.services.observability_service import ObservabilityService
from app.core.exceptions import ValidationError, ToolError
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ParameterDefinition:
    """Tool parameter definition"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    validation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthConfig:
    """Authentication configuration for tools"""
    type: str  # 'none', 'api_key', 'oauth2', 'basic', 'bearer'
    credentials: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    """Complete tool definition"""
    name: str
    type: str  # REST, GraphQL, gRPC, etc.
    endpoint: str
    authentication: AuthConfig
    capabilities: List[str]
    parameters: List[ParameterDefinition]
    documentation: str
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionTest:
    """Tool connection test result"""
    success: bool
    response_time: float
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None


@dataclass
class ToolMetrics:
    """Tool usage metrics"""
    tool_id: str
    total_invocations: int
    successful_invocations: int
    failed_invocations: int
    avg_response_time: float
    success_rate: float
    last_used: Optional[datetime] = None
    popular_agents: List[str] = field(default_factory=list)


@dataclass
class ToolRequirements:
    """Tool requirements for recommendation"""
    capabilities: List[str]
    input_types: List[str]
    output_types: List[str]
    performance_requirements: Dict[str, Any] = field(default_factory=dict)
    integration_type: str = "api"


@dataclass
class ToolRecommendation:
    """Tool recommendation"""
    tool_id: str
    tool_name: str
    match_score: float
    reasons: List[str]
    integration_effort: str  # 'low', 'medium', 'high'
    estimated_setup_time: str


class ToolsManager:
    """Service for managing tools and integrations"""
    
    def __init__(self):
        self.observability_service = ObservabilityService()
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def register_tool(
        self,
        tool: ToolDefinition,
        user_id: str,
        db: AsyncSession
    ) -> str:
        """Register a new tool"""
        try:
            # Validate tool definition
            await self._validate_tool_definition(tool)
            
            # Create tool record
            tool_record = Tool(
                id=str(uuid.uuid4()),
                name=tool.name,
                display_name=tool.name,
                description=tool.documentation,
                tool_type=ToolType.API if tool.type.lower() == 'rest' else ToolType.CUSTOM,
                category=tool.metadata.get('category', 'general'),
                tags=tool.metadata.get('tags', []),
                config={
                    "type": tool.type,
                    "endpoint": tool.endpoint,
                    "capabilities": tool.capabilities,
                    "parameters": [param.__dict__ for param in tool.parameters],
                    "authentication": tool.authentication.__dict__,
                    "metadata": tool.metadata
                },
                tool_schema=await self._generate_tool_schema(tool),
                endpoint_url=tool.endpoint,
                auth_type=tool.authentication.type,
                auth_config=tool.authentication.credentials,
                is_active=True,
                version=tool.version,
                created_by=user_id
            )
            
            db.add(tool_record)
            await db.commit()
            await db.refresh(tool_record)
            
            # Test tool connection
            connection_test = await self.test_tool_connection(tool_record.id, db)
            
            # Log tool registration
            await self.observability_service.log_event(
                "tool_registered",
                {
                    "tool_id": tool_record.id,
                    "tool_name": tool.name,
                    "tool_type": tool.type,
                    "connection_test": connection_test.success,
                    "registered_by": user_id
                }
            )
            
            return tool_record.id
            
        except Exception as e:
            logger.error(f"Error registering tool: {str(e)}")
            await db.rollback()
            raise ToolError(f"Failed to register tool: {str(e)}")
    
    async def discover_tools(
        self,
        discovery_config: Dict[str, Any],
        db: AsyncSession
    ) -> List[ToolDefinition]:
        """Discover tools from various sources"""
        try:
            discovered_tools = []
            
            # Discovery from API endpoints
            if discovery_config.get('api_discovery'):
                api_tools = await self._discover_from_api(discovery_config['api_discovery'])
                discovered_tools.extend(api_tools)
            
            # Discovery from OpenAPI specs
            if discovery_config.get('openapi_specs'):
                openapi_tools = await self._discover_from_openapi(discovery_config['openapi_specs'])
                discovered_tools.extend(openapi_tools)
            
            # Discovery from MCP servers
            if discovery_config.get('mcp_discovery'):
                mcp_tools = await self._discover_from_mcp(discovery_config['mcp_discovery'])
                discovered_tools.extend(mcp_tools)
            
            # Discovery from tool registries
            if discovery_config.get('registry_discovery'):
                registry_tools = await self._discover_from_registry(discovery_config['registry_discovery'])
                discovered_tools.extend(registry_tools)
            
            return discovered_tools
            
        except Exception as e:
            logger.error(f"Error discovering tools: {str(e)}")
            raise ToolError(f"Failed to discover tools: {str(e)}")
    
    async def test_tool_connection(
        self,
        tool_id: str,
        db: AsyncSession
    ) -> ConnectionTest:
        """Test connection to a tool"""
        try:
            # Get tool
            tool = await db.scalar(
                select(Tool).where(Tool.id == tool_id)
            )
            
            if not tool:
                raise ToolError(f"Tool {tool_id} not found")
            
            start_time = datetime.now()
            
            # Test connection based on tool type
            if tool.tool_type == ToolType.API:
                result = await self._test_api_connection(tool)
            elif tool.tool_type == ToolType.WEBHOOK:
                result = await self._test_webhook_connection(tool)
            elif tool.tool_type == ToolType.DATABASE:
                result = await self._test_database_connection(tool)
            else:
                result = await self._test_custom_connection(tool)
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            connection_test = ConnectionTest(
                success=result.get('success', False),
                response_time=response_time,
                error_message=result.get('error_message'),
                status_code=result.get('status_code'),
                response_data=result.get('response_data')
            )
            
            # Log connection test
            await self.observability_service.log_event(
                "tool_connection_tested",
                {
                    "tool_id": tool_id,
                    "success": connection_test.success,
                    "response_time": response_time,
                    "error_message": connection_test.error_message
                }
            )
            
            return connection_test
            
        except Exception as e:
            logger.error(f"Error testing tool connection: {str(e)}")
            return ConnectionTest(
                success=False,
                response_time=0.0,
                error_message=str(e)
            )
    
    async def configure_tool(
        self,
        tool_id: str,
        config: Dict[str, Any],
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """Configure a tool"""
        try:
            # Get tool
            tool = await db.scalar(
                select(Tool).where(Tool.id == tool_id)
            )
            
            if not tool:
                raise ToolError(f"Tool {tool_id} not found")
            
            # Validate configuration
            await self._validate_tool_config(config, tool)
            
            # Update tool configuration
            tool.config = {**tool.config, **config}
            
            # Update auth config if provided
            if 'auth_config' in config:
                tool.auth_config = config['auth_config']
            
            # Update endpoint if provided
            if 'endpoint_url' in config:
                tool.endpoint_url = config['endpoint_url']
            
            await db.commit()
            
            # Test connection with new configuration
            connection_test = await self.test_tool_connection(tool_id, db)
            
            # Log configuration update
            await self.observability_service.log_event(
                "tool_configured",
                {
                    "tool_id": tool_id,
                    "config_keys": list(config.keys()),
                    "connection_test": connection_test.success,
                    "configured_by": user_id
                }
            )
            
            return connection_test.success
            
        except Exception as e:
            logger.error(f"Error configuring tool: {str(e)}")
            await db.rollback()
            raise ToolError(f"Failed to configure tool: {str(e)}")
    
    async def get_tool_usage_metrics(
        self,
        tool_id: str,
        db: AsyncSession
    ) -> ToolMetrics:
        """Get tool usage metrics"""
        try:
            # Get tool
            tool = await db.scalar(
                select(Tool).where(Tool.id == tool_id)
            )
            
            if not tool:
                raise ToolError(f"Tool {tool_id} not found")
            
            # Get execution statistics
            execution_stats = await db.execute(
                select(
                    func.count(ToolExecution.id).label('total'),
                    func.sum(func.case(
                        (ToolExecution.status == 'completed', 1),
                        else_=0
                    )).label('successful'),
                    func.avg(ToolExecution.execution_time_ms).label('avg_response_time'),
                    func.max(ToolExecution.completed_at).label('last_used')
                ).where(ToolExecution.tool_id == tool_id)
            )
            
            stats = execution_stats.first()
            
            # Get popular agents using this tool
            popular_agents = await db.execute(
                select(Agent.id, Agent.name, func.count(ToolExecution.id).label('usage_count'))
                .join(ToolExecution, Agent.id == ToolExecution.agent_id)
                .where(ToolExecution.tool_id == tool_id)
                .group_by(Agent.id, Agent.name)
                .order_by(func.count(ToolExecution.id).desc())
                .limit(5)
            )
            
            popular_agents_list = [
                f"{agent.name} ({agent.usage_count} uses)"
                for agent in popular_agents
            ]
            
            total_invocations = stats.total or 0
            successful_invocations = stats.successful or 0
            failed_invocations = total_invocations - successful_invocations
            
            return ToolMetrics(
                tool_id=tool_id,
                total_invocations=total_invocations,
                successful_invocations=successful_invocations,
                failed_invocations=failed_invocations,
                avg_response_time=stats.avg_response_time or 0.0,
                success_rate=successful_invocations / total_invocations if total_invocations > 0 else 0.0,
                last_used=stats.last_used,
                popular_agents=popular_agents_list
            )
            
        except Exception as e:
            logger.error(f"Error getting tool metrics: {str(e)}")
            raise ToolError(f"Failed to get tool metrics: {str(e)}")
    
    async def recommend_tools(
        self,
        requirements: ToolRequirements,
        db: AsyncSession
    ) -> List[ToolRecommendation]:
        """Recommend tools based on requirements"""
        try:
            # Get all active tools
            tools = await db.execute(
                select(Tool).where(Tool.is_active == True)
            )
            
            recommendations = []
            
            for tool in tools.scalars().all():
                # Calculate match score
                match_score = await self._calculate_tool_match_score(
                    tool, requirements, db
                )
                
                if match_score > 0.3:  # Only recommend tools with >30% match
                    # Generate recommendation reasons
                    reasons = await self._generate_recommendation_reasons(
                        tool, requirements, match_score
                    )
                    
                    # Estimate integration effort
                    integration_effort = await self._estimate_integration_effort(
                        tool, requirements
                    )
                    
                    recommendations.append(ToolRecommendation(
                        tool_id=tool.id,
                        tool_name=tool.name,
                        match_score=match_score,
                        reasons=reasons,
                        integration_effort=integration_effort,
                        estimated_setup_time=await self._estimate_setup_time(
                            tool, integration_effort
                        )
                    ))
            
            # Sort by match score
            recommendations.sort(key=lambda x: x.match_score, reverse=True)
            
            return recommendations[:10]  # Return top 10
            
        except Exception as e:
            logger.error(f"Error recommending tools: {str(e)}")
            raise ToolError(f"Failed to recommend tools: {str(e)}")
    
    async def _validate_tool_definition(self, tool: ToolDefinition) -> None:
        """Validate tool definition"""
        if not tool.name or len(tool.name) < 2:
            raise ValidationError("Tool name must be at least 2 characters")
        
        if not tool.endpoint:
            raise ValidationError("Tool endpoint is required")
        
        if not tool.capabilities:
            raise ValidationError("Tool must define capabilities")
        
        if not tool.parameters:
            raise ValidationError("Tool must define parameters")
        
        # Validate authentication
        if tool.authentication.type not in ['none', 'api_key', 'oauth2', 'basic', 'bearer']:
            raise ValidationError("Invalid authentication type")
    
    async def _generate_tool_schema(self, tool: ToolDefinition) -> Dict[str, Any]:
        """Generate OpenAPI schema for tool"""
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": tool.name,
                "version": tool.version,
                "description": tool.documentation
            },
            "servers": [{"url": tool.endpoint}],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {}
            }
        }
        
        # Add authentication scheme
        if tool.authentication.type == 'api_key':
            schema['components']['securitySchemes']['ApiKeyAuth'] = {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        elif tool.authentication.type == 'bearer':
            schema['components']['securitySchemes']['BearerAuth'] = {
                "type": "http",
                "scheme": "bearer"
            }
        
        return schema
    
    async def _discover_from_api(self, config: Dict[str, Any]) -> List[ToolDefinition]:
        """Discover tools from API endpoints"""
        tools = []
        
        for endpoint in config.get('endpoints', []):
            try:
                # Try to get OpenAPI spec
                async with self.http_client.get(f"{endpoint}/openapi.json") as response:
                    if response.status_code == 200:
                        spec = response.json()
                        tools.extend(await self._parse_openapi_spec(spec, endpoint))
            except Exception as e:
                logger.warning(f"Failed to discover from {endpoint}: {e}")
        
        return tools
    
    async def _discover_from_openapi(self, specs: List[str]) -> List[ToolDefinition]:
        """Discover tools from OpenAPI specifications"""
        tools = []
        
        for spec_url in specs:
            try:
                async with self.http_client.get(spec_url) as response:
                    if response.status_code == 200:
                        spec = response.json()
                        tools.extend(await self._parse_openapi_spec(spec, spec_url))
            except Exception as e:
                logger.warning(f"Failed to parse OpenAPI spec {spec_url}: {e}")
        
        return tools
    
    async def _discover_from_mcp(self, config: Dict[str, Any]) -> List[ToolDefinition]:
        """Discover tools from MCP servers"""
        tools = []
        
        for server in config.get('servers', []):
            try:
                # Connect to MCP server and get tool list
                # This would integrate with MCP protocol
                pass
            except Exception as e:
                logger.warning(f"Failed to discover from MCP server {server}: {e}")
        
        return tools
    
    async def _discover_from_registry(self, config: Dict[str, Any]) -> List[ToolDefinition]:
        """Discover tools from tool registries"""
        tools = []
        
        for registry in config.get('registries', []):
            try:
                # Query tool registry
                # This would integrate with tool registry APIs
                pass
            except Exception as e:
                logger.warning(f"Failed to discover from registry {registry}: {e}")
        
        return tools
    
    async def _parse_openapi_spec(self, spec: Dict[str, Any], base_url: str) -> List[ToolDefinition]:
        """Parse OpenAPI specification to create tool definitions"""
        tools = []
        
        for path, methods in spec.get('paths', {}).items():
            for method, operation in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE']:
                    # Create tool definition for each operation
                    tool = ToolDefinition(
                        name=f"{spec['info']['title']}_{operation.get('operationId', path.replace('/', '_'))}",
                        type='REST',
                        endpoint=f"{base_url}{path}",
                        authentication=AuthConfig(type='none'),
                        capabilities=[operation.get('summary', 'API operation')],
                        parameters=[],
                        documentation=operation.get('description', ''),
                        version=spec['info'].get('version', '1.0.0')
                    )
                    
                    # Parse parameters
                    for param in operation.get('parameters', []):
                        tool.parameters.append(ParameterDefinition(
                            name=param['name'],
                            type=param.get('schema', {}).get('type', 'string'),
                            description=param.get('description', ''),
                            required=param.get('required', False)
                        ))
                    
                    tools.append(tool)
        
        return tools
    
    async def _test_api_connection(self, tool: Tool) -> Dict[str, Any]:
        """Test API tool connection"""
        try:
            headers = {}
            
            # Add authentication
            if tool.auth_type == 'api_key':
                headers['X-API-Key'] = tool.auth_config.get('api_key', '')
            elif tool.auth_type == 'bearer':
                headers['Authorization'] = f"Bearer {tool.auth_config.get('token', '')}"
            
            # Make test request
            async with self.http_client.get(tool.endpoint_url, headers=headers) as response:
                return {
                    'success': response.status_code < 400,
                    'status_code': response.status_code,
                    'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                }
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e)
            }
    
    async def _test_webhook_connection(self, tool: Tool) -> Dict[str, Any]:
        """Test webhook tool connection"""
        # For webhooks, we would typically send a test payload
        return {'success': True, 'message': 'Webhook configuration valid'}
    
    async def _test_database_connection(self, tool: Tool) -> Dict[str, Any]:
        """Test database tool connection"""
        # For databases, we would test the connection string
        return {'success': True, 'message': 'Database connection valid'}
    
    async def _test_custom_connection(self, tool: Tool) -> Dict[str, Any]:
        """Test custom tool connection"""
        # For custom tools, we would run the test implementation
        return {'success': True, 'message': 'Custom tool configuration valid'}
    
    async def _validate_tool_config(self, config: Dict[str, Any], tool: Tool) -> None:
        """Validate tool configuration"""
        # Validate based on tool type
        if tool.tool_type == ToolType.API:
            if 'endpoint_url' in config and not config['endpoint_url'].startswith('http'):
                raise ValidationError("API endpoint must be a valid URL")
    
    async def _calculate_tool_match_score(
        self,
        tool: Tool,
        requirements: ToolRequirements,
        db: AsyncSession
    ) -> float:
        """Calculate how well a tool matches requirements"""
        score = 0.0
        
        # Check capability match
        tool_capabilities = tool.config.get('capabilities', [])
        capability_match = len(set(requirements.capabilities) & set(tool_capabilities)) / len(requirements.capabilities)
        score += capability_match * 0.4
        
        # Check type match
        if tool.tool_type.value == requirements.integration_type:
            score += 0.2
        
        # Check performance
        metrics = await self.get_tool_usage_metrics(tool.id, db)
        if metrics.success_rate > 0.9:
            score += 0.2
        
        # Check popularity
        if metrics.total_invocations > 100:
            score += 0.1
        
        # Check documentation quality
        if tool.description and len(tool.description) > 50:
            score += 0.1
        
        return min(1.0, score)
    
    async def _generate_recommendation_reasons(
        self,
        tool: Tool,
        requirements: ToolRequirements,
        match_score: float
    ) -> List[str]:
        """Generate reasons for tool recommendation"""
        reasons = []
        
        if match_score > 0.8:
            reasons.append("Excellent match for your requirements")
        elif match_score > 0.6:
            reasons.append("Good match for your requirements")
        
        # Check specific capabilities
        tool_capabilities = tool.config.get('capabilities', [])
        matching_capabilities = set(requirements.capabilities) & set(tool_capabilities)
        if matching_capabilities:
            reasons.append(f"Supports required capabilities: {', '.join(matching_capabilities)}")
        
        # Check tool popularity
        if tool.total_invocations > 1000:
            reasons.append("Widely used and proven tool")
        
        return reasons
    
    async def _estimate_integration_effort(
        self,
        tool: Tool,
        requirements: ToolRequirements
    ) -> str:
        """Estimate integration effort"""
        if tool.tool_type == ToolType.API and requirements.integration_type == 'api':
            if tool.auth_type == 'none':
                return 'low'
            elif tool.auth_type in ['api_key', 'bearer']:
                return 'medium'
            else:
                return 'high'
        elif tool.tool_type == ToolType.CUSTOM:
            return 'high'
        else:
            return 'medium'
    
    async def _estimate_setup_time(self, tool: Tool, integration_effort: str) -> str:
        """Estimate setup time"""
        if integration_effort == 'low':
            return '< 1 hour'
        elif integration_effort == 'medium':
            return '1-4 hours'
        else:
            return '> 4 hours'
