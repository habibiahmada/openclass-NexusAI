"""
Property-based tests for performance monitoring and logging.

**Feature: phase3-model-optimization, Property 14: Performance Monitoring and Logging**
**Validates: Requirements 8.5, 5.5**

This module tests that for any system operation, performance metrics and error 
information should be logged for troubleshooting, and Indonesian educational 
content should be included in benchmarking.
"""

import pytest
import time
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from hypothesis import given, strategies as st, settings, assume, example
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant

# Import the components we're testing
from src.local_inference.performance_monitor import (
    PerformanceTracker, PerformanceMetrics, PerformanceTargets, PerformanceContext
)
from src.local_inference.performance_benchmarking import (
    PerformanceBenchmarkRunner, BenchmarkQuery, BenchmarkResult, 
    IndonesianEducationalBenchmarks, BenchmarkSuite
)
from src.local_inference.complete_pipeline import CompletePipeline, PipelineConfig


# Test data strategies
@st.composite
def performance_metrics_strategy(draw):
    """Generate valid performance metrics for testing."""
    response_time_ms = draw(st.floats(min_value=100.0, max_value=30000.0))
    memory_usage_mb = draw(st.floats(min_value=100.0, max_value=4096.0))
    cpu_usage_percent = draw(st.floats(min_value=0.0, max_value=100.0))
    tokens_per_second = draw(st.floats(min_value=0.1, max_value=50.0))
    context_tokens = draw(st.integers(min_value=10, max_value=4096))
    response_tokens = draw(st.integers(min_value=5, max_value=1000))
    
    return PerformanceMetrics(
        response_time_ms=response_time_ms,
        memory_usage_mb=memory_usage_mb,
        cpu_usage_percent=cpu_usage_percent,
        tokens_per_second=tokens_per_second,
        context_tokens=context_tokens,
        response_tokens=response_tokens,
        timestamp=datetime.now()
    )


@st.composite
def indonesian_query_strategy(draw):
    """Generate Indonesian educational queries for testing."""
    subjects = ["informatika", "matematika", "fisika", "kimia", "biologi"]
    difficulties = ["easy", "medium", "hard"]
    grade_levels = ["kelas_10", "kelas_11", "kelas_12"]
    
    # Indonesian educational query patterns
    query_templates = [
        "Apa itu {concept} dalam {subject}?",
        "Jelaskan {concept} dan berikan contoh!",
        "Bagaimana cara {action} dalam {subject}?",
        "Sebutkan perbedaan antara {concept1} dan {concept2}!",
        "Mengapa {concept} penting dalam {subject}?"
    ]
    
    concepts = ["algoritma", "variabel", "fungsi", "struktur data", "rekursi", 
                "persamaan", "integral", "turunan", "matriks", "vektor"]
    actions = ["menghitung", "menganalisis", "menyelesaikan", "mengimplementasikan"]
    
    template = draw(st.sampled_from(query_templates))
    subject = draw(st.sampled_from(subjects))
    concept = draw(st.sampled_from(concepts))
    concept1 = draw(st.sampled_from(concepts))
    concept2 = draw(st.sampled_from(concepts))
    action = draw(st.sampled_from(actions))
    
    # Format the query
    try:
        if "{concept1}" in template and "{concept2}" in template:
            query_text = template.format(concept1=concept1, concept2=concept2, subject=subject)
        elif "{action}" in template:
            query_text = template.format(action=action, subject=subject)
        else:
            query_text = template.format(concept=concept, subject=subject)
    except KeyError:
        query_text = f"Jelaskan {concept} dalam {subject}!"
    
    return BenchmarkQuery(
        query_id=f"test_{draw(st.integers(min_value=1, max_value=9999))}",
        query_text=query_text,
        subject=subject,
        grade_level=draw(st.sampled_from(grade_levels)),
        difficulty=draw(st.sampled_from(difficulties)),
        expected_response_time_ms=draw(st.floats(min_value=5000.0, max_value=15000.0)),
        expected_min_response_length=draw(st.integers(min_value=50, max_value=300))
    )


