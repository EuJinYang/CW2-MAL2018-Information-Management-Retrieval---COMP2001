from .base import BaseModel
from .user import User
from .location import Location
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class Difficulty(str, Enum):
    EASY = "Easy"
    MODERATE = "Moderate"
    HARD = "Hard"

class RouteType(str, Enum):
    LOOP = "Loop"
    OUT_AND_BACK = "Out & back"
    POINT_TO_POINT = "Point-to-point"

@dataclass
class TrailPoint(BaseModel):
    point_id: int = 0
    point_order: int = 0
    latitude: float = 0.0
    longitude: float = 0.0
    description: Optional[str] = None
    elevation: Optional[float] = None
    created_at: Optional[datetime] = None
    
    def get_id(self) -> int:
        return self.point_id
    
    def get_coordinates(self) -> tuple[float, float]:
        return (self.latitude, self.longitude)
    
    def set_coordinates(self, lat: float, lon: float) -> None:
        self.latitude = lat
        self.longitude = lon
    
    def get_elevation(self) -> Optional[float]:
        return self.elevation
    
    def set_elevation(self, elevation: float) -> None:
        self.elevation = elevation
    
    def to_dict(self) -> dict:
        result = {
            "point_id": self.point_id,
            "point_order": self.point_order,
            "latitude": self.latitude,
            "longitude": self.longitude
        }
        if self.description:
            result["description"] = self.description
        if self.elevation is not None:
            result["elevation"] = self.elevation
        if self.created_at:
            result["created_at"] = self.created_at.isoformat()
        return result
    
    def from_dict(self, data: dict) -> 'TrailPoint':
        self.point_id = data.get("point_id", 0)
        self.point_order = data.get("point_order", 0)
        self.latitude = float(data.get("latitude", 0))
        self.longitude = float(data.get("longitude", 0))
        self.description = data.get("description")
        self.elevation = data.get("elevation")
        if "created_at" in data and data["created_at"]:
            self.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        return self

@dataclass
class Trail(BaseModel):
    trail_id: int = 0
    trail_name: str = ""
    location_id: Optional[int] = None
    difficulty: Difficulty = Difficulty.EASY
    length: float = 0.0
    elevation_gain: Optional[int] = None
    est_time_min: int = 0
    est_time_max: int = 0
    route_type: RouteType = RouteType.LOOP
    description: Optional[str] = None
    user_id: int = 0
    is_public: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Relationships
    location: Optional[Location] = None
    user: Optional[User] = None
    points: List[TrailPoint] = field(default_factory=list)
    
    def get_id(self) -> int:
        return self.trail_id
    
    def set_id(self, trail_id: int) -> None:
        self.trail_id = trail_id
    
    def get_name(self) -> str:
        return self.trail_name
    
    def set_name(self, name: str) -> None:
        self.trail_name = name
    
    def get_difficulty(self) -> Difficulty:
        return self.difficulty
    
    def set_difficulty(self, difficulty: str) -> None:
        try:
            self.difficulty = Difficulty(difficulty)
        except ValueError:
            raise ValueError(f"Difficulty must be one of: {[d.value for d in Difficulty]}")
    
    def get_length(self) -> float:
        return self.length
    
    def set_length(self, length: float) -> None:
        if length <= 0:
            raise ValueError("Length must be positive")
        self.length = length
    
    def get_route_type(self) -> RouteType:
        return self.route_type
    
    def set_route_type(self, route_type: str) -> None:
        try:
            self.route_type = RouteType(route_type)
        except ValueError:
            raise ValueError(f"Route type must be one of: {[r.value for r in RouteType]}")
    
    def get_user(self) -> Optional[User]:
        return self.user
    
    def set_user(self, user: User) -> None:
        self.user = user
        self.user_id = user.user_id if user else 0
    
    def get_location(self) -> Optional[Location]:
        return self.location
    
    def set_location(self, location: Location) -> None:
        self.location = location
        self.location_id = location.location_id if location else None
    
    def add_point(self, point: TrailPoint) -> None:
        """Add a trail point"""
        self.points.append(point)
    
    def remove_point(self, point_id: int) -> bool:
        """Remove a trail point by ID"""
        for i, point in enumerate(self.points):
            if point.point_id == point_id:
                self.points.pop(i)
                return True
        return False
    
    def get_points_sorted(self) -> List[TrailPoint]:
        """Get points sorted by order"""
        return sorted(self.points, key=lambda p: p.point_order)
    
    def calculate_estimated_time(self) -> tuple[int, int]:
        """Calculate estimated time based on length and difficulty"""
        base_time_per_km = {
            Difficulty.EASY: 15,
            Difficulty.MODERATE: 20,
            Difficulty.HARD: 25
        }
        base_minutes = self.length * base_time_per_km.get(self.difficulty, 20)
        return (int(base_minutes * 0.8), int(base_minutes * 1.2))
    
    def update_timestamps(self) -> None:
        """Update created/updated timestamps"""
        now = datetime.now()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now
    
    def to_dict(self) -> dict:
        result = {
            "trail_id": self.trail_id,
            "trail_name": self.trail_name,
            "difficulty": self.difficulty.value,
            "length": self.length,
            "est_time_min": self.est_time_min,
            "est_time_max": self.est_time_max,
            "route_type": self.route_type.value,
            "user_id": self.user_id,
            "is_public": self.is_public
        }
        
        if self.location_id:
            result["location_id"] = self.location_id
        if self.elevation_gain is not None:
            result["elevation_gain"] = self.elevation_gain
        if self.description:
            result["description"] = self.description
        if self.created_at:
            result["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            result["updated_at"] = self.updated_at.isoformat()
        if self.location:
            result["location"] = self.location.to_dict()
        if self.user:
            result["user"] = self.user.to_dict()
        if self.points:
            result["points"] = [p.to_dict() for p in self.get_points_sorted()]
        
        return result
    
    def from_dict(self, data: dict) -> 'Trail':
        self.trail_id = data.get("trail_id", 0)
        self.trail_name = data.get("trail_name", "")
        self.location_id = data.get("location_id")
        self.difficulty = Difficulty(data.get("difficulty", "Easy"))
        self.length = float(data.get("length", 0))
        self.elevation_gain = data.get("elevation_gain")
        self.est_time_min = data.get("est_time_min", 0)
        self.est_time_max = data.get("est_time_max", 0)
        self.route_type = RouteType(data.get("route_type", "Loop"))
        self.description = data.get("description")
        self.user_id = data.get("user_id", 0)
        self.is_public = data.get("is_public", True)
        
        if "created_at" in data and data["created_at"]:
            self.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if "updated_at" in data and data["updated_at"]:
            self.updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        
        if "location" in data:
            from src.models.location import Location
            self.location = Location().from_dict(data["location"])
        if "user" in data:
            from src.models.user import User
            self.user = User().from_dict(data["user"])
        if "points" in data:
            self.points = [TrailPoint().from_dict(p) for p in data["points"]]
        
        return self
    
    def validate(self) -> bool:
        return bool(
            self.trail_name.strip() and 
            self.length > 0 and 
            self.est_time_min > 0 and 
            self.est_time_max >= self.est_time_min and 
            self.user_id > 0
        )