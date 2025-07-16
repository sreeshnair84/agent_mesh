"""
Capability Discovery Engine
Handles agent capability discovery, skill combinations, and recommendations
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.agent import Agent
from app.models.master_data import Skill, Tool
from app.models.user import User
from app.services.skills_manager import SkillsManager
from app.services.tools_manager import ToolsManager
from app.services.observability_service import ObservabilityService
from app.core.exceptions import ValidationError
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class Capability:
    """Agent capability definition"""
    id: str
    name: str
    description: str
    category: str
    input_types: List[str]
    output_types: List[str]
    confidence_score: float
    required_skills: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillCombination:
    """Recommended skill combination"""
    skills: List[str]
    combination_name: str
    description: str
    synergy_score: float
    expected_performance: Dict[str, Any]
    use_cases: List[str]
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class SkillGap:
    """Identified skill gap"""
    target_capability: str
    missing_skills: List[str]
    available_alternatives: List[str]
    impact_assessment: str
    recommendations: List[str]
    priority: str  # 'high', 'medium', 'low'


class CapabilityDiscovery:
    """Engine for discovering and analyzing agent capabilities"""
    
    def __init__(self):
        self.skills_manager = SkillsManager()
        self.tools_manager = ToolsManager()
        self.observability_service = ObservabilityService()
    
    async def discover_agent_capabilities(
        self,
        agent_id: str,
        db: AsyncSession
    ) -> List[Capability]:
        """Discover all capabilities of an agent"""
        try:
            # Get agent with relationships
            agent = await db.scalar(
                select(Agent)
                .options(
                    selectinload(Agent.skills),
                    selectinload(Agent.tools_assoc),
                    selectinload(Agent.constraints)
                )
                .where(Agent.id == agent_id)
            )
            
            if not agent:
                raise ValidationError(f"Agent {agent_id} not found")
            
            capabilities = []
            
            # Discover capabilities from skills
            skill_capabilities = await self._discover_from_skills(agent.skills, db)
            capabilities.extend(skill_capabilities)
            
            # Discover capabilities from tools
            tool_capabilities = await self._discover_from_tools(agent.tools_assoc, db)
            capabilities.extend(tool_capabilities)
            
            # Discover capabilities from configuration
            config_capabilities = await self._discover_from_config(agent, db)
            capabilities.extend(config_capabilities)
            
            # Discover emergent capabilities (skill + tool combinations)
            emergent_capabilities = await self._discover_emergent_capabilities(
                agent.skills, agent.tools_assoc, db
            )
            capabilities.extend(emergent_capabilities)
            
            # Remove duplicates and merge similar capabilities
            capabilities = await self._merge_capabilities(capabilities)
            
            # Calculate confidence scores
            for capability in capabilities:
                capability.confidence_score = await self._calculate_capability_confidence(
                    capability, agent, db
                )
            
            # Sort by confidence score
            capabilities.sort(key=lambda x: x.confidence_score, reverse=True)
            
            # Log capability discovery
            await self.observability_service.log_event(
                "capabilities_discovered",
                {
                    "agent_id": agent_id,
                    "capabilities_count": len(capabilities),
                    "high_confidence_count": len([c for c in capabilities if c.confidence_score > 0.8])
                }
            )
            
            return capabilities
            
        except Exception as e:
            logger.error(f"Error discovering agent capabilities: {str(e)}")
            raise ValidationError(f"Failed to discover capabilities: {str(e)}")
    
    async def suggest_skill_combinations(
        self,
        task_description: str,
        db: AsyncSession
    ) -> List[SkillCombination]:
        """Suggest skill combinations for a given task"""
        try:
            # Analyze task description to identify requirements
            task_requirements = await self._analyze_task_requirements(task_description)
            
            # Get relevant skills
            relevant_skills = await self.skills_manager.search_skills(
                task_description,
                {
                    'category': task_requirements.get('category'),
                    'input_types': task_requirements.get('input_types', []),
                    'output_types': task_requirements.get('output_types', [])
                },
                db
            )
            
            # Generate skill combinations
            combinations = await self._generate_skill_combinations(
                relevant_skills, task_requirements, db
            )
            
            # Score combinations
            for combination in combinations:
                combination.synergy_score = await self._calculate_synergy_score(
                    combination.skills, task_requirements, db
                )
            
            # Sort by synergy score
            combinations.sort(key=lambda x: x.synergy_score, reverse=True)
            
            # Log suggestion
            await self.observability_service.log_event(
                "skill_combinations_suggested",
                {
                    "task_description": task_description,
                    "combinations_count": len(combinations),
                    "top_synergy_score": combinations[0].synergy_score if combinations else 0
                }
            )
            
            return combinations[:10]  # Return top 10
            
        except Exception as e:
            logger.error(f"Error suggesting skill combinations: {str(e)}")
            raise ValidationError(f"Failed to suggest skill combinations: {str(e)}")
    
    async def identify_skill_gaps(
        self,
        target_capabilities: List[str],
        agent_id: Optional[str] = None,
        db: AsyncSession = None
    ) -> List[SkillGap]:
        """Identify skill gaps for target capabilities"""
        try:
            skill_gaps = []
            
            # Get current skills (if agent specified)
            current_skills = []
            if agent_id:
                agent = await db.scalar(
                    select(Agent)
                    .options(selectinload(Agent.skills))
                    .where(Agent.id == agent_id)
                )
                if agent:
                    current_skills = [skill.name for skill in agent.skills]
            
            # Analyze each target capability
            for capability in target_capabilities:
                # Find required skills for this capability
                required_skills = await self._find_required_skills(capability, db)
                
                # Identify missing skills
                missing_skills = [
                    skill for skill in required_skills 
                    if skill not in current_skills
                ]
                
                if missing_skills:
                    # Find alternatives
                    alternatives = await self._find_skill_alternatives(
                        missing_skills, capability, db
                    )
                    
                    # Assess impact
                    impact = await self._assess_gap_impact(
                        capability, missing_skills, db
                    )
                    
                    # Generate recommendations
                    recommendations = await self._generate_gap_recommendations(
                        capability, missing_skills, alternatives, db
                    )
                    
                    # Determine priority
                    priority = await self._determine_gap_priority(
                        capability, missing_skills, impact, db
                    )
                    
                    skill_gaps.append(SkillGap(
                        target_capability=capability,
                        missing_skills=missing_skills,
                        available_alternatives=alternatives,
                        impact_assessment=impact,
                        recommendations=recommendations,
                        priority=priority
                    ))
            
            # Sort by priority
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            skill_gaps.sort(key=lambda x: priority_order.get(x.priority, 0), reverse=True)
            
            # Log gap analysis
            await self.observability_service.log_event(
                "skill_gaps_identified",
                {
                    "agent_id": agent_id,
                    "target_capabilities": len(target_capabilities),
                    "gaps_found": len(skill_gaps),
                    "high_priority_gaps": len([g for g in skill_gaps if g.priority == 'high'])
                }
            )
            
            return skill_gaps
            
        except Exception as e:
            logger.error(f"Error identifying skill gaps: {str(e)}")
            raise ValidationError(f"Failed to identify skill gaps: {str(e)}")
    
    async def recommend_tools(
        self,
        requirements: Dict[str, Any],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Recommend tools based on requirements"""
        try:
            # Use tools manager for recommendations
            from app.services.tools_manager import ToolRequirements
            
            tool_requirements = ToolRequirements(
                capabilities=requirements.get('capabilities', []),
                input_types=requirements.get('input_types', []),
                output_types=requirements.get('output_types', []),
                performance_requirements=requirements.get('performance_requirements', {}),
                integration_type=requirements.get('integration_type', 'api')
            )
            
            recommendations = await self.tools_manager.recommend_tools(
                tool_requirements, db
            )
            
            # Enhance recommendations with capability insights
            enhanced_recommendations = []
            for rec in recommendations:
                # Get tool capabilities
                tool = await db.scalar(
                    select(Tool).where(Tool.id == rec.tool_id)
                )
                
                if tool:
                    # Analyze how this tool enhances agent capabilities
                    capability_enhancement = await self._analyze_tool_capability_enhancement(
                        tool, requirements, db
                    )
                    
                    enhanced_rec = {
                        'tool_id': rec.tool_id,
                        'tool_name': rec.tool_name,
                        'match_score': rec.match_score,
                        'reasons': rec.reasons,
                        'integration_effort': rec.integration_effort,
                        'estimated_setup_time': rec.estimated_setup_time,
                        'capability_enhancement': capability_enhancement
                    }
                    
                    enhanced_recommendations.append(enhanced_rec)
            
            return enhanced_recommendations
            
        except Exception as e:
            logger.error(f"Error recommending tools: {str(e)}")
            raise ValidationError(f"Failed to recommend tools: {str(e)}")
    
    async def _discover_from_skills(
        self,
        skills: List[Skill],
        db: AsyncSession
    ) -> List[Capability]:
        """Discover capabilities from agent skills"""
        capabilities = []
        
        for skill in skills:
            config = skill.config or {}
            
            capability = Capability(
                id=f"skill_{skill.id}",
                name=f"Skill: {skill.name}",
                description=skill.description or "",
                category=skill.category or "general",
                input_types=config.get('input_types', []),
                output_types=config.get('output_types', []),
                confidence_score=0.8,  # Will be calculated later
                required_skills=[skill.name],
                required_tools=[],
                performance_metrics={}
            )
            
            capabilities.append(capability)
        
        return capabilities
    
    async def _discover_from_tools(
        self,
        tools: List[Tool],
        db: AsyncSession
    ) -> List[Capability]:
        """Discover capabilities from agent tools"""
        capabilities = []
        
        for tool in tools:
            config = tool.config or {}
            tool_capabilities = config.get('capabilities', [])
            
            for cap_name in tool_capabilities:
                capability = Capability(
                    id=f"tool_{tool.id}_{cap_name}",
                    name=f"Tool: {cap_name}",
                    description=f"Capability provided by {tool.name}",
                    category=tool.category or "tool",
                    input_types=config.get('input_types', []),
                    output_types=config.get('output_types', []),
                    confidence_score=0.7,  # Will be calculated later
                    required_skills=[],
                    required_tools=[tool.name],
                    performance_metrics={}
                )
                
                capabilities.append(capability)
        
        return capabilities
    
    async def _discover_from_config(
        self,
        agent: Agent,
        db: AsyncSession
    ) -> List[Capability]:
        """Discover capabilities from agent configuration"""
        capabilities = []
        
        # Check agent's stated capabilities
        if agent.capabilities:
            for cap_name in agent.capabilities:
                capability = Capability(
                    id=f"config_{cap_name}",
                    name=f"Config: {cap_name}",
                    description=f"Capability from agent configuration",
                    category="configuration",
                    input_types=[],
                    output_types=[],
                    confidence_score=0.6,  # Will be calculated later
                    required_skills=[],
                    required_tools=[],
                    performance_metrics={}
                )
                
                capabilities.append(capability)
        
        return capabilities
    
    async def _discover_emergent_capabilities(
        self,
        skills: List[Skill],
        tools: List[Tool],
        db: AsyncSession
    ) -> List[Capability]:
        """Discover emergent capabilities from skill+tool combinations"""
        capabilities = []
        
        # Look for skill-tool synergies
        for skill in skills:
            skill_outputs = skill.config.get('output_types', [])
            
            for tool in tools:
                tool_inputs = tool.config.get('input_types', [])
                
                # Check if skill output matches tool input
                if any(output in tool_inputs for output in skill_outputs):
                    capability = Capability(
                        id=f"emergent_{skill.id}_{tool.id}",
                        name=f"Emergent: {skill.name} + {tool.name}",
                        description=f"Combined capability from {skill.name} and {tool.name}",
                        category="emergent",
                        input_types=skill.config.get('input_types', []),
                        output_types=tool.config.get('output_types', []),
                        confidence_score=0.5,  # Will be calculated later
                        required_skills=[skill.name],
                        required_tools=[tool.name],
                        performance_metrics={}
                    )
                    
                    capabilities.append(capability)
        
        return capabilities
    
    async def _merge_capabilities(
        self,
        capabilities: List[Capability]
    ) -> List[Capability]:
        """Merge similar capabilities"""
        merged = []
        capability_groups = {}
        
        # Group similar capabilities
        for cap in capabilities:
            key = (cap.category, tuple(sorted(cap.input_types)), tuple(sorted(cap.output_types)))
            if key not in capability_groups:
                capability_groups[key] = []
            capability_groups[key].append(cap)
        
        # Merge groups
        for group in capability_groups.values():
            if len(group) == 1:
                merged.append(group[0])
            else:
                # Create merged capability
                merged_cap = Capability(
                    id=f"merged_{uuid.uuid4()}",
                    name=f"Merged: {group[0].category}",
                    description=f"Combined capability from {len(group)} sources",
                    category=group[0].category,
                    input_types=group[0].input_types,
                    output_types=group[0].output_types,
                    confidence_score=max(cap.confidence_score for cap in group),
                    required_skills=list(set(skill for cap in group for skill in cap.required_skills)),
                    required_tools=list(set(tool for cap in group for tool in cap.required_tools)),
                    performance_metrics={}
                )
                merged.append(merged_cap)
        
        return merged
    
    async def _calculate_capability_confidence(
        self,
        capability: Capability,
        agent: Agent,
        db: AsyncSession
    ) -> float:
        """Calculate confidence score for a capability"""
        base_score = capability.confidence_score
        
        # Adjust based on agent experience
        if agent.usageCount > 100:
            base_score += 0.1
        
        # Adjust based on skill/tool availability
        if capability.required_skills:
            agent_skills = [skill.name for skill in agent.skills]
            skill_availability = len(set(capability.required_skills) & set(agent_skills)) / len(capability.required_skills)
            base_score *= skill_availability
        
        if capability.required_tools:
            agent_tools = [tool.name for tool in agent.tools_assoc]
            tool_availability = len(set(capability.required_tools) & set(agent_tools)) / len(capability.required_tools)
            base_score *= tool_availability
        
        return min(1.0, max(0.0, base_score))
    
    async def _analyze_task_requirements(
        self,
        task_description: str
    ) -> Dict[str, Any]:
        """Analyze task description to identify requirements"""
        # This would typically use NLP to analyze the task
        # For now, return basic analysis
        requirements = {
            'category': 'general',
            'input_types': ['text'],
            'output_types': ['text'],
            'complexity': 'medium',
            'domain': 'general'
        }
        
        # Simple keyword-based analysis
        if 'data' in task_description.lower():
            requirements['category'] = 'data'
            requirements['input_types'] = ['data', 'text']
            requirements['output_types'] = ['analysis', 'visualization']
        
        if 'code' in task_description.lower():
            requirements['category'] = 'development'
            requirements['input_types'] = ['code', 'text']
            requirements['output_types'] = ['code', 'documentation']
        
        return requirements
    
    async def _generate_skill_combinations(
        self,
        skills: List[Skill],
        requirements: Dict[str, Any],
        db: AsyncSession
    ) -> List[SkillCombination]:
        """Generate skill combinations for requirements"""
        combinations = []
        
        # Single skill combinations
        for skill in skills:
            combination = SkillCombination(
                skills=[skill.name],
                combination_name=f"Single: {skill.name}",
                description=f"Using {skill.name} alone",
                synergy_score=0.5,  # Will be calculated later
                expected_performance={'efficiency': 0.7, 'accuracy': 0.8},
                use_cases=[skill.description or "General use"],
                prerequisites=skill.config.get('prerequisites', [])
            )
            combinations.append(combination)
        
        # Pair combinations
        for i, skill1 in enumerate(skills):
            for skill2 in skills[i+1:]:
                # Check if skills are complementary
                if await self._are_skills_complementary(skill1, skill2, db):
                    combination = SkillCombination(
                        skills=[skill1.name, skill2.name],
                        combination_name=f"Pair: {skill1.name} + {skill2.name}",
                        description=f"Combining {skill1.name} and {skill2.name}",
                        synergy_score=0.7,  # Will be calculated later
                        expected_performance={'efficiency': 0.8, 'accuracy': 0.9},
                        use_cases=[f"Tasks requiring both {skill1.name} and {skill2.name}"],
                        prerequisites=list(set(
                            skill1.config.get('prerequisites', []) + 
                            skill2.config.get('prerequisites', [])
                        ))
                    )
                    combinations.append(combination)
        
        return combinations
    
    async def _are_skills_complementary(
        self,
        skill1: Skill,
        skill2: Skill,
        db: AsyncSession
    ) -> bool:
        """Check if two skills are complementary"""
        # Check if output of one matches input of another
        skill1_outputs = skill1.config.get('output_types', [])
        skill2_inputs = skill2.config.get('input_types', [])
        skill2_outputs = skill2.config.get('output_types', [])
        skill1_inputs = skill1.config.get('input_types', [])
        
        # Complementary if outputs match inputs
        return (
            any(output in skill2_inputs for output in skill1_outputs) or
            any(output in skill1_inputs for output in skill2_outputs)
        )
    
    async def _calculate_synergy_score(
        self,
        skill_names: List[str],
        requirements: Dict[str, Any],
        db: AsyncSession
    ) -> float:
        """Calculate synergy score for skill combination"""
        if len(skill_names) == 1:
            return 0.5  # Base score for single skills
        
        # Get skills
        skills = await db.execute(
            select(Skill).where(Skill.name.in_(skill_names))
        )
        skill_list = skills.scalars().all()
        
        if len(skill_list) != len(skill_names):
            return 0.0  # Some skills not found
        
        # Calculate complementarity
        complementarity = 0.0
        for i, skill1 in enumerate(skill_list):
            for skill2 in skill_list[i+1:]:
                if await self._are_skills_complementary(skill1, skill2, db):
                    complementarity += 0.2
        
        # Check requirement match
        requirement_match = 0.0
        req_category = requirements.get('category', 'general')
        matching_skills = sum(1 for skill in skill_list if skill.category == req_category)
        requirement_match = matching_skills / len(skill_list)
        
        # Calculate final score
        synergy_score = min(1.0, complementarity + requirement_match * 0.5)
        
        return synergy_score
    
    async def _find_required_skills(
        self,
        capability: str,
        db: AsyncSession
    ) -> List[str]:
        """Find skills required for a capability"""
        # This would typically use a knowledge base
        # For now, return basic mapping
        capability_skills = {
            'data_analysis': ['data-processing', 'statistics', 'visualization'],
            'content_creation': ['writing', 'research', 'editing'],
            'code_generation': ['programming', 'debugging', 'documentation'],
            'customer_service': ['communication', 'problem-solving', 'empathy']
        }
        
        return capability_skills.get(capability.lower(), [])
    
    async def _find_skill_alternatives(
        self,
        missing_skills: List[str],
        capability: str,
        db: AsyncSession
    ) -> List[str]:
        """Find alternative skills for missing ones"""
        alternatives = []
        
        # Search for similar skills
        for skill in missing_skills:
            similar_skills = await self.skills_manager.search_skills(
                skill, {'category': 'general'}, db, limit=5
            )
            alternatives.extend([s.name for s in similar_skills if s.name != skill])
        
        return alternatives
    
    async def _assess_gap_impact(
        self,
        capability: str,
        missing_skills: List[str],
        db: AsyncSession
    ) -> str:
        """Assess the impact of skill gaps"""
        impact_score = len(missing_skills) * 0.3
        
        if impact_score > 0.8:
            return "High impact - capability severely limited"
        elif impact_score > 0.5:
            return "Medium impact - capability partially limited"
        else:
            return "Low impact - capability slightly limited"
    
    async def _generate_gap_recommendations(
        self,
        capability: str,
        missing_skills: List[str],
        alternatives: List[str],
        db: AsyncSession
    ) -> List[str]:
        """Generate recommendations for addressing skill gaps"""
        recommendations = []
        
        if missing_skills:
            recommendations.append(f"Acquire missing skills: {', '.join(missing_skills)}")
        
        if alternatives:
            recommendations.append(f"Consider alternatives: {', '.join(alternatives[:3])}")
        
        recommendations.append(f"Focus on {capability} capability development")
        
        return recommendations
    
    async def _determine_gap_priority(
        self,
        capability: str,
        missing_skills: List[str],
        impact: str,
        db: AsyncSession
    ) -> str:
        """Determine priority for addressing skill gap"""
        if "High impact" in impact:
            return "high"
        elif "Medium impact" in impact:
            return "medium"
        else:
            return "low"
    
    async def _analyze_tool_capability_enhancement(
        self,
        tool: Tool,
        requirements: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze how a tool enhances agent capabilities"""
        enhancement = {
            'new_capabilities': [],
            'enhanced_capabilities': [],
            'performance_boost': 0.0,
            'integration_benefits': []
        }
        
        tool_capabilities = tool.config.get('capabilities', [])
        enhancement['new_capabilities'] = tool_capabilities
        
        # Calculate performance boost
        if tool.total_invocations > 100:
            success_rate = tool.successful_invocations / tool.total_invocations
            enhancement['performance_boost'] = success_rate * 0.3
        
        # Integration benefits
        if tool.auth_type == 'none':
            enhancement['integration_benefits'].append('Easy integration - no authentication required')
        
        if tool.endpoint_url:
            enhancement['integration_benefits'].append('REST API available')
        
        return enhancement
