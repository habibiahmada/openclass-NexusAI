import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AppConfig:
    """Unified Application Configuration Manager"""
    
    def __init__(self):
        # Model Configuration
        self.local_model_path = os.getenv('LOCAL_MODEL_PATH', './models/openclass-nexus-q4.gguf')
        self.vector_db_path = os.getenv('VECTOR_DB_PATH', './data/vector_db')
        self.processed_data_path = os.getenv('PROCESSED_DATA_PATH', './data/processed')
        self.model_cache_dir = os.getenv('MODEL_CACHE_DIR', './models')
        self.chroma_db_path = os.getenv('CHROMA_DB_PATH', './data/vector_db')
        self.chroma_collection_name = os.getenv('CHROMA_COLLECTION_NAME', 'educational_content')
        
        # AI Model Settings
        self.max_context_length = int(os.getenv('MAX_CONTEXT_LENGTH', '2048'))
        self.max_response_tokens = int(os.getenv('MAX_RESPONSE_TOKENS', '512'))
        self.n_threads = int(os.getenv('N_THREADS', '4'))
        self.n_gpu_layers = int(os.getenv('N_GPU_LAYERS', '0'))
        
        # Text Processing Settings
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '800'))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '100'))
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', '0.7'))
        
        # API Server Settings
        self.api_host = os.getenv('API_HOST', '0.0.0.0')
        self.api_port = int(os.getenv('API_PORT', '8000'))
        self.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
        self.token_expiry_hours = int(os.getenv('TOKEN_EXPIRY_HOURS', '24'))
        self.cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
        
        # Performance Settings
        self.memory_limit_mb = int(os.getenv('MEMORY_LIMIT_MB', '3072'))
        self.max_concurrent_requests = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
        self.max_queue_size = int(os.getenv('MAX_QUEUE_SIZE', '20'))
        
        # Database Settings
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://root:root@127.0.0.1:5432/nexusai_db')
        
        # AWS S3 Buckets
        self.s3_curriculum_raw_bucket = os.getenv('S3_CURRICULUM_RAW_BUCKET', 'nexusai-curriculum-raw')
        self.s3_vkp_packages_bucket = os.getenv('S3_VKP_PACKAGES_BUCKET', 'nexusai-vkp-packages')
        self.s3_model_distribution_bucket = os.getenv('S3_MODEL_DISTRIBUTION_BUCKET', 'nexusai-model-distribution')
        
        # Application Settings
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.app_title = "OpenClass Nexus AI"
        self.app_icon = "🎓"
        self.max_chat_history = 50
        self.supported_subjects = ['Informatika']
        
        # Paths
        self.frontend_dir = Path(os.getenv('FRONTEND_DIR', 'frontend'))
        self.backup_dir = Path(os.getenv('BACKUP_DIR', 'backups'))
    
    def get_model_config(self):
        """Get model configuration for llama.cpp"""
        return {
            'model_path': self.local_model_path,
            'n_ctx': self.max_context_length,
            'n_threads': self.n_threads,
            'n_gpu_layers': self.n_gpu_layers,
            'verbose': self.debug
        }
    
    def get_chunking_config(self):
        """Get text chunking configuration"""
        return {
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'separators': ["\n\n", "\n", ". ", " "]
        }
    
    def validate(self):
        """Validate configuration and return list of warnings"""
        warnings = []
        
        # Check if model path exists
        if not Path(self.local_model_path).exists():
            warnings.append(f"Model file not found: {self.local_model_path}")
        
        # Check if vector DB path exists
        if not Path(self.vector_db_path).exists():
            warnings.append(f"Vector database not found: {self.vector_db_path}")
        
        # Check if frontend directory exists
        if not self.frontend_dir.exists():
            warnings.append(f"Frontend directory not found: {self.frontend_dir}")
        
        return warnings

# Global configuration instance
app_config = AppConfig()

# Backward compatibility aliases
config = app_config
HOST = app_config.api_host
PORT = app_config.api_port
DEBUG = app_config.debug
LOG_LEVEL = app_config.log_level
CORS_ORIGINS = app_config.cors_origins
SECRET_KEY = app_config.secret_key
TOKEN_EXPIRY_HOURS = app_config.token_expiry_hours
DATABASE_URL = app_config.database_url
MODEL_CACHE_DIR = app_config.model_cache_dir
CHROMA_DB_PATH = app_config.chroma_db_path
CHROMA_COLLECTION_NAME = app_config.chroma_collection_name
MEMORY_LIMIT_MB = app_config.memory_limit_mb
MAX_CONCURRENT_REQUESTS = app_config.max_concurrent_requests
MAX_QUEUE_SIZE = app_config.max_queue_size
FRONTEND_DIR = app_config.frontend_dir
BACKUP_DIR = app_config.backup_dir