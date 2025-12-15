"""
Data validation utilities for TrailService
"""
import re
from typing import Dict, List, Tuple, Any
from datetime import datetime

def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, ""
    return False, "Invalid email format"

def validate_coordinates(latitude: float, longitude: float) -> Tuple[bool, str]:
    """Validate geographic coordinates"""
    if not (-90 <= latitude <= 90):
        return False, "Latitude must be between -90 and 90"
    if not (-180 <= longitude <= 180):
        return False, "Longitude must be between -180 and 180"
    return True, ""

def validate_trail_data(trail_data: Dict[str, Any], is_update: bool = False) -> Dict:
    """
    Validate trail creation/update data
    Returns: {"valid": bool, "errors": List[str]}
    """
    errors = []
    
    # Required fields for creation
    if not is_update:
        required_fields = ["trail_name", "difficulty", "length", "route_type"]
        for field in required_fields:
            if field not in trail_data or not trail_data[field]:
                errors.append(f"Missing required field: {field}")
    
    # Validate field values
    if "trail_name" in trail_data:
        if not isinstance(trail_data["trail_name"], str) or len(trail_data["trail_name"]) > 100:
            errors.append("Trail name must be a string under 100 characters")
    
    if "difficulty" in trail_data:
        valid_difficulties = ["Easy", "Moderate", "Hard"]
        if trail_data["difficulty"] not in valid_difficulties:
            errors.append(f"Difficulty must be one of: {', '.join(valid_difficulties)}")
    
    if "length" in trail_data:
        try:
            length = float(trail_data["length"])
            if length <= 0 or length > 999.99:
                errors.append("Length must be between 0.1 and 999.99 km")
        except (ValueError, TypeError):
            errors.append("Length must be a number")
    
    if "elevation_gain" in trail_data and trail_data["elevation_gain"] is not None:
        try:
            elevation = int(trail_data["elevation_gain"])
            if elevation < 0:
                errors.append("Elevation gain cannot be negative")
        except (ValueError, TypeError):
            errors.append("Elevation gain must be an integer")
    
    if "route_type" in trail_data:
        valid_route_types = ["Loop", "Out & back", "Point-to-point"]
        if trail_data["route_type"] not in valid_route_types:
            errors.append(f"Route type must be one of: {', '.join(valid_route_types)}")
    
    # Validate trail points if provided
    if "points" in trail_data and isinstance(trail_data["points"], list):
        for i, point in enumerate(trail_data["points"]):
            if "latitude" not in point or "longitude" not in point:
                errors.append(f"Point {i+1} must include latitude and longitude")
            else:
                try:
                    lat = float(point["latitude"])
                    lon = float(point["longitude"])
                    valid, msg = validate_coordinates(lat, lon)
                    if not valid:
                        errors.append(f"Point {i+1}: {msg}")
                except (ValueError, TypeError):
                    errors.append(f"Point {i+1}: Invalid coordinate values")
    
    # Validate feature IDs if provided
    if "feature_ids" in trail_data and isinstance(trail_data["feature_ids"], list):
        for feature_id in trail_data["feature_ids"]:
            if not isinstance(feature_id, int) or feature_id <= 0:
                errors.append("Feature IDs must be positive integers")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def sanitize_input(data: Any) -> Any:
    """
    Sanitize input data to prevent XSS
    """
    if isinstance(data, str):
        # Basic XSS prevention - escape HTML special characters
        data = (data
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    
    return data

def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password strength
    Note: Actual passwords are handled by external Authenticator API
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors