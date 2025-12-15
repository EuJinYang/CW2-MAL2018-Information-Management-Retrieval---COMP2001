"""
Trail management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import logging

from src.api.auth import get_current_user, get_optional_user, require_ownership_or_admin
from src.models.trail import Trail, TrailPoint, Difficulty, RouteType
from src.models.user import User
from src.database.connection import get_db_connection
from src.utils.validation import validate_trail_data
import traceback
from datetime import datetime
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/trails", response_model=dict)
async def get_trails(
    difficulty: Optional[Difficulty] = Query(None, description="Filter by difficulty"),
    min_length: Optional[float] = Query(None, ge=0.1, description="Minimum trail length in km"),
    max_length: Optional[float] = Query(None, ge=0.1, description="Maximum trail length in km"),
    location_id: Optional[int] = Query(None, description="Filter by location"),
    limit: int = Query(20, ge=1, le=100, description="Number of trails to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all public trails with optional filtering
    # Public users: see only public trails
    # Authenticated users: see public trails + their own private trails
    """
    try:
        db = get_db_connection()
        
        # Build filters
        filters = {}
        
        # Add filters that apply to all users
        if difficulty:
            filters["difficulty"] = difficulty.value
        if min_length:
            filters["min_length"] = min_length
        if max_length:
            filters["max_length"] = max_length
        if location_id:
            filters["location_id"] = location_id
        
        # Add authentication status to filters
        filters["current_user_id"] = current_user.user_id if current_user else None
        
        # Get trails from database
        trails_data = db.get_trails(filters, limit, offset)
        total_trails = db.count_trails(filters)
        
        # Convert to Trail objects
        trails = []
        for trail_data in trails_data:
            trail = Trail().from_dict(trail_data)
            trails.append({
                "trail_id": trail_data["TrailID"],
                "trail_name": trail_data["TrailName"],
                "location_id": trail_data["LocationID"],
                "difficulty": trail_data["Difficulty"],
                "length": trail_data["Length"],
                "elevation_gain": trail_data["ElevationGain"],
                "est_time_min": trail_data["EstTimeMin"],
                "est_time_max": trail_data["EstTimeMax"],
                "route_type": trail_data["RouteType"],
                "description": trail_data["Description"],
                "user_id": trail_data["UserID"],
                "is_public": trail_data["IsPublic"],
                "created_at": trail_data["CreatedAt"],
                "updated_at": trail_data["UpdatedAt"],
                "username": trail_data["Username"],
                "location_name": trail_data["LocationName"],
            })
        
        return {
            "trails": trails,
            "total": total_trails,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(trails)) < total_trails,
            "authenticated": current_user is not None
        }
    except Exception as e:
        logger.error(f"Error getting trails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving trails"
        )

