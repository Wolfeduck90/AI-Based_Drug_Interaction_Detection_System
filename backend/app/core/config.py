"""
Configuration settings for the Drug Interaction Detection System
"""

import os
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Basic settings
    DEBUG: bool = Field(default=False, env="DEBUG")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://localhost:3000"
        ],
        env="CORS_ORIGINS"
    )
    
    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    
    # File upload
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp", "application/pdf"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # OCR Services
    GOOGLE_VISION_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_VISION_API_KEY")
    AZURE_VISION_ENDPOINT: Optional[str] = Field(default=None, env="AZURE_VISION_ENDPOINT")
    AZURE_VISION_KEY: Optional[str] = Field(default=None, env="AZURE_VISION_KEY")
    TESSERACT_CMD: Optional[str] = Field(default=None, env="TESSERACT_CMD")
    
    # External APIs
    FDA_API_KEY: Optional[str] = Field(default=None, env="FDA_API_KEY")
    RXNORM_API_BASE: str = Field(
        default="https://rxnav.nlm.nih.gov/REST",
        env="RXNORM_API_BASE"
    )
    
    # ML Models
    HUGGINGFACE_API_KEY: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    MODEL_CACHE_DIR: str = Field(default="models", env="MODEL_CACHE_DIR")
    
    # Redis (for caching and background tasks)
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get application settings (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings