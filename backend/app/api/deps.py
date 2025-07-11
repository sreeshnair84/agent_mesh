"""
API dependencies
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generator, Optional

from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_user
from app.models.user import User, UserRole


async def get_current_user_from_db(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> User:
    """
    Get current user from database
    """
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
        role=UserRole.DEVELOPER,
        is_active=True,
        is_verified=True
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
