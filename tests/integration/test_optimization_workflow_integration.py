"""
Integration Tests for Optimization Workflow

This module provides comprehensive integration tests for the complete optimization
workflow, testing end-to-end functionality including cleanup, demonstration,
documentation generation, and workflow orchestration.

Tests requirements 1.4, 2.5, 3.5 from the specification.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.optimization.optimization_workflow import OptimizationWorkflow, run_optimization_workflow
from src.optimization.config import OptimizationConfig
from src.optimization.models import (
    CleanupReport, DemonstrationReport, DocumentationPackage,
    PerformanceBenchmark, ValidationResults, DemoResponse
)


class TestOptimizationWorkflowIntegration:
    """Integration tests for the complete optimization workflow."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create basic project structure
        (temp_dir / "src").mkdir()
        (temp_dir / "src" / "optimization").mkdir()
        (temp_dir / "config").mkdir()
        (temp_dir / "docs").mkdir()
        (temp_dir / "tests").mkdir()
        
        # Create some test files
        (temp_dir / "README.md").write_text("# Test Project")
        (temp_dir / "requirements.txt").write_text("pytest>=6.0.0")
        (temp_dir / ".env.example").write_text("TEST_VAR=example")
        
        # Create some temporary files to clean up
        (temp_dir / "temp.tmp").write_text("temporary file")
        (temp_dir / "cache.cache").write_text("cache file")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def test_config(self, temp_project_dir):
        """Create test configuration."""
        config = OptimizationConfig()
        config.project_root = temp_project_dir
        config.optimization_output_dir = temp_project_dir / "optimization_output"
        config.documentation_output_dir = temp_project_dir / "docs" / "optimization"
        
        # Adjust for testing
        config.temp_file_patterns = ["*.tmp", "*.cache"]
        config.preserve_essential_files = ["README.md", "requirements.txt", ".env.example", "src/", "config/", "docs/", "tests/"]
        
        return config
    
    def test_complete_workflow_execution(self, test_config):
        """Test complete optimization workflow execution."""
        # Mock the demonstration engine to avoid actual AI model loading
        with patch('src.optimization.optimization_workflow.SystemDemonstrationEngine') as mock_demo_engine:
            # Setup mock demonstration engine
            mock_engine_instance = Mock()
            mock_demo_engine.return_value = mock_engine_instance
            mock_engine_instance.initialize_pipeline.return_value = True
            
            # Create mock demo responses
            mock_demo_responses = [
                DemoResponse(
                    query="Test query 1",
                    response="Test response 1",
                    response_time_ms=1500.0,
                    memory_usage_mb=512.0,
                    curriculum_alignment_score=0.85,
                    language_quality_score=0.80,
                    sources_used=["source1.txt"],
                    confidence_score=0.82,
                    educational_grade="Good"
                ),
                DemoResponse(
                    query="Test query 2", 
                    response="Test response 2",
                    response_time_ms=1800.0,
                    memory_usage_mb=480.0,
                    curriculum_alignment_score=0.90,
                    language_quality_score=0.85,
                    sources_used=["source2.txt"],
                    confidence_score=0.87,
                    educational_grade="Excellent"
                )
            ]
            
            mock_engine_instance.generate_sample_responses.return_value = mock_demo_responses
            
            # Create mock demonstration report
            mock_benchmark = PerformanceBenchmark(
                average_response_time_ms=1650.0,
                peak_memory_usage_mb=512.0,
                throughput_queries_per_minute=36.0,
                concurrent_query_capacity=3,
                curriculum_alignment_accuracy=0.875,
                system_stability_score=0.95,
                hardware_efficiency_score=0.88
            )
            
            mock_validation = ValidationResults(
                curriculum_alignment_score=0.875,
                language_quality_score=0.825,
                age_appropriateness_score=0.85,
                source_attribution_accuracy=0.90,
                overall_quality_score=0.86
            )
            
            mock_demo_report = DemonstrationReport(
                demo_responses=mock_demo_responses,
                performance_benchmark=mock_benchmark,
                validation_results=mock_validation,
                summary="Mock demonstration completed successfully"
            )
            
            mock_engine_instance.create_demonstration_report.return_value = mock_demo_report
            
            # Create workflow and execute
            workflow = OptimizationWorkflow(test_config)
            results = workflow.execute_complete_workflow()
            
            # Verify workflow completed successfully
            assert results.success is True
            assert results.cleanup_report is not None
            assert results.demonstration_report is not None
            assert results.documentation_package is not None
            assert results.workflow_progress is not None
            
            # Verify cleanup results
            cleanup = results.cleanup_report
            assert cleanup.files_removed >= 0  # May be 0 if no temp files found
            assert cleanup.cleanup_duration_seconds >= 0
            assert isinstance(cleanup.recommendations, list)
            
            # Verify demonstration results
            demo = results.demonstration_report
            assert demo.summary == "Mock demonstration completed successfully"
            assert len(demo.demo_responses) == 2
            assert demo.performance_benchmark.average_response_time_ms == 1650.0
            
            # Verify documentation results
            docs = results.documentation_package
            assert docs.language_versions is not None
            assert len(docs.language_versions) > 0
            
            # Verify output files were created
            assert test_config.optimization_output_dir.exists()
            
            # Check for workflow results file
            results_file = test_config.optimization_output_dir / "optimization_workflow_results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    exported_results = json.load(f)
                    assert exported_results['success'] is True
    
    def test_workflow_with_progress_callback(self, test_config):
        """Test workflow execution with progress callback."""
        progress_updates = []
        
        def progress_callback(progress):
            progress_updates.append({
                'step': progress.current_step,
                'operation': progress.current_operation,
                'percentage': progress.progress_percentage
            })
        
        # Mock demonstration engine
        with patch('src.optimization.optimization_workflow.SystemDemonstrationEngine') as mock_demo_engine:
            mock_engine_instance = Mock()
            mock_demo_engine.return_value = mock_engine_instance
            mock_engine_instance.initialize_pipeline.return_value = True
            mock_engine_instance.generate_sample_responses.return_value = []
            
            # Create minimal mock report
            mock_benchmark = PerformanceBenchmark(
                average_response_time_ms=0.0,
                peak_memory_usage_mb=0.0,
                throughput_queries_per_minute=0.0,
                concurrent_query_capacity=0,
                curriculum_alignment_accuracy=0.0,
                system_stability_score=0.0,
                hardware_efficiency_score=0.0
            )
            
            mock_validation = ValidationResults(
                curriculum_alignment_score=0.0,
                language_quality_score=0.0,
                age_appropriateness_score=0.0,
                source_attribution_accuracy=0.0,
                overall_quality_score=0.0
            )
            
            mock_demo_report = DemonstrationReport(
                demo_responses=[],
                performance_benchmark=mock_benchmark,
                validation_results=mock_validation,
                summary="Empty demonstration for testing"
            )
            
            mock_engine_instance.create_demonstration_report.return_value = mock_demo_report
            
            # Run workflow with progress callback
            results = run_optimization_workflow(test_config, progress_callback)
            
            # Verify progress updates were received
            assert len(progress_updates) > 0
            
            # Verify progress updates are sequential
            for i in range(1, len(progress_updates)):
                assert progress_updates[i]['step'] >= progress_updates[i-1]['step']
            
            # Verify final progress is 100%
            if progress_updates:
                final_progress = progress_updates[-1]
                assert final_progress['percentage'] == 100.0
    
    def test_workflow_error_handling(self, test_config):
        """Test workflow error handling and recovery."""
        # Mock demonstration engine to raise an error
        with patch('src.optimization.optimization_workflow.SystemDemonstrationEngine') as mock_demo_engine:
            mock_engine_instance = Mock()
            mock_demo_engine.return_value = mock_engine_instance
            mock_engine_instance.initialize_pipeline.side_effect = RuntimeError("Mock initialization error")
            
            # Create workflow and execute
            workflow = OptimizationWorkflow(test_config)
            results = workflow.execute_complete_workflow()
            
            # Verify workflow handled error gracefully
            assert results.success is False
            assert "Mock initialization error" in results.summary
            assert len(results.workflow_progress.errors_encountered) > 0
            
            # Verify partial results are still available
            assert results.cleanup_report is not None  # Cleanup should succeed
            assert results.workflow_progress is not None
    
    def test_workflow_checkpoint_validation(self, test_config):
        """Test workflow checkpoint validation."""
        # Create workflow
        workflow = OptimizationWorkflow(test_config)
        
        # Setup checkpoints
        workflow._setup_checkpoints()
        
        # Verify checkpoints were created
        assert len(workflow.checkpoints) > 0
        
        # Test individual checkpoint validation
        project_checkpoint = next(
            (cp for cp in workflow.checkpoints if cp.name == "project_structure_validation"), 
            None
        )
        assert project_checkpoint is not None
        
        # Execute project structure validation
        result = workflow._validate_project_structure()
        assert result is True  # Should pass with our test project structure
    
    def test_workflow_component_initialization(self, test_config):
        """Test workflow component initialization."""
        workflow = OptimizationWorkflow(test_config)
        
        # Test component initialization
        success = workflow._initialize_components()
        assert success is True
        
        # Verify components were initialized
        assert workflow.cleanup_manager is not None
        assert workflow.demonstration_engine is not None
        assert workflow.documentation_generator is not None
    
    def test_workflow_results_serialization(self, test_config):
        """Test workflow results can be properly serialized."""
        # Mock demonstration engine
        with patch('src.optimization.optimization_workflow.SystemDemonstrationEngine') as mock_demo_engine:
            mock_engine_instance = Mock()
            mock_demo_engine.return_value = mock_engine_instance
            mock_engine_instance.initialize_pipeline.return_value = True
            mock_engine_instance.generate_sample_responses.return_value = []
            
            # Create minimal mock report
            mock_benchmark = PerformanceBenchmark(
                average_response_time_ms=1000.0,
                peak_memory_usage_mb=256.0,
                throughput_queries_per_minute=60.0,
                concurrent_query_capacity=2,
                curriculum_alignment_accuracy=0.80,
                system_stability_score=0.90,
                hardware_efficiency_score=0.85
            )
            
            mock_validation = ValidationResults(
                curriculum_alignment_score=0.80,
                language_quality_score=0.75,
                age_appropriateness_score=0.82,
                source_attribution_accuracy=0.88,
                overall_quality_score=0.81
            )
            
            mock_demo_report = DemonstrationReport(
                demo_responses=[],
                performance_benchmark=mock_benchmark,
                validation_results=mock_validation,
                summary="Serialization test"
            )
            
            mock_engine_instance.create_demonstration_report.return_value = mock_demo_report
            
            # Run workflow
            results = run_optimization_workflow(test_config)
            
            # Test serialization
            results_dict = results.to_dict()
            
            # Verify serialization structure
            assert isinstance(results_dict, dict)
            assert 'success' in results_dict
            assert 'summary' in results_dict
            assert 'workflow_duration_seconds' in results_dict
            
            # Verify nested objects are serialized
            if results_dict['cleanup_report']:
                assert isinstance(results_dict['cleanup_report'], dict)
            
            if results_dict['demonstration_report']:
                assert isinstance(results_dict['demonstration_report'], dict)
            
            if results_dict['documentation_package']:
                assert isinstance(results_dict['documentation_package'], dict)
            
            # Test JSON serialization
            json_str = json.dumps(results_dict, ensure_ascii=False)
            assert len(json_str) > 0
            
            # Test deserialization
            deserialized = json.loads(json_str)
            assert deserialized['success'] == results_dict['success']


