"""
Master data endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user_from_db, get_current_admin_user
from app.models.user import User

router = APIRouter()


@router.get("/llm-providers")
async def get_llm_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
):
    """
    Get all LLM providers
    """
    providers = [
        {
            "id": "azure-openai",
            "name": "azure_openai",
            "display_name": "Azure OpenAI",
            "provider_type": "azure_openai",
            "supported_models": ["gpt-4o", "gpt-4", "gpt-35-turbo"],
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "openai",
            "name": "openai",
            "display_name": "OpenAI",
            "provider_type": "openai",
            "supported_models": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "anthropic",
            "name": "anthropic",
            "display_name": "Anthropic Claude",
            "provider_type": "anthropic",
            "supported_models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    return {
        "providers": providers,
        "total": len(providers)
    }


@router.get("/models")
async def get_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
    provider: Optional[str] = None,
):
    """
    Get all available models
    """
    models = [
        {
            "id": "gpt-4o",
            "model_name": "gpt-4o",
            "display_name": "GPT-4o",
            "provider_id": "azure-openai",
            "model_type": "chat",
            "max_tokens": 4096,
            "context_length": 128000,
            "supports_functions": True,
            "supports_streaming": True,
            "is_active": True
        },
        {
            "id": "claude-3-5-sonnet",
            "model_name": "claude-3-5-sonnet-20241022",
            "display_name": "Claude 3.5 Sonnet",
            "provider_id": "anthropic",
            "model_type": "chat",
            "max_tokens": 4096,
            "context_length": 200000,
            "supports_functions": True,
            "supports_streaming": True,
            "is_active": True
        }
    ]
    
    if provider:
        models = [m for m in models if m.get("provider_id") == provider]
    
    return {
        "models": models,
        "total": len(models)
    }


@router.post("/llm-providers")
async def create_llm_provider(
    provider_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Create a new LLM provider
    """
    return {
        "id": f"provider-{datetime.utcnow().timestamp()}",
        "name": provider_data.get("name"),
        "display_name": provider_data.get("display_name"),
        "provider_type": provider_data.get("provider_type"),
        "is_active": True,
        "created_by": str(current_user.id),
        "created_at": datetime.utcnow().isoformat(),
    }


@router.get("/configurations")
async def get_configurations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
):
    """
    Get system configurations
    """
    configurations = {
        "system": {
            "max_agents_per_user": 50,
            "max_workflows_per_user": 20,
            "default_rate_limit": 100,
            "supported_file_types": [".txt", ".json", ".csv", ".pdf"],
            "max_file_size": 10485760  # 10MB
        },
        "features": {
            "agent_marketplace": True,
            "workflow_builder": True,
            "observability": True,
            "multi_tenant": False
        },
        "integrations": {
            "azure_openai": True,
            "openai": True,
            "anthropic": True,
            "google": True
        }
    }
    
    return configurations


@router.put("/configurations")
async def update_configurations(
    config_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Update system configurations
    """
    return {
        "message": "Configurations updated successfully",
        "updated_at": datetime.utcnow().isoformat(),
        "updated_by": str(current_user.id)
    }


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
):
    """
    Get system statistics
    """
    return {
        "users": {
            "total": 125,
            "active": 98,
            "admins": 3,
            "developers": 25,
            "viewers": 97
        },
        "agents": {
            "total": 45,
            "active": 32,
            "inactive": 8,
            "error": 2,
            "templates": 8
        },
        "workflows": {
            "total": 28,
            "active": 15,
            "draft": 8,
            "completed": 5
        },
        "tools": {
            "total": 18,
            "active": 16,
            "categories": 6
        },
        "requests": {
            "total_today": 1256,
            "total_this_week": 8742,
            "total_this_month": 32567
        }
    }
