"""
Security utilities and authentication
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer(auto_error=False)  # Don't auto-error to support optional auth


# Setup encryption key for environment secrets
def _get_encryption_key():
    """
    Generate a deterministic encryption key using PBKDF2
    """
    salt = settings.SECRET_KEY[:16].encode().ljust(16, b'0')  # Use first 16 chars of secret key as salt, pad if needed
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
    return key


# Create Fernet cipher using the derived key
_cipher = Fernet(_get_encryption_key())


def encrypt_value(value: str) -> str:
    """
    Encrypt a string value using Fernet symmetric encryption
    """
    if not value:
        return ""
    
    try:
        return _cipher.encrypt(value.encode()).decode()
    except Exception as e:
        logging.error(f"Encryption error: {e}")
        raise ValueError(f"Could not encrypt value: {e}")


def decrypt_value(encrypted_value: str) -> str:
    """
    Decrypt a Fernet-encrypted string
    """
    if not encrypted_value:
        return ""
    
    try:
        return _cipher.decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        logging.error(f"Decryption error: {e}")
        raise ValueError(f"Could not decrypt value: {e}")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # Refresh token expires in 7 days
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token and return payload
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logging.error(f"JWT verification failed: {e}")
        raise AuthenticationError("Invalid token")


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_password_reset_token(email: str) -> str:
    """
    Generate password reset token
    """
    delta = timedelta(hours=1)  # Reset token expires in 1 hour
    now = datetime.utcnow()
    expires = now + delta
    
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "email": email, "type": "password_reset"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token and return email
    """
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if decoded_token.get("type") != "password_reset":
            return None
            
        return decoded_token.get("email")
    except JWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user from JWT token
    """
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationError("Invalid token")
        
        # Token type validation
        token_type = payload.get("type", "access")
        if token_type != "access":
            raise AuthenticationError("Invalid token type")
        
        return {"user_id": user_id, "token_data": payload}
    
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    Get current user from JWT token (optional for default user support)
    """
    if credentials is None:
        return None
    
    return await get_current_user(credentials)


async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current active user
    """
    # In a real implementation, you would check if the user is active in the database
    # For now, we'll just return the user data
    return current_user


def require_role(required_role: str):
    """
    Decorator to require specific role
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_active_user)):
        user_role = current_user.get("token_data", {}).get("role", "viewer")
        
        role_hierarchy = {
            "viewer": 0,
            "developer": 1,
            "admin": 2,
        }
        
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return role_checker


def require_admin(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Require admin role
    """
    return require_role("admin")(current_user)


def require_developer(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Require developer role or higher
    """
    return require_role("developer")(current_user)


class RateLimiter:
    """
    Simple rate limiter
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed
        """
        now = datetime.utcnow()
        
        # Clean old entries
        self.requests = {
            k: v for k, v in self.requests.items()
            if now - v["window_start"] < timedelta(seconds=self.window_seconds)
        }
        
        if key not in self.requests:
            self.requests[key] = {
                "count": 1,
                "window_start": now
            }
            return True
        
        request_data = self.requests[key]
        
        # Check if we're still in the same window
        if now - request_data["window_start"] < timedelta(seconds=self.window_seconds):
            if request_data["count"] >= self.max_requests:
                return False
            request_data["count"] += 1
        else:
            # Start new window
            request_data["count"] = 1
            request_data["window_start"] = now
        
        return True


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW
)


async def check_rate_limit(request: Request):
    """
    Check rate limit for request
    """
    client_ip = request.client.host
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    return True
