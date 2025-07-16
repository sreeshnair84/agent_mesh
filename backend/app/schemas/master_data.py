"""
Master data schemas for skills, constraints, prompts, models, and environment secrets
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.schemas.agent import (
    SkillBase, SkillCreate, SkillUpdate, SkillResponse,
    ConstraintBase, ConstraintCreate, ConstraintUpdate, ConstraintResponse,
    PromptBase, PromptCreate, PromptUpdate, PromptResponse,
    ModelBase, ModelCreate, ModelUpdate, ModelResponse,
    TimestampedSchema
)


# Environment Secret Schemas
class EnvironmentSecretBase(BaseModel):
    """Base environment secret schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    key: str = Field(..., min_length=1, max_length=200)
    is_active: bool = True
    scope: str = Field(default="global", pattern="^(global|user|agent|workspace)$")


class EnvironmentSecretCreate(EnvironmentSecretBase):
    """Schema for creating environment secrets"""
    value: str = Field(..., min_length=1)


class EnvironmentSecretUpdate(BaseModel):
    """Schema for updating environment secrets"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    key: Optional[str] = Field(None, min_length=1, max_length=200)
    value: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None
    scope: Optional[str] = Field(None, pattern="^(global|user|agent|workspace)$")


class EnvironmentSecretResponse(TimestampedSchema, EnvironmentSecretBase):
    """Schema for environment secret responses"""
    # Note: value is not included in responses for security
    owner_id: str


# Re-export schemas from agent.py for convenience
__all__ = [
    # Skill schemas
    "SkillBase", "SkillCreate", "SkillUpdate", "SkillResponse",
    # Constraint schemas
    "ConstraintBase", "ConstraintCreate", "ConstraintUpdate", "ConstraintResponse",
    # Prompt schemas
    "PromptBase", "PromptCreate", "PromptUpdate", "PromptResponse",
    # Model schemas
    "ModelBase", "ModelCreate", "ModelUpdate", "ModelResponse",
    # Environment secret schemas
    "EnvironmentSecretBase", "EnvironmentSecretCreate", "EnvironmentSecretUpdate", "EnvironmentSecretResponse"
]
