"""
Unit tests for Configuration Management System.

Tests the configuration file management, hardware detection,
validation, and auto-optimization features.
"""

import pytest
import json
import yaml
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from edge_runtime.config_manager import (
    ConfigurationManager, HardwareDetector, ConfigurationValidator,
    SystemConfiguration, HardwareProfile, ConfigFormat
)
from edge_runtime.model_config import ModelConfig, InferenceConfig


class TestHardwareDetector:
    """Test hardware detection and optimization."""
    
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_count')
    @patch('psutil.cpu_freq')
    @patch('platform.machine')
    def test_detect_hardware_4gb_system(self, mock_machine, mock_cpu_freq, 
                                       mock_cpu_count, mock_memory):
        """Test hardware detection for 4GB system."""
        # Mock 4GB system
        mock_memory.return_value = MagicMock(total=4 * 1024**3)  # 4GB
        mock_cpu_count.side_effect = [4, 8]  # 4 cores, 8 threads
        mock_cpu_freq.return_value = MagicMock(max=2400)  # 2.4GHz
        mock_machine.return_value = "x86_64"
        
        detector = HardwareDetector()
        profile = detector.detect_hardware()
        
        assert profile.total_memory_gb == 4.0
        assert profile.cpu_cores == 4
        assert profile.cpu_threads == 8
        assert profile.performance_tier == "low"
        assert profile.profile_name == "low_resource"
        assert profile.recommended_memory_limit_mb == 3072
        assert profile.recommended_threads <= 4
    
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_count')
    @patch('psutil.cpu_freq')
    @patch('platform.machine')
    def test_detect_hardware_8gb_system(self, mock_machine, mock_cpu_freq,
                                       mock_cpu_count, mock_memory):
        """Test hardware detection for 8GB system."""
        # Mock 8GB system
        mock_memory.return_value = MagicMock(total=8 * 1024**3)  # 8GB
        mock_cpu_count.side_effect = [6, 12]  # 6 cores, 12 threads
        mock_cpu_freq.return_value = MagicMock(max=3200)  # 3.2GHz
        mock_machine.return_value = "x86_64"
        
        detector = HardwareDetector()
        profile = detector.detect_hardware()
        
        assert profile.total_memory_gb == 8.0
        assert profile.cpu_cores == 6
        assert profile.cpu_threads == 12
        assert profile.performance_tier == "high"
        assert profile.profile_name == "high_performance"
        assert profile.recommended_memory_limit_mb > 3072
        assert profile.recommended_threads <= 8
    
    def test_optimize_inference_config_low_resource(self):
        """Test inference optimization for low-resource systems."""
        detector = HardwareDetector()
        
        # Create low-resource hardware profile
        hardware_profile = HardwareProfile(
            total_memory_gb=4.0,
            cpu_cores=4,
            cpu_threads=4,
            cpu_frequency_ghz=2.0,
            architecture="x86_64",
            recommended_threads=4,
            recommended_memory_limit_mb=3072,
            recommended_context_size=2048,
            recommended_batch_size=256,
            profile_name="low_resource",
            performance_tier="low"
        )
        
        config = detector.optimize_inference_config(hardware_profile)
        
        assert config.n_ctx == 2048
        assert config.n_threads == 4
        assert config.memory_limit_mb == 3072
        assert config.batch_size == 256
        assert config.use_mlock == False  # Disabled for low-resource
        assert config.streaming == True


class TestConfigurationValidator:
    """Test configuration validation."""
    
    def test_validate_valid_model_config(self):
        """Test validation of valid model configuration."""
        validator = ConfigurationValidator()
        model_config = ModelConfig()
        
        errors = validator.validate_model_config(model_config)
        assert len(errors) == 0
    
    def test_validate_invalid_model_config(self):
        """Test validation of invalid model configuration."""
        validator = ConfigurationValidator()
        model_config = ModelConfig(
            model_id="",  # Invalid: empty
            file_size_mb=-100,  # Invalid: negative
            context_window=0  # Invalid: zero
        )
        
        errors = validator.validate_model_config(model_config)
        assert len(errors) > 0
        assert any("model_id cannot be empty" in error for error in errors)
        assert any("file_size_mb must be positive" in error for error in errors)
        assert any("context_window must be positive" in error for error in errors)
    
    def test_validate_valid_inference_config(self):
        """Test validation of valid inference configuration."""
        validator = ConfigurationValidator()
        inference_config = InferenceConfig()
        
        errors = validator.validate_inference_config(inference_config)
        assert len(errors) == 0
    
    def test_validate_invalid_inference_config(self):
        """Test validation of invalid inference configuration."""
        validator = ConfigurationValidator()
        inference_config = InferenceConfig(
            n_ctx=0,  # Invalid: zero
            temperature=2.5,  # Invalid: too high
            top_p=1.5,  # Invalid: > 1.0
            memory_limit_mb=-1000  # Invalid: negative
        )
        
        errors = validator.validate_inference_config(inference_config)
        assert len(errors) > 0
        assert any("n_ctx must be positive" in error for error in errors)
        assert any("temperature must be between" in error for error in errors)
        assert any("top_p must be between" in error for error in errors)
        assert any("memory_limit_mb must be positive" in error for error in errors)


