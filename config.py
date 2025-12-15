"""
Configuration settings for TrailService
"""
import os
from typing import Dict, Any

class Config:
    """Base configuration"""
    # API Settings
    API_TITLE = "TrailService API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "Microservice for managing hiking trails"
    
    # Server Settings
    HOST = "0.0.0.0"
    PORT = 5000
    DEBUG = False
    
    # Database Settings
    DB_SERVER = "localhost"
    DB_NAME = "TrailDB"
    DB_DRIVER = "ODBC Driver 17 for SQL Server"
    DB_USER = "SA"
    DB_PASSWORD = "C0mp2001!"
    
    # Authentication
    AUTH_API_URL = "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users"
    JWT_ALGORITHM = "HS256"
    TOKEN_EXPIRE_MINUTES = 30
    
    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "production-secret-key")
    CORS_ORIGINS = ["*"]  # Restrict in production
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_DEFAULT = "100 per minute"
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/trail_service.log"
    
    # Features
    ENABLE_SWAGGER = True
    ENABLE_CORS = True
    ENABLE_LOGGING = True
    
    @classmethod
    def get_db_connection_string(cls) -> str:
        """Get database connection string"""
        return (
            f"DRIVER={{{cls.DB_DRIVER}}};"
            f"SERVER={cls.DB_SERVER};"
            f"DATABASE={cls.DB_NAME};"
            f"UID={cls.DB_USER};"
            f"PWD={cls.DB_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith("_") and not callable(value)
        }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    CORS_ORIGINS = ["*"]

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = "WARNING"
    SECRET_KEY = os.environ.get("SECRET_KEY", "production-secret-key")
    CORS_ORIGINS = [
        "https://web.socem.plymouth.ac.uk",
        "http://localhost:5000"
    ]

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DB_NAME = "TrailDB_Test"
    ENABLE_SWAGGER = False

# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}

def get_config(config_name: str = None) -> Config:
    """Get configuration by name"""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")
    return config.get(config_name, config["default"])