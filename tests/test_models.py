"""
Test data models
"""
import pytest
from datetime import datetime

from src.models.user import User
from src.models.trail import Trail, TrailPoint, Difficulty, RouteType
from src.models.location import Location
from src.models.feature import Feature

class TestUserModel:
    def test_user_creation(self):
        user = User(
            user_id=1,
            username="testuser",
            email="test@example.com",
            role="user"
        )
        
        assert user.user_id == 1
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "user"
    
    def test_user_validation(self):
        user = User(
            username="validuser",
            email="valid@example.com"
        )
        
        assert user.validate() is True
        
        user.email = "invalid-email"
        assert user.validate() is False
    
    def test_user_to_dict(self):
        user = User(
            user_id=1,
            username="testuser",
            email="test@example.com"
        )
        
        user_dict = user.to_dict()
        assert "user_id" in user_dict
        assert user_dict["username"] == "testuser"
    
    def test_user_from_dict(self):
        data = {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "role": "admin"
        }
        
        user = User().from_dict(data)
        assert user.user_id == 1
        assert user.role == "admin"

class TestTrailModel:
    def test_trail_creation(self):
        trail = Trail(
            trail_id=1,
            trail_name="Test Trail",
            difficulty=Difficulty.EASY,
            length=5.0,
            route_type=RouteType.LOOP,
            user_id=1
        )
        
        assert trail.trail_id == 1
        assert trail.trail_name == "Test Trail"
        assert trail.difficulty == Difficulty.EASY
        assert trail.length == 5.0
    
    def test_trail_validation(self):
        trail = Trail(
            trail_name="Valid Trail",
            length=5.0,
            difficulty="Easy",
            route_type="Loop",
            user_id=1
        )
        
        assert trail.validate() is True
        
        trail.trail_name = ""
        assert trail.validate() is False
    
    def test_trail_points(self):
        trail = Trail(trail_id=1)
        point = TrailPoint(
            point_order=1,
            latitude=50.0,
            longitude=-4.0
        )
        
        trail.add_point(point)
        assert len(trail.points) == 1
        assert trail.get_points_sorted()[0].point_order == 1
    
    def test_calculate_estimated_time(self):
        trail = Trail(
            length=10.0,
            difficulty=Difficulty.EASY
        )
        
        min_time, max_time = trail.calculate_estimated_time()
        assert min_time > 0
        assert max_time >= min_time

class TestLocationModel:
    def test_location_coordinates(self):
        location = Location()
        location.set_coordinates(50.3964, -4.0916)
        
        lat, lon = location.get_coordinates()
        assert lat == 50.3964
        assert lon == -4.0916
        
        assert location.coordinates == "50.3964,-4.0916"
    
    def test_location_validation(self):
        location = Location(location_name="Test Location")
        assert location.validate() is True
        
        location.location_name = ""
        assert location.validate() is False

class TestFeatureModel:
    def test_feature_creation(self):
        feature = Feature(
            feature_id=1,
            feature_name="Waterfall",
            description="Trail includes a waterfall"
        )
        
        assert feature.feature_id == 1
        assert feature.feature_name == "Waterfall"
        assert feature.description is not None
    
    def test_feature_validation(self):
        feature = Feature(feature_name="Forest")
        assert feature.validate() is True
        
        feature.feature_name = ""
        assert feature.validate() is False