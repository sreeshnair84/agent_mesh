"""
Agent Registry UI Backend Service
Service for managing agent registry user interface operations
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict

from app.core.database import get_db
from app.models.agent import Agent, AgentStatus, AgentVersion, AgentMetric
from app.models.user import User
from app.schemas.agent import AgentResponse
from app.services.agent_health_monitor import AgentHealthMonitor
from app.services.agent_deployment import AgentDeploymentManager
from app.core.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)


@dataclass
class AgentRegistryStats:
    """Statistics for agent registry dashboard"""
    total_agents: int
    active_agents: int
    inactive_agents: int
    total_deployments: int
    successful_deployments: int
    failed_deployments: int
    average_response_time: float
    total_users: int
    recent_activity: List[Dict[str, Any]]


@dataclass
class AgentRegistryFilter:
    """Filter options for agent registry"""
    search: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_published: Optional[bool] = None
    is_private: Optional[bool] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 20


@dataclass
class AgentRegistryItem:
    """Agent registry item with extended information"""
    id: int
    name: str
    description: str
    category: str
    status: str
    version: str
    user_id: int
    user_name: str
    created_at: datetime
    updated_at: datetime
    is_published: bool
    is_private: bool
    deployment_count: int
    last_deployment: Optional[datetime]
    health_status: str
    response_time: float
    usage_count: int
    rating: float
    tags: List[str]


class AgentRegistryUIBackend:
    """
    Backend service for agent registry UI operations
    Provides data and functionality for the agent registry interface
    """

    def __init__(self, db: Session):
        self.db = db
        self.health_monitor = AgentHealthMonitor(db)
        self.deployment_manager = AgentDeploymentManager(db)

    async def get_registry_stats(self) -> AgentRegistryStats:
        """
        Get comprehensive statistics for the agent registry dashboard
        """
        try:
            # Agent statistics
            total_agents = self.db.query(Agent).count()
            active_agents = self.db.query(Agent).filter(
                Agent.status == AgentStatus.RUNNING
            ).count()
            inactive_agents = total_agents - active_agents

            # Deployment statistics
            deployment_stats = await self._get_deployment_stats()
            
            # Performance statistics
            avg_response_time = await self._get_average_response_time()
            
            # User statistics
            total_users = self.db.query(User).count()
            
            # Recent activity
            recent_activity = await self._get_recent_activity()

            return AgentRegistryStats(
                total_agents=total_agents,
                active_agents=active_agents,
                inactive_agents=inactive_agents,
                total_deployments=deployment_stats["total"],
                successful_deployments=deployment_stats["successful"],
                failed_deployments=deployment_stats["failed"],
                average_response_time=avg_response_time,
                total_users=total_users,
                recent_activity=recent_activity
            )

        except Exception as e:
            logger.error(f"Error getting registry stats: {e}")
            raise

    async def get_registry_agents(
        self, 
        filters: AgentRegistryFilter,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get filtered and paginated list of agents for the registry
        """
        try:
            query = self.db.query(Agent).join(User, Agent.user_id == User.id)

            # Apply filters
            if filters.search:
                query = query.filter(
                    Agent.name.ilike(f"%{filters.search}%") |
                    Agent.description.ilike(f"%{filters.search}%")
                )

            if filters.category:
                query = query.filter(Agent.category == filters.category)

            if filters.status:
                query = query.filter(Agent.status == filters.status)

            if filters.user_id:
                query = query.filter(Agent.user_id == filters.user_id)

            if filters.is_published is not None:
                query = query.filter(Agent.is_published == filters.is_published)

            if filters.is_private is not None:
                query = query.filter(Agent.is_private == filters.is_private)

            if filters.date_from:
                query = query.filter(Agent.created_at >= filters.date_from)

            if filters.date_to:
                query = query.filter(Agent.created_at <= filters.date_to)

            # Privacy filter - only show public agents unless it's the owner
            if current_user_id:
                query = query.filter(
                    (Agent.is_private == False) | (Agent.user_id == current_user_id)
                )
            else:
                query = query.filter(Agent.is_private == False)

            # Get total count before pagination
            total_count = query.count()

            # Apply sorting
            if filters.sort_by == "name":
                order_col = Agent.name
            elif filters.sort_by == "created_at":
                order_col = Agent.created_at
            elif filters.sort_by == "updated_at":
                order_col = Agent.updated_at
            elif filters.sort_by == "category":
                order_col = Agent.category
            elif filters.sort_by == "status":
                order_col = Agent.status
            else:
                order_col = Agent.created_at

            if filters.sort_order == "desc":
                query = query.order_by(order_col.desc())
            else:
                query = query.order_by(order_col.asc())

            # Apply pagination
            offset = (filters.page - 1) * filters.page_size
            agents = query.offset(offset).limit(filters.page_size).all()

            # Enrich agents with additional data
            registry_items = []
            for agent in agents:
                item = await self._create_registry_item(agent)
                registry_items.append(item)

            return {
                "items": registry_items,
                "total_count": total_count,
                "page": filters.page,
                "page_size": filters.page_size,
                "total_pages": (total_count + filters.page_size - 1) // filters.page_size
            }

        except Exception as e:
            logger.error(f"Error getting registry agents: {e}")
            raise

    async def get_agent_details(self, agent_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific agent for the registry
        """
        try:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise NotFoundError(f"Agent {agent_id} not found")

            # Get registry item
            registry_item = await self._create_registry_item(agent)

            # Get additional details
            deployment_history = await self._get_deployment_history(agent_id)
            version_history = await self._get_version_history(agent_id)
            performance_metrics = await self._get_performance_metrics(agent_id)
            usage_analytics = await self._get_usage_analytics(agent_id)

            return {
                "agent": asdict(registry_item),
                "deployment_history": deployment_history,
                "version_history": version_history,
                "performance_metrics": performance_metrics,
                "usage_analytics": usage_analytics
            }

        except Exception as e:
            logger.error(f"Error getting agent details: {e}")
            raise

    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get all available agent categories with counts
        """
        try:
            categories = self.db.query(
                Agent.category,
                self.db.func.count(Agent.id).label("count")
            ).group_by(Agent.category).all()

            return [
                {
                    "name": category,
                    "count": count,
                    "description": self._get_category_description(category)
                }
                for category, count in categories
            ]

        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            raise

    async def get_user_agents(self, user_id: int) -> List[AgentRegistryItem]:
        """
        Get all agents for a specific user
        """
        try:
            agents = self.db.query(Agent).filter(Agent.user_id == user_id).all()
            
            registry_items = []
            for agent in agents:
                item = await self._create_registry_item(agent)
                registry_items.append(item)

            return registry_items

        except Exception as e:
            logger.error(f"Error getting user agents: {e}")
            raise

    async def search_agents(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[AgentRegistryItem]:
        """
        Search agents by name, description, or tags
        """
        try:
            agents = self.db.query(Agent).filter(
                Agent.name.ilike(f"%{query}%") |
                Agent.description.ilike(f"%{query}%")
            ).filter(Agent.is_private == False).limit(limit).all()

            registry_items = []
            for agent in agents:
                item = await self._create_registry_item(agent)
                registry_items.append(item)

            return registry_items

        except Exception as e:
            logger.error(f"Error searching agents: {e}")
            raise

    async def get_trending_agents(self, limit: int = 10) -> List[AgentRegistryItem]:
        """
        Get trending agents based on usage and ratings
        """
        try:
            # Get agents with high usage in the last week
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            
            agents = self.db.query(Agent).filter(
                Agent.updated_at >= one_week_ago,
                Agent.is_private == False
            ).order_by(Agent.updated_at.desc()).limit(limit).all()

            registry_items = []
            for agent in agents:
                item = await self._create_registry_item(agent)
                registry_items.append(item)

            return registry_items

        except Exception as e:
            logger.error(f"Error getting trending agents: {e}")
            raise

    async def get_featured_agents(self, limit: int = 5) -> List[AgentRegistryItem]:
        """
        Get featured agents for the registry homepage
        """
        try:
            # Get published agents with good ratings
            agents = self.db.query(Agent).filter(
                Agent.is_published == True,
                Agent.is_private == False
            ).order_by(Agent.created_at.desc()).limit(limit).all()

            registry_items = []
            for agent in agents:
                item = await self._create_registry_item(agent)
                registry_items.append(item)

            return registry_items

        except Exception as e:
            logger.error(f"Error getting featured agents: {e}")
            raise

    async def _create_registry_item(self, agent: Agent) -> AgentRegistryItem:
        """
        Create a registry item with enriched data
        """
        try:
            # Get user information
            user = self.db.query(User).filter(User.id == agent.user_id).first()
            user_name = user.username if user else "Unknown"

            # Get deployment count
            deployment_count = await self._get_deployment_count(agent.id)
            
            # Get last deployment
            last_deployment = await self._get_last_deployment(agent.id)
            
            # Get health status
            health_status = await self._get_agent_health_status(agent.id)
            
            # Get response time
            response_time = await self._get_agent_response_time(agent.id)
            
            # Get usage count
            usage_count = await self._get_usage_count(agent.id)
            
            # Get rating (placeholder)
            rating = 4.5  # This would come from actual ratings

            # Get tags (placeholder)
            tags = ["ai", "assistant"]  # This would come from actual tags

            return AgentRegistryItem(
                id=agent.id,
                name=agent.name,
                description=agent.description or "",
                category=agent.category or "General",
                status=agent.status.value if agent.status else "unknown",
                version=agent.version or "1.0.0",
                user_id=agent.user_id,
                user_name=user_name,
                created_at=agent.created_at,
                updated_at=agent.updated_at,
                is_published=agent.is_published or False,
                is_private=agent.is_private or False,
                deployment_count=deployment_count,
                last_deployment=last_deployment,
                health_status=health_status,
                response_time=response_time,
                usage_count=usage_count,
                rating=rating,
                tags=tags
            )

        except Exception as e:
            logger.error(f"Error creating registry item: {e}")
            raise

    async def _get_deployment_stats(self) -> Dict[str, int]:
        """Get deployment statistics"""
        # This would query actual deployment records
        return {
            "total": 150,
            "successful": 142,
            "failed": 8
        }

    async def _get_average_response_time(self) -> float:
        """Get average response time across all agents"""
        # This would query actual metrics
        return 250.5

    async def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent activity for the dashboard"""
        # This would query actual activity logs
        return [
            {
                "type": "agent_created",
                "message": "New agent 'Customer Support Bot' created",
                "timestamp": datetime.utcnow() - timedelta(hours=2),
                "user": "john_doe"
            },
            {
                "type": "agent_deployed",
                "message": "Agent 'Data Analyst' deployed to production",
                "timestamp": datetime.utcnow() - timedelta(hours=4),
                "user": "jane_smith"
            }
        ]

    async def _get_deployment_count(self, agent_id: int) -> int:
        """Get deployment count for an agent"""
        # This would query actual deployment records
        return 5

    async def _get_last_deployment(self, agent_id: int) -> Optional[datetime]:
        """Get last deployment timestamp for an agent"""
        # This would query actual deployment records
        return datetime.utcnow() - timedelta(days=2)

    async def _get_agent_health_status(self, agent_id: int) -> str:
        """Get health status for an agent"""
        try:
            health_check = await self.health_monitor.check_agent_health(agent_id)
            return health_check.status if health_check else "unknown"
        except:
            return "unknown"

    async def _get_agent_response_time(self, agent_id: int) -> float:
        """Get response time for an agent"""
        try:
            metrics = await self.health_monitor.get_agent_metrics(agent_id, 1)
            return metrics.get("response_time", 0.0) if metrics else 0.0
        except:
            return 0.0

    async def _get_usage_count(self, agent_id: int) -> int:
        """Get usage count for an agent"""
        # This would query actual usage records
        return 42

    async def _get_deployment_history(self, agent_id: int) -> List[Dict[str, Any]]:
        """Get deployment history for an agent"""
        # This would query actual deployment records
        return [
            {
                "version": "1.0.0",
                "environment": "production",
                "status": "success",
                "deployed_at": datetime.utcnow() - timedelta(days=2),
                "deployed_by": "john_doe"
            }
        ]

    async def _get_version_history(self, agent_id: int) -> List[Dict[str, Any]]:
        """Get version history for an agent"""
        versions = self.db.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id
        ).order_by(AgentVersion.created_at.desc()).all()

        return [
            {
                "version": v.version,
                "description": v.description,
                "created_at": v.created_at,
                "is_current": v.is_current
            }
            for v in versions
        ]

    async def _get_performance_metrics(self, agent_id: int) -> Dict[str, Any]:
        """Get performance metrics for an agent"""
        # This would query actual metrics
        return {
            "response_time": 250.5,
            "success_rate": 98.5,
            "error_rate": 1.5,
            "throughput": 1000
        }

    async def _get_usage_analytics(self, agent_id: int) -> Dict[str, Any]:
        """Get usage analytics for an agent"""
        # This would query actual usage analytics
        return {
            "total_requests": 1000,
            "unique_users": 50,
            "requests_per_day": [10, 15, 20, 25, 30, 35, 40],
            "popular_actions": ["chat", "analyze", "report"]
        }

    def _get_category_description(self, category: str) -> str:
        """Get description for a category"""
        descriptions = {
            "Assistant": "General purpose assistants",
            "Analysis": "Data analysis and reporting",
            "Customer Support": "Customer service agents",
            "Research": "Research and information gathering",
            "Creative": "Creative content generation",
            "Technical": "Technical support and coding",
            "Education": "Educational and tutoring",
            "Sales": "Sales and marketing support"
        }
        return descriptions.get(category, "Custom agent category")


# Usage example and factory function
def create_registry_ui_backend(db: Session) -> AgentRegistryUIBackend:
    """
    Factory function to create an AgentRegistryUIBackend instance
    """
    return AgentRegistryUIBackend(db)
