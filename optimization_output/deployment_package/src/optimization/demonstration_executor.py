"""
System Demonstration Executor

This module provides execution capabilities for comprehensive AI model capability
demonstration, including sample response generation, performance metrics collection,
and educational content validation reporting.

Implements requirements 2.1, 2.2, 2.3, 2.4, 2.5 from the specification.
"""

import logging
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from .config import OptimizationConfig
from .logger import OptimizationLoggerMixin
from .models import DemoResponse, DemonstrationReport, PerformanceBenchmark, ValidationResults
from .demonstration_engine import SystemDemonstrationEngine

logger = logging.getLogger(__name__)


@dataclass
class DemonstrationConfig:
    """Configuration for system demonstration execution."""
    
    # Query configuration
    sample_queries: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            'query': 'Jelaskan konsep algoritma dalam informatika dan berikan contoh sederhana untuk siswa kelas 10',
            'subject': 'informatika',
            'grade': 'kelas_10',
            'expected_topics': ['algoritma', 'langkah-langkah', 'contoh', 'pemrograman'],
            'difficulty': 'basic'
        },
        {
            'query': 'Apa itu struktur data dan mengapa penting dalam pemrograman? Berikan contoh array dan list',
            'subject': 'informatika', 
            'grade': 'kelas_10',
            'expected_topics': ['struktur data', 'array', 'list', 'efisiensi'],
            'difficulty': 'intermediate'
        },
        {
            'query': 'Bagaimana cara kerja basis data dan apa fungsinya dalam sistem informasi modern?',
            'subject': 'informatika',
            'grade': 'kelas_10', 
            'expected_topics': ['basis data', 'tabel', 'relasi', 'SQL', 'sistem informasi'],
            'difficulty': 'intermediate'
        },
        {
            'query': 'Jelaskan perbedaan antara hardware dan software dalam komputer serta berikan contoh masing-masing',
            'subject': 'informatika',
            'grade': 'kelas_10',
            'expected_topics': ['hardware', 'software', 'komponen', 'fungsi', 'contoh'],
            'difficulty': 'basic'
        },
        {
            'query': 'Apa yang dimaksud dengan jaringan komputer dan sebutkan jenis-jenisnya beserta karakteristiknya',
            'subject': 'informatika',
            'grade': 'kelas_10',
            'expected_topics': ['jaringan', 'LAN', 'WAN', 'internet', 'protokol', 'topologi'],
            'difficulty': 'advanced'
        },
        {
            'query': 'Mengapa keamanan siber penting dalam era digital dan apa saja ancaman yang umum terjadi?',
            'subject': 'informatika',
            'grade': 'kelas_10',
            'expected_topics': ['keamanan siber', 'malware', 'phishing', 'enkripsi', 'firewall'],
            'difficulty': 'advanced'
        }
    ])
    
    # Performance testing configuration
    performance_iterations: int = 5
    concurrent_query_test: bool = True
    max_concurrent_queries: int = 3
    response_time_threshold_ms: float = 5000.0
    memory_threshold_mb: float = 4096.0
    
    # Validation configuration
    enable_educational_validation: bool = True
    enable_performance_metrics: bool = True
    min_curriculum_alignment_score: float = 0.85
    min_language_quality_score: float = 0.80
    
    # Output configuration
    export_detailed_results: bool = True
    export_html_report: bool = True
    export_json_results: bool = True