class TestDemonstrationExecutorIntegration:
    """Integration tests for the demonstration executor."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_demonstration_executor_integration(self, temp_output_dir):
        """Test demonstration executor integration."""
        from src.optimization.demonstration_executor import SystemDemonstrationExecutor, DemonstrationConfig
        
        # Create test configuration
        config = OptimizationConfig()
        config.optimization_output_dir = temp_output_dir
        
        demo_config = DemonstrationConfig()
        demo_config.sample_queries = [
            {
                'query': 'Test query for integration',
                'subject': 'informatika',
                'grade': 'kelas_10',
                'expected_topics': ['test', 'integration'],
                'difficulty': 'basic'
            }
        ]
        demo_config.export_detailed_results = True
        demo_config.export_json_results = True
        
        # Mock the demonstration engine
        with patch('src.optimization.demonstration_executor.SystemDemonstrationEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_engine.initialize_pipeline.return_value = True
            
            # Create mock demo response
            mock_response = DemoResponse(
                query="Test query for integration",
                response="Test response for integration testing",
                response_time_ms=1200.0,
                memory_usage_mb=300.0,
                curriculum_alignment_score=0.88,
                language_quality_score=0.82,
                sources_used=["test_source.txt"],
                confidence_score=0.85,
                educational_grade="Good"
            )
            
            mock_engine.generate_sample_responses.return_value = [mock_response]
            
            # Create mock demonstration report
            mock_benchmark = PerformanceBenchmark(
                average_response_time_ms=1200.0,
                peak_memory_usage_mb=300.0,
                throughput_queries_per_minute=50.0,
                concurrent_query_capacity=2,
                curriculum_alignment_accuracy=0.88,
                system_stability_score=0.92,
                hardware_efficiency_score=0.86
            )
            
            mock_validation = ValidationResults(
                curriculum_alignment_score=0.88,
                language_quality_score=0.82,
                age_appropriateness_score=0.85,
                source_attribution_accuracy=0.90,
                overall_quality_score=0.86
            )
            
            mock_demo_report = DemonstrationReport(
                demo_responses=[mock_response],
                performance_benchmark=mock_benchmark,
                validation_results=mock_validation,
                summary="Integration test demonstration"
            )
            
            mock_engine.create_demonstration_report.return_value = mock_demo_report
            
            # Create and execute demonstration executor
            executor = SystemDemonstrationExecutor(config, demo_config)
            
            # Mock the demonstration engine in the executor
            executor.demonstration_engine = mock_engine
            
            # Execute demonstration
            report = executor.execute_comprehensive_demonstration()
            
            # Verify results
            assert report is not None
            assert report.summary == "Integration test demonstration"
            assert len(report.demo_responses) == 1
            assert report.performance_benchmark.average_response_time_ms == 1200.0
            assert report.validation_results.curriculum_alignment_score == 0.88


class TestDocumentationExecutorIntegration:
    """Integration tests for the documentation executor."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory with source code."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create project structure
        src_dir = temp_dir / "src"
        src_dir.mkdir()
        
        # Create a sample Python module for API documentation
        sample_module = src_dir / "sample_module.py"
        sample_module.write_text('''
"""Sample module for testing API documentation generation."""

def sample_function(param1: str, param2: int = 10) -> str:
    """
    Sample function for testing.
    
    Args:
        param1: First parameter
        param2: Second parameter with default value
    
    Returns:
        Formatted string result
    """
    return f"{param1}: {param2}"

class SampleClass:
    """Sample class for testing."""
    
    def __init__(self, name: str):
        """Initialize sample class."""
        self.name = name
    
    def get_name(self) -> str:
        """Get the name."""
        return self.name
''')
        
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_documentation_executor_integration(self, temp_project_dir):
        """Test documentation executor integration."""
        from src.optimization.documentation_executor import DocumentationPackageExecutor, DocumentationExecutionConfig
        
        # Create test configuration
        config = OptimizationConfig()
        config.project_root = temp_project_dir
        config.documentation_output_dir = temp_project_dir / "docs"
        
        exec_config = DocumentationExecutionConfig()
        exec_config.generate_indonesian = True
        exec_config.generate_english = False  # Skip English for faster testing
        exec_config.create_archive = False  # Skip archive creation for testing
        exec_config.export_html_versions = False  # Skip HTML for testing
        
        # Create and execute documentation executor
        executor = DocumentationPackageExecutor(config, exec_config)
        package = executor.execute_complete_documentation_generation()
        
        # Verify results
        assert package is not None
        assert len(package.language_versions) > 0
        assert "indonesian" in package.language_versions
        
        # Verify files were created
        assert Path(package.user_guide_path).exists()
        assert Path(package.api_documentation_path).exists()
        assert Path(package.deployment_guide_path).exists()
        assert Path(package.troubleshooting_guide_path).exists()
        
        # Verify examples directory
        examples_dir = Path(package.examples_directory)
        assert examples_dir.exists()
        assert (examples_dir / "README.md").exists()
        
        # Verify metrics
        assert executor.metrics.total_documents_generated > 0
        assert executor.metrics.user_guides_generated > 0
        assert executor.metrics.api_docs_generated > 0
        assert executor.metrics.deployment_guides_generated > 0
        assert executor.metrics.troubleshooting_guides_generated > 0


