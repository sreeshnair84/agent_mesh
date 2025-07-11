"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    hash_password,
    verify_token,
    get_current_user
)
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, LoginResponse, Token

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    User login endpoint
    """
    # In a real implementation, you would:
    # 1. Query the database for the user
    # 2. Verify the password
    # 3. Create tokens
    # 4. Update login tracking
    
    # For now, we'll simulate a successful login
    if form_data.username == "admin" and form_data.password == "admin123":
        # Create tokens
        access_token = create_access_token(
            data={"sub": "admin-user-id", "role": "admin", "username": "admin"}
        )
        refresh_token = create_refresh_token(
            data={"sub": "admin-user-id", "username": "admin"}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,  # 30 minutes
            "user": {
                "id": "admin-user-id",
                "email": "admin@agentmesh.com",
                "username": "admin",
                "full_name": "System Administrator",
                "role": "admin",
                "is_active": True,
                "is_verified": True
            }
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    User registration endpoint
    """
    # In a real implementation, you would:
    # 1. Validate user data
    # 2. Check if user already exists
    # 3. Hash password
    # 4. Create user in database
    # 5. Send verification email
    
    # For now, we'll simulate successful registration
    return {
        "id": "new-user-id",
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "role": "viewer",
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.utcnow().isoformat()
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token
    """
    try:
        payload = verify_token(token)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": payload.get("sub"), "username": payload.get("username")}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800
        }
    
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    User logout endpoint
    """
    # In a real implementation, you would:
    # 1. Invalidate the current session
    # 2. Add token to blacklist
    # 3. Update logout tracking
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user information
    """
    # In a real implementation, you would query the database
    # For now, we'll return mock data
    return {
        "id": current_user.get("user_id"),
        "email": "user@example.com",
        "username": current_user.get("token_data", {}).get("username", "user"),
        "full_name": "User Name",
        "role": current_user.get("token_data", {}).get("role", "viewer"),
        "is_active": True,
        "is_verified": True,
        "created_at": datetime.utcnow().isoformat()
    }


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify user email
    """
    # Implementation for email verification
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Forgot password endpoint
    """
    # Implementation for password reset
    return {"message": "Password reset email sent"}


@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password endpoint
    """
    # Implementation for password reset
    return {"message": "Password reset successfully"}
