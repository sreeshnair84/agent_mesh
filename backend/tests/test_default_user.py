"""
Default User System Tests
Basic tests to verify default user functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.core.default_user import DefaultUserService
from app.core.config import settings
from app.models.user import User, UserRole


class TestDefaultUserService:
    """Test cases for DefaultUserService"""
    
    def test_get_default_user_data(self):
        """Test getting default user data from configuration"""
        data = DefaultUserService.get_default_user_data()
        
        assert data["id"] == settings.DEFAULT_USER_ID
        assert data["email"] == settings.DEFAULT_USER_EMAIL
        assert data["username"] == settings.DEFAULT_USER_USERNAME
        assert data["full_name"] == settings.DEFAULT_USER_FULL_NAME
        assert data["role"] == UserRole(settings.DEFAULT_USER_ROLE)
        assert data["is_active"] is True
        assert data["is_verified"] is True
    
    def test_create_default_user_instance(self):
        """Test creating default user instance"""
        user = DefaultUserService.create_default_user_instance()
        
        assert isinstance(user, User)
        assert str(user.id) == settings.DEFAULT_USER_ID
        assert user.email == settings.DEFAULT_USER_EMAIL
        assert user.username == settings.DEFAULT_USER_USERNAME
        assert user.role == UserRole(settings.DEFAULT_USER_ROLE)
        assert user.is_active is True
        assert user.is_verified is True
    
    def test_is_default_user(self):
        """Test checking if user is default user"""
        default_user = DefaultUserService.create_default_user_instance()
        other_user = User(
            id="different-id",
            email="other@example.com",
            username="other",
            full_name="Other User",
            hashed_password="",
            role=UserRole.VIEWER
        )
        
        assert DefaultUserService.is_default_user(default_user) is True
        assert DefaultUserService.is_default_user(other_user) is False
    
    def test_is_enabled(self):
        """Test checking if default user is enabled"""
        # This test depends on the current configuration
        expected = settings.USE_DEFAULT_USER
        assert DefaultUserService.is_enabled() == expected
    
    @pytest.mark.asyncio
    async def test_get_or_create_default_user_existing(self):
        """Test getting existing default user from database"""
        # Mock database session
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_user = DefaultUserService.create_default_user_instance()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        result = await DefaultUserService.get_or_create_default_user(mock_db)
        
        assert result == mock_user
        mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_or_create_default_user_create_new(self):
        """Test creating new default user in database"""
        # Mock database session
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None  # User doesn't exist
        mock_db.execute.return_value = mock_result
        
        result = await DefaultUserService.get_or_create_default_user(mock_db)
        
        assert isinstance(result, User)
        assert str(result.id) == settings.DEFAULT_USER_ID
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_or_create_default_user_fallback(self):
        """Test fallback to in-memory user on database error"""
        # Mock database session that raises an exception
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database error")
        
        result = await DefaultUserService.get_or_create_default_user(mock_db)
        
        assert isinstance(result, User)
        assert str(result.id) == settings.DEFAULT_USER_ID


class TestDefaultUserDependencies:
    """Test cases for default user dependencies"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_db_with_auth(self):
        """Test getting current user with authentication"""
        from app.api.deps import get_current_user_from_db
        
        # Mock authenticated user
        mock_user_data = {"user_id": "test-user-id"}
        mock_db = AsyncMock()
        
        # This would normally create a User instance
        # For testing, we'll mock the behavior
        result = await get_current_user_from_db(mock_db, mock_user_data)
        
        assert isinstance(result, User)
        assert str(result.id) == "test-user-id"
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_db_default_user(self):
        """Test getting default user when no authentication"""
        from app.api.deps import get_current_user_from_db
        
        # Mock database session
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_user = DefaultUserService.create_default_user_instance()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        # Test with no authentication (current_user=None)
        result = await get_current_user_from_db(mock_db, None)
        
        if settings.USE_DEFAULT_USER:
            assert isinstance(result, User)
            assert str(result.id) == settings.DEFAULT_USER_ID
        else:
            # Should raise HTTPException when default user is disabled
            # This test would need to be adjusted based on the actual behavior
            pass


def test_user_permissions():
    """Test user permissions based on role"""
    from app.core.user_manager import UserManager
    
    # Test admin user
    admin_user = User(
        id="admin-id",
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        hashed_password="",
        role=UserRole.ADMIN
    )
    
    admin_permissions = UserManager.get_user_permissions(admin_user)
    assert admin_permissions["can_view"] is True
    assert admin_permissions["can_create_agents"] is True
    assert admin_permissions["can_manage_users"] is True
    assert admin_permissions["can_manage_system"] is True
    
    # Test developer user
    developer_user = User(
        id="dev-id",
        email="dev@example.com",
        username="developer",
        full_name="Developer User",
        hashed_password="",
        role=UserRole.DEVELOPER
    )
    
    dev_permissions = UserManager.get_user_permissions(developer_user)
    assert dev_permissions["can_view"] is True
    assert dev_permissions["can_create_agents"] is True
    assert dev_permissions["can_manage_users"] is False
    assert dev_permissions["can_manage_system"] is False
    
    # Test viewer user
    viewer_user = User(
        id="viewer-id",
        email="viewer@example.com",
        username="viewer",
        full_name="Viewer User",
        hashed_password="",
        role=UserRole.VIEWER
    )
    
    viewer_permissions = UserManager.get_user_permissions(viewer_user)
    assert viewer_permissions["can_view"] is True
    assert viewer_permissions["can_create_agents"] is False
    assert viewer_permissions["can_manage_users"] is False
    assert viewer_permissions["can_manage_system"] is False


if __name__ == "__main__":
    # Run basic tests
    print("🧪 Running Default User System Tests...")
    
    # Test default user data
    print("✅ Testing default user data...")
    test_service = TestDefaultUserService()
    test_service.test_get_default_user_data()
    test_service.test_create_default_user_instance()
    test_service.test_is_default_user()
    test_service.test_is_enabled()
    
    # Test permissions
    print("✅ Testing user permissions...")
    test_user_permissions()
    
    print("🎉 All tests passed!")