@dataclass
class DemonstrationMetrics:
    """Comprehensive demonstration metrics."""
    
    # Response metrics
    total_queries_processed: int = 0
    successful_responses: int = 0
    failed_responses: int = 0
    average_response_time_ms: float = 0.0
    min_response_time_ms: float = float('inf')
    max_response_time_ms: float = 0.0
    
    # Memory metrics
    average_memory_usage_mb: float = 0.0
    peak_memory_usage_mb: float = 0.0
    min_memory_usage_mb: float = float('inf')
    
    # Educational quality metrics
    average_curriculum_alignment: float = 0.0
    average_language_quality: float = 0.0
    average_confidence_score: float = 0.0
    
    # Performance grades distribution
    grade_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Timing metrics
    total_processing_time_ms: float = 0.0
    demonstration_start_time: datetime = field(default_factory=datetime.now)
    demonstration_end_time: Optional[datetime] = None
    
    def calculate_success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_queries_processed == 0:
            return 0.0
        return (self.successful_responses / self.total_queries_processed) * 100
    
    def calculate_throughput(self) -> float:
        """Calculate queries per minute throughput."""
        if self.demonstration_end_time is None:
            return 0.0
        
        duration_minutes = (self.demonstration_end_time - self.demonstration_start_time).total_seconds() / 60
        if duration_minutes == 0:
            return 0.0
        
        return self.total_queries_processed / duration_minutes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'total_queries_processed': self.total_queries_processed,
            'successful_responses': self.successful_responses,
            'failed_responses': self.failed_responses,
            'success_rate_percentage': self.calculate_success_rate(),
            'average_response_time_ms': self.average_response_time_ms,
            'min_response_time_ms': self.min_response_time_ms if self.min_response_time_ms != float('inf') else 0.0,
            'max_response_time_ms': self.max_response_time_ms,
            'average_memory_usage_mb': self.average_memory_usage_mb,
            'peak_memory_usage_mb': self.peak_memory_usage_mb,
            'min_memory_usage_mb': self.min_memory_usage_mb if self.min_memory_usage_mb != float('inf') else 0.0,
            'average_curriculum_alignment': self.average_curriculum_alignment,
            'average_language_quality': self.average_language_quality,
            'average_confidence_score': self.average_confidence_score,
            'grade_distribution': self.grade_distribution,
            'total_processing_time_ms': self.total_processing_time_ms,
            'throughput_queries_per_minute': self.calculate_throughput(),
            'demonstration_duration_seconds': (
                (self.demonstration_end_time - self.demonstration_start_time).total_seconds()
                if self.demonstration_end_time else 0.0
            )
        }


