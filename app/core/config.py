from typing import List, Optional
from pydantic import BaseModel
import os


class Settings(BaseModel):
    """Application settings."""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    DEBUG: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database
    DATABASE_URL: Optional[str] = None
    TEST_DATABASE_URL: Optional[str] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    def __init__(self, **kwargs):
        """Initialize settings with environment variables."""
        super().__init__(**kwargs)
        
        # Load from environment variables
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.SECRET_KEY = os.getenv("SECRET_KEY", self.SECRET_KEY)
        
        cors_origins = os.getenv("CORS_ORIGINS", "")
        if cors_origins:
            self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",")]
        
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        self.TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
        self.REDIS_URL = os.getenv("REDIS_URL", self.REDIS_URL)
        
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        
        self.CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", self.CELERY_BROKER_URL)
        self.CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", self.CELERY_RESULT_BACKEND)
        
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", self.FRONTEND_URL)
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", self.LOG_LEVEL)


settings = Settings()