@router.get("/trails/{trail_id}", response_model=dict)
async def get_trail(
    trail_id: int,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get detailed information about a specific trail
    # Public: can view public trails only
    # Authenticated: can view public trails + own private trails
    """
    try:
        db = get_db_connection()
        
        # Get trail from database
        trail_data = db.get_trail_by_id(trail_id)
        if not trail_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trail with ID {trail_id} not found"
            )
        
        # Check authorization
        is_public = trail_data.get("IsPublic", False)
        trail_user_id = trail_data.get("UserID")
        
        # Determine if user can view this trail
        can_view = (
            is_public or  # Anyone can view public trails
            (current_user and (
                current_user.user_id == trail_user_id or  # Owner can view
                current_user.role == "admin"  # Admin can view
            ))
        )
        
        if not can_view:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this trail"
            )
        
        # Get trail points
        points_data = db.get_trail_points(trail_id)
        
        # Get trail features
        features_data = db.get_trail_features(trail_id)
        
        # Get user info (Only basic info for public, full for owner/admin)
        user_data = None
        if current_user and (current_user.user_id == trail_user_id or current_user.role == "admin"):
            user_data = db.get_user_by_id(trail_user_id)
        elif is_public:
            # For public trails, show minimal user info
            user_data = db.execute_query(
                "SELECT UserID, Username FROM CW2.[User] WHERE UserID = ?",
                (trail_user_id,)
            )
            if user_data:
                user_data = user_data[0]
        
        # Get location info if exists
        location_data = None
        if trail_data.get("location_id"):
            location_data = db.get_location_by_id(trail_data.get("location_id"))
        
        # Create Trail object
        trail = Trail().from_dict(trail_data)
        if user_data:
            from src.models.user import User
            trail.user = User().from_dict(user_data)
        if location_data:
            from src.models.location import Location
            trail.location = Location().from_dict(location_data)
        
        # Add points
        for point_data in points_data:
            point = TrailPoint().from_dict(point_data)
            trail.add_point(point)
        
        # Prepare response
        response = trail.to_dict()
        response["features"] = features_data
        
        # Add review summary if trail is public or user is authorized
        if is_public or (current_user and current_user.user_id == trail_user_id):
            review_summary = db.get_trail_review_summary(trail_id)
            response["reviews"] = review_summary
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trail {trail_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving trail"
        )

# POST, PUT, DELETE endpoints remain protected (require authentication)
@router.post("/trails", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_trail(
    trail_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new trail
    """
    try:
        # Remove user_id from trail_data if provided (it should come from token)
        if "user_id" in trail_data:
            del trail_data["user_id"]
            logger.warning("user_id was provided in request but will be overridden by authenticated user")
        
        # Validate trail data
        validation_result = validate_trail_data(trail_data)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result["errors"]
            )
        
        # Create Trail object
        trail = Trail().from_dict(trail_data)
        trail.user_id = current_user.user_id  # Set from authenticated user
        
        # Calculate estimated times if not provided
        if not trail.est_time_min or not trail.est_time_max:
            est_min, est_max = trail.calculate_estimated_time()
            trail.est_time_min = est_min
            trail.est_time_max = est_max
        
        # Update timestamps
        trail.update_timestamps()
        
        # Save to database
        db = get_db_connection()
        
        try:
            # Save trail
            trail_dict = trail.to_dict()
            trail_id = db.create_trail(trail_dict)
            
            if not trail_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create trail - no trail ID returned"
                )
            
            trail.trail_id = trail_id
            
            # Save trail points if provided
            if "points" in trail_data and trail_data["points"]:
                for i, point_data in enumerate(trail_data["points"]):
                    point = TrailPoint().from_dict(point_data)
                    point.trail_id = trail_id
                    point.created_at = datetime.now()
                    point.point_order = i + 1  # Assign order based on array position
                    
                    db.create_trail_point(point.to_dict())
            
            # Save trail features if provided
            if "feature_ids" in trail_data and trail_data["feature_ids"]:
                for feature_id in trail_data["feature_ids"]:
                    db.add_trail_feature(trail_id, feature_id, current_user.user_id)
            
            # Log the creation
            db.log_trail_action(
                trail_id=trail_id,
                user_id=current_user.user_id,
                action="CREATE",
                details=f"Created trail: {trail.trail_name}"
            )
            
            # Return created trail
            return {
                "trail_id": trail_id,
                "message": "Trail created successfully",
                "trail": trail.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error creating trail in database: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating trail in database"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating trail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating trail"
        )