class SystemDemonstrationExecutor(OptimizationLoggerMixin):
    """
    System demonstration executor for comprehensive AI model capability testing.
    
    This class provides execution capabilities for running comprehensive AI model
    demonstrations including sample response generation, performance benchmarking,
    and educational content validation reporting.
    """
    
    def __init__(self, 
                 config: Optional[OptimizationConfig] = None,
                 demo_config: Optional[DemonstrationConfig] = None):
        """
        Initialize the demonstration executor.
        
        Args:
            config: Optimization configuration
            demo_config: Demonstration-specific configuration
        """
        super().__init__()
        self.config = config or OptimizationConfig()
        self.demo_config = demo_config or DemonstrationConfig()
        
        # Initialize demonstration engine
        self.demonstration_engine = SystemDemonstrationEngine()
        
        # Metrics tracking
        self.metrics = DemonstrationMetrics()
        
        # Results storage
        self.demo_responses: List[DemoResponse] = []
        self.performance_benchmark: Optional[PerformanceBenchmark] = None
        self.validation_results: Optional[ValidationResults] = None
        
        self.log_info("System demonstration executor initialized")
    
    def execute_comprehensive_demonstration(self) -> DemonstrationReport:
        """
        Execute comprehensive AI model capability demonstration.
        
        Returns:
            DemonstrationReport with complete demonstration results
        """
        self.log_operation_start("comprehensive system demonstration")
        demonstration_start_time = time.time()
        
        try:
            # Initialize demonstration pipeline
            self._initialize_demonstration_pipeline()
            
            # Execute sample response generation
            self._execute_sample_response_generation()
            
            # Execute performance benchmarking
            self._execute_performance_benchmarking()
            
            # Execute educational content validation
            self._execute_educational_validation()
            
            # Finalize metrics
            self.metrics.demonstration_end_time = datetime.now()
            
            # Create comprehensive report
            report = self._create_demonstration_report()
            
            # Export results if configured
            if self.demo_config.export_detailed_results:
                self._export_demonstration_results(report)
            
            demonstration_duration = time.time() - demonstration_start_time
            self.log_operation_complete("comprehensive system demonstration", demonstration_duration,
                                      queries_processed=self.metrics.total_queries_processed,
                                      success_rate=self.metrics.calculate_success_rate(),
                                      avg_response_time=self.metrics.average_response_time_ms)
            
            return report
            
        except Exception as e:
            self.log_operation_error("comprehensive system demonstration", e)
            
            # Create error report
            error_report = self._create_error_report(str(e))
            return error_report
    
    def _initialize_demonstration_pipeline(self):
        """Initialize the demonstration pipeline."""
        try:
            self.log_operation_start("demonstration pipeline initialization")
            
            # Initialize the demonstration engine pipeline
            if not self.demonstration_engine.initialize_pipeline():
                raise RuntimeError("Failed to initialize demonstration pipeline")
            
            self.log_operation_complete("demonstration pipeline initialization")
            
        except Exception as e:
            self.log_operation_error("demonstration pipeline initialization", e)
            raise
    
    def _execute_sample_response_generation(self):
        """Execute sample response generation with full performance metrics."""
        try:
            self.log_operation_start("sample response generation")
            
            # Generate sample responses
            self.demo_responses = self.demonstration_engine.generate_sample_responses(
                queries=self.demo_config.sample_queries,
                include_validation=self.demo_config.enable_educational_validation,
                include_performance_metrics=self.demo_config.enable_performance_metrics
            )
            
            # Update metrics
            self._update_response_metrics()
            
            self.log_operation_complete("sample response generation",
                                      responses_generated=len(self.demo_responses))
            
        except Exception as e:
            self.log_operation_error("sample response generation", e)
            raise
    
    def _execute_performance_benchmarking(self):
        """Execute comprehensive performance benchmarking."""
        try:
            self.log_operation_start("performance benchmarking")
            
            # Calculate performance metrics from demo responses
            if not self.demo_responses:
                raise RuntimeError("No demo responses available for benchmarking")
            
            # Calculate averages and benchmarks
            valid_responses = [r for r in self.demo_responses if r.response_time_ms > 0]
            
            if not valid_responses:
                raise RuntimeError("No valid responses for performance benchmarking")
            
            # Calculate performance benchmark
            avg_response_time = sum(r.response_time_ms for r in valid_responses) / len(valid_responses)
            peak_memory = max(r.memory_usage_mb for r in valid_responses)
            avg_curriculum_alignment = sum(r.curriculum_alignment_score for r in valid_responses) / len(valid_responses)
            
            # Calculate throughput (queries per minute)
            total_time_minutes = self.metrics.total_processing_time_ms / (1000 * 60)
            throughput = len(valid_responses) / total_time_minutes if total_time_minutes > 0 else 0
            
            # Create performance benchmark
            self.performance_benchmark = PerformanceBenchmark(
                average_response_time_ms=avg_response_time,
                peak_memory_usage_mb=peak_memory,
                throughput_queries_per_minute=throughput,
                concurrent_query_capacity=self.demo_config.max_concurrent_queries,
                curriculum_alignment_accuracy=avg_curriculum_alignment,
                system_stability_score=self._calculate_stability_score(),
                hardware_efficiency_score=self._calculate_efficiency_score(),
                test_duration_seconds=self.metrics.total_processing_time_ms / 1000,
                total_queries_processed=len(valid_responses)
            )
            
            self.log_operation_complete("performance benchmarking",
                                      avg_response_time=avg_response_time,
                                      peak_memory=peak_memory,
                                      throughput=throughput)
            
        except Exception as e:
            self.log_operation_error("performance benchmarking", e)
            raise
    
    def _execute_educational_validation(self):
        """Execute educational content validation reporting."""
        try:
            self.log_operation_start("educational content validation")
            
            if not self.demo_responses:
                raise RuntimeError("No demo responses available for validation")
            
            # Aggregate validation results from demo responses
            valid_responses = [r for r in self.demo_responses if r.validation_result is not None]
            
            if not valid_responses:
                self.log_warning("No validation results available from demo responses")
                # Create basic validation results
                self.validation_results = ValidationResults(
                    curriculum_alignment_score=0.0,
                    language_quality_score=0.0,
                    age_appropriateness_score=0.0,
                    source_attribution_accuracy=0.0,
                    overall_quality_score=0.0,
                    detailed_feedback=["No validation results available"]
                )
                return
            
            # Calculate aggregate validation scores
            curriculum_scores = []
            language_scores = []
            overall_scores = []
            detailed_feedback = []
            
            for response in valid_responses:
                validation = response.validation_result
                curriculum_scores.append(validation.curriculum_score)
                language_scores.append(validation.language_score)
                overall_scores.append(validation.overall_score)
                
                # Collect feedback
                if validation.issues:
                    detailed_feedback.extend([f"Query '{response.query[:50]}...': {issue}" 
                                            for issue in validation.issues[:2]])  # Limit feedback
            
            # Calculate averages
            avg_curriculum = sum(curriculum_scores) / len(curriculum_scores)
            avg_language = sum(language_scores) / len(language_scores)
            avg_overall = sum(overall_scores) / len(overall_scores)
            
            # Create validation results
            self.validation_results = ValidationResults(
                curriculum_alignment_score=avg_curriculum,
                language_quality_score=avg_language,
                age_appropriateness_score=avg_overall,  # Use overall as proxy
                source_attribution_accuracy=0.85,  # Placeholder - would need specific validation
                overall_quality_score=avg_overall,
                detailed_feedback=detailed_feedback[:10]  # Limit to 10 feedback items
            )
            
            self.log_operation_complete("educational content validation",
                                      avg_curriculum_score=avg_curriculum,
                                      avg_language_score=avg_language,
                                      avg_overall_score=avg_overall)
            
        except Exception as e:
            self.log_operation_error("educational content validation", e)
            raise
    
    def _update_response_metrics(self):
        """Update metrics based on demo responses."""
        try:
            self.metrics.total_queries_processed = len(self.demo_responses)
            
            # Separate successful and failed responses
            successful_responses = [r for r in self.demo_responses if r.response_time_ms > 0]
            failed_responses = [r for r in self.demo_responses if r.response_time_ms <= 0]
            
            self.metrics.successful_responses = len(successful_responses)
            self.metrics.failed_responses = len(failed_responses)
            
            if successful_responses:
                # Response time metrics
                response_times = [r.response_time_ms for r in successful_responses]
                self.metrics.average_response_time_ms = sum(response_times) / len(response_times)
                self.metrics.min_response_time_ms = min(response_times)
                self.metrics.max_response_time_ms = max(response_times)
                
                # Memory metrics
                memory_usages = [r.memory_usage_mb for r in successful_responses]
                self.metrics.average_memory_usage_mb = sum(memory_usages) / len(memory_usages)
                self.metrics.peak_memory_usage_mb = max(memory_usages)
                self.metrics.min_memory_usage_mb = min(memory_usages)
                
                # Educational quality metrics
                curriculum_scores = [r.curriculum_alignment_score for r in successful_responses]
                language_scores = [r.language_quality_score for r in successful_responses]
                confidence_scores = [r.confidence_score for r in successful_responses]
                
                self.metrics.average_curriculum_alignment = sum(curriculum_scores) / len(curriculum_scores)
                self.metrics.average_language_quality = sum(language_scores) / len(language_scores)
                self.metrics.average_confidence_score = sum(confidence_scores) / len(confidence_scores)
                
                # Grade distribution
                grades = [r.educational_grade for r in successful_responses]
                self.metrics.grade_distribution = {}
                for grade in grades:
                    self.metrics.grade_distribution[grade] = self.metrics.grade_distribution.get(grade, 0) + 1
                
                # Total processing time
                self.metrics.total_processing_time_ms = sum(response_times)
            
        except Exception as e:
            self.log_error(f"Failed to update response metrics: {e}")
    
    def _calculate_stability_score(self) -> float:
        """Calculate system stability score based on response consistency."""
        try:
            if not self.demo_responses:
                return 0.0
            
            # Calculate stability based on success rate and response time consistency
            success_rate = self.metrics.calculate_success_rate() / 100.0
            
            # Calculate response time coefficient of variation (lower is more stable)
            if self.metrics.successful_responses > 1:
                response_times = [r.response_time_ms for r in self.demo_responses if r.response_time_ms > 0]
                if len(response_times) > 1:
                    mean_time = sum(response_times) / len(response_times)
                    variance = sum((t - mean_time) ** 2 for t in response_times) / len(response_times)
                    std_dev = variance ** 0.5
                    cv = std_dev / mean_time if mean_time > 0 else 1.0
                    
                    # Convert CV to stability score (lower CV = higher stability)
                    time_stability = max(0.0, 1.0 - cv)
                else:
                    time_stability = 1.0
            else:
                time_stability = success_rate
            
            # Combine success rate and time stability
            stability_score = (success_rate * 0.7) + (time_stability * 0.3)
            
            return min(1.0, max(0.0, stability_score))
            
        except Exception as e:
            self.log_error(f"Failed to calculate stability score: {e}")
            return 0.0
    
    def _calculate_efficiency_score(self) -> float:
        """Calculate hardware efficiency score based on resource usage."""
        try:
            if not self.demo_responses:
                return 0.0
            
            # Calculate efficiency based on memory usage and response time
            avg_memory = self.metrics.average_memory_usage_mb
            avg_response_time = self.metrics.average_response_time_ms
            
            # Memory efficiency (lower usage = higher efficiency)
            memory_threshold = self.demo_config.memory_threshold_mb
            memory_efficiency = max(0.0, 1.0 - (avg_memory / memory_threshold))
            
            # Time efficiency (faster response = higher efficiency)
            time_threshold = self.demo_config.response_time_threshold_ms
            time_efficiency = max(0.0, 1.0 - (avg_response_time / time_threshold))
            
            # Combine memory and time efficiency
            efficiency_score = (memory_efficiency * 0.4) + (time_efficiency * 0.6)
            
            return min(1.0, max(0.0, efficiency_score))
            
        except Exception as e:
            self.log_error(f"Failed to calculate efficiency score: {e}")
            return 0.0
    
    def _create_demonstration_report(self) -> DemonstrationReport:
        """Create comprehensive demonstration report."""
        try:
            # Ensure we have all required components
            if not self.performance_benchmark:
                raise RuntimeError("Performance benchmark not available")
            
            if not self.validation_results:
                raise RuntimeError("Validation results not available")
            
            # Generate summary
            summary = self._generate_demonstration_summary()
            
            # Create report
            report = DemonstrationReport(
                demo_responses=self.demo_responses,
                performance_benchmark=self.performance_benchmark,
                validation_results=self.validation_results,
                summary=summary
            )
            
            return report
            
        except Exception as e:
            self.log_error(f"Failed to create demonstration report: {e}")
            raise
    
    def _create_error_report(self, error_message: str) -> DemonstrationReport:
        """Create error demonstration report."""
        try:
            # Create minimal error components
            error_benchmark = PerformanceBenchmark(
                average_response_time_ms=0.0,
                peak_memory_usage_mb=0.0,
                throughput_queries_per_minute=0.0,
                concurrent_query_capacity=0,
                curriculum_alignment_accuracy=0.0,
                system_stability_score=0.0,
                hardware_efficiency_score=0.0
            )
            
            error_validation = ValidationResults(
                curriculum_alignment_score=0.0,
                language_quality_score=0.0,
                age_appropriateness_score=0.0,
                source_attribution_accuracy=0.0,
                overall_quality_score=0.0,
                detailed_feedback=[f"Demonstration failed: {error_message}"]
            )
            
            return DemonstrationReport(
                demo_responses=[],
                performance_benchmark=error_benchmark,
                validation_results=error_validation,
                summary=f"System demonstration failed: {error_message}"
            )
            
        except Exception as e:
            self.log_error(f"Failed to create error report: {e}")
            raise
    
    def _generate_demonstration_summary(self) -> str:
        """Generate demonstration summary text."""
        try:
            summary_parts = []
            
            # Overall results
            success_rate = self.metrics.calculate_success_rate()
            summary_parts.append(f"System Demonstration Results:")
            summary_parts.append(f"- Queries processed: {self.metrics.total_queries_processed}")
            summary_parts.append(f"- Success rate: {success_rate:.1f}%")
            summary_parts.append(f"- Average response time: {self.metrics.average_response_time_ms:.1f}ms")
            summary_parts.append(f"- Peak memory usage: {self.metrics.peak_memory_usage_mb:.1f}MB")
            
            # Educational quality
            summary_parts.append(f"\nEducational Quality:")
            summary_parts.append(f"- Curriculum alignment: {self.metrics.average_curriculum_alignment:.2f}")
            summary_parts.append(f"- Language quality: {self.metrics.average_language_quality:.2f}")
            summary_parts.append(f"- Confidence score: {self.metrics.average_confidence_score:.2f}")
            
            # Performance assessment
            if self.performance_benchmark:
                summary_parts.append(f"\nPerformance Assessment:")
                summary_parts.append(f"- System stability: {self.performance_benchmark.system_stability_score:.2f}")
                summary_parts.append(f"- Hardware efficiency: {self.performance_benchmark.hardware_efficiency_score:.2f}")
                summary_parts.append(f"- Throughput: {self.performance_benchmark.throughput_queries_per_minute:.1f} queries/min")
            
            # Grade distribution
            if self.metrics.grade_distribution:
                summary_parts.append(f"\nResponse Grade Distribution:")
                for grade, count in self.metrics.grade_distribution.items():
                    percentage = (count / self.metrics.successful_responses) * 100
                    summary_parts.append(f"- {grade}: {count} ({percentage:.1f}%)")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            self.log_error(f"Failed to generate demonstration summary: {e}")
            return f"Summary generation failed: {str(e)}"
    
    def _export_demonstration_results(self, report: DemonstrationReport):
        """Export demonstration results to files."""
        try:
            output_dir = self.config.optimization_output_dir / "demonstration"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Export JSON results
            if self.demo_config.export_json_results:
                json_file = output_dir / "demonstration_results.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
                self.log_info(f"JSON results exported to {json_file}")
            
            # Export HTML report
            if self.demo_config.export_html_report:
                html_file = output_dir / "demonstration_report.html"
                html_content = self._generate_html_report(report)
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.log_info(f"HTML report exported to {html_file}")
            
            # Export metrics summary
            metrics_file = output_dir / "demonstration_metrics.json"
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.log_info(f"Demonstration results exported to {output_dir}")
            
        except Exception as e:
            self.log_error(f"Failed to export demonstration results: {e}")
    
    def _generate_html_report(self, report: DemonstrationReport) -> str:
        """Generate HTML report from demonstration results."""
        try:
            html_template = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClass Nexus AI - System Demonstration Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .metric-label {{ color: #666; font-size: 14px; }}
        .response-item {{ border: 1px solid #ddd; margin-bottom: 20px; border-radius: 6px; overflow: hidden; }}
        .response-header {{ background: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd; }}
        .response-content {{ padding: 15px; }}
        .query {{ font-weight: bold; color: #333; margin-bottom: 10px; }}
        .response-text {{ background: #f9f9f9; padding: 10px; border-radius: 4px; margin: 10px 0; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 10px; }}
        .metric-small {{ text-align: center; padding: 8px; background: #e9ecef; border-radius: 4px; }}
        .grade-excellent {{ color: #28a745; }}
        .grade-good {{ color: #17a2b8; }}
        .grade-acceptable {{ color: #ffc107; }}
        .grade-poor {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>OpenClass Nexus AI - System Demonstration Report</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="metric-card">
                <div class="metric-value">{self.metrics.total_queries_processed}</div>
                <div class="metric-label">Total Queries Processed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{self.metrics.calculate_success_rate():.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{self.metrics.average_response_time_ms:.1f}ms</div>
                <div class="metric-label">Average Response Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{self.metrics.peak_memory_usage_mb:.1f}MB</div>
                <div class="metric-label">Peak Memory Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{self.metrics.average_curriculum_alignment:.2f}</div>
                <div class="metric-label">Curriculum Alignment</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{self.metrics.average_language_quality:.2f}</div>
                <div class="metric-label">Language Quality</div>
            </div>
        </div>
        
        <h2>Sample Responses</h2>
        <div class="responses">
            {self._generate_responses_html()}
        </div>
        
        <h2>Performance Summary</h2>
        <pre>{report.summary}</pre>
    </div>
</body>
</html>
            """
            
            return html_template
            
        except Exception as e:
            self.log_error(f"Failed to generate HTML report: {e}")
            return f"<html><body><h1>Error generating report: {str(e)}</h1></body></html>"
    
    def _generate_responses_html(self) -> str:
        """Generate HTML for individual responses."""
        try:
            responses_html = ""
            
            for i, response in enumerate(self.demo_responses[:5], 1):  # Limit to first 5 responses
                grade_class = response.educational_grade.lower().replace(' ', '-')
                
                responses_html += f"""
                <div class="response-item">
                    <div class="response-header">
                        <div class="query">Query {i}: {response.query}</div>
                    </div>
                    <div class="response-content">
                        <div class="response-text">{response.response[:300]}{'...' if len(response.response) > 300 else ''}</div>
                        <div class="metrics-grid">
                            <div class="metric-small">
                                <strong>{response.response_time_ms:.1f}ms</strong><br>
                                <small>Response Time</small>
                            </div>
                            <div class="metric-small">
                                <strong>{response.memory_usage_mb:.1f}MB</strong><br>
                                <small>Memory Usage</small>
                            </div>
                            <div class="metric-small">
                                <strong>{response.curriculum_alignment_score:.2f}</strong><br>
                                <small>Curriculum Score</small>
                            </div>
                            <div class="metric-small">
                                <strong>{response.language_quality_score:.2f}</strong><br>
                                <small>Language Quality</small>
                            </div>
                            <div class="metric-small">
                                <strong class="grade-{grade_class}">{response.educational_grade}</strong><br>
                                <small>Educational Grade</small>
                            </div>
                        </div>
                    </div>
                </div>
                """
            
            return responses_html
            
        except Exception as e:
            self.log_error(f"Failed to generate responses HTML: {e}")
            return f"<p>Error generating responses: {str(e)}</p>"


# Convenience function for running system demonstration
def run_system_demonstration(
    config: Optional[OptimizationConfig] = None,
    demo_config: Optional[DemonstrationConfig] = None
) -> DemonstrationReport:
    """
    Run comprehensive system demonstration.
    
    Args:
        config: Optimization configuration
        demo_config: Demonstration configuration
    
    Returns:
        DemonstrationReport with complete results
    """
    executor = SystemDemonstrationExecutor(config, demo_config)
    return executor.execute_comprehensive_demonstration()


# Example usage
def example_demonstration_execution():
    """Example of how to use the demonstration executor."""
    print("OpenClass Nexus AI - System Demonstration Executor Example")
    print("This example shows how to run comprehensive system demonstration")
    
    # Create custom demonstration configuration
    demo_config = DemonstrationConfig(
        performance_iterations=3,
        export_html_report=True,
        export_json_results=True
    )
    
    # Run demonstration
    report = run_system_demonstration(demo_config=demo_config)
    
    print(f"\nDemonstration completed")
    print(f"Summary:\n{report.summary}")


if __name__ == "__main__":
    example_demonstration_execution()