class TestConfigurationManager:
    """Test configuration manager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigurationManager(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir)
    
    @patch.object(HardwareDetector, 'detect_hardware')
    def test_create_default_configuration(self, mock_detect):
        """Test creation of default configuration."""
        # Mock hardware detection
        mock_profile = HardwareProfile(
            total_memory_gb=4.0,
            cpu_cores=4,
            cpu_threads=4,
            cpu_frequency_ghz=2.4,
            architecture="x86_64",
            recommended_threads=4,
            recommended_memory_limit_mb=3072,
            recommended_context_size=4096,
            recommended_batch_size=512,
            profile_name="low_resource",
            performance_tier="low"
        )
        mock_detect.return_value = mock_profile
        
        config = self.config_manager.create_default_configuration()
        
        assert isinstance(config, SystemConfiguration)
        assert config.app_name == "OpenClass Nexus AI"
        assert config.hardware_profile.profile_name == "low_resource"
        assert config.inference_config.memory_limit_mb == 3072
        assert "indonesian" in config.supported_languages
    
    @patch.object(HardwareDetector, 'detect_hardware')
    def test_save_and_load_yaml_configuration(self, mock_detect):
        """Test saving and loading YAML configuration."""
        # Mock hardware detection
        mock_profile = HardwareProfile(
            total_memory_gb=4.0,
            cpu_cores=4,
            cpu_threads=4,
            cpu_frequency_ghz=2.4,
            architecture="x86_64",
            recommended_threads=4,
            recommended_memory_limit_mb=3072,
            recommended_context_size=4096,
            recommended_batch_size=512,
            profile_name="low_resource",
            performance_tier="low"
        )
        mock_detect.return_value = mock_profile
        
        # Create and save configuration
        original_config = self.config_manager.create_default_configuration()
        config_path = self.config_manager.save_configuration(
            original_config, 
            format_type=ConfigFormat.YAML
        )
        
        # Verify file exists and is valid YAML
        assert config_path.exists()
        with open(config_path, 'r') as f:
            yaml_data = yaml.safe_load(f)
        assert yaml_data['app_name'] == "OpenClass Nexus AI"
        
        # Load configuration back
        loaded_config = self.config_manager.load_configuration()
        
        # Verify loaded configuration matches original
        assert loaded_config.app_name == original_config.app_name
        assert loaded_config.hardware_profile.profile_name == original_config.hardware_profile.profile_name
        assert loaded_config.inference_config.memory_limit_mb == original_config.inference_config.memory_limit_mb
    
    @patch.object(HardwareDetector, 'detect_hardware')
    def test_save_and_load_json_configuration(self, mock_detect):
        """Test saving and loading JSON configuration."""
        # Mock hardware detection
        mock_profile = HardwareProfile(
            total_memory_gb=8.0,
            cpu_cores=6,
            cpu_threads=12,
            cpu_frequency_ghz=3.2,
            architecture="x86_64",
            recommended_threads=8,
            recommended_memory_limit_mb=4096,
            recommended_context_size=4096,
            recommended_batch_size=512,
            profile_name="high_performance",
            performance_tier="high"
        )
        mock_detect.return_value = mock_profile
        
        # Create and save configuration
        original_config = self.config_manager.create_default_configuration()
        config_path = self.config_manager.save_configuration(
            original_config,
            format_type=ConfigFormat.JSON
        )
        
        # Verify file exists and is valid JSON
        assert config_path.exists()
        with open(config_path, 'r') as f:
            json_data = json.load(f)
        assert json_data['app_name'] == "OpenClass Nexus AI"
        
        # Load configuration back
        loaded_config = self.config_manager.load_configuration()
        
        # Verify loaded configuration matches original
        assert loaded_config.app_name == original_config.app_name
        assert loaded_config.hardware_profile.profile_name == original_config.hardware_profile.profile_name
    
    def test_load_nonexistent_configuration(self):
        """Test loading non-existent configuration file."""
        with pytest.raises(FileNotFoundError):
            self.config_manager.load_configuration("nonexistent.yaml")
    
    @patch.object(HardwareDetector, 'detect_hardware')
    def test_update_hardware_settings(self, mock_detect):
        """Test updating hardware settings in existing configuration."""
        # Create initial configuration with mock hardware
        initial_profile = HardwareProfile(
            total_memory_gb=4.0,
            cpu_cores=4,
            cpu_threads=4,
            cpu_frequency_ghz=2.0,
            architecture="x86_64",
            recommended_threads=4,
            recommended_memory_limit_mb=3072,
            recommended_context_size=2048,
            recommended_batch_size=256,
            profile_name="low_resource",
            performance_tier="low"
        )
        mock_detect.return_value = initial_profile
        
        original_config = self.config_manager.create_default_configuration()
        
        # Mock new hardware detection (upgraded system)
        new_profile = HardwareProfile(
            total_memory_gb=8.0,
            cpu_cores=6,
            cpu_threads=12,
            cpu_frequency_ghz=3.2,
            architecture="x86_64",
            recommended_threads=8,
            recommended_memory_limit_mb=4096,
            recommended_context_size=4096,
            recommended_batch_size=512,
            profile_name="high_performance",
            performance_tier="high"
        )
        mock_detect.return_value = new_profile
        
        # Update hardware settings
        updated_config = self.config_manager.update_hardware_settings(original_config)
        
        # Verify hardware profile was updated
        assert updated_config.hardware_profile.profile_name == "high_performance"
        assert updated_config.hardware_profile.total_memory_gb == 8.0
        # Note: memory_limit_mb is capped by InferenceConfig post_init for safety
        assert updated_config.inference_config.memory_limit_mb >= 3072
        
        # Verify other settings were preserved
        assert updated_config.app_name == original_config.app_name
        assert updated_config.model_config.model_id == original_config.model_config.model_id
    
    @patch.object(HardwareDetector, 'detect_hardware')
    def test_get_or_create_configuration_new(self, mock_detect):
        """Test get_or_create when no configuration exists."""
        # Mock hardware detection
        mock_profile = HardwareProfile(
            total_memory_gb=4.0,
            cpu_cores=4,
            cpu_threads=4,
            cpu_frequency_ghz=2.4,
            architecture="x86_64",
            recommended_threads=4,
            recommended_memory_limit_mb=3072,
            recommended_context_size=4096,
            recommended_batch_size=512,
            profile_name="low_resource",
            performance_tier="low"
        )
        mock_detect.return_value = mock_profile
        
        # Should create new configuration
        config = self.config_manager.get_or_create_configuration()
        
        assert isinstance(config, SystemConfiguration)
        assert config.hardware_profile.profile_name == "low_resource"
        
        # Verify configuration file was created
        config_files = list(Path(self.temp_dir).glob("*.yaml"))
        assert len(config_files) > 0
    
    def test_invalid_configuration_validation(self):
        """Test validation of invalid configuration during save."""
        # Create invalid configuration
        invalid_config = SystemConfiguration(
            model_config=ModelConfig(model_id=""),  # Invalid: empty model_id
            inference_config=InferenceConfig(n_ctx=0),  # Invalid: zero context
            hardware_profile=HardwareProfile(
                total_memory_gb=-1,  # Invalid: negative memory
                cpu_cores=0,  # Invalid: zero cores
                cpu_threads=0,
                cpu_frequency_ghz=0,
                architecture="",
                recommended_threads=0,
                recommended_memory_limit_mb=0,
                recommended_context_size=0,
                recommended_batch_size=0,
                profile_name="",
                performance_tier="invalid"  # Invalid tier
            )
        )
        
        # Should raise ValueError during save
        with pytest.raises(ValueError) as exc_info:
            self.config_manager.save_configuration(invalid_config)
        
        assert "Configuration validation failed" in str(exc_info.value)


class TestSystemConfiguration:
    """Test SystemConfiguration dataclass."""
    
    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        # Create test configuration
        model_config = ModelConfig()
        inference_config = InferenceConfig()
        hardware_profile = HardwareProfile(
            total_memory_gb=4.0,
            cpu_cores=4,
            cpu_threads=4,
            cpu_frequency_ghz=2.4,
            architecture="x86_64",
            recommended_threads=4,
            recommended_memory_limit_mb=3072,
            recommended_context_size=4096,
            recommended_batch_size=512,
            profile_name="test_profile",
            performance_tier="low"
        )
        
        original_config = SystemConfiguration(
            model_config=model_config,
            inference_config=inference_config,
            hardware_profile=hardware_profile
        )
        
        # Convert to dict and back
        config_dict = original_config.to_dict()
        restored_config = SystemConfiguration.from_dict(config_dict)
        
        # Verify restoration
        assert restored_config.app_name == original_config.app_name
        assert restored_config.model_config.model_id == original_config.model_config.model_id
        assert restored_config.inference_config.n_ctx == original_config.inference_config.n_ctx
        assert restored_config.hardware_profile.profile_name == original_config.hardware_profile.profile_name
    
    def test_post_init_defaults(self):
        """Test post-initialization default values."""
        config = SystemConfiguration(
            model_config=ModelConfig(),
            inference_config=InferenceConfig(),
            hardware_profile=HardwareProfile(
                total_memory_gb=4.0,
                cpu_cores=4,
                cpu_threads=4,
                cpu_frequency_ghz=2.4,
                architecture="x86_64",
                recommended_threads=4,
                recommended_memory_limit_mb=3072,
                recommended_context_size=4096,
                recommended_batch_size=512,
                profile_name="test",
                performance_tier="low"
            )
        )
        
        # Check default values were set
        assert "indonesian" in config.supported_languages
        assert "english" in config.supported_languages
        assert "Informatika" in config.educational_subjects
        assert config.response_language == "indonesian"


if __name__ == '__main__':
    pytest.main([__file__])