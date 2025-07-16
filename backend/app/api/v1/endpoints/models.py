"""
Models Management API Endpoints
REST API for LLM models management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func

from app.core.database import get_db
from app.models.master_data import Model
from app.schemas.agent import ModelCreate, ModelUpdate, ModelResponse
from app.api.deps import get_current_user_from_db

router = APIRouter(
    prefix="/models",
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=ModelResponse)
async def create_model(
    model: ModelCreate,
    db: AsyncSession = Depends(get_db),
    #current_user = Depends(get_current_user_from_db)
):
    """
    Create a new model configuration
    
    Creates a new LLM model configuration that can be used by agents.
    """
    try:
        model_obj = Model(
            name=model.name,
            provider=model.provider,
            model_id=model.model_id,
            config=model.config,
            is_active=model.is_active,
            #owner_id=current_user.id
        )
        
        db.add(model_obj)
        await db.commit()
        await db.refresh(model_obj)
        
        # Convert the database model to the response schema
        return ModelResponse(
            id=str(model_obj.id),
            name=model_obj.name,
            provider=model_obj.provider,
            model_id=model_obj.model_id,
            config=model_obj.config,
            is_active=model_obj.is_active,
            owner_id=str(model_obj.owner_id),
            created_at=model_obj.created_at,
            updated_at=model_obj.updated_at
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ModelResponse])
async def list_models(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    List and filter models
    
    Returns a list of models that can be filtered.
    """
    try:
        query = select(Model)#.filter(Model.owner_id == current_user.id)
        
        if provider:
            query = query.filter(Model.provider == provider)
        
        if is_active is not None:
            query = query.filter(Model.is_active == is_active)
        
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        models = result.scalars().all()
        
        # Convert database models to response schema
        return [
            ModelResponse(
                id=str(model.id),
                name=model.name,
                provider=model.provider,
                model_id=model.model_id,
                config=model.config,
                is_active=model.is_active,
                owner_id=str(model.owner_id),
                created_at=model.created_at,
                updated_at=model.updated_at
            ) for model in models
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    Get model details
    
    Retrieves the details of a specific model by ID.
    """
    try:
        query = select(Model).filter(Model.id == model_id)
        result = await db.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Check ownership
        #if str(model.owner_id) != str(current_user.id):
         #   raise HTTPException(status_code=403, detail="Not authorized to access this model")
        
        # Convert database model to response schema
        return ModelResponse(
            id=str(model.id),
            name=model.name,
            provider=model.provider,
            model_id=model.model_id,
            config=model.config,
            is_active=model.is_active,
            owner_id=str(model.owner_id),
            created_at=model.created_at,
            updated_at=model.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    model: ModelUpdate,
    db: AsyncSession = Depends(get_db),
    #current_user = Depends(get_current_user_from_db)
):
    """
    Update a model
    
    Updates an existing model configuration.
    """
    try:
        query = select(Model).filter(Model.id == model_id)
        result = await db.execute(query)
        model_obj = result.scalar_one_or_none()
        
        if not model_obj:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Check ownership
        #if str(model_obj.owner_id) != str(current_user.id):
        #   raise HTTPException(status_code=403, detail="Not authorized to update this model")
        
        # Update fields based on the provided data
        update_data = model.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(model_obj, key):
                setattr(model_obj, key, value)
        
        await db.commit()
        await db.refresh(model_obj)
        
        # Convert database model to response schema
        return ModelResponse(
            id=str(model_obj.id),
            name=model_obj.name,
            provider=model_obj.provider,
            model_id=model_obj.model_id,
            config=model_obj.config,
            is_active=model_obj.is_active,
            owner_id=str(model_obj.owner_id),
            created_at=model_obj.created_at,
            updated_at=model_obj.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{model_id}", response_model=Dict[str, str])
async def delete_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    #current_user = Depends(get_current_user_from_db)
):
    """
    Delete a model
    
    Deletes a model configuration from the system. This operation cannot be undone.
    """
    try:
        query = select(Model).filter(Model.id == model_id)
        result = await db.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Check ownership
        #if str(model.owner_id) != str(current_user.id):
        #   raise HTTPException(status_code=403, detail="Not authorized to delete this model")
        
        await db.delete(model)
        await db.commit()
        
        return {"message": "Model deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/providers/", response_model=List[str])
async def get_model_providers(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    Get all model providers
    
    Returns a list of all unique model providers in the system.
    """
    try:
        query = select(Model.provider).distinct()
        result = await db.execute(query)
        providers = result.scalars().all()
        return [provider for provider in providers if provider]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
