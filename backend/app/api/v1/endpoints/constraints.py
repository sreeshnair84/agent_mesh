"""
Constraints Management API Endpoints
REST API for agent constraints management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select

from app.core.database import get_db
from app.models.master_data import Constraint
from app.schemas.agent import ConstraintCreate, ConstraintUpdate, ConstraintResponse
from app.api.deps import get_current_user_from_db

router = APIRouter(
    prefix="/constraints",
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=ConstraintResponse)
async def create_constraint(
    constraint: ConstraintCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    Create a new constraint
    
    Creates a new constraint that can be applied to agents.
    """
    try:
        constraint_obj = Constraint(
            name=constraint.name,
            description=constraint.description,
            config=constraint.config,
            type=constraint.type
        )
        
        db.add(constraint_obj)
        db.commit()
        db.refresh(constraint_obj)
        
        # Convert the database model to the response schema
        return ConstraintResponse(
            id=str(constraint_obj.id),
            name=constraint_obj.name,
            description=constraint_obj.description,
            config=constraint_obj.config,
            type=constraint_obj.type,
            created_at=constraint_obj.created_at,
            updated_at=constraint_obj.updated_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ConstraintResponse])
async def list_constraints(
    query: Optional[str] = Query(None, description="Search query"),
    type: Optional[str] = Query(None, description="Filter by constraint type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    List and search constraints
    
    Returns a list of constraints that can be filtered and searched.
    """
    try:
        query_filter = db.query(Constraint)
        
        if query:
            search_filter = or_(
                Constraint.name.ilike(f"%{query}%"),
                Constraint.description.ilike(f"%{query}%")
            )
            query_filter = query_filter.filter(search_filter)
        
        if type:
            query_filter = query_filter.filter(Constraint.type == type)
        
        constraints = query_filter.offset(offset).limit(limit).all()
        
        # Convert database models to response schema
        return [
            ConstraintResponse(
                id=str(constraint.id),
                name=constraint.name,
                description=constraint.description,
                config=constraint.config,
                type=constraint.type,
                created_at=constraint.created_at,
                updated_at=constraint.updated_at
            ) for constraint in constraints
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{constraint_id}", response_model=ConstraintResponse)
async def get_constraint(
    constraint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    Get constraint details
    
    Retrieves the details of a specific constraint by ID.
    """
    try:
        constraint = db.query(Constraint).filter(Constraint.id == constraint_id).first()
        if not constraint:
            raise HTTPException(status_code=404, detail="Constraint not found")
        
        # Convert database model to response schema
        return ConstraintResponse(
            id=str(constraint.id),
            name=constraint.name,
            description=constraint.description,
            config=constraint.config,
            type=constraint.type,
            created_at=constraint.created_at,
            updated_at=constraint.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{constraint_id}", response_model=ConstraintResponse)
async def update_constraint(
    constraint_id: str,
    constraint: ConstraintUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    Update a constraint
    
    Updates an existing constraint with new information.
    """
    try:
        constraint_obj = db.query(Constraint).filter(Constraint.id == constraint_id).first()
        if not constraint_obj:
            raise HTTPException(status_code=404, detail="Constraint not found")
        
        # Update fields based on the provided data
        update_data = constraint.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(constraint_obj, key):
                setattr(constraint_obj, key, value)
        
        db.commit()
        db.refresh(constraint_obj)
        
        # Convert database model to response schema
        return ConstraintResponse(
            id=str(constraint_obj.id),
            name=constraint_obj.name,
            description=constraint_obj.description,
            config=constraint_obj.config,
            type=constraint_obj.type,
            created_at=constraint_obj.created_at,
            updated_at=constraint_obj.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{constraint_id}", response_model=Dict[str, str])
async def delete_constraint(
    constraint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    Delete a constraint
    
    Deletes a constraint from the system. This operation cannot be undone.
    """
    try:
        constraint = db.query(Constraint).filter(Constraint.id == constraint_id).first()
        if not constraint:
            raise HTTPException(status_code=404, detail="Constraint not found")
        
        db.delete(constraint)
        db.commit()
        
        return {"message": "Constraint deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/types/", response_model=List[str])
async def get_constraint_types(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    Get all constraint types
    
    Returns a list of all unique constraint types in the system.
    """
    try:
        types = db.query(Constraint.type).distinct().all()
        return [type[0] for type in types if type[0]]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
