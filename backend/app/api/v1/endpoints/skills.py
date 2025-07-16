"""
Skills Management API Endpoints
REST API for skills marketplace and management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func
import uuid

from app.core.database import get_db
from app.models.master_data import Skill
from app.schemas.agent import SkillCreate, SkillUpdate, SkillResponse
from app.api.deps import get_current_user_from_db

router = APIRouter(
    prefix="/skills",
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=SkillResponse)
async def create_skill(
    skill: SkillCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)  # Temporarily disabled for testing
):
    """
    Create a new skill
    
    Creates a new skill that can be associated with agents.
    """
    try:
        skill_obj = Skill(
            name=skill.name,
            description=skill.description,
            category=skill.category,
            config=skill.config or {},
            tags=skill.tags or [],
            status=skill.status or "active",
            dependencies=skill.dependencies or [],
            examples=skill.examples or [],
            usage_count=skill.usage_count or 0
        )
        
        db.add(skill_obj)
        await db.commit()
        await db.refresh(skill_obj)
        
        # Convert the database model to the response schema
        return SkillResponse(
            id=str(skill_obj.id),
            name=skill_obj.name,
            description=skill_obj.description,
            category=skill_obj.category,
            config=skill_obj.config,
            tags=skill_obj.tags,
            status=skill_obj.status,
            dependencies=skill_obj.dependencies,
            examples=skill_obj.examples,
            usage_count=skill_obj.usage_count,
            created_at=skill_obj.created_at,
            updated_at=skill_obj.updated_at
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[SkillResponse])
async def list_skills(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(get_current_user_from_db)  # Temporarily disabled for testing
):
    """
    List and search skills
    
    Returns a list of skills that can be filtered and searched.
    """
    try:
        stmt = select(Skill)
        
        if query:
            search_filter = or_(
                Skill.name.ilike(f"%{query}%"),
                Skill.description.ilike(f"%{query}%")
            )
            stmt = stmt.where(search_filter)
        
        if category:
            stmt = stmt.where(Skill.category == category)
        
        stmt = stmt.offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        skills = result.scalars().all()
        
        # Convert database models to response schema
        return [
            SkillResponse(
                id=str(skill.id),
                name=skill.name,
                description=skill.description,
                category=skill.category,
                config=skill.config,
                tags=skill.tags,
                status=skill.status,
                dependencies=skill.dependencies,
                examples=skill.examples,
                usage_count=skill.usage_count,
                created_at=skill.created_at,
                updated_at=skill.updated_at
            ) for skill in skills
        ]
        
    except Exception as e:
        # No need to rollback for read-only operation
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categories", response_model=List[str])
async def get_skill_categories(
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(get_current_user_from_db)  # Temporarily disabled for testing
):
    """
    Get all skill categories
    
    Returns a list of all unique skill categories in the system.
    """
    try:
        stmt = select(Skill.category).distinct().where(Skill.category.isnot(None))
        result = await db.execute(stmt)
        categories = result.all()
        return [category[0] for category in categories if category[0]]
        
    except Exception as e:
        # No need to rollback for read-only operation
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(get_current_user_from_db)  # Temporarily disabled for testing
):
    """
    Get skill details
    
    Retrieves the details of a specific skill by ID.
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(skill_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")
        
        stmt = select(Skill).where(Skill.id == skill_id)
        result = await db.execute(stmt)
        skill = result.scalars().first()
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        # Convert database model to response schema
        return SkillResponse(
            id=str(skill.id),
            name=skill.name,
            description=skill.description,
            category=skill.category,
            config=skill.config,
            tags=skill.tags,
            status=skill.status,
            dependencies=skill.dependencies,
            examples=skill.examples,
            usage_count=skill.usage_count,
            created_at=skill.created_at,
            updated_at=skill.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # No need to rollback for read-only operation
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    skill: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(get_current_user_from_db)  # Temporarily disabled for testing
):
    """
    Update a skill
    
    Updates an existing skill with new information.
    """
    try:
        stmt = select(Skill).where(Skill.id == skill_id)
        result = await db.execute(stmt)
        skill_obj = result.scalars().first()
        if not skill_obj:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        # Update fields based on the provided data
        update_data = skill.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(skill_obj, key):
                setattr(skill_obj, key, value)
        
        await db.commit()
        await db.refresh(skill_obj)
        
        # Convert database model to response schema
        return SkillResponse(
            id=str(skill_obj.id),
            name=skill_obj.name,
            description=skill_obj.description,
            category=skill_obj.category,
            config=skill_obj.config,
            tags=skill_obj.tags,
            status=skill_obj.status,
            dependencies=skill_obj.dependencies,
            examples=skill_obj.examples,
            usage_count=skill_obj.usage_count,
            created_at=skill_obj.created_at,
            updated_at=skill_obj.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{skill_id}", response_model=Dict[str, str])
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(get_current_user_from_db)  # Temporarily disabled for testing
):
    """
    Delete a skill
    
    Deletes a skill from the system. This operation cannot be undone.
    """
    try:
        stmt = select(Skill).where(Skill.id == skill_id)
        result = await db.execute(stmt)
        skill = result.scalars().first()
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        await db.delete(skill)
        await db.commit()
        
        return {"message": "Skill deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
