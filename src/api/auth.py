"""
Authentication and authorization utilities for TrailService
"""
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging
import secrets
import datetime
from datetime import timezone

from src.models.user import User
from src.database.connection import get_db_connection

logger = logging.getLogger(__name__)

# External Authenticator API URL
AUTH_API_URL = "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users"

# Create security schemes
optional_security = HTTPBearer(auto_error=False)
required_security = HTTPBearer(auto_error=True)

# For session tokens
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
SESSION_DURATION_HOURS = 24

def verify_external_credentials(email: str, password: str) -> bool:
    """
    Verify credentials with external API
    Returns True if valid, False otherwise
    """
    try:
        credentials = {
            "email": email,
            "password": password
        }
        
        response = requests.post(AUTH_API_URL, json=credentials, timeout=10)
        
        if response.status_code == 200:
            # API returns ["Verified","True"] for valid credentials
            result = response.json()
            return isinstance(result, list) and len(result) >= 2 and result[0] == "Verified" and result[1] == "True"
        
        return False
        
    except requests.RequestException as e:
        logger.error(f"Error verifying credentials: {e}")
        return False

def create_session_token(email: str, user_id: int) -> str:
    """
    Create a JWT session token
    """
    import jwt
    
    token_data = {
        "sub": email,
        "user_id": user_id,
        "email": email,
        "exp": datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(hours=SESSION_DURATION_HOURS),
        "iat": datetime.datetime.now(tz=timezone.utc)
    }
    
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify our session token
    """
    import jwt
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check expiration
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            exp_datetime = datetime.datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            if exp_datetime < datetime.datetime.now(tz=timezone.utc):
                logger.warning("Token has expired")
                return None
        
        return {
            "valid": True,
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "exp": payload.get("exp")
        }
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Optional[User]:
    """
    Get current authenticated user from session token if provided
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # Verify session token
    auth_data = verify_session_token(token)
    if not auth_data or not auth_data.get("valid"):
        logger.warning("Invalid or expired session token")
        return None
    
    # Get user from our database
    user_id = auth_data.get("user_id")
    if not user_id:
        return None
    
    db = get_db_connection()
    try:
        user_data = db.get_user_by_id(user_id)
        if not user_data:
            return None
        
        user = User().from_dict(user_data)
        return user
    except Exception as e:
        logger.error(f"Error getting user from DB: {e}")
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(required_security)
) -> User:
    """
    Get current authenticated user from session token (required)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Verify session token
    auth_data = verify_session_token(token)
    if not auth_data or not auth_data.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from our database
    user_id = auth_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user in token",
        )
    
    db = get_db_connection()
    try:
        user_data = db.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        user = User().from_dict(user_data)
        
        # Update last activity (optional)
        db.update_user_last_login(user.user_id)
        user.last_login = db.get_current_timestamp()
        
        return user
    except Exception as e:
        logger.error(f"Error getting user from DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing authentication",
        )

# Keep existing role-checking functions
def require_role(required_role: str):
    """
    Dependency to require specific user role
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        user_role = str(current_user.role).strip().lower()
        required = str(required_role).strip().lower()
        
        # Admin has access to everything
        if user_role == "admin":
            return current_user
        
        # Check for required role
        if user_role == required:
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires {required_role} role"
        )
    return role_checker

def require_ownership_or_admin(resource_user_id: int):
    """
    Dependency to require ownership or admin role
    """
    async def ownership_checker(current_user: User = Depends(get_current_user)):
        if current_user.user_id != resource_user_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this resource"
            )
        return current_user
    return ownership_checker