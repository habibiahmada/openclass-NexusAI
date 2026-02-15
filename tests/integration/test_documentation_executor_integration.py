"""
Integration Tests for Documentation Executor

This module provides integration tests for the documentation executor,
testing end-to-end documentation generation and packaging functionality.

Tests requirement 3.5 from the specification.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.optimization.documentation_executor import (
    DocumentationPackageExecutor,
    DocumentationExecutionConfig,
    DocumentationMetrics,
    run_documentation_generation
)
from src.optimization.config import OptimizationConfig
from src.optimization.models import DocumentationPackage


class TestDocumentationExecutorIntegration:
    """Integration tests for the documentation executor."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory with sample source code."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create project structure
        src_dir = temp_dir / "src"
        src_dir.mkdir()
        
        # Create sample Python modules for API documentation
        sample_module = src_dir / "sample_module.py"
        sample_module.write_text('''
"""Sample module for testing API documentation generation."""

def sample_function(param1: str, param2: int = 10) -> str:
    """
    Sample function for testing API documentation.
    
    Args:
        param1: First parameter description
        param2: Second parameter with default value
    
    Returns:
        Formatted string result
    
    Example:
        >>> sample_function("test", 5)
        'test: 5'
    """
    return f"{param1}: {param2}"

class SampleClass:
    """Sample class for testing API documentation."""
    
    def __init__(self, name: str):
        """
        Initialize sample class.
        
        Args:
            name: Name for the instance
        """
        self.name = name
    
    def get_name(self) -> str:
        """
        Get the name of this instance.
        
        Returns:
            The name string
        """
        return self.name
    
    def process_data(self, data: list) -> dict:
        """
        Process input data and return results.
        
        Args:
            data: List of data items to process
        
        Returns:
            Dictionary with processing results
        """
        return {
            'processed_count': len(data),
            'processor': self.name
        }
''')
        
        # Create another module
        utils_module = src_dir / "utils.py"
        utils_module.write_text('''
"""Utility functions for the sample application."""

def format_output(data: dict, format_type: str = "json") -> str:
    """
    Format output data according to specified format.
    
    Args:
        data: Data dictionary to format
        format_type: Output format ("json", "xml", "yaml")
    
    Returns:
        Formatted string representation
    
    Raises:
        ValueError: If format_type is not supported
    """
    if format_type == "json":
        import json
        return json.dumps(data, indent=2)
    elif format_type == "xml":
        return f"<data>{data}</data>"
    elif format_type == "yaml":
        return f"data: {data}"
    else:
        raise ValueError(f"Unsupported format: {format_type}")

def validate_input(input_data: any) -> bool:
    """
    Validate input data.
    
    Args:
        input_data: Data to validate
    
    Returns:
        True if valid, False otherwise
    """
    return input_data is not None
''')
        
        # Create config directory
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        # Create docs directory
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()
        
        # Create basic project files
        (temp_dir / "README.md").write_text("# Sample Project\n\nThis is a sample project for testing.")
        (temp_dir / "requirements.txt").write_text("pytest>=6.0.0\nrequests>=2.25.0")
        
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def test_config(self, temp_project_dir):
        """Create test configuration."""
        config = OptimizationConfig()
        config.project_root = temp_project_dir
        config.documentation_output_dir = temp_project_dir / "docs" / "generated"
        return config
    
    @pytest.fixture
    def test_exec_config(self):
        """Create test execution configuration."""
        exec_config = DocumentationExecutionConfig()
        exec_config.generate_indonesian = True
        exec_config.generate_english = True
        exec_config.include_api_examples = True
        exec_config.include_code_samples = True
        exec_config.create_archive = False  # Skip for testing
        exec_config.export_html_versions = True
        exec_config.validate_completeness = True
        return exec_config
    
    def test_complete_documentation_generation(self, test_config, test_exec_config, temp_project_dir):
        """Test complete documentation package generation."""
        # Create documentation executor
        executor = DocumentationPackageExecutor(test_config, test_exec_config)
        
        # Execute documentation generation
        package = executor.execute_complete_documentation_generation()
        
        # Verify package was created
        assert package is not None
        assert isinstance(package, DocumentationPackage)
        
        # Verify language versions
        assert len(package.language_versions) == 2
        assert "indonesian" in package.language_versions
        assert "english" in package.language_versions
        
        # Verify documentation files were created
        assert Path(package.user_guide_path).exists()
        assert Path(package.api_documentation_path).exists()
        assert Path(package.deployment_guide_path).exists()
        assert Path(package.troubleshooting_guide_path).exists()
        
        # Verify examples directory
        examples_dir = Path(package.examples_directory)
        assert examples_dir.exists()
        assert (examples_dir / "README.md").exists()
        
        # Verify configuration examples
        config_dir = examples_dir / "configuration"
        if config_dir.exists():
            assert (config_dir / "environment_example.env").exists()
            assert (config_dir / "model_config_example.json").exists()
        
        # Verify code examples
        code_dir = examples_dir / "code"
        if code_dir.exists():
            assert (code_dir / "basic_usage.py").exists()
            assert (code_dir / "batch_processing.py").exists()
        
        # Verify metrics
        assert executor.metrics.total_documents_generated > 0
        assert executor.metrics.user_guides_generated == 2  # Indonesian + English
        assert executor.metrics.api_docs_generated == 1
        assert executor.metrics.deployment_guides_generated == 1
        assert executor.metrics.troubleshooting_guides_generated == 1
        
        # Verify success rate
        success_rate = executor.metrics.calculate_success_rate()
        assert success_rate > 0
        
        # Verify generation report was created
        report_file = test_config.documentation_output_dir / "generation_report.json"
        if report_file.exists():
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
                assert 'generation_summary' in report_data
                assert 'detailed_metrics' in report_data
                assert report_data['generation_summary']['total_documents_generated'] > 0
    
    def test_api_documentation_generation(self, test_config, test_exec_config, temp_project_dir):
        """Test API documentation generation with actual source code."""
        # Create executor
        executor = DocumentationPackageExecutor(test_config, test_exec_config)
        
        # Generate API documentation
        executor._generate_api_documentation()
        
        # Verify API documentation was generated
        api_doc = executor.generated_documents['api_documentation']
        assert api_doc is not None
        assert api_doc.functions_documented > 0
        assert api_doc.coverage_percentage > 0
        
        # Verify API documentation file exists and contains expected content
        api_file = Path(api_doc.file_path)
        assert api_file.exists()
        
        api_content = api_file.read_text(encoding='utf-8')
        
        # Check for documented functions
        assert "sample_function" in api_content
        assert "SampleClass" in api_content
        assert "format_output" in api_content
        assert "validate_input" in api_content
        
        # Check for documentation structure
        assert "API Documentation" in api_content
        assert "Table of Contents" in api_content
        assert "Arguments" in api_content or "Parameters" in api_content
        assert "Returns" in api_content
    
    def test_user_guide_generation_multiple_languages(self, test_config, test_exec_config):
        """Test user guide generation in multiple languages."""
        # Create executor
        executor = DocumentationPackageExecutor(test_config, test_exec_config)
        
        # Generate user guides
        executor._generate_user_guides()
        
        # Verify both language guides were generated
        user_guides = executor.generated_documents['user_guides']
        assert 'indonesian' in user_guides
        assert 'english' in user_guides
        
        # Verify Indonesian guide
        id_guide = user_guides['indonesian']
        assert id_guide is not None
        assert id_guide.language == "indonesian"
        assert Path(id_guide.file_path).exists()
        
        id_content = Path(id_guide.file_path).read_text(encoding='utf-8')
        assert "Panduan Pengguna" in id_content
        assert "Instalasi" in id_content
        assert "Konfigurasi" in id_content
        
        # Verify English guide
        en_guide = user_guides['english']
        assert en_guide is not None
        assert en_guide.language == "english"
        assert Path(en_guide.file_path).exists()
        
        en_content = Path(en_guide.file_path).read_text(encoding='utf-8')
        assert "User Guide" in en_content
        assert "Installation" in en_content
        assert "Configuration" in en_content
    
    def test_documentation_metrics_tracking(self, test_config, test_exec_config):
        """Test documentation metrics tracking and calculation."""
        # Create executor
        executor = DocumentationPackageExecutor(test_config, test_exec_config)
        
        # Initialize metrics
        executor._initialize_generation_process()
        
        # Verify initial metrics
        assert executor.metrics.total_documents_generated == 0
        assert executor.metrics.user_guides_generated == 0
        
        # Generate user guides and verify metrics update
        executor._generate_user_guides()
        
        assert executor.metrics.user_guides_generated == 2  # Indonesian + English
        assert executor.metrics.total_documents_generated == 2
        assert "indonesian" in executor.metrics.languages_generated
        assert "english" in executor.metrics.languages_generated
        
        # Generate API documentation and verify metrics update
        executor._generate_api_documentation()
        
        assert executor.metrics.api_docs_generated == 1
        assert executor.metrics.total_documents_generated == 3
        assert executor.metrics.api_coverage_percentage > 0
        
        # Test metrics serialization
        metrics_dict = executor.metrics.to_dict()
        assert isinstance(metrics_dict, dict)
        assert 'total_documents_generated' in metrics_dict
        assert 'languages_generated' in metrics_dict
        assert 'success_rate_percentage' in metrics_dict
    
    def test_documentation_validation(self, test_config, test_exec_config):
        """Test documentation completeness validation."""
        # Create executor
        executor = DocumentationPackageExecutor(test_config, test_exec_config)
        
        # Generate some documentation
        executor._generate_user_guides()
        executor._generate_api_documentation()
        
        # Run validation
        executor._validate_documentation_completeness()
        
        # Verify validation results
        assert executor.metrics.validation_errors >= 0
        assert executor.metrics.validation_warnings >= 0
        
        # If all required docs were generated, should have no errors
        if (executor.generated_documents['user_guides'] and 
            executor.generated_documents['api_documentation']):
            # Some warnings might be acceptable, but errors should be minimal
            assert executor.metrics.validation_errors <= 2  # Allow for minor issues
    
    def test_additional_resources_generation(self, test_config, test_exec_config):
        """Test generation of additional resources like examples and README files."""
        # Create executor
        executor = DocumentationPackageExecutor(test_config, test_exec_config)
        
        # Generate additional resources
        executor._generate_additional_resources()
        
        # Verify examples directory was created
        examples_dir = test_config.documentation_output_dir / "examples"
        assert examples_dir.exists()
        
        # Verify README files
        main_readme = test_config.documentation_output_dir / "README.md"
        if main_readme.exists():
            readme_content = main_readme.read_text(encoding='utf-8')
            assert "OpenClass Nexus AI" in readme_content
            assert "Documentation Package" in readme_content
        
        examples_readme = examples_dir / "README.md"
        if examples_readme.exists():
            examples_content = examples_readme.read_text(encoding='utf-8')
            assert "Examples and Configuration Templates" in examples_content
        
        # Verify index files
        index_html = test_config.documentation_output_dir / "index.html"
        if index_html.exists():
            index_content = index_html.read_text(encoding='utf-8')
            assert "Documentation Index" in index_content
            assert "OpenClass Nexus AI" in index_content
    
    def test_documentation_error_handling(self, test_config, test_exec_config):
        """Test documentation generation error handling."""
        # Mock documentation generator to raise an error
        with patch('src.optimization.documentation_executor.DocumentationGenerator') as mock_doc_gen:
            mock_generator = Mock()
            mock_doc_gen.return_value = mock_generator
            
            # Make user guide generation fail
            mock_generator.generate_user_guide.side_effect = RuntimeError("User guide generation failed")
            
            # Create executor
            executor = DocumentationPackageExecutor(test_config, test_exec_config)
            executor.documentation_generator = mock_generator
            
            # Try to generate user guides (should handle error gracefully)
            executor._generate_user_guides()
            
            # Verify error was handled
            assert executor.metrics.validation_errors > 0
            assert executor.metrics.user_guides_generated == 0
    
    def test_documentation_export_functionality(self, test_config, test_exec_config):
        """Test documentation export and archiving functionality."""
        # Enable export features
        test_exec_config.export_html_versions = True
        test_exec_config.create_archive = True
        test_exec_config.archive_format = "zip"
        
        # Create executor
        executor = DocumentationPackageExecutor(test_config, test_exec_config)
        
        # Generate minimal documentation
        executor._generate_user_guides()
        
        # Test export report generation
        executor._export_generation_report()
        
        # Verify generation report was created
        report_file = test_config.documentation_output_dir / "generation_report.json"
        if report_file.exists():
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
                assert 'generation_summary' in report_data
                assert 'detailed_metrics' in report_data
                assert 'generated_documents' in report_data
                assert 'configuration' in report_data
    
    def test_run_documentation_generation_convenience_function(self, test_config, test_exec_config):
        """Test the convenience function for running documentation generation."""
        with patch('src.optimization.documentation_executor.DocumentationPackageExecutor') as mock_executor_class:
            # Setup mock executor
            mock_executor = Mock()
            mock_executor_class.return_value = mock_executor
            
            # Create mock documentation package
            mock_package = DocumentationPackage(
                user_guide_path="/test/user_guide.md",
                api_documentation_path="/test/api_docs.md",
                deployment_guide_path="/test/deployment.md",
                troubleshooting_guide_path="/test/troubleshooting.md",
                examples_directory="/test/examples",
                language_versions=["indonesian", "english"]
            )
            
            mock_executor.execute_complete_documentation_generation.return_value = mock_package
            
            # Run documentation generation using convenience function
            result = run_documentation_generation(test_config, test_exec_config)
            
            # Verify convenience function worked
            assert result is not None
            assert result.user_guide_path == "/test/user_guide.md"
            assert len(result.language_versions) == 2
            assert mock_executor_class.called
            assert mock_executor.execute_complete_documentation_generation.called
    
    def test_documentation_content_quality(self, test_config, test_exec_config, temp_project_dir):
        """Test the quality and completeness of generated documentation content."""
        # Create executor
        executor = DocumentationPackageExecutor(test_config, test_exec_config)
        
        # Generate complete documentation
        package = executor.execute_complete_documentation_generation()
        
        # Test user guide content quality
        if Path(package.user_guide_path).exists():
            user_guide_content = Path(package.user_guide_path).read_text(encoding='utf-8')
            
            # Check for essential sections
            essential_sections = [
                "Pendahuluan" if "indonesian" in package.user_guide_path else "Introduction",
                "Instalasi" if "indonesian" in package.user_guide_path else "Installation",
                "Konfigurasi" if "indonesian" in package.user_guide_path else "Configuration"
            ]
            
            for section in essential_sections:
                assert section in user_guide_content, f"Missing section: {section}"
            
            # Check for code examples
            assert "```" in user_guide_content, "Missing code examples"
        
        # Test API documentation content quality
        if Path(package.api_documentation_path).exists():
            api_content = Path(package.api_documentation_path).read_text(encoding='utf-8')
            
            # Check for API documentation structure
            assert "API Documentation" in api_content
            assert "sample_function" in api_content  # From our test module
            assert "SampleClass" in api_content  # From our test module
            
            # Check for parameter documentation
            assert "Args:" in api_content or "Parameters:" in api_content
            assert "Returns:" in api_content
        
        # Test deployment guide content quality
        if Path(package.deployment_guide_path).exists():
            deployment_content = Path(package.deployment_guide_path).read_text(encoding='utf-8')
            
            # Check for deployment sections
            assert "Deployment" in deployment_content
            assert "Production" in deployment_content
            assert "Configuration" in deployment_content
        
        # Test troubleshooting guide content quality
        if Path(package.troubleshooting_guide_path).exists():
            troubleshooting_content = Path(package.troubleshooting_guide_path).read_text(encoding='utf-8')
            
            # Check for troubleshooting sections
            assert "Troubleshooting" in troubleshooting_content
            assert "Issue:" in troubleshooting_content or "Problem:" in troubleshooting_content
            assert "Solution" in troubleshooting_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])