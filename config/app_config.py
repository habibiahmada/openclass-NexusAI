"""
Application Configuration
Central configuration management for the OpenClass Nexus AI application
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AppConfig:
    """Application Configuration Manager"""
    
    def __init__(self):
        # Local Model Configuration
        self.local_model_path = os.getenv('LOCAL_MODEL_PATH', './models/openclass-nexus-q4.gguf')
        self.vector_db_path = os.getenv('VECTOR_DB_PATH', './data/vector_db')
        self.processed_data_path = os.getenv('PROCESSED_DATA_PATH', './data/processed')
        
        # AI Model Settings
        self.max_context_length = int(os.getenv('MAX_CONTEXT_LENGTH', '2048'))
        self.max_response_tokens = int(os.getenv('MAX_RESPONSE_TOKENS', '512'))
        self.n_threads = int(os.getenv('N_THREADS', '4'))
        self.n_gpu_layers = int(os.getenv('N_GPU_LAYERS', '0'))
        
        # Text Processing Settings
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '800'))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '100'))
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', '0.7'))
        
        # Application Settings
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Supported subjects
        self.supported_subjects = [
            'Informatika',
        ]
        
        # UI Configuration
        self.app_title = "OpenClass Nexus AI"
        self.app_icon = "🎓"
        self.max_chat_history = 50
    
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

# Global configuration instance
app_config = AppConfig()