"""
Default User Service
Provides a default logged-in user for development and testing purposes
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.core.config import settings
from app.core.database import get_db


class DefaultUserService:
    """Service for managing default user functionality"""
    
    _default_user: Optional[User] = None
    
    @classmethod
    def get_default_user_data(cls) -> dict:
        """Get default user data from configuration"""
        return {
            "id": settings.DEFAULT_USER_ID,
            "email": settings.DEFAULT_USER_EMAIL,
            "username": settings.DEFAULT_USER_USERNAME,
            "full_name": settings.DEFAULT_USER_FULL_NAME,
            "role": settings.DEFAULT_USER_ROLE,  # Use string value directly
            "is_active": True,
            "is_verified": True,
            "avatar_url": None,
            "preferences": {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc),
            "login_count": 0,
        }
    
    @classmethod
    def create_default_user_instance(cls) -> User:
        """Create a default user instance"""
        if cls._default_user is None:
            data = cls.get_default_user_data()
            cls._default_user = User(
                id=data["id"],
                email=data["email"],
                username=data["username"],
                full_name=data["full_name"],
                hashed_password="",  # No password for default user
                role=data["role"],
                is_active=data["is_active"],
                is_verified=data["is_verified"],
                avatar_url=data["avatar_url"],
                preferences=data["preferences"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                last_login=data["last_login"],
                login_count=data["login_count"],
            )
        return cls._default_user
    
    @classmethod
    async def get_or_create_default_user(cls, db: AsyncSession) -> User:
        """Get or create default user in database"""
        try:
            # Try to get the user from database
            stmt = select(User).where(User.id == settings.DEFAULT_USER_ID)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                return user
            
            # Create default user in database if it doesn't exist
            user_data = cls.get_default_user_data()
            user = User(
                id=user_data["id"],
                email=user_data["email"],
                username=user_data["username"],
                full_name=user_data["full_name"],
                hashed_password="",  # No password for default user
                role=user_data["role"],
                is_active=user_data["is_active"],
                is_verified=user_data["is_verified"],
                avatar_url=user_data["avatar_url"],
                preferences=user_data["preferences"],
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            return user
            
        except Exception as e:
            # If database operations fail, return in-memory instance
            return cls.create_default_user_instance()
    
    @classmethod
    def is_default_user(cls, user: User) -> bool:
        """Check if the given user is the default user"""
        return str(user.id) == str(settings.DEFAULT_USER_ID)
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if default user functionality is enabled"""
        return settings.USE_DEFAULT_USER


# Global instance
default_user_service = DefaultUserService()
