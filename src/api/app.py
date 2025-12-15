"""
Main FastAPI application for TrailService microservice
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.docs import get_swagger_ui_html
import logging
from typing import Optional
import os

from src.database.connection import get_db_connection
from src.api.auth import verify_session_token as verify_token, get_current_user
from src.api.endpoints import trail_endpoints, location_endpoints, user_endpoints, auth_endpoints
from src.api.swagger import setup_swagger
from src.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..", "..")

# Create templates directory if it doesn't exist
templates_dir = os.path.join(project_root, "templates")
os.makedirs(templates_dir, exist_ok=True)

# Create static directory if it doesn't exist
static_dir = os.path.join(project_root, "static")
os.makedirs(static_dir, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="TrailService API",
    description="Microservice for managing hiking trails in a wellbeing application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Setup templates
templates = Jinja2Templates(directory=templates_dir)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme
security = HTTPBearer()

# Include routers
app.include_router(auth_endpoints.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(trail_endpoints.router, prefix="/api/v1", tags=["Trails"])
app.include_router(location_endpoints.router, prefix="/api/v1", tags=["Locations"])
app.include_router(user_endpoints.router, prefix="/api/v1", tags=["Users"])

# Setup Swagger
setup_swagger(app)

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    logger.info("Starting TrailService API...")
    # Test database connection
    try:
        db = get_db_connection()
        db.test_connection()
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down TrailService API...")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - Serve HTML dashboard"""
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "service": "TrailService",
            "version": "1.0.0",
            "status": "operational",
            "description": "Microservice for managing hiking trails in a wellbeing application"
        }
    )

@app.get("/api")
async def api_info():
    """API information endpoint - JSON response"""
    return {
        "service": "TrailService",
        "version": "1.0.0",
        "description": "Microservice for managing hiking trails",
        "endpoints": {
            "trails": "/api/v1/trails",
            "locations": "/api/v1/locations",
            "users": "/api/v1/users",
            "docs": "/docs",
            "health": "/health",
            "api": "/api"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = get_db_connection()
        db.test_connection()
        return {
            "status": "healthy",
            "database": "connected",
            "service": "TrailService"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api": "TrailService",
        "version": "1.0.0",
        "status": "operational",
        "uptime": "todo"
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": request.url.path
        }
    )