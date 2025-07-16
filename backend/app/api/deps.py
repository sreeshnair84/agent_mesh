"""
API dependencies
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generator, Optional

from app.core.database import get_db
from app.core.security import get_current_user_optional, get_current_active_user
from app.core.default_user import default_user_service
from app.core.config import settings
from app.models.user import User, UserRole


async def get_current_user_from_db(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> User:
    """
    Get current user from database or return default user
    """
    # If default user is enabled and no authentication is provided, use default user
    if settings.USE_DEFAULT_USER and current_user is None:
        return await default_user_service.get_or_create_default_user(db)
    
    # If we have a current user from authentication, process it
    if current_user:
        user_id = current_user.get("user_id")
        
        # This would typically query the database for the user
        # For now, we'll return a mock user object
        # In a real implementation, you would do:
        # user = await db.get(User, user_id)
        # if not user:
        #     raise HTTPException(status_code=404, detail="User not found")
        # return user
        
        return User(
            id=user_id,
            email="user@example.com",
            username="user",
            full_name="User Name",
            role="developer",  # Use string directly instead of enum
            is_active=True,
            is_verified=True
        )
    
    # If no authentication and default user is disabled, raise error
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_admin_user(
    current_user: User = Depends(get_current_user_from_db)
) -> User:
    """
    Get current admin user
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_developer_user(
    current_user: User = Depends(get_current_user_from_db)
) -> User:
    """
    Get current developer user
    """
    if not current_user.is_developer():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Developer access required"
        )
    return current_user


async def get_default_user_if_enabled(
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get default user if enabled, otherwise return None
    """
    if settings.USE_DEFAULT_USER:
        return await default_user_service.get_or_create_default_user(db)
    return None


async def get_user_or_default(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> User:
    """
    Get authenticated user or default user (alias for get_current_user_from_db)
    """
    return await get_current_user_from_db(db, current_user)


def get_pagination_params(
    skip: int = 0,
    limit: int = 100,
    max_limit: int = 1000
) -> dict:
    """
    Get pagination parameters
    """
    if limit > max_limit:
        limit = max_limit
    
    return {
        "skip": skip,
        "limit": limit
    }


def get_search_params(
    q: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc"
) -> dict:
    """
    Get search parameters
    """
    return {
        "q": q,
        "category": category,
        "status": status,
        "sort_by": sort_by,
        "sort_order": sort_order
    }