class TestWorkflowErrorRecovery:
    """Test workflow error recovery and resilience."""
    
    @pytest.fixture
    def minimal_config(self):
        """Create minimal configuration for error testing."""
        temp_dir = Path(tempfile.mkdtemp())
        config = OptimizationConfig()
        config.project_root = temp_dir
        config.optimization_output_dir = temp_dir / "output"
        return config, temp_dir
    
    def test_workflow_partial_failure_recovery(self, minimal_config):
        """Test workflow recovery from partial failures."""
        config, temp_dir = minimal_config
        
        try:
            # Mock demonstration engine to fail
            with patch('src.optimization.optimization_workflow.SystemDemonstrationEngine') as mock_demo_engine:
                mock_engine_instance = Mock()
                mock_demo_engine.return_value = mock_engine_instance
                mock_engine_instance.initialize_pipeline.return_value = False  # Fail initialization
                
                # Create workflow
                workflow = OptimizationWorkflow(config)
                results = workflow.execute_complete_workflow()
                
                # Verify workflow handled partial failure
                assert results.success is False
                assert results.cleanup_report is not None  # Cleanup should still work
                assert len(results.workflow_progress.errors_encountered) > 0
                
                # Verify error is properly recorded
                error_found = any("Failed to initialize demonstration pipeline" in error 
                                for error in results.workflow_progress.errors_encountered)
                assert error_found
        
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_workflow_component_isolation(self, minimal_config):
        """Test that component failures don't affect other components."""
        config, temp_dir = minimal_config
        
        try:
            # Create basic project structure
            (temp_dir / "src").mkdir()
            (temp_dir / "README.md").write_text("# Test")
            
            # Mock only documentation generator to fail
            with patch('src.optimization.optimization_workflow.DocumentationGenerator') as mock_doc_gen:
                mock_doc_gen.side_effect = RuntimeError("Documentation generation failed")
                
                # Mock demonstration engine to succeed
                with patch('src.optimization.optimization_workflow.SystemDemonstrationEngine') as mock_demo_engine:
                    mock_engine_instance = Mock()
                    mock_demo_engine.return_value = mock_engine_instance
                    mock_engine_instance.initialize_pipeline.return_value = True
                    mock_engine_instance.generate_sample_responses.return_value = []
                    
                    # Create minimal mock report
                    mock_benchmark = PerformanceBenchmark(
                        average_response_time_ms=0.0,
                        peak_memory_usage_mb=0.0,
                        throughput_queries_per_minute=0.0,
                        concurrent_query_capacity=0,
                        curriculum_alignment_accuracy=0.0,
                        system_stability_score=0.0,
                        hardware_efficiency_score=0.0
                    )
                    
                    mock_validation = ValidationResults(
                        curriculum_alignment_score=0.0,
                        language_quality_score=0.0,
                        age_appropriateness_score=0.0,
                        source_attribution_accuracy=0.0,
                        overall_quality_score=0.0
                    )
                    
                    mock_demo_report = DemonstrationReport(
                        demo_responses=[],
                        performance_benchmark=mock_benchmark,
                        validation_results=mock_validation,
                        summary="Mock report"
                    )
                    
                    mock_engine_instance.create_demonstration_report.return_value = mock_demo_report
                    
                    # Create workflow
                    workflow = OptimizationWorkflow(config)
                    results = workflow.execute_complete_workflow()
                    
                    # Verify cleanup and demonstration succeeded despite documentation failure
                    assert results.cleanup_report is not None
                    assert results.demonstration_report is not None
                    assert results.success is False  # Overall failure due to documentation
                    
                    # Verify specific error is recorded
                    error_found = any("Documentation generation failed" in error 
                                    for error in results.workflow_progress.errors_encountered)
                    assert error_found
        
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])