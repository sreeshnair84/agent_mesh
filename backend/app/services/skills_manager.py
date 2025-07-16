"""
Skills Manager Service
Handles skill management, discovery, and performance analytics
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.master_data import Skill
from app.models.agent import Agent
from app.models.user import User
from app.schemas.agent import SkillCreate, SkillUpdate, SkillResponse
from app.services.observability_service import ObservabilityService
from app.core.exceptions import ValidationError
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class SkillExample:
    """Example of skill usage"""
    input: Dict[str, Any]
    output: Dict[str, Any]
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillDefinition:
    """Complete skill definition with metadata"""
    name: str
    description: str
    category: str
    input_types: List[str]
    output_types: List[str]
    prerequisites: List[str]
    examples: List[SkillExample]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillRelationships:
    """Skill relationships and dependencies"""
    prerequisites: List[str]
    depends_on: List[str]
    enables: List[str]
    conflicts_with: List[str]
    complements: List[str]


@dataclass
class SkillAnalytics:
    """Skill performance analytics"""
    skill_id: str
    usage_count: int
    success_rate: float
    avg_execution_time: float
    performance_score: float
    agent_adoption_rate: float
    recent_trends: Dict[str, Any]
    recommendations: List[str]


class SkillsManager:
    """Service for managing skills and their capabilities"""
    
    def __init__(self):
        self.observability_service = ObservabilityService()
    
    async def create_skill(
        self,
        skill: SkillDefinition,
        user_id: str,
        db: AsyncSession
    ) -> str:
        """Create a new skill"""
        try:
            # Validate skill definition
            await self._validate_skill_definition(skill)
            
            # Create skill record
            skill_record = Skill(
                id=str(uuid.uuid4()),
                name=skill.name,
                description=skill.description,
                category=skill.category,
                config={
                    "input_types": skill.input_types,
                    "output_types": skill.output_types,
                    "prerequisites": skill.prerequisites,
                    "examples": [example.__dict__ for example in skill.examples],
                    "metadata": skill.metadata
                }
            )
            
            db.add(skill_record)
            await db.commit()
            await db.refresh(skill_record)
            
            # Log skill creation
            await self.observability_service.log_event(
                "skill_created",
                {
                    "skill_id": skill_record.id,
                    "skill_name": skill.name,
                    "category": skill.category,
                    "created_by": user_id
                }
            )
            
            return skill_record.id
            
        except Exception as e:
            logger.error(f"Error creating skill: {str(e)}")
            await db.rollback()
            raise ValidationError(f"Failed to create skill: {str(e)}")
    
    async def update_skill(
        self,
        skill_id: str,
        updates: Dict[str, Any],
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """Update an existing skill"""
        try:
            # Get existing skill
            skill = await db.scalar(
                select(Skill).where(Skill.id == skill_id)
            )
            
            if not skill:
                raise ValidationError(f"Skill {skill_id} not found")
            
            # Update skill fields
            for field, value in updates.items():
                if hasattr(skill, field):
                    setattr(skill, field, value)
            
            await db.commit()
            
            # Log skill update
            await self.observability_service.log_event(
                "skill_updated",
                {
                    "skill_id": skill_id,
                    "updated_fields": list(updates.keys()),
                    "updated_by": user_id
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating skill: {str(e)}")
            await db.rollback()
            raise ValidationError(f"Failed to update skill: {str(e)}")
    
    async def search_skills(
        self,
        query: str,
        filters: Dict[str, Any],
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ) -> List[Skill]:
        """Search for skills with filters"""
        try:
            # Build query
            stmt = select(Skill)
            
            # Apply search query
            if query:
                stmt = stmt.where(
                    or_(
                        Skill.name.ilike(f"%{query}%"),
                        Skill.description.ilike(f"%{query}%")
                    )
                )
            
            # Apply filters
            if filters.get('category'):
                stmt = stmt.where(Skill.category == filters['category'])
            
            if filters.get('prerequisites'):
                for prereq in filters['prerequisites']:
                    stmt = stmt.where(
                        Skill.config['prerequisites'].astext.contains(prereq)
                    )
            
            if filters.get('input_types'):
                for input_type in filters['input_types']:
                    stmt = stmt.where(
                        Skill.config['input_types'].astext.contains(input_type)
                    )
            
            if filters.get('output_types'):
                for output_type in filters['output_types']:
                    stmt = stmt.where(
                        Skill.config['output_types'].astext.contains(output_type)
                    )
            
            # Apply pagination
            stmt = stmt.limit(limit).offset(offset)
            
            # Execute query
            result = await db.execute(stmt)
            skills = result.scalars().all()
            
            return skills
            
        except Exception as e:
            logger.error(f"Error searching skills: {str(e)}")
            raise ValidationError(f"Failed to search skills: {str(e)}")
    
    async def get_skill_relationships(
        self,
        skill_id: str,
        db: AsyncSession
    ) -> SkillRelationships:
        """Get skill relationships and dependencies"""
        try:
            # Get skill
            skill = await db.scalar(
                select(Skill).where(Skill.id == skill_id)
            )
            
            if not skill:
                raise ValidationError(f"Skill {skill_id} not found")
            
            # Get prerequisites from skill config
            prerequisites = skill.config.get('prerequisites', [])
            
            # Find skills that depend on this skill
            depends_on_result = await db.execute(
                select(Skill).where(
                    Skill.config['prerequisites'].astext.contains(skill.name)
                )
            )
            depends_on = [s.id for s in depends_on_result.scalars().all()]
            
            # Find skills that this skill enables (based on output -> input matching)
            output_types = skill.config.get('output_types', [])
            enables_result = await db.execute(
                select(Skill).where(
                    and_(
                        Skill.id != skill_id,
                        *[Skill.config['input_types'].astext.contains(output_type) 
                          for output_type in output_types]
                    )
                )
            )
            enables = [s.id for s in enables_result.scalars().all()]
            
            # Find potential conflicts (skills with same output types)
            conflicts_result = await db.execute(
                select(Skill).where(
                    and_(
                        Skill.id != skill_id,
                        Skill.category == skill.category,
                        *[Skill.config['output_types'].astext.contains(output_type) 
                          for output_type in output_types]
                    )
                )
            )
            conflicts_with = [s.id for s in conflicts_result.scalars().all()]
            
            # Find complementary skills (same category, different capabilities)
            complements_result = await db.execute(
                select(Skill).where(
                    and_(
                        Skill.id != skill_id,
                        Skill.category == skill.category
                    )
                )
            )
            complements = [s.id for s in complements_result.scalars().all()]
            
            return SkillRelationships(
                prerequisites=prerequisites,
                depends_on=depends_on,
                enables=enables,
                conflicts_with=conflicts_with,
                complements=complements
            )
            
        except Exception as e:
            logger.error(f"Error getting skill relationships: {str(e)}")
            raise ValidationError(f"Failed to get skill relationships: {str(e)}")
    
    async def analyze_skill_performance(
        self,
        skill_id: str,
        db: AsyncSession
    ) -> SkillAnalytics:
        """Analyze skill performance and usage"""
        try:
            # Get skill
            skill = await db.scalar(
                select(Skill).where(Skill.id == skill_id)
            )
            
            if not skill:
                raise ValidationError(f"Skill {skill_id} not found")
            
            # Get agents using this skill
            agents_with_skill = await db.execute(
                select(Agent).where(
                    Agent.skills.any(id=skill_id)
                )
            )
            agents = agents_with_skill.scalars().all()
            
            # Calculate metrics
            usage_count = len(agents)
            
            # Get execution metrics from observability
            execution_metrics = await self._get_skill_execution_metrics(skill_id, db)
            
            # Calculate performance score
            performance_score = await self._calculate_performance_score(
                skill_id, execution_metrics, db
            )
            
            # Get recent trends
            recent_trends = await self._get_skill_trends(skill_id, db)
            
            # Generate recommendations
            recommendations = await self._generate_skill_recommendations(
                skill_id, skill, agents, db
            )
            
            return SkillAnalytics(
                skill_id=skill_id,
                usage_count=usage_count,
                success_rate=execution_metrics.get('success_rate', 0.0),
                avg_execution_time=execution_metrics.get('avg_execution_time', 0.0),
                performance_score=performance_score,
                agent_adoption_rate=execution_metrics.get('adoption_rate', 0.0),
                recent_trends=recent_trends,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error analyzing skill performance: {str(e)}")
            raise ValidationError(f"Failed to analyze skill performance: {str(e)}")
    
    async def _validate_skill_definition(self, skill: SkillDefinition) -> None:
        """Validate skill definition"""
        if not skill.name or len(skill.name) < 2:
            raise ValidationError("Skill name must be at least 2 characters")
        
        if not skill.description:
            raise ValidationError("Skill description is required")
        
        if not skill.category:
            raise ValidationError("Skill category is required")
        
        if not skill.input_types:
            raise ValidationError("Skill must define input types")
        
        if not skill.output_types:
            raise ValidationError("Skill must define output types")
        
        # Validate examples
        for example in skill.examples:
            if not example.input or not example.output:
                raise ValidationError("Skill examples must have input and output")
    
    async def _get_skill_execution_metrics(
        self,
        skill_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get skill execution metrics from observability data"""
        # This would typically query the observability service
        # For now, return mock data
        return {
            "success_rate": 0.95,
            "avg_execution_time": 150.0,
            "adoption_rate": 0.75,
            "total_executions": 1000
        }
    
    async def _calculate_performance_score(
        self,
        skill_id: str,
        execution_metrics: Dict[str, Any],
        db: AsyncSession
    ) -> float:
        """Calculate overall performance score for skill"""
        success_rate = execution_metrics.get('success_rate', 0.0)
        avg_execution_time = execution_metrics.get('avg_execution_time', 0.0)
        adoption_rate = execution_metrics.get('adoption_rate', 0.0)
        
        # Weighted scoring
        time_score = max(0, 1 - (avg_execution_time / 1000))  # Penalize slow execution
        
        performance_score = (
            success_rate * 0.4 +
            time_score * 0.3 +
            adoption_rate * 0.3
        )
        
        return min(1.0, max(0.0, performance_score))
    
    async def _get_skill_trends(
        self,
        skill_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get recent trends for skill usage"""
        # This would typically analyze time-series data
        # For now, return mock trends
        return {
            "usage_trend": "increasing",
            "performance_trend": "stable",
            "adoption_trend": "increasing",
            "weekly_usage": [10, 15, 12, 18, 20, 22, 25],
            "monthly_performance": [0.92, 0.94, 0.95, 0.96]
        }
    
    async def _generate_skill_recommendations(
        self,
        skill_id: str,
        skill: Skill,
        agents: List[Agent],
        db: AsyncSession
    ) -> List[str]:
        """Generate recommendations for skill improvement"""
        recommendations = []
        
        # Check usage patterns
        if len(agents) == 0:
            recommendations.append("Consider promoting this skill to increase adoption")
        elif len(agents) < 3:
            recommendations.append("Low adoption - consider improving documentation or examples")
        
        # Check skill relationships
        relationships = await self.get_skill_relationships(skill_id, db)
        if not relationships.prerequisites:
            recommendations.append("Consider adding prerequisites to improve skill clarity")
        
        # Performance-based recommendations
        if len(skill.config.get('examples', [])) < 3:
            recommendations.append("Add more examples to improve skill usability")
        
        return recommendations