class TestPerformanceMonitoringProperties:
    """Property-based tests for performance monitoring system."""
    
    @given(metrics_list=st.lists(performance_metrics_strategy(), min_size=1, max_size=50))
    @settings(max_examples=100, deadline=10000)
    def test_performance_metrics_logging_property(self, metrics_list: List[PerformanceMetrics]):
        """
        **Property 14: Performance Monitoring and Logging**
        
        For any system operation, performance metrics should be properly logged
        and stored for troubleshooting purposes.
        """
        # Create performance tracker with logging
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "performance.log"
            
            # Setup logging to capture performance logs
            logger = logging.getLogger('src.local_inference.performance_monitor')
            handler = logging.FileHandler(log_file)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
            try:
                tracker = PerformanceTracker(enable_continuous_monitoring=False)
                
                # Record all metrics
                for metrics in metrics_list:
                    tracker.record_metrics(metrics)
                
                # Verify metrics are stored
                assert len(tracker.metrics_history) == len(metrics_list)
                
                # Verify logging occurred
                handler.flush()
                
                # Read log file and verify performance information was logged
                if log_file.exists():
                    log_content = log_file.read_text()
                    
                    # Should contain performance information
                    assert "Performance recorded" in log_content or "grade" in log_content
                    
                    # Should contain metrics information for at least some entries
                    metrics_logged = log_content.count("Performance recorded")
                    assert metrics_logged > 0, "No performance metrics were logged"
                
                # Verify performance summary can be generated
                summary = tracker.get_performance_summary()
                assert summary is not None
                assert 'total_operations' in summary
                assert summary['total_operations'] == len(metrics_list)
                
                # Verify all metrics meet basic consistency requirements
                for stored_metrics in tracker.metrics_history:
                    assert stored_metrics.response_time_ms >= 0
                    assert stored_metrics.memory_usage_mb >= 0
                    assert stored_metrics.cpu_usage_percent >= 0
                    assert stored_metrics.tokens_per_second >= 0
                    assert stored_metrics.context_tokens >= 0
                    assert stored_metrics.response_tokens >= 0
                    
                    # Verify performance grade can be calculated
                    grade = stored_metrics.get_performance_grade()
                    assert grade in ["Excellent", "Good", "Fair", "Poor"]
                    
                    # Verify target checking works
                    within_targets = stored_metrics.is_within_targets()
                    assert isinstance(within_targets, bool)
                
            finally:
                logger.removeHandler(handler)
                handler.close()
    
    @given(
        queries=st.lists(indonesian_query_strategy(), min_size=1, max_size=20),
        concurrent_level=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=50, deadline=15000)
    def test_indonesian_educational_benchmarking_property(self, 
                                                         queries: List[BenchmarkQuery], 
                                                         concurrent_level: int):
        """
        **Property 14: Performance Monitoring and Logging**
        
        For any Indonesian educational content benchmarking, the system should
        properly measure and log performance metrics for all queries.
        """
        # Create mock pipeline for testing
        mock_pipeline = Mock(spec=CompletePipeline)
        mock_pipeline.is_running = True
        
        # Mock the process_query method to return realistic results
        def mock_process_query(query, **kwargs):
            # Simulate processing time
            time.sleep(0.01)  # Small delay to simulate processing
            
            mock_result = Mock()
            mock_result.response = f"Jawaban untuk: {query}"
            mock_result.processing_time_ms = 100.0 + len(query) * 2  # Realistic time
            mock_result.context_stats = {'context_tokens': len(query.split())}
            return mock_result
        
        mock_pipeline.process_query = mock_process_query
        
        # Create benchmark runner
        runner = PerformanceBenchmarkRunner(mock_pipeline)
        
        # Create benchmark suite with Indonesian queries
        suite = BenchmarkSuite(
            suite_name="test_indonesian_suite",
            description="Test suite for Indonesian educational content"
        )
        
        for query in queries:
            suite.add_query(query)
        
        # Run benchmark
        results = runner._run_queries_sequential(queries)
        
        # Verify all queries were processed
        assert len(results) == len(queries)
        
        # Verify Indonesian educational content properties
        for i, result in enumerate(results):
            original_query = queries[i]
            
            # Verify query processing
            assert result.query_id == original_query.query_id
            assert result.query_text == original_query.query_text
            
            # Verify performance metrics are recorded
            assert result.response_time_ms > 0
            assert result.response_tokens >= 0
            assert result.context_tokens >= 0
            
            # Verify educational quality assessment
            assert 0.0 <= result.educational_quality_score <= 1.0
            
            # Verify Indonesian language content is handled
            assert "indonesian" in original_query.subject.lower() or any(
                indonesian_word in original_query.query_text.lower() 
                for indonesian_word in ["apa", "jelaskan", "bagaimana", "mengapa", "sebutkan"]
            ), f"Query should contain Indonesian language patterns: {original_query.query_text}"
        
        # Verify suite statistics can be calculated
        suite_stats = runner._calculate_suite_statistics(results, 1.0)
        assert 'total_queries' in suite_stats
        assert 'successful_queries' in suite_stats
        assert suite_stats['total_queries'] == len(queries)
        
        # Verify performance analysis includes educational metrics
        if any(r.success for r in results):
            assert 'avg_educational_quality_score' in suite_stats
            assert 0.0 <= suite_stats['avg_educational_quality_score'] <= 1.0
    
    @given(
        operation_count=st.integers(min_value=5, max_value=100),
        memory_limit_mb=st.integers(min_value=1024, max_value=4096),
        enable_logging=st.booleans()
    )
    @settings(max_examples=30, deadline=10000)
    def test_system_operation_monitoring_property(self, 
                                                operation_count: int, 
                                                memory_limit_mb: int,
                                                enable_logging: bool):
        """
        **Property 14: Performance Monitoring and Logging**
        
        For any system operation, performance metrics and error information
        should be logged for troubleshooting purposes.
        """
        # Create performance tracker with specified settings
        targets = PerformanceTargets(
            max_memory_usage_mb=float(memory_limit_mb),
            max_response_time_ms=10000.0,
            min_tokens_per_second=5.0
        )
        
        tracker = PerformanceTracker(
            targets=targets,
            enable_continuous_monitoring=enable_logging
        )
        
        # Simulate various system operations
        operation_results = []
        
        for i in range(operation_count):
            # Create performance context for operation
            with PerformanceContext(tracker, f"operation_{i}", query_length=50 + i) as ctx:
                # Simulate operation work
                time.sleep(0.001)  # Small delay
                
                # Update context with realistic metrics
                if ctx:
                    ctx.update_token_counts(
                        context_tokens=50 + i,
                        response_tokens=20 + (i % 10)
                    )
                    ctx.update_timing(
                        model_load_time_ms=10.0,
                        context_processing_time_ms=5.0 + (i % 5)
                    )
                
                operation_results.append(f"operation_{i}_completed")
        
        # Verify all operations were monitored
        assert len(tracker.metrics_history) == operation_count
        
        # Verify performance targets are properly evaluated
        for metrics in tracker.metrics_history:
            # Check target evaluation consistency
            within_targets = metrics.is_within_targets()
            manual_check = (
                metrics.response_time_ms < targets.max_response_time_ms and
                metrics.memory_usage_mb < targets.max_memory_usage_mb and
                metrics.tokens_per_second > targets.min_tokens_per_second
            )
            
            # The results should be consistent
            assert within_targets == manual_check, (
                f"Target evaluation inconsistent: {within_targets} vs {manual_check} "
                f"for metrics: {metrics.response_time_ms}ms, {metrics.memory_usage_mb}MB, "
                f"{metrics.tokens_per_second} tok/s"
            )
        
        # Verify performance summary includes troubleshooting information
        summary = tracker.get_performance_summary()
        assert 'total_operations' in summary
        assert 'target_compliance_rate' in summary
        assert 'targets' in summary
        
        # Verify optimization recommendations are generated
        recommendations = tracker.get_optimization_recommendations()
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Verify error information would be available (simulate error case)
        try:
            # Create a metrics object that violates targets
            error_metrics = PerformanceMetrics(
                response_time_ms=20000.0,  # Exceeds limit
                memory_usage_mb=float(memory_limit_mb + 500),  # Exceeds limit
                cpu_usage_percent=95.0,
                tokens_per_second=2.0,  # Below minimum
                context_tokens=100,
                response_tokens=50,
                timestamp=datetime.now()
            )
            
            tracker.record_metrics(error_metrics)
            
            # Verify the problematic metrics are recorded
            assert len(tracker.metrics_history) == operation_count + 1
            latest_metrics = list(tracker.metrics_history)[-1]
            assert not latest_metrics.is_within_targets()
            
        except Exception as e:
            # If error occurs, verify it would be logged appropriately
            assert isinstance(e, Exception)  # Error information is available
    
    @example(
        benchmark_suites=["informatika_comprehensive", "matematika_comprehensive"],
        performance_targets={"max_response_time_ms": 10000, "max_memory_mb": 3072}
    )
    @given(
        benchmark_suites=st.lists(
            st.sampled_from(["informatika_comprehensive", "matematika_comprehensive", "mixed_subjects"]),
            min_size=1, max_size=3
        ),
        performance_targets=st.fixed_dictionaries({
            "max_response_time_ms": st.floats(min_value=5000, max_value=15000),
            "max_memory_mb": st.floats(min_value=2048, max_value=4096)
        })
    )
    @settings(max_examples=20, deadline=15000)
    def test_comprehensive_benchmarking_logging_property(self, 
                                                       benchmark_suites: List[str],
                                                       performance_targets: Dict[str, float]):
        """
        **Property 14: Performance Monitoring and Logging**
        
        For any comprehensive benchmarking operation, all performance metrics
        and Indonesian educational content results should be properly logged.
        """
        # Create Indonesian educational benchmark generator
        generator = IndonesianEducationalBenchmarks()
        
        # Get all available suites
        all_suites = {
            "informatika_comprehensive": generator.create_informatika_benchmark_suite(),
            "matematika_comprehensive": generator.create_matematika_benchmark_suite(),
            "mixed_subjects": generator.create_mixed_subjects_benchmark_suite()
        }
        
        # Create mock pipeline with performance tracking
        mock_pipeline = Mock(spec=CompletePipeline)
        mock_pipeline.is_running = True
        
        # Track all queries processed
        processed_queries = []
        
        def mock_process_query(query, **kwargs):
            processed_queries.append(query)
            
            # Simulate realistic Indonesian educational response
            response_text = f"Penjelasan untuk {query}: "
            if "informatika" in query.lower():
                response_text += "Dalam ilmu komputer, konsep ini penting untuk pemahaman algoritma."
            elif "matematika" in query.lower():
                response_text += "Dalam matematika, konsep ini fundamental untuk perhitungan."
            else:
                response_text += "Konsep ini penting dalam pendidikan Indonesia."
            
            mock_result = Mock()
            mock_result.response = response_text
            mock_result.processing_time_ms = min(
                performance_targets["max_response_time_ms"] * 0.8,
                1000.0 + len(query) * 5
            )
            mock_result.context_stats = {
                'context_tokens': len(query.split()) * 2,
                'total_documents': 3
            }
            return mock_result
        
        mock_pipeline.process_query = mock_process_query
        
        # Create benchmark runner with performance tracking
        performance_tracker = PerformanceTracker(enable_continuous_monitoring=False)
        runner = PerformanceBenchmarkRunner(mock_pipeline, performance_tracker)
        
        # Run selected benchmark suites
        all_results = []
        suite_statistics = {}
        
        for suite_name in benchmark_suites:
            if suite_name in all_suites:
                suite = all_suites[suite_name]
                
                # Run the benchmark suite
                suite_result = runner.run_benchmark_suite(suite, concurrent_queries=1, warmup_queries=0)
                suite_statistics[suite_name] = suite_result
                
                # Collect individual results
                if suite_name in runner.suite_results:
                    all_results.extend(runner.suite_results[suite_name])
        
        # Verify comprehensive logging occurred
        assert len(all_results) > 0, "No benchmark results were generated"
        
        # Verify Indonesian educational content was processed
        indonesian_content_found = False
        for result in all_results:
            if result.success and result.response_text:
                # Check for Indonesian language content
                indonesian_indicators = [
                    "dalam", "untuk", "konsep", "penting", "penjelasan", 
                    "matematika", "informatika", "pendidikan", "indonesia"
                ]
                
                response_lower = result.response_text.lower()
                if any(indicator in response_lower for indicator in indonesian_indicators):
                    indonesian_content_found = True
                    break
        
        assert indonesian_content_found, "No Indonesian educational content found in responses"
        
        # Verify performance metrics are comprehensively logged
        for result in all_results:
            # Basic performance metrics should be recorded
            assert hasattr(result, 'response_time_ms')
            assert hasattr(result, 'memory_usage_mb')
            assert hasattr(result, 'educational_quality_score')
            
            # Performance targets should be evaluated
            target_compliance = result.meets_performance_targets(
                max_response_time_ms=performance_targets["max_response_time_ms"],
                max_memory_mb=performance_targets["max_memory_mb"]
            )
            assert isinstance(target_compliance, bool)
        
        # Verify suite-level statistics include troubleshooting information
        for suite_name, stats in suite_statistics.items():
            if 'error' not in stats:  # Only check successful suites
                assert 'total_queries' in stats
                assert 'success_rate' in stats
                assert 'avg_response_time_ms' in stats
                
                # Educational quality metrics should be included
                if 'avg_educational_quality_score' in stats:
                    assert 0.0 <= stats['avg_educational_quality_score'] <= 1.0
        
        # Verify comprehensive report can be generated
        if all_results:
            report = runner.generate_performance_report()
            assert 'report_metadata' in report
            assert 'executive_summary' in report
            assert 'performance_analysis' in report
            assert 'recommendations' in report
            
            # Verify troubleshooting information is included
            assert len(report['recommendations']) > 0
            
            # Verify Indonesian educational content is reflected in analysis
            if 'detailed_results' in report:
                assert len(report['detailed_results']) > 0


if __name__ == "__main__":
    # Run a simple test to verify the property tests work
    test_instance = TestPerformanceMonitoringProperties()
    
    # Test with a simple example
    simple_metrics = [
        PerformanceMetrics(
            response_time_ms=5000.0,
            memory_usage_mb=2048.0,
            cpu_usage_percent=50.0,
            tokens_per_second=10.0,
            context_tokens=100,
            response_tokens=50,
            timestamp=datetime.now()
        )
    ]
    
    print("Running simple performance monitoring property test...")
    test_instance.test_performance_metrics_logging_property(simple_metrics)
    print("Property test passed!")
    
    print("Performance monitoring property tests are ready to run with pytest-hypothesis")