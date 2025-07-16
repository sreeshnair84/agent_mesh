"""
Prompts Management API Endpoints
REST API for prompts marketplace and management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func

from app.core.database import get_db
from app.models.master_data import Prompt
from app.schemas.agent import PromptCreate, PromptUpdate, PromptResponse
from app.api.deps import get_current_user_from_db

router = APIRouter(
    prefix="/prompts",
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=PromptResponse)
async def create_prompt(
    prompt: PromptCreate,
    db: AsyncSession = Depends(get_db),
    #current_user = Depends(get_current_user_from_db)
):
    """
    Create a new prompt
    
    Creates a new prompt template that can be used by agents.
    """
    try:
        prompt_obj = Prompt(
            name=prompt.name,
            content=prompt.content,
            version=prompt.version,
            description=prompt.description,
            tags=prompt.tags or [],
            #owner_id=current_user.id
        )
        
        db.add(prompt_obj)
        await db.commit()
        await db.refresh(prompt_obj)
        
        # Convert the database model to the response schema
        return PromptResponse(
            id=str(prompt_obj.id),
            name=prompt_obj.name,
            content=prompt_obj.content,
            version=prompt_obj.version,
            description=prompt_obj.description,
            tags=prompt_obj.tags,
            owner_id=str(prompt_obj.owner_id),
            created_at=prompt_obj.created_at,
            updated_at=prompt_obj.updated_at
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[PromptResponse])
async def list_prompts(
    query: Optional[str] = Query(None, description="Search query"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    #current_user = Depends(get_current_user_from_db)
):
    """
    List and search prompts
    
    Returns a list of prompts that can be filtered and searched.
    """
    try:
        stmt = select(Prompt)
        
        if query:
            search_filter = or_(
                Prompt.name.ilike(f"%{query}%"),
                Prompt.description.ilike(f"%{query}%"),
                Prompt.content.ilike(f"%{query}%")
            )
            stmt = stmt.where(search_filter)
        
        if tag:
            stmt = stmt.where(Prompt.tags.contains([tag]))
        
        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        prompts = result.scalars().all()
        
        # Convert database models to response schema
        return [
            PromptResponse(
                id=str(prompt.id),
                name=prompt.name,
                content=prompt.content,
                version=prompt.version,
                description=prompt.description,
                tags=prompt.tags,
                owner_id=str(prompt.owner_id),
                created_at=prompt.created_at,
                updated_at=prompt.updated_at
            ) for prompt in prompts
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
    #current_user = Depends(get_current_user_from_db)
):
    """
    Get prompt details
    
    Retrieves the details of a specific prompt by ID.
    """
    try:
        stmt = select(Prompt).where(Prompt.id == prompt_id)
        result = await db.execute(stmt)
        prompt = result.scalars().first()
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        # Check ownership
        #if str(prompt.owner_id) != str(current_user.id):
        #    raise HTTPException(status_code=403, detail="Not authorized to access this prompt")
        
        # Convert database model to response schema
        return PromptResponse(
            id=str(prompt.id),
            name=prompt.name,
            content=prompt.content,
            version=prompt.version,
            description=prompt.description,
            tags=prompt.tags,
            owner_id=str(prompt.owner_id),
            created_at=prompt.created_at,
            updated_at=prompt.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    prompt: PromptUpdate,
    db: AsyncSession = Depends(get_db),
    #current_user = Depends(get_current_user_from_db)
):
    """
    Update a prompt
    
    Updates an existing prompt with new information.
    """
    try:
        stmt = select(Prompt).where(Prompt.id == prompt_id)
        result = await db.execute(stmt)
        prompt_obj = result.scalars().first()
        if not prompt_obj:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        # Check ownership
        #if str(prompt_obj.owner_id) != str(current_user.id):
         #   raise HTTPException(status_code=403, detail="Not authorized to update this prompt")
        
        # Update fields based on the provided data
        update_data = prompt.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(prompt_obj, key):
                setattr(prompt_obj, key, value)
        
        await db.commit()
        await db.refresh(prompt_obj)
        
        # Convert database model to response schema
        return PromptResponse(
            id=str(prompt_obj.id),
            name=prompt_obj.name,
            content=prompt_obj.content,
            version=prompt_obj.version,
            description=prompt_obj.description,
            tags=prompt_obj.tags,
            owner_id=str(prompt_obj.owner_id),
            created_at=prompt_obj.created_at,
            updated_at=prompt_obj.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{prompt_id}", response_model=Dict[str, str])
async def delete_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
    #current_user = Depends(get_current_user_from_db)
):
    """
    Delete a prompt
    
    Deletes a prompt from the system. This operation cannot be undone.
    """
    try:
        stmt = select(Prompt).where(Prompt.id == prompt_id)
        result = await db.execute(stmt)
        prompt = result.scalars().first()
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        # Check ownership
        #if str(prompt.owner_id) != str(current_user.id):
        #    raise HTTPException(status_code=403, detail="Not authorized to delete this prompt")
        
        await db.delete(prompt)
        await db.commit()
        
        return {"message": "Prompt deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tags/", response_model=List[str])
async def get_prompt_tags(
    db: AsyncSession = Depends(get_db),
    #current_user = Depends(get_current_user_from_db)
):
    """
    Get all prompt tags
    
    Returns a list of all unique prompt tags in the system.
    """
    try:
        stmt = select(Prompt)#.where(Prompt.owner_id == current_user.id)
        result = await db.execute(stmt)
        prompts = result.scalars().all()
        tags = set()
        for prompt in prompts:
            if prompt.tags:
                tags.update(prompt.tags)
        return sorted(list(tags))
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
