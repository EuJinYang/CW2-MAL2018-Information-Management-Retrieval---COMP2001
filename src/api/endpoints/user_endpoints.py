"""
User management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
import logging

from src.api.auth import get_current_user, require_role, get_optional_user
from src.models.user import User
from src.database.connection import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter()

# Protected endpoint - requires auth
@router.get("/users/me", response_model=dict)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)  # Changed from dict to User
):
    """
    Get current user's profile  - PROTECTED ENDPOINT
    """
    try:
        db = get_db_connection()
        
        # Get user's trails count
        trails_count = db.execute_query(
            "SELECT COUNT(*) as count FROM CW2.Trail WHERE UserID = ?",
            (current_user.user_id,)  # Changed from ["user_id"] to .user_id
        )[0]["count"]
        
        # Get user's reviews count
        reviews_count = db.execute_query(
            "SELECT COUNT(*) as count FROM CW2.Review WHERE UserID = ?",
            (current_user.user_id,)  # Changed from ["user_id"] to .user_id
        )[0]["count"]
        
        # Get recent activity
        recent_activity = db.execute_query(
            """
            SELECT TOP 10 Action, ActionDate, Details 
            FROM CW2.Trail_Log 
            WHERE UserID = ? 
            ORDER BY ActionDate DESC
            """,
            (current_user.user_id,)  # Changed from ["user_id"] to .user_id
        )
        
        return {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "last_login": current_user.last_login,
            "stats": {
                "trails_created": trails_count,
                "reviews_written": reviews_count
            },
            "recent_activity": recent_activity
        }
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user profile"
        )

# Admin-only endpoint
@router.get("/users", response_model=List[dict])
async def get_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("admin"))  # Changed from dict to User
):
    """
    Get all users (admin only)
    """
    try:
        db = get_db_connection()
        
        query = """
        SELECT UserID, Username, Email, Role, CreatedAt, LastLogin
        FROM CW2.[User]
        WHERE 1=1
        """
        
        params = []
        
        if role:
            query += " AND Role = ?"
            params.append(role)
        
        if search:
            query += " AND (Username LIKE ? OR Email LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        query += " ORDER BY CreatedAt DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
        
        users = db.execute_query(query, tuple(params))
        return users
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )

@router.get("/users/{user_id}", response_model=dict)
async def get_user_by_id(
    user_id: int,
    current_user: Optional[User] = Depends(get_optional_user)  # Changed from dict to Optional[User]
):
    """
    Get user by ID
    # Public: basic info only (username, public stats)
    # Self/Admin: full info
    """
    try:
        db = get_db_connection()
        
        # Get user
        user_data = db.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Prepare response
        response = {
            "user_id": user_data["UserID"],
            "username": user_data["Username"],
            "public_stats": {}
        }
        
        # Add public stats (available to everyone)
        trails_count = db.execute_query(
            "SELECT COUNT(*) as count FROM CW2.Trail WHERE UserID = ? AND IsPublic = 1",
            (user_id,)
        )[0]["count"]

        response["public_stats"]["public_trails"] = trails_count
        
        # Add private info if user is viewing themselves or is admin
        if current_user and (current_user.user_id == user_id or current_user.role == "admin"):  # Fixed attribute access
            response["email"] = user_data["Email"]
            response["role"] = user_data["Role"]
            response["created_at"] = user_data["CreatedAt"]
            response["last_login"] = user_data["LastLogin"]
            
            # Add private stats
            total_trails = db.execute_query(
                "SELECT COUNT(*) as count FROM CW2.Trail WHERE UserID = ?",
                (user_id,)
            )[0]["count"]
            
            response["private_stats"] = {
                "total_trails": total_trails,
                "private_trails": total_trails - trails_count
            }
        
        # Admin gets additional info
        if current_user and current_user.role == "admin":  # Fixed attribute access and None check
            recent_actions = db.execute_query(
                """
                SELECT TOP 5 Action, ActionDate, Details 
                FROM CW2.Trail_Log 
                WHERE UserID = ? 
                ORDER BY ActionDate DESC
                """,
                (user_id,)
            )
            response["recent_actions"] = recent_actions
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user"
        )

# Admin-only endpoint
@router.put("/users/{user_id}/role", response_model=dict)
async def update_user_role(
    user_id: int,
    role_data: dict,
    current_user: User = Depends(require_role("admin"))  # Changed from dict to User
):
    """
    Update user role (admin only)
    """
    try:
        new_role = role_data.get("role")
        if not new_role or new_role not in ["admin", "user", "moderator"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'admin', 'user', or 'moderator'"
            )
        
        # Cannot change own role
        if user_id == current_user.user_id:  # Changed from ["user_id"] to .user_id
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own role"
            )
        
        db = get_db_connection()
        
        # Check if user exists
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Update role
        query = "UPDATE CW2.[User] SET Role = ? WHERE UserID = ?"
        db.execute_update(query, (new_role, user_id))
        
        # Log the action
        db.log_trail_action(
            trail_id=None,
            user_id=current_user.user_id,  # Changed from ["user_id"] to .user_id
            action="UPDATE_USER_ROLE",
            details=f"Changed user {user_id} role from {user['Role']} to {new_role}"
        )
        
        return {
            "message": f"User role updated to {new_role}",
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user role"
        )

@router.get("/users/{user_id}/trails", response_model=List[dict])
async def get_user_trails(
    user_id: int,
    include_private: bool = Query(False, description="Include private trails (admin or owner only)"),
    current_user: Optional[User] = Depends(get_optional_user)  # Changed from dict to Optional[User]
):
    """
    Get trails created by a specific user
    # Public: public trails only
    # Self/Admin: can include private trails if requested
    """
    try:
        db = get_db_connection()
        
        # Check if user exists
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Check authorization for private trails
        can_view_private = False
        if current_user:
            can_view_private = (
                current_user.user_id == user_id or  # Changed from .user_id attribute
                current_user.role == "admin"        # Changed from .role attribute
            )
        
        query = """
        SELECT t.*, l.LocationName
        FROM CW2.Trail t
        LEFT JOIN CW2.Location l ON t.LocationID = l.LocationID
        WHERE t.UserID = ?
        """
        
        params = [user_id]
        
        if not include_private or not can_view_private:
            query += " AND t.IsPublic = 1"
        
        query += " ORDER BY t.CreatedAt DESC"
        
        trails = db.execute_query(query, tuple(params))
        return trails
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id} trails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user trails"
        )