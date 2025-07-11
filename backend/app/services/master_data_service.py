"""
Master Data Service
Handles management of master data entities (skills, constraints, prompts, models, secrets)
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.master_data import (
    Skill, Constraint, Prompt, Model, EnvironmentSecret
)
from app.models.user import User
from app.schemas.master_data import (
    SkillCreate, SkillUpdate, SkillResponse,
    ConstraintCreate, ConstraintUpdate, ConstraintResponse,
    PromptCreate, PromptUpdate, PromptResponse,
    ModelCreate, ModelUpdate, ModelResponse,
    EnvironmentSecretCreate, EnvironmentSecretUpdate, EnvironmentSecretResponse
)
from app.services.observability_service import ObservabilityService
from app.core.exceptions import MasterDataError, ValidationError
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class MasterDataService:
    """Service for managing master data entities"""
    
    def __init__(self):
        self.observability_service = ObservabilityService()
    
    # Skills Management
    async def create_skill(
        self,
        skill_data: SkillCreate,
        user_id: str,
        db: AsyncSession
    ) -> SkillResponse:
        """Create a new skill"""
        try:
            # Validate skill data
            await self._validate_skill_data(skill_data)
            
            # Create skill
            skill = Skill(
                id=str(uuid.uuid4()),
                name=skill_data.name,
                display_name=skill_data.display_name,
                description=skill_data.description,
                category=skill_data.category,
                skill_type=skill_data.skill_type,
                config=skill_data.config,
                parameters=skill_data.parameters,
                metadata=skill_data.metadata,
                tags=skill_data.tags,
                version=skill_data.version,
                status="active",
                created_by=user_id,
                organization_id=None  # TODO: Get from user context
            )
            
            db.add(skill)
            await db.commit()
            await db.refresh(skill)
            
            # Log skill creation
            await self.observability_service.log_event(
                "skill_created",
                {
                    "skill_id": skill.id,
                    "skill_name": skill.name,
                    "skill_type": skill.skill_type,
                    "created_by": user_id
                }
            )
            
            return SkillResponse.model_validate(skill)
            
        except Exception as e:
            logger.error(f"Error creating skill: {str(e)}")
            await db.rollback()
            raise MasterDataError(f"Failed to create skill: {str(e)}")
    
    async def get_skill(
        self,
        skill_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[SkillResponse]:
        """Get skill by ID"""
        try:
            stmt = select(Skill).where(Skill.id == skill_id)
            result = await db.execute(stmt)
            skill = result.scalar_one_or_none()
            
            if not skill:
                return None
            
            return SkillResponse.model_validate(skill)
            
        except Exception as e:
            logger.error(f"Error getting skill {skill_id}: {str(e)}")
            raise MasterDataError(f"Failed to get skill: {str(e)}")
    
    async def list_skills(
        self,
        user_id: str,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        skill_type: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[SkillResponse]:
        """List skills with filtering"""
        try:
            stmt = select(Skill)
            
            # Apply filters
            if skill_type:
                stmt = stmt.where(Skill.skill_type == skill_type)
            
            if category:
                stmt = stmt.where(Skill.category == category)
            
            if status:
                stmt = stmt.where(Skill.status == status)
            
            if search:
                stmt = stmt.where(
                    or_(
                        Skill.name.ilike(f"%{search}%"),
                        Skill.display_name.ilike(f"%{search}%"),
                        Skill.description.ilike(f"%{search}%")
                    )
                )
            
            stmt = stmt.offset(skip).limit(limit)
            
            result = await db.execute(stmt)
            skills = result.scalars().all()
            
            return [SkillResponse.model_validate(s) for s in skills]
            
        except Exception as e:
            logger.error(f"Error listing skills: {str(e)}")
            raise MasterDataError(f"Failed to list skills: {str(e)}")
    
    async def update_skill(
        self,
        skill_id: str,
        skill_data: SkillUpdate,
        user_id: str,
        db: AsyncSession
    ) -> Optional[SkillResponse]:
        """Update skill"""
        try:
            # Get existing skill
            skill = await self.get_skill(skill_id, user_id, db)
            if not skill:
                return None
            
            # Validate data if provided
            if skill_data.config:
                await self._validate_skill_data(skill_data)
            
            # Update skill
            update_data = skill_data.model_dump(exclude_unset=True)
            if update_data:
                stmt = update(Skill).where(Skill.id == skill_id).values(**update_data)
                await db.execute(stmt)
                await db.commit()
            
            # Return updated skill
            return await self.get_skill(skill_id, user_id, db)
            
        except Exception as e:
            logger.error(f"Error updating skill {skill_id}: {str(e)}")
            await db.rollback()
            raise MasterDataError(f"Failed to update skill: {str(e)}")
    
    async def delete_skill(
        self,
        skill_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """Delete skill"""
        try:
            stmt = delete(Skill).where(Skill.id == skill_id)
            result = await db.execute(stmt)
            await db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error deleting skill {skill_id}: {str(e)}")
            await db.rollback()
            raise MasterDataError(f"Failed to delete skill: {str(e)}")
    
    # Constraints Management
    async def create_constraint(
        self,
        constraint_data: ConstraintCreate,
        user_id: str,
        db: AsyncSession
    ) -> ConstraintResponse:
        """Create a new constraint"""
        try:
            # Validate constraint data
            await self._validate_constraint_data(constraint_data)
            
            # Create constraint
            constraint = Constraint(
                id=str(uuid.uuid4()),
                name=constraint_data.name,
                display_name=constraint_data.display_name,
                description=constraint_data.description,
                constraint_type=constraint_data.constraint_type,
                rule_definition=constraint_data.rule_definition,
                parameters=constraint_data.parameters,
                metadata=constraint_data.metadata,
                tags=constraint_data.tags,
                version=constraint_data.version,
                status="active",
                created_by=user_id,
                organization_id=None
            )
            
            db.add(constraint)
            await db.commit()
            await db.refresh(constraint)
            
            # Log constraint creation
            await self.observability_service.log_event(
                "constraint_created",
                {
                    "constraint_id": constraint.id,
                    "constraint_name": constraint.name,
                    "constraint_type": constraint.constraint_type,
                    "created_by": user_id
                }
            )
            
            return ConstraintResponse.model_validate(constraint)
            
        except Exception as e:
            logger.error(f"Error creating constraint: {str(e)}")
            await db.rollback()
            raise MasterDataError(f"Failed to create constraint: {str(e)}")
    
    async def get_constraint(
        self,
        constraint_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[ConstraintResponse]:
        """Get constraint by ID"""
        try:
            stmt = select(Constraint).where(Constraint.id == constraint_id)
            result = await db.execute(stmt)
            constraint = result.scalar_one_or_none()
            
            if not constraint:
                return None
            
            return ConstraintResponse.model_validate(constraint)
            
        except Exception as e:
            logger.error(f"Error getting constraint {constraint_id}: {str(e)}")
            raise MasterDataError(f"Failed to get constraint: {str(e)}")
    
    async def list_constraints(
        self,
        user_id: str,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        constraint_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[ConstraintResponse]:
        """List constraints with filtering"""
        try:
            stmt = select(Constraint)
            
            # Apply filters
            if constraint_type:
                stmt = stmt.where(Constraint.constraint_type == constraint_type)
            
            if status:
                stmt = stmt.where(Constraint.status == status)
            
            if search:
                stmt = stmt.where(
                    or_(
                        Constraint.name.ilike(f"%{search}%"),
                        Constraint.display_name.ilike(f"%{search}%"),
                        Constraint.description.ilike(f"%{search}%")
                    )
                )
            
            stmt = stmt.offset(skip).limit(limit)
            
            result = await db.execute(stmt)
            constraints = result.scalars().all()
            
            return [ConstraintResponse.model_validate(c) for c in constraints]
            
        except Exception as e:
            logger.error(f"Error listing constraints: {str(e)}")
            raise MasterDataError(f"Failed to list constraints: {str(e)}")
    
    # Prompts Management
    async def create_prompt(
        self,
        prompt_data: PromptCreate,
        user_id: str,
        db: AsyncSession
    ) -> PromptResponse:
        """Create a new prompt"""
        try:
            # Validate prompt data
            await self._validate_prompt_data(prompt_data)
            
            # Create prompt
            prompt = Prompt(
                id=str(uuid.uuid4()),
                name=prompt_data.name,
                display_name=prompt_data.display_name,
                description=prompt_data.description,
                prompt_type=prompt_data.prompt_type,
                template=prompt_data.template,
                variables=prompt_data.variables,
                metadata=prompt_data.metadata,
                tags=prompt_data.tags,
                version=prompt_data.version,
                status="active",
                created_by=user_id,
                organization_id=None
            )
            
            db.add(prompt)
            await db.commit()
            await db.refresh(prompt)
            
            # Log prompt creation
            await self.observability_service.log_event(
                "prompt_created",
                {
                    "prompt_id": prompt.id,
                    "prompt_name": prompt.name,
                    "prompt_type": prompt.prompt_type,
                    "created_by": user_id
                }
            )
            
            return PromptResponse.model_validate(prompt)
            
        except Exception as e:
            logger.error(f"Error creating prompt: {str(e)}")
            await db.rollback()
            raise MasterDataError(f"Failed to create prompt: {str(e)}")
    
    async def get_prompt(
        self,
        prompt_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[PromptResponse]:
        """Get prompt by ID"""
        try:
            stmt = select(Prompt).where(Prompt.id == prompt_id)
            result = await db.execute(stmt)
            prompt = result.scalar_one_or_none()
            
            if not prompt:
                return None
            
            return PromptResponse.model_validate(prompt)
            
        except Exception as e:
            logger.error(f"Error getting prompt {prompt_id}: {str(e)}")
            raise MasterDataError(f"Failed to get prompt: {str(e)}")
    
    async def list_prompts(
        self,
        user_id: str,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        prompt_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[PromptResponse]:
        """List prompts with filtering"""
        try:
            stmt = select(Prompt)
            
            # Apply filters
            if prompt_type:
                stmt = stmt.where(Prompt.prompt_type == prompt_type)
            
            if status:
                stmt = stmt.where(Prompt.status == status)
            
            if search:
                stmt = stmt.where(
                    or_(
                        Prompt.name.ilike(f"%{search}%"),
                        Prompt.display_name.ilike(f"%{search}%"),
                        Prompt.description.ilike(f"%{search}%")
                    )
                )
            
            stmt = stmt.offset(skip).limit(limit)
            
            result = await db.execute(stmt)
            prompts = result.scalars().all()
            
            return [PromptResponse.model_validate(p) for p in prompts]
            
        except Exception as e:
            logger.error(f"Error listing prompts: {str(e)}")
            raise MasterDataError(f"Failed to list prompts: {str(e)}")
    
    # Models Management
    async def create_model(
        self,
        model_data: ModelCreate,
        user_id: str,
        db: AsyncSession
    ) -> ModelResponse:
        """Create a new model"""
        try:
            # Validate model data
            await self._validate_model_data(model_data)
            
            # Create model
            model = Model(
                id=str(uuid.uuid4()),
                name=model_data.name,
                display_name=model_data.display_name,
                description=model_data.description,
                model_type=model_data.model_type,
                provider=model_data.provider,
                model_name=model_data.model_name,
                config=model_data.config,
                parameters=model_data.parameters,
                metadata=model_data.metadata,
                tags=model_data.tags,
                version=model_data.version,
                status="active",
                created_by=user_id,
                organization_id=None
            )
            
            db.add(model)
            await db.commit()
            await db.refresh(model)
            
            # Log model creation
            await self.observability_service.log_event(
                "model_created",
                {
                    "model_id": model.id,
                    "model_name": model.name,
                    "model_type": model.model_type,
                    "provider": model.provider,
                    "created_by": user_id
                }
            )
            
            return ModelResponse.model_validate(model)
            
        except Exception as e:
            logger.error(f"Error creating model: {str(e)}")
            await db.rollback()
            raise MasterDataError(f"Failed to create model: {str(e)}")
    
    async def get_model(
        self,
        model_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[ModelResponse]:
        """Get model by ID"""
        try:
            stmt = select(Model).where(Model.id == model_id)
            result = await db.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return ModelResponse.model_validate(model)
            
        except Exception as e:
            logger.error(f"Error getting model {model_id}: {str(e)}")
            raise MasterDataError(f"Failed to get model: {str(e)}")
    
    async def list_models(
        self,
        user_id: str,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        model_type: Optional[str] = None,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[ModelResponse]:
        """List models with filtering"""
        try:
            stmt = select(Model)
            
            # Apply filters
            if model_type:
                stmt = stmt.where(Model.model_type == model_type)
            
            if provider:
                stmt = stmt.where(Model.provider == provider)
            
            if status:
                stmt = stmt.where(Model.status == status)
            
            if search:
                stmt = stmt.where(
                    or_(
                        Model.name.ilike(f"%{search}%"),
                        Model.display_name.ilike(f"%{search}%"),
                        Model.description.ilike(f"%{search}%")
                    )
                )
            
            stmt = stmt.offset(skip).limit(limit)
            
            result = await db.execute(stmt)
            models = result.scalars().all()
            
            return [ModelResponse.model_validate(m) for m in models]
            
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            raise MasterDataError(f"Failed to list models: {str(e)}")
    
    # Environment Secrets Management
    async def create_environment_secret(
        self,
        secret_data: EnvironmentSecretCreate,
        user_id: str,
        db: AsyncSession
    ) -> EnvironmentSecretResponse:
        """Create a new environment secret"""
        try:
            # Validate secret data
            await self._validate_secret_data(secret_data)
            
            # Create environment secret
            secret = EnvironmentSecret(
                id=str(uuid.uuid4()),
                name=secret_data.name,
                display_name=secret_data.display_name,
                description=secret_data.description,
                secret_type=secret_data.secret_type,
                value=secret_data.value,  # TODO: Encrypt this
                metadata=secret_data.metadata,
                tags=secret_data.tags,
                version=secret_data.version,
                status="active",
                created_by=user_id,
                organization_id=None
            )
            
            db.add(secret)
            await db.commit()
            await db.refresh(secret)
            
            # Log secret creation (don't log the actual value)
            await self.observability_service.log_event(
                "environment_secret_created",
                {
                    "secret_id": secret.id,
                    "secret_name": secret.name,
                    "secret_type": secret.secret_type,
                    "created_by": user_id
                }
            )
            
            return EnvironmentSecretResponse.model_validate(secret)
            
        except Exception as e:
            logger.error(f"Error creating environment secret: {str(e)}")
            await db.rollback()
            raise MasterDataError(f"Failed to create environment secret: {str(e)}")
    
    async def get_environment_secret(
        self,
        secret_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[EnvironmentSecretResponse]:
        """Get environment secret by ID"""
        try:
            stmt = select(EnvironmentSecret).where(EnvironmentSecret.id == secret_id)
            result = await db.execute(stmt)
            secret = result.scalar_one_or_none()
            
            if not secret:
                return None
            
            return EnvironmentSecretResponse.model_validate(secret)
            
        except Exception as e:
            logger.error(f"Error getting environment secret {secret_id}: {str(e)}")
            raise MasterDataError(f"Failed to get environment secret: {str(e)}")
    
    async def list_environment_secrets(
        self,
        user_id: str,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        secret_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[EnvironmentSecretResponse]:
        """List environment secrets with filtering"""
        try:
            stmt = select(EnvironmentSecret)
            
            # Apply filters
            if secret_type:
                stmt = stmt.where(EnvironmentSecret.secret_type == secret_type)
            
            if status:
                stmt = stmt.where(EnvironmentSecret.status == status)
            
            if search:
                stmt = stmt.where(
                    or_(
                        EnvironmentSecret.name.ilike(f"%{search}%"),
                        EnvironmentSecret.display_name.ilike(f"%{search}%"),
                        EnvironmentSecret.description.ilike(f"%{search}%")
                    )
                )
            
            stmt = stmt.offset(skip).limit(limit)
            
            result = await db.execute(stmt)
            secrets = result.scalars().all()
            
            return [EnvironmentSecretResponse.model_validate(s) for s in secrets]
            
        except Exception as e:
            logger.error(f"Error listing environment secrets: {str(e)}")
            raise MasterDataError(f"Failed to list environment secrets: {str(e)}")
    
    # Validation Methods
    async def _validate_skill_data(self, skill_data: Union[SkillCreate, SkillUpdate]) -> None:
        """Validate skill data"""
        try:
            if hasattr(skill_data, 'name') and skill_data.name:
                if len(skill_data.name) < 2:
                    raise ValidationError("Skill name must be at least 2 characters")
            
            if hasattr(skill_data, 'config') and skill_data.config:
                # Validate config structure
                if not isinstance(skill_data.config, dict):
                    raise ValidationError("Skill config must be a dictionary")
                    
        except Exception as e:
            logger.error(f"Error validating skill data: {str(e)}")
            raise ValidationError(f"Invalid skill data: {str(e)}")
    
    async def _validate_constraint_data(self, constraint_data: Union[ConstraintCreate, ConstraintUpdate]) -> None:
        """Validate constraint data"""
        try:
            if hasattr(constraint_data, 'rule_definition') and constraint_data.rule_definition:
                # Validate rule definition structure
                if not isinstance(constraint_data.rule_definition, dict):
                    raise ValidationError("Constraint rule definition must be a dictionary")
                    
        except Exception as e:
            logger.error(f"Error validating constraint data: {str(e)}")
            raise ValidationError(f"Invalid constraint data: {str(e)}")
    
    async def _validate_prompt_data(self, prompt_data: Union[PromptCreate, PromptUpdate]) -> None:
        """Validate prompt data"""
        try:
            if hasattr(prompt_data, 'template') and prompt_data.template:
                if len(prompt_data.template) < 10:
                    raise ValidationError("Prompt template must be at least 10 characters")
                    
        except Exception as e:
            logger.error(f"Error validating prompt data: {str(e)}")
            raise ValidationError(f"Invalid prompt data: {str(e)}")
    
    async def _validate_model_data(self, model_data: Union[ModelCreate, ModelUpdate]) -> None:
        """Validate model data"""
        try:
            if hasattr(model_data, 'provider') and model_data.provider:
                valid_providers = ["openai", "anthropic", "google", "azure", "custom"]
                if model_data.provider not in valid_providers:
                    raise ValidationError(f"Invalid provider. Must be one of: {valid_providers}")
                    
        except Exception as e:
            logger.error(f"Error validating model data: {str(e)}")
            raise ValidationError(f"Invalid model data: {str(e)}")
    
    async def _validate_secret_data(self, secret_data: Union[EnvironmentSecretCreate, EnvironmentSecretUpdate]) -> None:
        """Validate secret data"""
        try:
            if hasattr(secret_data, 'value') and secret_data.value:
                if len(secret_data.value) < 1:
                    raise ValidationError("Secret value cannot be empty")
                    
        except Exception as e:
            logger.error(f"Error validating secret data: {str(e)}")
            raise ValidationError(f"Invalid secret data: {str(e)}")
    
    # Utility Methods
    async def get_master_data_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get master data statistics"""
        try:
            # Get counts for each entity type
            skills_count = await db.scalar(select(func.count(Skill.id)))
            constraints_count = await db.scalar(select(func.count(Constraint.id)))
            prompts_count = await db.scalar(select(func.count(Prompt.id)))
            models_count = await db.scalar(select(func.count(Model.id)))
            secrets_count = await db.scalar(select(func.count(EnvironmentSecret.id)))
            
            return {
                "skills_count": skills_count or 0,
                "constraints_count": constraints_count or 0,
                "prompts_count": prompts_count or 0,
                "models_count": models_count or 0,
                "secrets_count": secrets_count or 0,
                "total_entities": (skills_count or 0) + (constraints_count or 0) + (prompts_count or 0) + (models_count or 0) + (secrets_count or 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting master data stats: {str(e)}")
            raise MasterDataError(f"Failed to get master data stats: {str(e)}")
    
    async def search_master_data(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        user_id: str = None,
        db: AsyncSession = None,
        limit: int = 50
    ) -> Dict[str, List[Any]]:
        """Search across all master data entities"""
        try:
            results = {}
            
            # Search skills
            if not entity_types or "skills" in entity_types:
                skills_stmt = select(Skill).where(
                    or_(
                        Skill.name.ilike(f"%{query}%"),
                        Skill.display_name.ilike(f"%{query}%"),
                        Skill.description.ilike(f"%{query}%")
                    )
                ).limit(limit)
                
                skills_result = await db.execute(skills_stmt)
                skills = skills_result.scalars().all()
                results["skills"] = [SkillResponse.model_validate(s) for s in skills]
            
            # Search constraints
            if not entity_types or "constraints" in entity_types:
                constraints_stmt = select(Constraint).where(
                    or_(
                        Constraint.name.ilike(f"%{query}%"),
                        Constraint.display_name.ilike(f"%{query}%"),
                        Constraint.description.ilike(f"%{query}%")
                    )
                ).limit(limit)
                
                constraints_result = await db.execute(constraints_stmt)
                constraints = constraints_result.scalars().all()
                results["constraints"] = [ConstraintResponse.model_validate(c) for c in constraints]
            
            # Search prompts
            if not entity_types or "prompts" in entity_types:
                prompts_stmt = select(Prompt).where(
                    or_(
                        Prompt.name.ilike(f"%{query}%"),
                        Prompt.display_name.ilike(f"%{query}%"),
                        Prompt.description.ilike(f"%{query}%")
                    )
                ).limit(limit)
                
                prompts_result = await db.execute(prompts_stmt)
                prompts = prompts_result.scalars().all()
                results["prompts"] = [PromptResponse.model_validate(p) for p in prompts]
            
            # Search models
            if not entity_types or "models" in entity_types:
                models_stmt = select(Model).where(
                    or_(
                        Model.name.ilike(f"%{query}%"),
                        Model.display_name.ilike(f"%{query}%"),
                        Model.description.ilike(f"%{query}%")
                    )
                ).limit(limit)
                
                models_result = await db.execute(models_stmt)
                models = models_result.scalars().all()
                results["models"] = [ModelResponse.model_validate(m) for m in models]
            
            # Search secrets (limited fields for security)
            if not entity_types or "secrets" in entity_types:
                secrets_stmt = select(EnvironmentSecret).where(
                    or_(
                        EnvironmentSecret.name.ilike(f"%{query}%"),
                        EnvironmentSecret.display_name.ilike(f"%{query}%"),
                        EnvironmentSecret.description.ilike(f"%{query}%")
                    )
                ).limit(limit)
                
                secrets_result = await db.execute(secrets_stmt)
                secrets = secrets_result.scalars().all()
                results["secrets"] = [EnvironmentSecretResponse.model_validate(s) for s in secrets]
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching master data: {str(e)}")
            raise MasterDataError(f"Failed to search master data: {str(e)}")
