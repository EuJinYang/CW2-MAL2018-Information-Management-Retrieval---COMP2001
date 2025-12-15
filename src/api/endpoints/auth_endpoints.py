"""
Authentication API endpoints
"""
from fastapi import APIRouter, HTTPException, status, Form, Depends
from typing import Optional
import logging

from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.api.auth import (
    verify_external_credentials, 
    create_session_token, 
    get_current_user,
    verify_session_token
)
from src.database.connection import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter()

# Define response models
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]
    message: str

class LogoutResponse(BaseModel):
    message: str
    user_id: int

class VerifyResponse(BaseModel):
    valid: bool
    user: Dict[str, Any]

class TestResponse(BaseModel):
    valid: bool
    message: str
    email: str

class RegisterResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]
    message: str

@router.post("/login", response_model=LoginResponse)
async def login(
    email: str = Form(...),
    password: str = Form(...)
):
    """
    Authenticate user with external API and create session
    """
    try:
        # Verify credentials with external API
        is_valid = verify_external_credentials(email, password)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Get or create user in our database
        db = get_db_connection()
        user_data = db.get_user_by_email(email)
        
        if not user_data:
            # Create new user
            user_id = db.create_user({
                "email": email,
                "username": email.split("@")[0],
                "role": "user"
            })
            user_data = db.get_user_by_id(user_id)
        else:
            # Update last login
            user_id = user_data["UserID"]
            db.update_user_last_login(user_id)
        
        # Create session token
        token = create_session_token(email, user_id)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 24 * 60 * 60,  # 24 hours in seconds
            "user": {
                "user_id": user_id,
                "email": email,
                "username": user_data["Username"],
                "role": user_data["Role"]
            },
            "message": "Login successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during authentication"
        )

@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: dict = Depends(get_current_user)
):
    """
    Logout user - client should discard token
    """
    return {
        "message": "Logout successful. Please discard your token.",
        "user_id": current_user.user_id
    }

@router.get("/verify", response_model=VerifyResponse)
async def verify_session(
    current_user: dict = Depends(get_current_user)
):
    """
    Verify current session is valid
    """
    return {
        "valid": True,
        "user": {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "username": current_user.username,
            "role": current_user.role
        }
    }

@router.post("/test", response_model=TestResponse)
async def test_credentials(
    email: str = Form(...),
    password: str = Form(...)
):
    """
    Test credentials without creating a session
    """
    try:
        is_valid = verify_external_credentials(email, password)
        
        if is_valid:
            return {
                "valid": True,
                "message": "Credentials are valid",
                "email": email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
            
    except Exception as e:
        logger.error(f"Error testing credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error testing credentials"
        )

@router.post("/register", response_model=RegisterResponse)
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
    username: Optional[str] = Form(None)
):
    """
    Register a new user (using external authentication)
    Note: The external API doesn't have registration, so this just creates a local user
    after verifying credentials are valid
    """
    try:
        # Verify credentials are valid with external API
        is_valid = verify_external_credentials(email, password)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid credentials or user not registered with external service"
            )
        
        # Check if user already exists in our DB
        db = get_db_connection()
        existing_user = db.get_user_by_email(email)
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already registered"
            )
        
        # Create user in our database
        username = username or email.split("@")[0]
        user_id = db.create_user({
            "email": email,
            "username": username,
            "role": "user"
        })
        
        # Create session token
        token = create_session_token(email, user_id)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "user_id": user_id,
                "email": email,
                "username": username,
                "role": "user"
            },
            "message": "Registration successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during registration"
        )