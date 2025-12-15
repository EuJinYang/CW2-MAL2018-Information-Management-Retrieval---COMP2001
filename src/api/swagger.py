"""
Swagger/OpenAPI documentation setup
"""
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI
import yaml
import os

def custom_openapi(app: FastAPI):
    """
    Generate custom OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter session token obtained from authentication"
        }
    }
    
    # Customize documentation
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png",
        "altText": "TrailService Logo"
    }
    
    # Add tags metadata
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication and session management"
        },
        {
            "name": "Trails",
            "description": "Trail management operations. Create, read, update, and delete hiking trails."
        },
        {
            "name": "Locations",
            "description": "Location management for trails (countries, cities, specific locations)."
        },
        {
            "name": "Users",
            "description": "User profile and management operations."
        },
        {
            "name": "Health",
            "description": "Health check and service status endpoints."
        }
    ]
    
    # Add security requirements to specific endpoints only
    for path, methods in openapi_schema["paths"].items():
        for method, details in methods.items():
            
            # Public endpoints - no authentication required
            public_paths = [
                "/", "/health", "/api", "/api/v1/status",
                "/docs", "/redoc", "/openapi.json",
                "/api/v1/auth/login", "/api/v1/auth/test", "/api/v1/auth/register"
            ]
            
            # Endpoints that require authentication
            if path not in public_paths:
                # Check if it's a GET request to public resources
                is_get_request = method.lower() == "get"
                
                # These GET endpoints don't require auth (they're public or optional)
                public_get_endpoints = [
                    "/api/v1/trails",
                    "/api/v1/locations",
                    "/api/v1/countries",
                    "/api/v1/countries/{country_id}/cities",
                    "/api/v1/locations/{location_id}",
                    "/api/v1/users/{user_id}",
                    "/api/v1/users/{user_id}/trails"
                ]
                
                # Check if this is a public GET endpoint
                is_public_get = False
                for public_endpoint in public_get_endpoints:
                    if path.startswith(public_endpoint.replace("{country_id}", "").replace("{location_id}", "").replace("{user_id}", "")):
                        is_public_get = True
                        break
                
                # Add security only to protected endpoints
                if not (is_get_request and is_public_get):
                    # Add security requirement
                    details["security"] = [{"BearerAuth": []}]
                    
                    # Add 401 response
                    if "401" not in details.get("responses", {}):
                        details.setdefault("responses", {})["401"] = {
                            "description": "Unauthorized - Invalid or expired token",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "detail": "Invalid or expired token"
                                    }
                                }
                            }
                        }
            
            # Add 500 response to all endpoints
            details.setdefault("responses", {})["500"] = {
                "description": "Internal Server Error",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": "Internal server error occurred"
                        }
                    }
                }
            }
            
            # Add appropriate responses for authentication endpoints
            if "/api/v1/auth/" in path:
                if "200" not in details.get("responses", {}):
                    if "login" in path or "register" in path:
                        details.setdefault("responses", {})["200"] = {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "access_token": "eyJhbGciOiJIUzI1NiIs...",
                                        "token_type": "bearer",
                                        "expires_in": 86400,
                                        "user": {
                                            "user_id": 1,
                                            "email": "user@example.com",
                                            "username": "user123",
                                            "role": "user"
                                        },
                                        "message": "Login successful"
                                    }
                                }
                            }
                        }
                    elif "verify" in path:
                        details.setdefault("responses", {})["200"] = {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "valid": True,
                                        "user": {
                                            "user_id": 1,
                                            "email": "user@example.com",
                                            "username": "user123",
                                            "role": "user"
                                        }
                                    }
                                }
                            }
                        }
                
                if "401" not in details.get("responses", {}):
                    details.setdefault("responses", {})["401"] = {
                        "description": "Unauthorized - Invalid credentials",
                        "content": {
                            "application/json": {
                                "example": {
                                    "detail": "Invalid email or password"
                                }
                            }
                        }
                    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def setup_swagger(app: FastAPI):
    """
    Setup Swagger documentation
    """
    # Set custom OpenAPI
    app.openapi = lambda: custom_openapi(app)
    
    # Export OpenAPI spec to file
    openapi_schema = custom_openapi(app)
    
    # Create docs directory if it doesn't exist
    os.makedirs("docs", exist_ok=True)
    
    # Save as JSON
    import json
    with open("docs/openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    # Save as YAML
    with open("docs/openapi.yaml", "w") as f:
        yaml.dump(openapi_schema, f, default_flow_style=False)
    
    print("OpenAPI documentation generated in docs/ directory")
    return openapi_schema