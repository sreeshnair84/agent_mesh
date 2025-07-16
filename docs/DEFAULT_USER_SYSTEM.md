# Default User System Documentation

## Overview

The Agent Mesh backend includes a default user system that provides seamless authentication bypass for development and testing purposes. This system allows the backend to operate without requiring actual user authentication, making it easier to develop and test features.

## Features

- **Automatic Authentication Bypass**: When enabled, all API endpoints automatically use a default user instead of requiring authentication
- **Configurable Default User**: The default user's properties can be configured via environment variables
- **Role-Based Access**: Default user supports all user roles (admin, developer, viewer)
- **Database Integration**: Default user is automatically created in the database if it doesn't exist
- **Fallback Support**: If database operations fail, the system falls back to an in-memory user instance

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```env
# Enable/disable default user system
USE_DEFAULT_USER=true

# Default user configuration
DEFAULT_USER_ID=550e8400-e29b-41d4-a716-446655440000
DEFAULT_USER_EMAIL=default@agentmesh.dev
DEFAULT_USER_USERNAME=defaultuser
DEFAULT_USER_FULL_NAME=Default User
DEFAULT_USER_ROLE=developer
```

### Default User Roles

- `admin`: Full system access, can manage users and system settings
- `developer`: Can create agents, manage tools, and access development features
- `viewer`: Read-only access to most resources

## Implementation Details

### Core Components

1. **DefaultUserService** (`app/core/default_user.py`)
   - Manages default user creation and configuration
   - Handles database operations for default user
   - Provides fallback mechanisms

2. **Authentication Dependencies** (`app/api/deps.py`)
   - `get_current_user_from_db()`: Primary dependency that returns authenticated user or default user
   - `get_user_or_default()`: Alias for the above function
   - `get_default_user_if_enabled()`: Returns default user only if enabled

3. **Security Module** (`app/core/security.py`)
   - `get_current_user_optional()`: Optional authentication that doesn't raise errors
   - Modified `HTTPBearer` to not auto-error on missing tokens

4. **User Manager** (`app/core/user_manager.py`)
   - Utilities for user management operations
   - Helper functions for default user operations

### Authentication Flow

1. **Request with Token**: Normal JWT authentication flow
2. **Request without Token (Default User Enabled)**: 
   - Returns default user from database or creates it
   - Falls back to in-memory user if database fails
3. **Request without Token (Default User Disabled)**:
   - Returns 401 Unauthorized error

## Usage Examples

### Basic API Endpoint

```python
from app.api.deps import get_current_user_from_db

@router.get("/example")
async def example_endpoint(
    current_user: User = Depends(get_current_user_from_db)
):
    # current_user will be either:
    # - Authenticated user (if token provided)
    # - Default user (if USE_DEFAULT_USER=true and no token)
    # - 401 error (if USE_DEFAULT_USER=false and no token)
    
    return {"user_id": str(current_user.id)}
```

### Check if Default User

```python
from app.core.user_manager import user_manager

@router.get("/user-info")
async def get_user_info(
    current_user: User = Depends(get_current_user_from_db)
):
    return {
        "user": user_manager.get_user_summary(current_user),
        "is_default": user_manager.is_default_user(current_user)
    }
```

### Admin-Only Endpoint

```python
from app.api.deps import get_current_admin_user

@router.get("/admin-only")
async def admin_endpoint(
    current_user: User = Depends(get_current_admin_user)
):
    # This will work with default user if DEFAULT_USER_ROLE=admin
    return {"message": "Admin access granted"}
```

## Best Practices

### Development

1. **Enable Default User**: Set `USE_DEFAULT_USER=true` in development
2. **Use Developer Role**: Set `DEFAULT_USER_ROLE=developer` for full access
3. **Unique ID**: Use a consistent UUID for `DEFAULT_USER_ID`

### Testing

1. **Test Both Modes**: Test with and without default user enabled
2. **Role Testing**: Test different default user roles
3. **Database Fallback**: Test behavior when database is unavailable

### Production

1. **Disable Default User**: Set `USE_DEFAULT_USER=false` in production
2. **Remove Default User**: Clean up default user from production database
3. **Secure Environment**: Ensure environment variables are properly secured

## Security Considerations

### Development Security

- Default user bypasses authentication entirely
- Should only be used in development/testing environments
- Default user has configurable permissions based on role

### Production Security

- **MUST** be disabled in production (`USE_DEFAULT_USER=false`)
- Remove default user from production database
- Implement proper authentication for production use

## Migration Guide

### From No Authentication to Default User

1. Add default user configuration to `.env`
2. Update API endpoints to use `get_current_user_from_db()`
3. Test endpoints with and without authentication

### From Default User to Real Authentication

1. Implement proper authentication endpoints
2. Update frontend to use authentication
3. Set `USE_DEFAULT_USER=false`
4. Test all endpoints with real authentication

## Troubleshooting

### Common Issues

1. **Default User Not Created**
   - Check database connection
   - Verify `USE_DEFAULT_USER=true`
   - Check logs for database errors

2. **Permission Denied**
   - Verify `DEFAULT_USER_ROLE` is set correctly
   - Check if endpoint requires specific role

3. **Authentication Still Required**
   - Ensure `USE_DEFAULT_USER=true`
   - Check if endpoint uses correct dependency

### Debug Information

Enable debug mode and check logs for:
- Default user creation attempts
- Database connection issues
- Authentication flow decisions

## API Reference

### Dependencies

- `get_current_user_from_db()`: Get current user or default user
- `get_current_admin_user()`: Get current admin user (requires admin role)
- `get_current_developer_user()`: Get current developer user (requires developer role)
- `get_default_user_if_enabled()`: Get default user only if enabled
- `get_user_or_default()`: Alias for `get_current_user_from_db()`

### Services

- `default_user_service`: Global default user service instance
- `user_manager`: Global user manager instance

### Configuration

All configuration is handled through environment variables and the `Settings` class in `app/core/config.py`.
