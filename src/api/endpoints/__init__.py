"""
API Endpoints Package
"""
from .trail_endpoints import router as trail_router
from .location_endpoints import router as location_router
from .user_endpoints import router as user_router
from .auth_endpoints import router as auth_router

__all__ = ['trail_router', 'location_router', 'user_router', 'auth_router']