@router.put("/trails/{trail_id}", response_model=dict)
async def update_trail(
    trail_id: int,
    trail_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing trail
    """
    try:
        db = get_db_connection()
        
        # Check if trail exists
        existing_trail = db.get_trail_by_id(trail_id)
        if not existing_trail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trail with ID {trail_id} not found"
            )
        
        # Check ownership or admin
        if current_user.user_id != existing_trail.get("user_id") and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this trail"
            )
        
        # Validate update data
        validation_result = validate_trail_data(trail_data, is_update=True)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result["errors"]
            )

        trail_table_fields = [
            "trail_id", "trail_name", "location_id", "difficulty", "length",
            "elevation_gain", "est_time_min", "est_time_max", "route_type",
            "description", "user_id", "is_public", "created_at", "updated_at"
        ]
        
        # Filter existing_trail to only include actual Trail table fields
        filtered_existing = {
            k: v for k, v in existing_trail.items() 
            if k in trail_table_fields
        }
        
        # Merge with update data
        updated_data = {**filtered_existing, **trail_data}
        updated_data["updated_at"] = db.get_current_timestamp()
        
        success = db.update_trail(trail_id, updated_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update trail"
            )
        
        # Log the update
        db.log_trail_action(
            trail_id=trail_id,
            user_id=current_user.user_id,
            action="UPDATE",
            details=f"Updated trail: {trail_data.get('trail_name', existing_trail.get('trail_name'))}"
        )
        
        return {
            "message": "Trail updated successfully",
            "trail_id": trail_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating trail {trail_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating trail"
        )

@router.delete("/trails/{trail_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trail(
    trail_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a trail
    """
    try:
        db = get_db_connection()
        
        # Check if trail exists
        existing_trail = db.get_trail_by_id(trail_id)
        if not existing_trail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trail with ID {trail_id} not found"
            )
        
        # Check ownership or admin
        if current_user.user_id != existing_trail.get("user_id") and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this trail"
            )
        
        # Delete trail (cascade will handle related records)
        success = db.delete_trail(trail_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete trail"
            )
        
        # Log the deletion
        db.log_trail_action(
            trail_id=trail_id,
            user_id=current_user.user_id,
            action="DELETE",
            details=f"Deleted trail: {existing_trail.get('trail_name')}"
        )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trail {trail_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting trail"
        )

@router.get("/trails/{trail_id}/points", response_model=List[dict])
async def get_trail_points(
    trail_id: int,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all points for a specific trail
    # Public: can view points of public trails
    # Authenticated: can view points of public trails + own private trails
    """
    try:
        db = get_db_connection()
        
        # Check if trail exists
        trail_data = db.get_trail_by_id(trail_id)
        if not trail_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trail with ID {trail_id} not found"
            )
        
        # Check authorization
        is_public = trail_data.get("is_public", False)
        trail_user_id = trail_data.get("user_id")
        
        can_view = (
            is_public or
            (current_user and (
                current_user.user_id == trail_user_id or
                current_user.role == "admin"
            ))
        )
        
        if not can_view:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this trail"
            )
        
        # Get points
        points_data = db.get_trail_points(trail_id)
        return points_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting points for trail {trail_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving trail points"
        )

@router.post("/trails/{trail_id}/points", status_code=status.HTTP_201_CREATED)
async def add_trail_point(
    trail_id: int,
    point_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Add a new point to a trail
    """
    try:
        db = get_db_connection()
        
        # Check if trail exists and user owns it
        trail_data = db.get_trail_by_id(trail_id)
        if not trail_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trail with ID {trail_id} not found"
            )
        
        if current_user.user_id != trail_data.get("user_id") and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this trail"
            )
        
        # Validate point data
        if "latitude" not in point_data or "longitude" not in point_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Point must include latitude and longitude"
            )
        
        # Create point
        point = TrailPoint().from_dict(point_data)
        point.trail_id = trail_id
        
        # Determine next point order
        existing_points = db.get_trail_points(trail_id)
        next_order = max([p.get("point_order", 0) for p in existing_points], default=0) + 1
        point.point_order = next_order
        
        # Save to database
        point_id = db.create_trail_point(point.to_dict())
        
        # Log the action
        db.log_trail_action(
            trail_id=trail_id,
            user_id=current_user.user_id,
            action="UPDATE",
            details=f"Added point {point_id} to trail"
        )
        
        return {
            "point_id": point_id,
            "message": "Point added successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding point to trail {trail_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding trail point"
        )