"""
API Configuration Module
Centralized configuration for FastAPI server
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class APIConfig:
    """API Server Configuration"""
    
    # Server Settings
    HOST = os.getenv('API_HOST', '0.0.0.0')
    PORT = int(os.getenv('API_PORT', '8000'))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # CORS Settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Security Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    TOKEN_EXPIRY_HOURS = int(os.getenv('TOKEN_EXPIRY_HOURS', '24'))
    
    # Database Settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://root:root@127.0.0.1:5432/nexusai_db')
    
    # Model Settings
    MODEL_CACHE_DIR = os.getenv('MODEL_CACHE_DIR', './models')
    CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './data/vector_db')
    CHROMA_COLLECTION_NAME = os.getenv('CHROMA_COLLECTION_NAME', 'educational_content')
    
    # Performance Settings
    MEMORY_LIMIT_MB = int(os.getenv('MEMORY_LIMIT_MB', '3072'))
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
    MAX_QUEUE_SIZE = int(os.getenv('MAX_QUEUE_SIZE', '20'))
    
    # Frontend Settings
    FRONTEND_DIR = Path(os.getenv('FRONTEND_DIR', 'frontend'))
    
    # Backup Settings
    BACKUP_DIR = Path(os.getenv('BACKUP_DIR', 'backups'))
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        errors = []
        
        if not Path(cls.MODEL_CACHE_DIR).exists():
            errors.append(f"Model cache directory not found: {cls.MODEL_CACHE_DIR}")
        
        if not cls.FRONTEND_DIR.exists():
            errors.append(f"Frontend directory not found: {cls.FRONTEND_DIR}")
        
        return errors


# Create singleton instance
config = APIConfig()
