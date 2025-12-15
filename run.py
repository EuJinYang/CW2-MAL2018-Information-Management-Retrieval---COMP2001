"""
Main entry point for TrailService API
"""
import uvicorn
from src.api.app import app
from config import get_config

if __name__ == "__main__":
    config = get_config()
    
    uvicorn.run(
        "src.api.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )