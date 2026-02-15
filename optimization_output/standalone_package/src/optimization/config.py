"""
Optimization Configuration

This module provides configuration management for optimization processes,
including cleanup settings, demonstration parameters, and validation thresholds.
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Configuration for optimization processes."""
    
    # Project paths
    project_root: Path = field(default_factory=lambda: Path.cwd())
    optimization_output_dir: Path = field(default_factory=lambda: Path("./optimization_output"))
    
    # Cleanup configuration
    cleanup_temp_files: bool = True
    cleanup_cache_dirs: bool = True
    cleanup_test_artifacts: bool = True
    preserve_essential_files: List[str] = field(default_factory=lambda: [
        "requirements.txt",
        "README.md",
        "LICENSE",
        ".env.example",
        "config/",
        "src/",
        "docs/",
        "scripts/"
    ])
    temp_file_patterns: List[str] = field(default_factory=lambda: [
        "*.tmp",
        "*.temp",
        "*.log",
        "__pycache__/",
        "*.pyc",
        ".pytest_cache/",
        ".coverage",
        "*.egg-info/",
        "build/",
        "dist/"
    ])
    
    # Demonstration configuration
    demo_queries: List[str] = field(default_factory=lambda: [
        "Jelaskan konsep algoritma dalam informatika untuk siswa kelas 10",
        "Apa perbedaan antara hardware dan software dalam komputer?",
        "Bagaimana cara kerja jaringan komputer sederhana?",
        "Jelaskan pentingnya keamanan data dalam era digital",
        "Apa itu pemrograman dan mengapa penting dipelajari?"
    ])
    demo_performance_iterations: int = 10
    demo_concurrent_queries: int = 3
    demo_timeout_seconds: int = 30
    
    # Performance validation thresholds
    max_response_time_ms: float = 5000.0  # 5 seconds
    max_memory_usage_mb: float = 4096.0   # 4GB
    min_curriculum_alignment_score: float = 0.85  # 85%
    min_language_quality_score: float = 0.80     # 80%
    min_system_stability_score: float = 0.90     # 90%
    
    # Documentation configuration
    supported_languages: List[str] = field(default_factory=lambda: ["indonesian", "english"])
    documentation_output_dir: Path = field(default_factory=lambda: Path("./docs/optimization"))
    include_api_examples: bool = True
    include_troubleshooting: bool = True
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: Optional[str] = "optimization.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def __post_init__(self):
        """Initialize configuration after creation."""
        # Ensure output directories exist
        self.optimization_output_dir.mkdir(parents=True, exist_ok=True)
        self.documentation_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        logger.info(f"Optimization configuration initialized")
        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Output directory: {self.optimization_output_dir}")
    
    def _setup_logging(self):
        """Setup logging configuration for optimization processes."""
        # Create logger for optimization module
        optimization_logger = logging.getLogger('src.optimization')
        optimization_logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(self.log_format)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.log_level.upper()))
        console_handler.setFormatter(formatter)
        optimization_logger.addHandler(console_handler)
        
        # File handler if log file specified
        if self.log_file:
            log_path = self.optimization_output_dir / self.log_file
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(getattr(logging, self.log_level.upper()))
            file_handler.setFormatter(formatter)
            optimization_logger.addHandler(file_handler)
    
    def get_cleanup_config(self) -> Dict[str, Any]:
        """Get cleanup-specific configuration."""
        return {
            'cleanup_temp_files': self.cleanup_temp_files,
            'cleanup_cache_dirs': self.cleanup_cache_dirs,
            'cleanup_test_artifacts': self.cleanup_test_artifacts,
            'preserve_essential_files': self.preserve_essential_files,
            'temp_file_patterns': self.temp_file_patterns
        }
    
    def get_demo_config(self) -> Dict[str, Any]:
        """Get demonstration-specific configuration."""
        return {
            'demo_queries': self.demo_queries,
            'demo_performance_iterations': self.demo_performance_iterations,
            'demo_concurrent_queries': self.demo_concurrent_queries,
            'demo_timeout_seconds': self.demo_timeout_seconds
        }
    
    def get_validation_thresholds(self) -> Dict[str, float]:
        """Get performance validation thresholds."""
        return {
            'max_response_time_ms': self.max_response_time_ms,
            'max_memory_usage_mb': self.max_memory_usage_mb,
            'min_curriculum_alignment_score': self.min_curriculum_alignment_score,
            'min_language_quality_score': self.min_language_quality_score,
            'min_system_stability_score': self.min_system_stability_score
        }
    
    def get_documentation_config(self) -> Dict[str, Any]:
        """Get documentation-specific configuration."""
        return {
            'supported_languages': self.supported_languages,
            'documentation_output_dir': str(self.documentation_output_dir),
            'include_api_examples': self.include_api_examples,
            'include_troubleshooting': self.include_troubleshooting
        }
    
    def validate_configuration(self) -> bool:
        """Validate the configuration settings."""
        try:
            # Check if project root exists
            if not self.project_root.exists():
                logger.error(f"Project root does not exist: {self.project_root}")
                return False
            
            # Check if essential directories exist
            essential_dirs = ['src', 'config']
            for dir_name in essential_dirs:
                dir_path = self.project_root / dir_name
                if not dir_path.exists():
                    logger.warning(f"Essential directory missing: {dir_path}")
            
            # Validate thresholds
            if self.max_response_time_ms <= 0:
                logger.error("max_response_time_ms must be positive")
                return False
            
            if self.max_memory_usage_mb <= 0:
                logger.error("max_memory_usage_mb must be positive")
                return False
            
            if not (0 <= self.min_curriculum_alignment_score <= 1):
                logger.error("min_curriculum_alignment_score must be between 0 and 1")
                return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    @classmethod
    def from_env(cls) -> 'OptimizationConfig':
        """Create configuration from environment variables."""
        config = cls()
        
        # Override with environment variables if present
        if os.getenv('OPTIMIZATION_OUTPUT_DIR'):
            config.optimization_output_dir = Path(os.getenv('OPTIMIZATION_OUTPUT_DIR'))
        
        if os.getenv('OPTIMIZATION_LOG_LEVEL'):
            config.log_level = os.getenv('OPTIMIZATION_LOG_LEVEL')
        
        if os.getenv('MAX_RESPONSE_TIME_MS'):
            config.max_response_time_ms = float(os.getenv('MAX_RESPONSE_TIME_MS'))
        
        if os.getenv('MAX_MEMORY_USAGE_MB'):
            config.max_memory_usage_mb = float(os.getenv('MAX_MEMORY_USAGE_MB'))
        
        if os.getenv('MIN_CURRICULUM_ALIGNMENT_SCORE'):
            config.min_curriculum_alignment_score = float(os.getenv('MIN_CURRICULUM_ALIGNMENT_SCORE'))
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'project_root': str(self.project_root),
            'optimization_output_dir': str(self.optimization_output_dir),
            'cleanup_temp_files': self.cleanup_temp_files,
            'cleanup_cache_dirs': self.cleanup_cache_dirs,
            'cleanup_test_artifacts': self.cleanup_test_artifacts,
            'preserve_essential_files': self.preserve_essential_files,
            'temp_file_patterns': self.temp_file_patterns,
            'demo_queries': self.demo_queries,
            'demo_performance_iterations': self.demo_performance_iterations,
            'demo_concurrent_queries': self.demo_concurrent_queries,
            'demo_timeout_seconds': self.demo_timeout_seconds,
            'max_response_time_ms': self.max_response_time_ms,
            'max_memory_usage_mb': self.max_memory_usage_mb,
            'min_curriculum_alignment_score': self.min_curriculum_alignment_score,
            'min_language_quality_score': self.min_language_quality_score,
            'min_system_stability_score': self.min_system_stability_score,
            'supported_languages': self.supported_languages,
            'documentation_output_dir': str(self.documentation_output_dir),
            'include_api_examples': self.include_api_examples,
            'include_troubleshooting': self.include_troubleshooting,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'log_format': self.log_format
        }


# Global configuration instance
optimization_config = OptimizationConfig.from_env()