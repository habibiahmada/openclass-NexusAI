"""
Integration Tests for Demonstration Executor

This module provides integration tests for the demonstration executor,
testing end-to-end demonstration execution and reporting functionality.

Tests requirement 2.5 from the specification.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.optimization.demonstration_executor import (
    SystemDemonstrationExecutor, 
    DemonstrationConfig,
    DemonstrationMetrics,
    run_system_demonstration
)
from src.optimization.config import OptimizationConfig
from src.optimization.models import DemoResponse, ValidationResults


class TestDemonstrationExecutorIntegration:
    """Integration tests for the demonstration executor."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def test_config(self, temp_output_dir):
        """Create test configuration."""
        config = OptimizationConfig()
        config.optimization_output_dir = temp_output_dir
        return config
    
    @pytest.fixture
    def test_demo_config(self):
        """Create test demonstration configuration."""
        demo_config = DemonstrationConfig()
        demo_config.sample_queries = [
            {
                'query': 'Jelaskan konsep algoritma dalam informatika',
                'subject': 'informatika',
                'grade': 'kelas_10',
                'expected_topics': ['algoritma', 'langkah-langkah'],
                'difficulty': 'basic'
            },
            {
                'query': 'Apa itu struktur data dan mengapa penting?',
                'subject': 'informatika',
                'grade': 'kelas_10',
                'expected_topics': ['struktur data', 'array', 'list'],
                'difficulty': 'intermediate'
            }
        ]
        demo_config.export_detailed_results = True
        demo_config.export_json_results = True
        demo_config.export_html_report = True
        return demo_config
    
    def test_complete_demonstration_execution(self, test_config, test_demo_config):
        """Test complete demonstration execution with mocked AI components."""
        # Mock the SystemDemonstrationEngine to avoid actual AI model loading
        with patch('src.optimization.demonstration_executor.SystemDemonstrationEngine') as mock_engine_class:
            # Setup mock engine
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_engine.initialize_pipeline.return_value = True
            
            # Create mock demo responses
            mock_responses = [
                DemoResponse(
                    query="Jelaskan konsep algoritma dalam informatika",
                    response="Algoritma adalah urutan langkah-langkah logis yang sistematis untuk menyelesaikan suatu masalah. Dalam informatika, algoritma merupakan fondasi dari pemrograman dan komputasi.",
                    response_time_ms=1500.0,
                    memory_usage_mb=512.0,
                    curriculum_alignment_score=0.90,
                    language_quality_score=0.85,
                    sources_used=["BSE_Informatika_Kelas_X.pdf"],
                    confidence_score=0.88,
                    educational_grade="Excellent"
                ),
                DemoResponse(
                    query="Apa itu struktur data dan mengapa penting?",
                    response="Struktur data adalah cara mengorganisir dan menyimpan data dalam komputer sehingga dapat digunakan secara efisien. Struktur data penting karena mempengaruhi efisiensi algoritma.",
                    response_time_ms=1800.0,
                    memory_usage_mb=480.0,
                    curriculum_alignment_score=0.87,
                    language_quality_score=0.82,
                    sources_used=["BSE_Informatika_Kelas_X.pdf", "Modul_Struktur_Data.pdf"],
                    confidence_score=0.85,
                    educational_grade="Good"
                )
            ]
            
            mock_engine.generate_sample_responses.return_value = mock_responses
            
            # Create mock demonstration report
            from src.optimization.models import PerformanceBenchmark, DemonstrationReport
            
            mock_benchmark = PerformanceBenchmark(
                average_response_time_ms=1650.0,
                peak_memory_usage_mb=512.0,
                throughput_queries_per_minute=36.0,
                concurrent_query_capacity=3,
                curriculum_alignment_accuracy=0.885,
                system_stability_score=0.95,
                hardware_efficiency_score=0.88
            )
            
            mock_validation = ValidationResults(
                curriculum_alignment_score=0.885,
                language_quality_score=0.835,
                age_appropriateness_score=0.86,
                source_attribution_accuracy=0.92,
                overall_quality_score=0.87
            )
            
            mock_demo_report = DemonstrationReport(
                demo_responses=mock_responses,
                performance_benchmark=mock_benchmark,
                validation_results=mock_validation,
                summary="Demonstration completed successfully with high educational quality scores"
            )
            
            mock_engine.create_demonstration_report.return_value = mock_demo_report
            
            # Create and execute demonstration executor
            executor = SystemDemonstrationExecutor(test_config, test_demo_config)
            
            # Replace the demonstration engine with our mock
            executor.demonstration_engine = mock_engine
            
            # Execute demonstration
            report = executor.execute_comprehensive_demonstration()
            
            # Verify results
            assert report is not None
            assert len(report.demo_responses) == 2
            assert report.performance_benchmark.average_response_time_ms == 1650.0
            assert report.validation_results.curriculum_alignment_score == 0.885
            assert "successfully" in report.summary.lower()
            
            # Verify metrics were updated
            assert executor.metrics.total_queries_processed == 2
            assert executor.metrics.successful_responses == 2
            assert executor.metrics.failed_responses == 0
            assert executor.metrics.calculate_success_rate() == 100.0
            
            # Verify output files were created
            output_dir = test_config.optimization_output_dir / "demonstration"
            if output_dir.exists():
                # Check for JSON results
                json_file = output_dir / "demonstration_results.json"
                if json_file.exists():
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        assert 'demo_responses' in json_data
                        assert 'performance_benchmark' in json_data
                        assert 'validation_results' in json_data
                
                # Check for HTML report
                html_file = output_dir / "demonstration_report.html"
                if html_file.exists():
                    html_content = html_file.read_text(encoding='utf-8')
                    assert "OpenClass Nexus AI" in html_content
                    assert "System Demonstration Report" in html_content
    
    def test_demonstration_metrics_calculation(self, test_config, test_demo_config):
        """Test demonstration metrics calculation and aggregation."""
        # Create test metrics
        metrics = DemonstrationMetrics()
        
        # Simulate processing queries
        metrics.total_queries_processed = 5
        metrics.successful_responses = 4
        metrics.failed_responses = 1
        
        # Set timing metrics
        metrics.average_response_time_ms = 1500.0
        metrics.min_response_time_ms = 1200.0
        metrics.max_response_time_ms = 2000.0
        
        # Set memory metrics
        metrics.average_memory_usage_mb = 400.0
        metrics.peak_memory_usage_mb = 600.0
        metrics.min_memory_usage_mb = 300.0
        
        # Set educational quality metrics
        metrics.average_curriculum_alignment = 0.85
        metrics.average_language_quality = 0.80
        metrics.average_confidence_score = 0.82
        
        # Set grade distribution
        metrics.grade_distribution = {
            "Excellent": 2,
            "Good": 2,
            "Acceptable": 0,
            "Poor": 0
        }
        
        # Test calculations
        assert metrics.calculate_success_rate() == 80.0  # 4/5 * 100
        
        # Test serialization
        metrics_dict = metrics.to_dict()
        assert metrics_dict['total_queries_processed'] == 5
        assert metrics_dict['success_rate_percentage'] == 80.0
        assert metrics_dict['average_response_time_ms'] == 1500.0
        assert metrics_dict['grade_distribution']['Excellent'] == 2
    
    def test_demonstration_error_handling(self, test_config, test_demo_config):
        """Test demonstration executor error handling."""
        # Mock the SystemDemonstrationEngine to raise an error
        with patch('src.optimization.demonstration_executor.SystemDemonstrationEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_engine.initialize_pipeline.side_effect = RuntimeError("Pipeline initialization failed")
            
            # Create demonstration executor
            executor = SystemDemonstrationExecutor(test_config, test_demo_config)
            executor.demonstration_engine = mock_engine
            
            # Execute demonstration (should handle error gracefully)
            report = executor.execute_comprehensive_demonstration()
            
            # Verify error report was created
            assert report is not None
            assert "failed" in report.summary.lower()
            assert len(report.demo_responses) == 0
            assert report.performance_benchmark.average_response_time_ms == 0.0
            assert "Pipeline initialization failed" in report.validation_results.detailed_feedback[0]
    
    def test_demonstration_with_partial_failures(self, test_config, test_demo_config):
        """Test demonstration handling with some successful and some failed responses."""
        with patch('src.optimization.demonstration_executor.SystemDemonstrationEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_engine.initialize_pipeline.return_value = True
            
            # Create mixed success/failure responses
            mock_responses = [
                DemoResponse(
                    query="Successful query",
                    response="Successful response",
                    response_time_ms=1500.0,
                    memory_usage_mb=400.0,
                    curriculum_alignment_score=0.85,
                    language_quality_score=0.80,
                    sources_used=["source1.pdf"],
                    confidence_score=0.82,
                    educational_grade="Good"
                ),
                DemoResponse(
                    query="Failed query",
                    response="Error processing query",
                    response_time_ms=0.0,  # Indicates failure
                    memory_usage_mb=0.0,
                    curriculum_alignment_score=0.0,
                    language_quality_score=0.0,
                    sources_used=[],
                    confidence_score=0.0,
                    educational_grade="Error"
                )
            ]
            
            mock_engine.generate_sample_responses.return_value = mock_responses
            
            # Create demonstration executor
            executor = SystemDemonstrationExecutor(test_config, test_demo_config)
            executor.demonstration_engine = mock_engine
            
            # Mock the performance benchmarking to handle partial failures
            with patch.object(executor, '_execute_performance_benchmarking') as mock_benchmark:
                from src.optimization.models import PerformanceBenchmark
                mock_benchmark.return_value = None
                executor.performance_benchmark = PerformanceBenchmark(
                    average_response_time_ms=1500.0,  # Only from successful response
                    peak_memory_usage_mb=400.0,
                    throughput_queries_per_minute=30.0,
                    concurrent_query_capacity=2,
                    curriculum_alignment_accuracy=0.85,
                    system_stability_score=0.50,  # Lower due to failures
                    hardware_efficiency_score=0.75
                )
                
                with patch.object(executor, '_execute_educational_validation') as mock_validation:
                    mock_validation.return_value = None
                    executor.validation_results = ValidationResults(
                        curriculum_alignment_score=0.85,
                        language_quality_score=0.80,
                        age_appropriateness_score=0.82,
                        source_attribution_accuracy=0.90,
                        overall_quality_score=0.84
                    )
                    
                    # Execute demonstration
                    report = executor.execute_comprehensive_demonstration()
                    
                    # Verify partial success handling
                    assert report is not None
                    assert len(report.demo_responses) == 2
                    
                    # Verify metrics reflect partial success
                    assert executor.metrics.total_queries_processed == 2
                    assert executor.metrics.successful_responses == 1
                    assert executor.metrics.failed_responses == 1
                    assert executor.metrics.calculate_success_rate() == 50.0
    
    def test_demonstration_export_functionality(self, test_config, test_demo_config):
        """Test demonstration result export functionality."""
        with patch('src.optimization.demonstration_executor.SystemDemonstrationEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_engine.initialize_pipeline.return_value = True
            
            # Create mock response
            mock_response = DemoResponse(
                query="Test export query",
                response="Test export response",
                response_time_ms=1000.0,
                memory_usage_mb=300.0,
                curriculum_alignment_score=0.88,
                language_quality_score=0.83,
                sources_used=["test_source.pdf"],
                confidence_score=0.85,
                educational_grade="Good"
            )
            
            mock_engine.generate_sample_responses.return_value = [mock_response]
            
            # Create mock report
            from src.optimization.models import PerformanceBenchmark, DemonstrationReport
            
            mock_benchmark = PerformanceBenchmark(
                average_response_time_ms=1000.0,
                peak_memory_usage_mb=300.0,
                throughput_queries_per_minute=60.0,
                concurrent_query_capacity=3,
                curriculum_alignment_accuracy=0.88,
                system_stability_score=0.95,
                hardware_efficiency_score=0.90
            )
            
            mock_validation = ValidationResults(
                curriculum_alignment_score=0.88,
                language_quality_score=0.83,
                age_appropriateness_score=0.85,
                source_attribution_accuracy=0.90,
                overall_quality_score=0.86
            )
            
            mock_demo_report = DemonstrationReport(
                demo_responses=[mock_response],
                performance_benchmark=mock_benchmark,
                validation_results=mock_validation,
                summary="Export test demonstration"
            )
            
            mock_engine.create_demonstration_report.return_value = mock_demo_report
            
            # Create executor with export enabled
            test_demo_config.export_detailed_results = True
            test_demo_config.export_json_results = True
            test_demo_config.export_html_report = True
            
            executor = SystemDemonstrationExecutor(test_config, test_demo_config)
            executor.demonstration_engine = mock_engine
            
            # Execute demonstration
            report = executor.execute_comprehensive_demonstration()
            
            # Verify export files were created
            output_dir = test_config.optimization_output_dir / "demonstration"
            
            # Check JSON export
            json_file = output_dir / "demonstration_results.json"
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    assert 'demo_responses' in json_data
                    assert len(json_data['demo_responses']) == 1
                    assert json_data['demo_responses'][0]['query'] == "Test export query"
            
            # Check HTML export
            html_file = output_dir / "demonstration_report.html"
            if html_file.exists():
                html_content = html_file.read_text(encoding='utf-8')
                assert "Test export query" in html_content
                assert "Test export response" in html_content
            
            # Check metrics export
            metrics_file = output_dir / "demonstration_metrics.json"
            if metrics_file.exists():
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    metrics_data = json.load(f)
                    assert 'total_queries_processed' in metrics_data
                    assert metrics_data['total_queries_processed'] == 1
    
    def test_run_system_demonstration_convenience_function(self, test_config, test_demo_config):
        """Test the convenience function for running system demonstration."""
        with patch('src.optimization.demonstration_executor.SystemDemonstrationExecutor') as mock_executor_class:
            # Setup mock executor
            mock_executor = Mock()
            mock_executor_class.return_value = mock_executor
            
            # Create mock report
            from src.optimization.models import PerformanceBenchmark, DemonstrationReport, ValidationResults
            
            mock_benchmark = PerformanceBenchmark(
                average_response_time_ms=1200.0,
                peak_memory_usage_mb=350.0,
                throughput_queries_per_minute=50.0,
                concurrent_query_capacity=2,
                curriculum_alignment_accuracy=0.86,
                system_stability_score=0.92,
                hardware_efficiency_score=0.88
            )
            
            mock_validation = ValidationResults(
                curriculum_alignment_score=0.86,
                language_quality_score=0.81,
                age_appropriateness_score=0.84,
                source_attribution_accuracy=0.89,
                overall_quality_score=0.85
            )
            
            mock_report = DemonstrationReport(
                demo_responses=[],
                performance_benchmark=mock_benchmark,
                validation_results=mock_validation,
                summary="Convenience function test"
            )
            
            mock_executor.execute_comprehensive_demonstration.return_value = mock_report
            
            # Run demonstration using convenience function
            result = run_system_demonstration(test_config, test_demo_config)
            
            # Verify convenience function worked
            assert result is not None
            assert result.summary == "Convenience function test"
            assert mock_executor_class.called
            assert mock_executor.execute_comprehensive_demonstration.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])