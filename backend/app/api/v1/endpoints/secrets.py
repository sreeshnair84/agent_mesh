"""
Environment Secrets Management API Endpoints
REST API for environment secrets management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select

from app.core.database import get_db
from app.models.master_data import EnvironmentSecret
from app.api.deps import get_current_user_from_db
from app.core.security import encrypt_value

router = APIRouter(
    prefix="/secrets",
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Dict[str, str])
async def create_secret(
    secret_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    Create a new environment secret
    
    Creates a new encrypted environment secret that can be used by agents.
    """
    try:
        if not all(k in secret_data for k in ['key', 'value', 'environment']):
            raise HTTPException(status_code=400, detail="Missing required fields: key, value, environment")
        
        # Check if secret already exists
        existing_query = select(EnvironmentSecret).filter(
            EnvironmentSecret.key == secret_data['key'],
            EnvironmentSecret.environment == secret_data['environment'],
            EnvironmentSecret.owner_id == current_user.id
        )
        result = await db.execute(existing_query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(status_code=409, detail="Secret with this key and environment already exists")
        
        # Encrypt the value
        encrypted_value = encrypt_value(secret_data['value'])
        
        secret = EnvironmentSecret(
            key=secret_data['key'],
            value=encrypted_value,
            environment=secret_data['environment'],
            description=secret_data.get('description'),
            owner_id=current_user.id
        )
        
        db.add(secret)
        await db.commit()
        await db.refresh(secret)
        
        return {"secret_id": str(secret.id), "message": "Secret created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[Dict[str, Any]])
async def list_secrets(
    environment: Optional[str] = Query(None, description="Filter by environment"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    List environment secrets
    
    Returns a list of environment secrets. Note that secret values are not returned.
    """
    try:
        query = select(EnvironmentSecret).filter(EnvironmentSecret.owner_id == current_user.id)
        
        if environment:
            query = query.filter(EnvironmentSecret.environment == environment)
        
        result = await db.execute(query)
        secrets = result.scalars().all()
        
        # Return secrets without the encrypted values
        return [
            {
                "id": str(secret.id),
                "key": secret.key,
                "environment": secret.environment,
                "description": secret.description,
                "created_at": secret.created_at.isoformat() if secret.created_at else None,
                "updated_at": secret.updated_at.isoformat() if secret.updated_at else None,
            } for secret in secrets
        ]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{secret_id}", response_model=Dict[str, Any])
async def get_secret(
    secret_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    Get secret details
    
    Retrieves the details of a specific secret by ID. Note that the secret value is not returned.
    """
    try:
        query = select(EnvironmentSecret).filter(EnvironmentSecret.id == secret_id)
        result = await db.execute(query)
        secret = result.scalar_one_or_none()
        if not secret:
            raise HTTPException(status_code=404, detail="Secret not found")
        
        # Check ownership
        if str(secret.owner_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to access this secret")
        
        return {
            "id": str(secret.id),
            "key": secret.key,
            "environment": secret.environment,
            "description": secret.description,
            "created_at": secret.created_at.isoformat() if secret.created_at else None,
            "updated_at": secret.updated_at.isoformat() if secret.updated_at else None,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{secret_id}", response_model=Dict[str, str])
async def update_secret(
    secret_id: str,
    secret_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    Update a secret
    
    Updates an existing secret with new information.
    """
    try:
        query = select(EnvironmentSecret).filter(EnvironmentSecret.id == secret_id)
        result = await db.execute(query)
        secret = result.scalar_one_or_none()
        if not secret:
            raise HTTPException(status_code=404, detail="Secret not found")
        
        # Check ownership
        if str(secret.owner_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to update this secret")
        
        # Update fields
        if 'key' in secret_data:
            secret.key = secret_data['key']
        
        if 'value' in secret_data:
            secret.value = encrypt_value(secret_data['value'])
        
        if 'environment' in secret_data:
            secret.environment = secret_data['environment']
        
        if 'description' in secret_data:
            secret.description = secret_data['description']
        
        await db.commit()
        await db.refresh(secret)
        
        return {"message": "Secret updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{secret_id}", response_model=Dict[str, str])
async def delete_secret(
    secret_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    Delete a secret
    
    Deletes a secret from the system. This operation cannot be undone.
    """
    try:
        query = select(EnvironmentSecret).filter(EnvironmentSecret.id == secret_id)
        result = await db.execute(query)
        secret = result.scalar_one_or_none()
        if not secret:
            raise HTTPException(status_code=404, detail="Secret not found")
        
        # Check ownership
        if str(secret.owner_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to delete this secret")
        
        await db.delete(secret)
        await db.commit()
        
        return {"message": "Secret deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/environments/", response_model=List[str])
async def get_environments(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_db)
):
    """
    Get all environments
    
    Returns a list of all unique environments in the system.
    """
    try:
        query = select(EnvironmentSecret.environment).distinct().filter(
            EnvironmentSecret.owner_id == current_user.id
        )
        result = await db.execute(query)
        environments = result.scalars().all()
        return [env for env in environments if env]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
