"""
Configuration settings for the Drug Interaction Detection System

This file contains all the configuration parameters needed for the application,
including database settings, API keys, model paths, and security configurations.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Database Configuration
DATABASE_CONFIG = {
    'db_path': BASE_DIR / 'data' / 'drug_database.db',
    'connection_timeout': 30,
    'echo': False  # Set to True for SQL debugging
}

# API Configuration
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 8000,
    'debug': True,
    'reload': True,
    'cors_origins': [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://your-frontend-domain.com"
    ]
}

# Security Configuration
SECURITY_CONFIG = {
    'secret_key': os.getenv('SECRET_KEY', 'your-secret-key-change-in-production'),
    'algorithm': 'HS256',
    'access_token_expire_minutes': 30,
    'refresh_token_expire_days': 7
}

# OCR Configuration
OCR_CONFIG = {
    'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe',  # Windows path
    # 'tesseract_cmd': '/usr/bin/tesseract',  # Linux/Mac path
    'confidence_threshold': 60,
    'supported_formats': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
    'max_file_size': 5 * 1024 * 1024,  # 5MB
    'image_preprocessing': {
        'resize_factor': 2.0,
        'gaussian_blur': 1,
        'contrast_factor': 1.5
    }
}

# Machine Learning Configuration
ML_CONFIG = {
    'model_path': BASE_DIR / 'models' / 'trained_models',
    'fastai_models': {
        'vision_model': 'drug_label_classifier.pkl',
        'text_model': 'drug_name_extractor.pkl'
    },
    'batch_size': 32,
    'learning_rate': 0.001,
    'epochs': 10,
    'validation_split': 0.2
}

# Drug Database Configuration
DRUG_DB_CONFIG = {
    'interaction_severity_levels': {
        'CRITICAL': 4,
        'MAJOR': 3,
        'MODERATE': 2,
        'MINOR': 1
    },
    'api_endpoints': {
        'fda_api': 'https://api.fda.gov/drug/drugsfda.json',
        'rxnorm_api': 'https://rxnav.nlm.nih.gov/REST/rxcui.json',
        'interaction_api': 'https://rxnav.nlm.nih.gov/REST/interaction/interaction.json'
    },
    'update_frequency': 24  # hours
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': BASE_DIR / 'logs' / 'app.log',
    'max_bytes': 10485760,  # 10MB
    'backup_count': 5
}

# File Upload Configuration
UPLOAD_CONFIG = {
    'upload_dir': BASE_DIR / 'uploads',
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'allowed_extensions': {'.jpg', '.jpeg', '.png', '.pdf', '.bmp', '.tiff'},
    'cleanup_interval': 3600  # seconds (1 hour)
}

# External API Keys (should be set via environment variables)
EXTERNAL_APIS = {
    'google_vision_api_key': os.getenv('GOOGLE_VISION_API_KEY'),
    'fda_api_key': os.getenv('FDA_API_KEY'),
    'openai_api_key': os.getenv('OPENAI_API_KEY')
}

# Development/Production Environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Email Configuration (for alerts and notifications)
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
    'email_user': os.getenv('EMAIL_USER'),
    'email_password': os.getenv('EMAIL_PASSWORD'),
    'use_tls': True
}

# Create necessary directories
def create_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        BASE_DIR / 'data',
        BASE_DIR / 'logs',
        BASE_DIR / 'uploads',
        BASE_DIR / 'models' / 'trained_models'
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Initialize directories when config is imported
create_directories()
