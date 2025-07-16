"""
User Management Utilities
Helper functions for user management and default user operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime, timezone

from app.models.user import User, UserRole
from app.core.default_user import default_user_service
from app.core.config import settings


class UserManager:
    """User management utility class"""
    
    @staticmethod
    async def get_user_by_id(user_id: str, db: AsyncSession) -> Optional[User]:
        """Get user by ID"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception:
            return None
    
    @staticmethod
    async def get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
        """Get user by email"""
        try:
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception:
            return None
    
    @staticmethod
    async def get_user_by_username(username: str, db: AsyncSession) -> Optional[User]:
        """Get user by username"""
        try:
            stmt = select(User).where(User.username == username)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception:
            return None
    
    @staticmethod
    async def create_user(
        email: str,
        username: str,
        full_name: str,
        hashed_password: str,
        role: UserRole = UserRole.VIEWER,
        db: AsyncSession = None
    ) -> User:
        """Create a new user"""
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            is_active=True,
            is_verified=False
        )
        
        if db:
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        return user
    
    @staticmethod
    async def update_user_login(user_id: str, db: AsyncSession) -> bool:
        """Update user login information"""
        try:
            stmt = update(User).where(User.id == user_id).values(
                last_login=datetime.now(timezone.utc),
                login_count=User.login_count + 1
            )
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception:
            return False
    
    @staticmethod
    async def deactivate_user(user_id: str, db: AsyncSession) -> bool:
        """Deactivate a user"""
        try:
            stmt = update(User).where(User.id == user_id).values(is_active=False)
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception:
            return False
    
    @staticmethod
    async def activate_user(user_id: str, db: AsyncSession) -> bool:
        """Activate a user"""
        try:
            stmt = update(User).where(User.id == user_id).values(is_active=True)
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception:
            return False
    
    @staticmethod
    async def change_user_role(user_id: str, new_role: UserRole, db: AsyncSession) -> bool:
        """Change user role"""
        try:
            stmt = update(User).where(User.id == user_id).values(role=new_role)
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception:
            return False
    
    @staticmethod
    async def get_users_by_role(role: UserRole, db: AsyncSession) -> List[User]:
        """Get all users with a specific role"""
        try:
            stmt = select(User).where(User.role == role)
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception:
            return []
    
    @staticmethod
    async def get_all_users(
        skip: int = 0, 
        limit: int = 100, 
        db: AsyncSession = None
    ) -> List[User]:
        """Get all users with pagination"""
        try:
            stmt = select(User).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception:
            return []
    
    @staticmethod
    def is_default_user(user: User) -> bool:
        """Check if user is the default user"""
        return default_user_service.is_default_user(user)
    
    @staticmethod
    async def ensure_default_user_exists(db: AsyncSession) -> User:
        """Ensure default user exists in database"""
        return await default_user_service.get_or_create_default_user(db)
    
    @staticmethod
    def get_user_permissions(user: User) -> Dict[str, bool]:
        """Get user permissions based on role"""
        permissions = {
            "can_view": True,
            "can_create_agents": user.can_create_agents(),
            "can_manage_tools": user.is_developer(),
            "can_manage_users": user.is_admin(),
            "can_manage_system": user.can_manage_system(),
            "can_access_admin": user.is_admin(),
            "can_develop": user.is_developer(),
        }
        return permissions
    
    @staticmethod
    def get_user_summary(user: User) -> Dict[str, Any]:
        """Get user summary information"""
        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_default": default_user_service.is_default_user(user),
            "permissions": UserManager.get_user_permissions(user),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "login_count": user.login_count,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }


# Global user manager instance
user_manager = UserManager()
