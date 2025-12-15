"""
Test API endpoints
"""
import pytest
from fastapi import status

class TestTrailEndpoints:
    def test_get_trails(self, client, mock_db_connection, mock_auth):
        # Mock database response
        mock_db_connection.get_trails.return_value = [
            {
                "trail_id": 1,
                "trail_name": "Test Trail",
                "difficulty": "Easy",
                "length": 5.0,
                "user_id": 1
            }
        ]
        mock_db_connection.count_trails.return_value = 1
        
        response = client.get("/api/v1/trails")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "trails" in data
        assert len(data["trails"]) > 0
    
    def test_get_trail_by_id(self, client, mock_db_connection, mock_auth):
        mock_db_connection.get_trail_by_id.return_value = {
            "trail_id": 1,
            "trail_name": "Test Trail",
            "is_public": True,
            "user_id": 1
        }
        mock_db_connection.get_trail_points.return_value = []
        mock_db_connection.get_trail_features.return_value = []
        mock_db_connection.get_trail_review_summary.return_value = {}
        
        response = client.get("/api/v1/trails/1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["trail_id"] == 1
    
    def test_create_trail(self, client, mock_db_connection, mock_auth):
        # Mock authentication to return a user
        mock_auth.return_value = {
            "valid": True,
            "email": "test@example.com"
        }
        mock_db_connection.get_user_by_email.return_value = {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "role": "user"
        }
        mock_db_connection.create_trail.return_value = 1
        mock_db_connection.get_current_timestamp.return_value = "2023-01-01T00:00:00"
        
        trail_data = {
            "trail_name": "New Trail",
            "difficulty": "Easy",
            "length": 5.0,
            "route_type": "Loop"
        }
        
        response = client.post(
            "/api/v1/trails",
            json=trail_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "trail_id" in data
    
    def test_update_trail(self, client, mock_db_connection, mock_auth):
        mock_auth.return_value = {
            "valid": True,
            "email": "owner@example.com"
        }
        mock_db_connection.get_user_by_email.return_value = {
            "user_id": 1,
            "username": "owner",
            "email": "owner@example.com",
            "role": "user"
        }
        mock_db_connection.get_trail_by_id.return_value = {
            "trail_id": 1,
            "trail_name": "Old Name",
            "user_id": 1,
            "is_public": True
        }
        mock_db_connection.update_trail.return_value = True
        
        update_data = {
            "trail_name": "Updated Trail Name"
        }
        
        response = client.put(
            "/api/v1/trails/1",
            json=update_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_delete_trail(self, client, mock_db_connection, mock_auth):
        mock_auth.return_value = {
            "valid": True,
            "email": "owner@example.com"
        }
        mock_db_connection.get_user_by_email.return_value = {
            "user_id": 1,
            "username": "owner",
            "email": "owner@example.com",
            "role": "admin"
        }
        mock_db_connection.get_trail_by_id.return_value = {
            "trail_id": 1,
            "user_id": 1
        }
        mock_db_connection.delete_trail.return_value = True
        
        response = client.delete(
            "/api/v1/trails/1",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT

class TestUserEndpoints:
    def test_get_current_user(self, client, mock_db_connection, mock_auth):
        mock_auth.return_value = {
            "valid": True,
            "email": "test@example.com"
        }
        mock_db_connection.get_user_by_email.return_value = {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "role": "user"
        }
        mock_db_connection.execute_query.side_effect = [
            [{"count": 5}],  # trails count
            [{"count": 3}],  # reviews count
            []  # recent activity
        ]
        
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_id" in data
        assert "stats" in data
    
    def test_get_users_admin(self, client, mock_db_connection, mock_auth):
        mock_auth.return_value = {
            "valid": True,
            "email": "admin@example.com"
        }
        mock_db_connection.get_user_by_email.return_value = {
            "user_id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin"
        }
        mock_db_connection.execute_query.return_value = [
            {
                "user_id": 2,
                "username": "user1",
                "email": "user1@example.com",
                "role": "user"
            }
        ]
        
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

class TestHealthEndpoints:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "service" in data
        assert data["service"] == "TrailService"
    
    def test_health_check(self, client, mock_db_connection):
        mock_db_connection.test_connection.return_value = True
        
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_api_status(self, client):
        response = client.get("/api/v1/status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["api"] == "TrailService"