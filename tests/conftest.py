"""
Pytest configuration and fixtures
"""
import pytest
import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api.app import app

@pytest.fixture
def client():
    """Test client fixture"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    with patch('src.database.connection.get_db_connection') as mock:
        mock_db = Mock()
        mock.return_value = mock_db
        yield mock_db

@pytest.fixture
def mock_auth():
    """Mock authentication"""
    with patch('src.api.auth.verify_token') as mock:
        mock.return_value = {"valid": True, "email": "test@example.com"}
        yield mock

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role": "user",
        "created_at": "2023-01-01T00:00:00"
    }

@pytest.fixture
def sample_trail_data():
    """Sample trail data for testing"""
    return {
        "trail_id": 1,
        "trail_name": "Test Trail",
        "difficulty": "Easy",
        "length": 5.0,
        "route_type": "Loop",
        "user_id": 1,
        "is_public": True
    }

@pytest.fixture
def auth_headers():
    """Authentication headers for testing"""
    return {"Authorization": "Bearer test_token"}