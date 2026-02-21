"""
Model configuration and management for Phase 3 local inference.

This module provides configuration classes and utilities for managing
AI models in the OpenClass Nexus AI system, specifically optimized
for Llama-3.2-3B-Instruct running on 4GB RAM systems.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import os


@dataclass
class ModelConfig:
    """Configuration for Llama-3.2-3B-Instruct model optimized for 4GB RAM systems.
    
    This configuration follows the design specifications for Phase 3,
    targeting the optimal balance between performance and resource usage
    for Indonesian educational content.
    """
    
    # Model identification
    model_id: str = "meta-llama/Llama-3.2-3B-Instruct"
    gguf_filename: str = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    gguf_repo: str = "bartowski/Llama-3.2-3B-Instruct-GGUF"
    
    # Local storage
    local_path: Optional[Path] = None
    cache_dir: str = "./models"
    
    # Model specifications
    file_size_mb: int = 2500
    checksum: Optional[str] = None
    quantization_format: str = "Q4_K_M"
    
    # Model capabilities
    context_window: int = 4096
    supports_indonesian: bool = True
    educational_optimized: bool = True
    
    def __post_init__(self):
        """Initialize computed properties after dataclass creation."""
        if self.local_path is None:
            self.local_path = Path(self.cache_dir) / self.gguf_filename
    
    def get_download_url(self) -> str:
        """Get the HuggingFace download URL for the GGUF model."""
        return f"https://huggingface.co/{self.gguf_repo}/resolve/main/{self.gguf_filename}"
    
    def get_model_path(self) -> Path:
        """Get the local path where the model should be stored."""
        return Path(self.cache_dir) / self.gguf_filename
    
    def is_downloaded(self) -> bool:
        """Check if the model is already downloaded locally."""
        model_path = self.get_model_path()
        return model_path.exists() and model_path.stat().st_size > 0
    
    def get_cache_dir(self) -> Path:
        """Get the cache directory path, creating it if necessary."""
        cache_path = Path(self.cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            'model_id': self.model_id,
            'gguf_filename': self.gguf_filename,
            'gguf_repo': self.gguf_repo,
            'local_path': str(self.local_path) if self.local_path else None,
            'cache_dir': self.cache_dir,
            'file_size_mb': self.file_size_mb,
            'checksum': self.checksum,
            'quantization_format': self.quantization_format,
            'context_window': self.context_window,
            'supports_indonesian': self.supports_indonesian,
            'educational_optimized': self.educational_optimized
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """Create ModelConfig from dictionary."""
        # Convert local_path back to Path if it exists
        if data.get('local_path'):
            data['local_path'] = Path(data['local_path'])
        return cls(**data)


@dataclass
class InferenceConfig:
    """Configuration for local inference engine optimized for 4GB RAM systems.
    
    These settings are specifically tuned for running Llama-3.2-3B-Instruct
    efficiently on resource-constrained hardware while maintaining
    educational content quality.
    """
    
    # Context and token limits
    n_ctx: int = 4096          # Context window size
    max_tokens: int = 512      # Maximum response length
    
    # CPU optimization
    n_threads: int = 4         # CPU threads to use
    n_gpu_layers: int = 0      # GPU layers (0 for CPU-only)
    
    # Generation parameters
    temperature: float = 0.7   # Response creativity (0.0-1.0)
    top_p: float = 0.9         # Nucleus sampling
    top_k: int = 40           # Top-k sampling
    repeat_penalty: float = 1.1  # Repetition penalty
    
    # Memory management
    memory_limit_mb: int = 3072  # Memory limit (3GB for 4GB systems)
    use_mmap: bool = True        # Use memory mapping for efficiency
    use_mlock: bool = False      # Lock model in memory (disabled for 4GB systems)
    
    # Performance settings
    batch_size: int = 512      # Batch size for processing
    streaming: bool = True     # Enable streaming responses
    
    def __post_init__(self):
        """Validate and adjust configuration after creation."""
        # Auto-detect optimal thread count if not specified
        if self.n_threads <= 0:
            self.n_threads = min(os.cpu_count() or 4, 6)  # Cap at 6 threads
        
        # Ensure memory limit is reasonable for 4GB systems
        if self.memory_limit_mb > 3584:  # Leave 512MB for OS
            self.memory_limit_mb = 3072
    
    def get_llama_cpp_params(self) -> Dict[str, Any]:
        """Get parameters formatted for llama-cpp-python."""
        return {
            'n_ctx': self.n_ctx,
            'n_threads': self.n_threads,
            'n_gpu_layers': self.n_gpu_layers,
            'use_mmap': self.use_mmap,
            'use_mlock': self.use_mlock,
            'verbose': False  # Reduce logging for production
        }
    
    def get_generation_params(self) -> Dict[str, Any]:
        """Get parameters for text generation."""
        return {
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'top_k': self.top_k,
            'repeat_penalty': self.repeat_penalty,
            'stream': self.streaming
        }


# Default configurations for different use cases
DEFAULT_MODEL_CONFIG = ModelConfig()

PERFORMANCE_INFERENCE_CONFIG = InferenceConfig(
    temperature=0.3,  # Lower temperature for more consistent responses
    max_tokens=256,   # Shorter responses for faster generation
    n_threads=6       # More threads for performance
)

QUALITY_INFERENCE_CONFIG = InferenceConfig(
    temperature=0.7,  # Higher temperature for more creative responses
    max_tokens=512,   # Longer responses for detailed explanations
    n_threads=4       # Balanced thread usage
)

MEMORY_OPTIMIZED_CONFIG = InferenceConfig(
    n_ctx=2048,       # Smaller context window
    max_tokens=256,   # Shorter responses
    memory_limit_mb=2048,  # Lower memory limit
    batch_size=256,   # Smaller batch size
    use_mlock=False   # Disable memory locking
)