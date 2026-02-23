"""
Model management utilities for OpenClass Nexus AI Phase 3.

This module provides high-level utilities for managing the complete
model lifecycle including configuration, validation, and setup.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import os

from .model_config import ModelConfig, InferenceConfig
from .hf_client import HuggingFaceClient, get_hf_client

# Configure logging
logger = logging.getLogger(__name__)


class ModelManager:
    """
    High-level model management for OpenClass Nexus AI.
    
    This class provides a unified interface for managing model configurations,
    validating setups, and preparing the system for local inference.
    """
    
    def __init__(self, base_dir: str = "./models"):
        """
        Initialize the model manager.
        
        Args:
            base_dir: Base directory for model storage and configuration
        """
        self.base_dir = Path(base_dir)
        self.cache_dir = self.base_dir / "cache"
        self.config_dir = self.base_dir / "configs"
        self.metadata_dir = self.base_dir / "metadata"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Initialize HuggingFace client
        self.hf_client = get_hf_client(cache_dir=str(self.cache_dir))
        
        # Load default configuration
        self.model_config = ModelConfig(cache_dir=str(self.cache_dir))
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for directory in [self.base_dir, self.cache_dir, self.config_dir, self.metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def load_config_from_file(self, config_path: Optional[str] = None) -> Tuple[ModelConfig, Dict[str, InferenceConfig]]:
        """
        Load model and inference configurations from JSON file.
        
        Args:
            config_path: Path to configuration file (defaults to default_model_config.json)
            
        Returns:
            Tuple of (ModelConfig, dict of InferenceConfigs)
        """
        if config_path is None:
            config_path = self.config_dir / "default_model_config.json"
        else:
            config_path = Path(config_path)
        
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return self.model_config, {"default": InferenceConfig()}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Load model configuration
            model_config_data = config_data.get('model_config', {})
            model_config = ModelConfig(**model_config_data)
            
            # Load inference configurations
            inference_configs = {}
            inference_configs_data = config_data.get('inference_configs', {})
            
            for name, config_data in inference_configs_data.items():
                inference_configs[name] = InferenceConfig(**config_data)
            
            logger.info(f"Successfully loaded configuration from {config_path}")
            return model_config, inference_configs
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            return self.model_config, {"default": InferenceConfig()}
    
    def save_config_to_file(self, 
                           model_config: ModelConfig, 
                           inference_configs: Dict[str, InferenceConfig],
                           config_path: Optional[str] = None) -> bool:
        """
        Save model and inference configurations to JSON file.
        
        Args:
            model_config: Model configuration to save
            inference_configs: Dictionary of inference configurations
            config_path: Path to save configuration (defaults to default_model_config.json)
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if config_path is None:
            config_path = self.config_dir / "default_model_config.json"
        else:
            config_path = Path(config_path)
        
        try:
            config_data = {
                'model_config': model_config.to_dict(),
                'inference_configs': {
                    name: {
                        'n_ctx': config.n_ctx,
                        'max_tokens': config.max_tokens,
                        'n_threads': config.n_threads,
                        'n_gpu_layers': config.n_gpu_layers,
                        'temperature': config.temperature,
                        'top_p': config.top_p,
                        'top_k': config.top_k,
                        'repeat_penalty': config.repeat_penalty,
                        'memory_limit_mb': config.memory_limit_mb,
                        'use_mmap': config.use_mmap,
                        'use_mlock': config.use_mlock,
                        'batch_size': config.batch_size,
                        'streaming': config.streaming
                    }
                    for name, config in inference_configs.items()
                },
                'metadata': {
                    'created_date': '2026-01-26',
                    'version': '1.0.0',
                    'description': 'Configuration for Llama-3.2-3B-Instruct optimized for 4GB RAM systems',
                    'target_hardware': '4GB RAM laptops',
                    'educational_focus': 'Indonesian curriculum content'
                }
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved configuration to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {config_path}: {e}")
            return False
    
    def validate_setup(self) -> Dict[str, Any]:
        """
        Validate the complete model management setup.
        
        Returns:
            Dict containing validation results and status information
        """
        validation_results = {
            'directories_exist': True,
            'hf_client_ready': False,
            'model_accessible': False,
            'config_valid': False,
            'dependencies_available': False,
            'overall_status': 'unknown',
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Check directories
            for dir_name, directory in [
                ('base', self.base_dir),
                ('cache', self.cache_dir),
                ('config', self.config_dir),
                ('metadata', self.metadata_dir)
            ]:
                if not directory.exists():
                    validation_results['directories_exist'] = False
                    validation_results['issues'].append(f"Missing directory: {directory}")
            
            # Check HuggingFace client
            try:
                hf_status = self.hf_client.validate_model_access(self.model_config)
                validation_results['hf_client_ready'] = True
                validation_results['model_accessible'] = hf_status
                
                if not hf_status:
                    validation_results['issues'].append("Model not accessible via HuggingFace Hub")
                    validation_results['recommendations'].append("Check internet connection and model repository")
                    
            except Exception as e:
                validation_results['issues'].append(f"HuggingFace client error: {e}")
                validation_results['recommendations'].append("Check HuggingFace Hub connectivity")
            
            # Check configuration
            try:
                model_config, inference_configs = self.load_config_from_file()
                validation_results['config_valid'] = True
                
                if not model_config.supports_indonesian:
                    validation_results['recommendations'].append("Consider using a model with better Indonesian support")
                    
            except Exception as e:
                validation_results['issues'].append(f"Configuration error: {e}")
                validation_results['recommendations'].append("Check configuration file format and content")
            
            # Check dependencies
            try:
                import llama_cpp
                import huggingface_hub
                validation_results['dependencies_available'] = True
            except ImportError as e:
                validation_results['issues'].append(f"Missing dependency: {e}")
                validation_results['recommendations'].append("Install missing dependencies with pip")
            
            # Determine overall status
            if (validation_results['directories_exist'] and 
                validation_results['hf_client_ready'] and 
                validation_results['model_accessible'] and 
                validation_results['config_valid'] and 
                validation_results['dependencies_available']):
                validation_results['overall_status'] = 'ready'
            elif len(validation_results['issues']) == 0:
                validation_results['overall_status'] = 'warning'
            else:
                validation_results['overall_status'] = 'error'
            
        except Exception as e:
            validation_results['overall_status'] = 'error'
            validation_results['issues'].append(f"Validation failed: {e}")
        
        return validation_results
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information relevant to model management.
        
        Returns:
            Dict containing system information
        """
        import psutil
        import platform
        
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': os.cpu_count(),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
            'disk_free_gb': round(psutil.disk_usage('.').free / (1024**3), 2),
            'model_cache_dir': str(self.cache_dir),
            'config_dir': str(self.config_dir),
            'hf_token_available': os.getenv('HF_TOKEN') is not None
        }
    
    def create_default_setup(self) -> bool:
        """
        Create a default setup with recommended configurations.
        
        Returns:
            bool: True if setup created successfully, False otherwise
        """
        try:
            # Create default model configuration
            model_config = ModelConfig(cache_dir=str(self.cache_dir))
            
            # Create inference configurations for different use cases
            inference_configs = {
                'default': InferenceConfig(),
                'performance': InferenceConfig(
                    temperature=0.3,
                    max_tokens=256,
                    n_threads=6
                ),
                'quality': InferenceConfig(
                    temperature=0.7,
                    max_tokens=512,
                    n_threads=4
                ),
                'memory_optimized': InferenceConfig(
                    n_ctx=2048,
                    max_tokens=256,
                    memory_limit_mb=2048,
                    batch_size=256
                )
            }
            
            # Save configuration
            success = self.save_config_to_file(model_config, inference_configs)
            
            if success:
                logger.info("Default setup created successfully")
            else:
                logger.error("Failed to create default setup")
            
            return success
            
        except Exception as e:
            logger.error(f"Error creating default setup: {e}")
            return False


def setup_model_management(base_dir: str = "./models") -> Dict[str, Any]:
    """
    Setup and validate the complete model management system.
    
    Args:
        base_dir: Base directory for model storage
        
    Returns:
        Dict containing setup results and system status
    """
    try:
        # Initialize model manager
        manager = ModelManager(base_dir=base_dir)
        
        # Create default setup if needed
        config_file = manager.config_dir / "default_model_config.json"
        if not config_file.exists():
            manager.create_default_setup()
        
        # Validate setup
        validation_results = manager.validate_setup()
        
        # Get system information
        system_info = manager.get_system_info()
        
        return {
            'setup_complete': True,
            'validation': validation_results,
            'system_info': system_info,
            'manager': manager
        }
        
    except Exception as e:
        logger.error(f"Model management setup failed: {e}")
        return {
            'setup_complete': False,
            'error': str(e),
            'validation': {'overall_status': 'error'},
            'system_info': {},
            'manager': None
        }