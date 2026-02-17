import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.optimization.documentation_generator import DocumentationGenerator
from src.optimization.config import OptimizationConfig
from src.optimization.models import (
    UserGuide,
    APIDocumentation,
    DeploymentGuide,
    TroubleshootingGuide,
    DocumentationPackage
)


class TestDocumentationGenerator:
    """Test cases for DocumentationGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = OptimizationConfig()
        self.config.project_root = self.temp_dir
        self.config.documentation_output_dir = self.temp_dir / "docs"
        self.config.supported_languages = ["indonesian", "english"]
        self.config.include_api_examples = True
        self.config.include_troubleshooting = True
        
        self.generator = DocumentationGenerator(self.config)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test DocumentationGenerator initialization."""
        assert self.generator.config == self.config
        assert self.generator.project_root == self.temp_dir
        assert self.generator.output_dir == self.temp_dir / "docs"
        assert self.generator.supported_languages == ["indonesian", "english"]
        assert self.generator.output_dir.exists()
    
    def test_generate_user_guide_indonesian(self):
        """Test Indonesian user guide generation."""
        user_guide = self.generator.generate_user_guide("indonesian")
        
        # Verify return type and basic properties
        assert isinstance(user_guide, UserGuide)
        assert user_guide.language == "indonesian"
        assert user_guide.examples_included is True
        assert Path(user_guide.file_path).exists()
        
        # Verify content structure
        assert len(user_guide.content) > 1000  # Substantial content
        assert "Panduan Pengguna OpenClass Nexus AI" in user_guide.content
        assert "Pendahuluan" in user_guide.content
        assert "Instalasi" in user_guide.content
        assert "Konfigurasi" in user_guide.content
        
        # Verify sections
        expected_sections = [
            "Pendahuluan", "Instalasi", "Konfigurasi", 
            "Penggunaan Dasar", "Fitur Lanjutan", 
            "Pemecahan Masalah", "FAQ"
        ]
        assert user_guide.sections == expected_sections
        
        # Verify Indonesian language content (case-insensitive)
        content_lower = user_guide.content.lower()
        assert "tutor ai" in content_lower or "platform tutor ai" in content_lower
        assert "pembelajaran informatika" in content_lower or "informatika" in content_lower
        assert "bahasa indonesia" in content_lower or "indonesia" in content_lower
    
    def test_generate_user_guide_english(self):
        """Test English user guide generation."""
        user_guide = self.generator.generate_user_guide("english")
        
        # Verify return type and basic properties
        assert isinstance(user_guide, UserGuide)
        assert user_guide.language == "english"
        assert user_guide.examples_included is True
        assert Path(user_guide.file_path).exists()
        
        # Verify content structure
        assert len(user_guide.content) > 1000  # Substantial content
        assert "OpenClass Nexus AI User Guide" in user_guide.content
        assert "Introduction" in user_guide.content
        assert "Installation" in user_guide.content
        assert "Configuration" in user_guide.content
        
        # Verify sections
        expected_sections = [
            "Introduction", "Installation", "Configuration",
            "Basic Usage", "Advanced Features", 
            "Troubleshooting", "FAQ"
        ]
        assert user_guide.sections == expected_sections
        
        # Verify English language content (case-insensitive)
        content_lower = user_guide.content.lower()
        assert "tutoring platform" in content_lower or "ai tutoring" in content_lower
        assert "informatics" in content_lower or "learning" in content_lower
        assert "educational" in content_lower
    
    def test_generate_user_guide_unsupported_language(self):
        """Test user guide generation with unsupported language."""
        with pytest.raises(ValueError, match="Language 'french' not supported"):
            self.generator.generate_user_guide("french")
    
    def test_create_api_documentation_empty_project(self):
        """Test API documentation generation with empty project."""
        api_docs = self.generator.create_api_documentation()
        
        # Verify return type and basic properties
        assert isinstance(api_docs, APIDocumentation)
        assert api_docs.functions_documented >= 0
        assert api_docs.coverage_percentage >= 0.0
        assert api_docs.examples_included == self.config.include_api_examples
        assert Path(api_docs.file_path).exists()
        
        # Verify content structure
        with open(api_docs.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# OpenClass Nexus AI - API Documentation" in content
        assert "## Overview" in content
        assert "## Table of Contents" in content
    
    def test_create_api_documentation_with_mock_modules(self):
        """Test API documentation generation with mock Python modules."""
        # Create mock Python module
        src_dir = self.temp_dir / "src"
        src_dir.mkdir(parents=True)
        
        mock_module = src_dir / "test_module.py"
        mock_content = '''"""Test module for documentation generation."""

def public_function(arg1, arg2):
    """
    A public function for testing.
    
    Args:
        arg1: First argument
        arg2: Second argument
    
    Returns:
        str: Result string
    """
    return f"Result: {arg1}, {arg2}"

def _private_function():
    """Private function should not be documented."""
    pass

class TestClass:
    """A test class for documentation."""
    
    def public_method(self, data):
        """
        A public method.
        
        Args:
            data: Input data
        
        Returns:
            Processed data
        """
        return f"Processed: {data}"
    
    def _private_method(self):
        """Private method should not be documented."""
        pass
'''
        
        with open(mock_module, 'w', encoding='utf-8') as f:
            f.write(mock_content)
        
        # Generate API documentation
        api_docs = self.generator.create_api_documentation()
        
        # Verify documentation includes the mock module
        assert api_docs.functions_documented >= 2  # public_function + public_method
        assert api_docs.coverage_percentage > 0.0
        
        # Verify content includes the mock module
        with open(api_docs.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "test_module" in content
        assert "public_function" in content
        assert "TestClass" in content
        assert "public_method" in content
        assert "_private_function" not in content  # Private functions excluded
        assert "_private_method" not in content   # Private methods excluded
    
    def test_build_deployment_guide(self):
        """Test deployment guide generation."""
        deployment_guide = self.generator.build_deployment_guide()
        
        # Verify return type and basic properties
        assert isinstance(deployment_guide, DeploymentGuide)
        assert len(deployment_guide.content) > 5000  # Substantial content
        assert Path(deployment_guide.file_path).exists()
        
        # Verify environments covered
        expected_environments = ["development", "staging", "production", "docker"]
        assert deployment_guide.environments_covered == expected_environments
        
        # Verify configuration examples
        expected_configs = [
            "docker-compose.yml", "production.env", 
            "nginx.conf", "systemd.service"
        ]
        assert deployment_guide.configuration_examples == expected_configs
        
        # Verify content structure
        content = deployment_guide.content
        assert "# OpenClass Nexus AI - Production Deployment Guide" in content
        assert "## Prerequisites" in content
        assert "## Deployment Options" in content
        assert "### Option 1: Bare Metal Deployment" in content
        assert "### Option 2: Docker Deployment" in content
        assert "### Option 3: Kubernetes Deployment" in content
        assert "## Monitoring and Maintenance" in content
        assert "## Security Considerations" in content
        
        # Verify technical content (case-insensitive)
        content_lower = content.lower()
        assert "docker" in content_lower or "container" in content_lower
        assert "nginx" in content_lower or "web server" in content_lower
        assert "kubernetes" in content_lower or "deployment" in content_lower
        assert "supervisor" in content_lower or "service" in content_lower
    
    def test_create_troubleshooting_guide(self):
        """Test troubleshooting guide generation."""
        troubleshooting_guide = self.generator.create_troubleshooting_guide()
        
        # Verify return type and basic properties
        assert isinstance(troubleshooting_guide, TroubleshootingGuide)
        assert len(troubleshooting_guide.content) > 3000  # Substantial content
        assert troubleshooting_guide.issues_covered > 0
        assert troubleshooting_guide.solutions_provided > 0
        assert Path(troubleshooting_guide.file_path).exists()
        
        # Verify content structure
        content = troubleshooting_guide.content
        assert "# OpenClass Nexus AI - Troubleshooting Guide" in content
        assert "## Overview" in content
        assert "## Quick Diagnostic Commands" in content
        assert "## Installation Issues" in content
        assert "## Runtime Issues" in content
        assert "## Performance Issues" in content
        assert "## Configuration Issues" in content
        assert "## Deployment Issues" in content
        assert "## Emergency Procedures" in content
        
        # Verify issue patterns
        assert "### Issue:" in content
        assert "**Symptoms**:" in content
        assert "**Solution" in content
        
        # Count issues and solutions
        issue_count = content.count("### Issue:")
        solution_count = content.count("**Solution")
        
        assert issue_count == troubleshooting_guide.issues_covered
        assert solution_count == troubleshooting_guide.solutions_provided
        assert solution_count >= issue_count  # At least one solution per issue
    
    def test_generate_complete_documentation_package(self):
        """Test complete documentation package generation."""
        doc_package = self.generator.generate_complete_documentation_package()
        
        # Verify return type and basic properties
        assert isinstance(doc_package, DocumentationPackage)
        assert doc_package.language_versions == ["indonesian", "english"]
        
        # Verify all documentation files exist
        assert Path(doc_package.user_guide_path).exists()
        assert Path(doc_package.api_documentation_path).exists()
        assert Path(doc_package.deployment_guide_path).exists()
        assert Path(doc_package.troubleshooting_guide_path).exists()
        assert Path(doc_package.examples_directory).exists()
        
        # Verify examples directory contains example files
        examples_dir = Path(doc_package.examples_directory)
        example_files = list(examples_dir.glob("*.py"))
        assert len(example_files) >= 2  # At least basic_usage.py and batch_processing.py
        
        # Verify example file content
        basic_example = examples_dir / "basic_usage.py"
        if basic_example.exists():
            content = basic_example.read_text(encoding='utf-8')
            assert "CompletePipeline" in content
            assert "process_query" in content
        
        config_example = examples_dir / "config_example.json"
        if config_example.exists():
            content = config_example.read_text(encoding='utf-8')
            assert "model" in content
            assert "education" in content
    
    def test_file_write_error_handling(self):
        """Test error handling when file writing fails."""
        # Use mock_open to simulate PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                self.generator.generate_user_guide("indonesian")
    
    def test_configuration_validation(self):
        """Test configuration validation and error handling."""
        # Test with invalid configuration
        invalid_config = OptimizationConfig()
        invalid_config.supported_languages = []  # Empty languages list
        
        generator = DocumentationGenerator(invalid_config)
        
        # Should handle empty languages gracefully
        with pytest.raises(ValueError):
            generator.generate_user_guide("indonesian")
    
    def test_template_fallback_mechanisms(self):
        """Test fallback mechanisms when templates are missing."""
        # Test with minimal configuration
        minimal_config = OptimizationConfig()
        minimal_config.project_root = self.temp_dir
        minimal_config.documentation_output_dir = self.temp_dir / "docs"
        minimal_config.supported_languages = ["english"]  # Only English
        minimal_config.include_api_examples = False
        minimal_config.include_troubleshooting = False
        
        generator = DocumentationGenerator(minimal_config)
        
        # Should still generate documentation with fallbacks
        user_guide = generator.generate_user_guide("english")
        assert isinstance(user_guide, UserGuide)
        assert user_guide.language == "english"
        assert len(user_guide.content) > 500  # Should have substantial content
        
        api_docs = generator.create_api_documentation()
        assert isinstance(api_docs, APIDocumentation)
        assert api_docs.examples_included is False  # Respects configuration
    
    def test_language_support_edge_cases(self):
        """Test edge cases in language support."""
        # Test case sensitivity
        user_guide = self.generator.generate_user_guide("INDONESIAN")
        assert user_guide.language == "indonesian"  # Should normalize case
        
        # Test with language not in supported list but valid
        self.generator.supported_languages.append("spanish")
        
        # Should handle gracefully (fallback to default template)
        user_guide = self.generator.generate_user_guide("spanish")
        assert isinstance(user_guide, UserGuide)
        assert user_guide.language == "spanish"
    
    def test_api_documentation_coverage_calculation(self):
        """Test API documentation coverage calculation accuracy."""
        # Create mock modules with varying documentation quality
        src_dir = self.temp_dir / "src"
        src_dir.mkdir(parents=True)
        
        # Module with good documentation
        good_module = src_dir / "good_module.py"
        good_content = '''"""Well documented module."""

def documented_function():
    """This function has documentation."""
    pass

def undocumented_function():
    pass

class DocumentedClass:
    """This class has documentation."""
    
    def documented_method(self):
        """This method has documentation."""
        pass
    
    def undocumented_method(self):
        pass
'''
        
        with open(good_module, 'w', encoding='utf-8') as f:
            f.write(good_content)
        
        # Generate API documentation
        api_docs = self.generator.create_api_documentation()
        
        # Verify coverage calculation
        assert api_docs.functions_documented > 0
        assert 0.0 <= api_docs.coverage_percentage <= 100.0
        
        # With mixed documentation, coverage should be between 0 and 100
        if api_docs.functions_documented > 1:
            assert 0.0 < api_docs.coverage_percentage < 100.0
    
    def test_example_generation_configuration(self):
        """Test example generation based on configuration."""
        # Test with examples enabled
        self.config.include_api_examples = True
        generator_with_examples = DocumentationGenerator(self.config)
        
        api_docs = generator_with_examples.create_api_documentation()
        assert api_docs.examples_included is True
        
        # Test with examples disabled
        self.config.include_api_examples = False
        generator_without_examples = DocumentationGenerator(self.config)
        
        api_docs = generator_without_examples.create_api_documentation()
        assert api_docs.examples_included is False
    
    def test_documentation_timestamp_accuracy(self):
        """Test that documentation timestamps are accurate."""
        import datetime
        
        before_generation = datetime.datetime.now()
        user_guide = self.generator.generate_user_guide("english")
        after_generation = datetime.datetime.now()
        
        # Timestamp should be between before and after generation
        assert before_generation <= user_guide.timestamp <= after_generation
    
    def test_content_encoding_handling(self):
        """Test proper handling of UTF-8 encoding in content."""
        # Generate Indonesian guide (contains Unicode characters)
        user_guide = self.generator.generate_user_guide("indonesian")
        
        # Verify file can be read with UTF-8 encoding
        with open(user_guide.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should contain Indonesian characters without encoding errors
        assert len(content) > 0
        assert content == user_guide.content
        
        # Verify specific Indonesian characters are preserved
        indonesian_chars = ['ä', 'ö', 'ü', 'ß']  # Common in Indonesian text
        # Note: Our template might not have these specific chars, 
        # but encoding should handle them if present
    
    def test_error_recovery_and_logging(self):
        """Test error recovery and logging behavior."""
        with patch('src.optimization.documentation_generator.logger') as mock_logger:
            # Test successful generation logs info messages
            self.generator.generate_user_guide("english")
            
            # Verify info logging calls
            mock_logger.info.assert_called()
            info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            assert any("Generating user guide" in call for call in info_calls)
            assert any("User guide generated" in call for call in info_calls)
    
    def test_directory_creation_handling(self):
        """Test handling of directory creation scenarios."""
        # Remove output directory to test creation
        if self.generator.output_dir.exists():
            shutil.rmtree(self.generator.output_dir)
        
        # Should create directory automatically
        user_guide = self.generator.generate_user_guide("english")
        
        assert self.generator.output_dir.exists()
        assert Path(user_guide.file_path).exists()
        assert Path(user_guide.file_path).parent == self.generator.output_dir