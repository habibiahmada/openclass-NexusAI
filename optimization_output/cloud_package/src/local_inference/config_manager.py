"""
Configuration Management System for Phase 3 Model Optimization.

This module provides comprehensive configuration management including:
- YAML/JSON configuration file support
- Auto-detection of optimal hardware settings
- Configuration validation and error handling
- Hardware-specific optimization profiles

Requirements: 8.1, 8.2, 8.4
"""

import json
import yaml
import os
import psutil
import platform
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict
import logging
from enum import Enum

from .model_config import ModelConfig, InferenceConfig


class ConfigFormat(Enum):
    """Supported configuration file formats."""
    JSON = "json"
    YAML = "yaml"
    YML = "yml"


@dataclass
class HardwareProfile:
    """Hardware profile for automatic configuration optimization."""
    
    # System specifications
    total_memory_gb: float
    cpu_cores: int
    cpu_threads: int
    cpu_frequency_ghz: float
    architecture: str
    
    # Recommended settings
    recommended_threads: int
    recommended_memory_limit_mb: int
    recommended_context_size: int
    recommended_batch_size: int
    
    # Performance profile
    profile_name: str
    performance_tier: str  # "low", "medium", "high"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HardwareProfile':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SystemConfiguration:
    """Complete system configuration including model, inference, and hardware settings."""
    
    # Core configurations
    model_config: ModelConfig
    inference_config: InferenceConfig
    hardware_profile: HardwareProfile
    
    # Application settings
    app_name: str = "OpenClass Nexus AI"
    version: str = "3.0.0"
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # Paths and directories
    models_dir: str = "./models"
    cache_dir: str = "./cache"
    logs_dir: str = "./logs"
    config_dir: str = "./config"
    
    # Educational settings
    supported_languages: List[str] = None
    educational_subjects: List[str] = None
    response_language: str = "indonesian"
    
    def __post_init__(self):
        """Initialize default values after creation."""
        if self.supported_languages is None:
            self.supported_languages = ["indonesian", "english"]
        
        if self.educational_subjects is None:
            self.educational_subjects = [
                "Informatika", "Matematika", "Fisika", "Kimia", 
                "Biologi", "Bahasa Indonesia", "Bahasa Inggris"
            ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "model_config": self.model_config.to_dict(),
            "inference_config": asdict(self.inference_config),
            "hardware_profile": self.hardware_profile.to_dict(),
            "app_name": self.app_name,
            "version": self.version,
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
            "models_dir": self.models_dir,
            "cache_dir": self.cache_dir,
            "logs_dir": self.logs_dir,
            "config_dir": self.config_dir,
            "supported_languages": self.supported_languages,
            "educational_subjects": self.educational_subjects,
            "response_language": self.response_language
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemConfiguration':
        """Create from dictionary."""
        model_config = ModelConfig.from_dict(data["model_config"])
        inference_config = InferenceConfig(**data["inference_config"])
        hardware_profile = HardwareProfile.from_dict(data["hardware_profile"])
        
        return cls(
            model_config=model_config,
            inference_config=inference_config,
            hardware_profile=hardware_profile,
            app_name=data.get("app_name", "OpenClass Nexus AI"),
            version=data.get("version", "3.0.0"),
            debug_mode=data.get("debug_mode", False),
            log_level=data.get("log_level", "INFO"),
            models_dir=data.get("models_dir", "./models"),
            cache_dir=data.get("cache_dir", "./cache"),
            logs_dir=data.get("logs_dir", "./logs"),
            config_dir=data.get("config_dir", "./config"),
            supported_languages=data.get("supported_languages", ["indonesian", "english"]),
            educational_subjects=data.get("educational_subjects", []),
            response_language=data.get("response_language", "indonesian")
        )


class HardwareDetector:
    """Hardware detection and optimization system."""
    
    @staticmethod
    def detect_hardware() -> HardwareProfile:
        """Detect current hardware and generate optimal configuration profile."""
        
        # Get system information
        memory_info = psutil.virtual_memory()
        cpu_info = psutil.cpu_count(logical=False), psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        
        total_memory_gb = memory_info.total / (1024**3)
        cpu_cores = cpu_info[0] or 4
        cpu_threads = cpu_info[1] or 4
        cpu_frequency_ghz = (cpu_freq.max / 1000) if cpu_freq else 2.0
        architecture = platform.machine()
        
        # Determine performance tier and recommendations
        if total_memory_gb >= 8:
            profile_name = "high_performance"
            performance_tier = "high"
            recommended_threads = min(cpu_threads, 8)
            recommended_memory_limit_mb = int(total_memory_gb * 1024 * 0.6)  # 60% of total
            recommended_context_size = 4096
            recommended_batch_size = 512
        elif total_memory_gb >= 6:
            profile_name = "medium_performance"
            performance_tier = "medium"
            recommended_threads = min(cpu_threads, 6)
            recommended_memory_limit_mb = int(total_memory_gb * 1024 * 0.5)  # 50% of total
            recommended_context_size = 3072
            recommended_batch_size = 384
        else:  # 4GB or less
            profile_name = "low_resource"
            performance_tier = "low"
            recommended_threads = min(cpu_threads, 4)
            recommended_memory_limit_mb = 3072  # Leave 1GB for OS
            recommended_context_size = 2048
            recommended_batch_size = 256
        
        return HardwareProfile(
            total_memory_gb=total_memory_gb,
            cpu_cores=cpu_cores,
            cpu_threads=cpu_threads,
            cpu_frequency_ghz=cpu_frequency_ghz,
            architecture=architecture,
            recommended_threads=recommended_threads,
            recommended_memory_limit_mb=recommended_memory_limit_mb,
            recommended_context_size=recommended_context_size,
            recommended_batch_size=recommended_batch_size,
            profile_name=profile_name,
            performance_tier=performance_tier
        )
    
    @staticmethod
    def optimize_inference_config(hardware_profile: HardwareProfile) -> InferenceConfig:
        """Generate optimized inference configuration based on hardware profile."""
        
        return InferenceConfig(
            n_ctx=hardware_profile.recommended_context_size,
            n_threads=hardware_profile.recommended_threads,
            memory_limit_mb=hardware_profile.recommended_memory_limit_mb,
            batch_size=hardware_profile.recommended_batch_size,
            
            # Adjust generation parameters based on performance tier
            temperature=0.7 if hardware_profile.performance_tier == "high" else 0.5,
            max_tokens=512 if hardware_profile.performance_tier == "high" else 256,
            
            # Memory optimization for low-resource systems
            use_mlock=hardware_profile.performance_tier == "high",
            use_mmap=True,  # Always use memory mapping for efficiency
            
            # Streaming for better user experience
            streaming=True
        )


class ConfigurationValidator:
    """Configuration validation and error checking."""
    
    @staticmethod
    def validate_system_config(config: SystemConfiguration) -> List[str]:
        """Validate complete system configuration and return list of errors."""
        errors = []
        
        # Validate model configuration
        model_errors = ConfigurationValidator.validate_model_config(config.model_config)
        errors.extend([f"Model Config: {error}" for error in model_errors])
        
        # Validate inference configuration
        inference_errors = ConfigurationValidator.validate_inference_config(config.inference_config)
        errors.extend([f"Inference Config: {error}" for error in inference_errors])
        
        # Validate hardware profile
        hardware_errors = ConfigurationValidator.validate_hardware_profile(config.hardware_profile)
        errors.extend([f"Hardware Profile: {error}" for error in hardware_errors])
        
        # Validate paths
        path_errors = ConfigurationValidator.validate_paths(config)
        errors.extend([f"Path Config: {error}" for error in path_errors])
        
        return errors
    
    @staticmethod
    def validate_model_config(config: ModelConfig) -> List[str]:
        """Validate model configuration."""
        errors = []
        
        if not config.model_id:
            errors.append("model_id cannot be empty")
        
        if not config.gguf_filename:
            errors.append("gguf_filename cannot be empty")
        
        if not config.gguf_repo:
            errors.append("gguf_repo cannot be empty")
        
        if config.file_size_mb <= 0:
            errors.append("file_size_mb must be positive")
        
        if config.context_window <= 0:
            errors.append("context_window must be positive")
        
        return errors
    
    @staticmethod
    def validate_inference_config(config: InferenceConfig) -> List[str]:
        """Validate inference configuration."""
        errors = []
        
        if config.n_ctx <= 0:
            errors.append("n_ctx must be positive")
        
        if config.n_threads <= 0:
            errors.append("n_threads must be positive")
        
        if config.max_tokens <= 0:
            errors.append("max_tokens must be positive")
        
        if not (0.0 <= config.temperature <= 2.0):
            errors.append("temperature must be between 0.0 and 2.0")
        
        if not (0.0 <= config.top_p <= 1.0):
            errors.append("top_p must be between 0.0 and 1.0")
        
        if config.memory_limit_mb <= 0:
            errors.append("memory_limit_mb must be positive")
        
        return errors
    
    @staticmethod
    def validate_hardware_profile(profile: HardwareProfile) -> List[str]:
        """Validate hardware profile."""
        errors = []
        
        if profile.total_memory_gb <= 0:
            errors.append("total_memory_gb must be positive")
        
        if profile.cpu_cores <= 0:
            errors.append("cpu_cores must be positive")
        
        if profile.recommended_threads <= 0:
            errors.append("recommended_threads must be positive")
        
        if profile.recommended_memory_limit_mb <= 0:
            errors.append("recommended_memory_limit_mb must be positive")
        
        if profile.performance_tier not in ["low", "medium", "high"]:
            errors.append("performance_tier must be 'low', 'medium', or 'high'")
        
        return errors
    
    @staticmethod
    def validate_paths(config: SystemConfiguration) -> List[str]:
        """Validate directory paths in configuration."""
        errors = []
        
        paths_to_check = [
            ("models_dir", config.models_dir),
            ("cache_dir", config.cache_dir),
            ("logs_dir", config.logs_dir),
            ("config_dir", config.config_dir)
        ]
        
        for path_name, path_value in paths_to_check:
            if not path_value:
                errors.append(f"{path_name} cannot be empty")
            else:
                try:
                    Path(path_value).resolve()
                except Exception as e:
                    errors.append(f"{path_name} is invalid: {str(e)}")
        
        return errors


class ConfigurationManager:
    """Main configuration management system."""
    
    def __init__(self, config_dir: str = "./config"):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory to store configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.hardware_detector = HardwareDetector()
        self.validator = ConfigurationValidator()
        
        # Default configuration file names
        self.default_config_files = {
            ConfigFormat.YAML: "openclass_config.yaml",
            ConfigFormat.JSON: "openclass_config.json"
        }
    
    def create_default_configuration(self) -> SystemConfiguration:
        """Create default system configuration with auto-detected hardware settings."""
        
        # Detect hardware and create optimized profile
        hardware_profile = self.hardware_detector.detect_hardware()
        
        # Create optimized inference configuration
        inference_config = self.hardware_detector.optimize_inference_config(hardware_profile)
        
        # Create default model configuration
        model_config = ModelConfig()
        
        # Create complete system configuration
        system_config = SystemConfiguration(
            model_config=model_config,
            inference_config=inference_config,
            hardware_profile=hardware_profile
        )
        
        self.logger.info(f"Created default configuration for {hardware_profile.profile_name} hardware profile")
        
        return system_config
    
    def save_configuration(self, config: SystemConfiguration, 
                          filename: Optional[str] = None,
                          format_type: ConfigFormat = ConfigFormat.YAML) -> Path:
        """Save configuration to file.
        
        Args:
            config: System configuration to save
            filename: Optional custom filename
            format_type: File format (YAML or JSON)
            
        Returns:
            Path to saved configuration file
            
        Raises:
            ValueError: If configuration validation fails
            IOError: If file cannot be written
        """
        
        # Validate configuration
        errors = self.validator.validate_system_config(config)
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        # Determine filename
        if filename is None:
            filename = self.default_config_files[format_type]
        
        config_path = self.config_dir / filename
        
        # Convert to dictionary
        config_dict = config.to_dict()
        
        try:
            # Save based on format
            if format_type == ConfigFormat.JSON:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:  # YAML
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
            
            self.logger.info(f"Configuration saved to {config_path}")
            return config_path
            
        except Exception as e:
            raise IOError(f"Failed to save configuration to {config_path}: {str(e)}")
    
    def load_configuration(self, filename: Optional[str] = None,
                          format_type: Optional[ConfigFormat] = None) -> SystemConfiguration:
        """Load configuration from file.
        
        Args:
            filename: Configuration file name (auto-detect if None)
            format_type: File format (auto-detect if None)
            
        Returns:
            Loaded system configuration
            
        Raises:
            FileNotFoundError: If configuration file not found
            ValueError: If configuration is invalid
        """
        
        # Auto-detect configuration file if not specified
        if filename is None:
            config_path = self._find_config_file()
            if config_path is None:
                raise FileNotFoundError("No configuration file found")
        else:
            config_path = self.config_dir / filename
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Auto-detect format if not specified
        if format_type is None:
            format_type = self._detect_format(config_path)
        
        try:
            # Load based on format
            if format_type == ConfigFormat.JSON:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
            else:  # YAML
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_dict = yaml.safe_load(f)
            
            # Create configuration object
            config = SystemConfiguration.from_dict(config_dict)
            
            # Validate loaded configuration
            errors = self.validator.validate_system_config(config)
            if errors:
                raise ValueError(f"Loaded configuration is invalid: {'; '.join(errors)}")
            
            self.logger.info(f"Configuration loaded from {config_path}")
            return config
            
        except Exception as e:
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise
            raise ValueError(f"Failed to load configuration from {config_path}: {str(e)}")
    
    def update_hardware_settings(self, config: SystemConfiguration) -> SystemConfiguration:
        """Update configuration with current hardware settings.
        
        Args:
            config: Existing configuration to update
            
        Returns:
            Updated configuration with current hardware profile
        """
        
        # Detect current hardware
        new_hardware_profile = self.hardware_detector.detect_hardware()
        
        # Update inference config based on new hardware
        optimized_inference = self.hardware_detector.optimize_inference_config(new_hardware_profile)
        
        # Create updated configuration
        updated_config = SystemConfiguration(
            model_config=config.model_config,
            inference_config=optimized_inference,
            hardware_profile=new_hardware_profile,
            app_name=config.app_name,
            version=config.version,
            debug_mode=config.debug_mode,
            log_level=config.log_level,
            models_dir=config.models_dir,
            cache_dir=config.cache_dir,
            logs_dir=config.logs_dir,
            config_dir=config.config_dir,
            supported_languages=config.supported_languages,
            educational_subjects=config.educational_subjects,
            response_language=config.response_language
        )
        
        self.logger.info(f"Hardware settings updated to {new_hardware_profile.profile_name} profile")
        
        return updated_config
    
    def get_or_create_configuration(self) -> SystemConfiguration:
        """Get existing configuration or create default if none exists.
        
        Returns:
            System configuration (loaded or newly created)
        """
        
        try:
            # Try to load existing configuration
            return self.load_configuration()
        except FileNotFoundError:
            # Create and save default configuration
            self.logger.info("No existing configuration found, creating default")
            default_config = self.create_default_configuration()
            self.save_configuration(default_config)
            return default_config
    
    def _find_config_file(self) -> Optional[Path]:
        """Find existing configuration file in config directory."""
        
        # Check for YAML files first (preferred format)
        for ext in ['yaml', 'yml']:
            for filename in self.default_config_files.values():
                config_path = self.config_dir / filename.replace('.json', f'.{ext}')
                if config_path.exists():
                    return config_path
        
        # Check for JSON files
        json_path = self.config_dir / self.default_config_files[ConfigFormat.JSON]
        if json_path.exists():
            return json_path
        
        return None
    
    def _detect_format(self, config_path: Path) -> ConfigFormat:
        """Detect configuration file format from extension."""
        
        suffix = config_path.suffix.lower()
        if suffix == '.json':
            return ConfigFormat.JSON
        elif suffix in ['.yaml', '.yml']:
            return ConfigFormat.YAML
        else:
            # Default to YAML
            return ConfigFormat.YAML


# Global configuration manager instance
config_manager = ConfigurationManager()