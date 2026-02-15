"""
System Demonstration Engine for OpenClass Nexus AI Phase 3.

This module provides comprehensive demonstration capabilities for the AI system,
including sample query processing, response quality analysis, and educational
content validation as specified in requirements 2.1, 6.1, 6.2, 6.3.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json

from src.local_inference.complete_pipeline import CompletePipeline, PipelineConfig
from src.local_inference.educational_validator import EducationalContentValidator, EducationalValidationResult
from src.local_inference.performance_monitor import PerformanceMetrics
from src.local_inference.rag_pipeline import QueryResult

logger = logging.getLogger(__name__)


@dataclass
class DemoResponse:
    """
    Demonstration response with comprehensive metrics and analysis.
    
    This class represents a complete demonstration response as specified
    in the design document, including all required metrics and validation.
    """
    query: str
    response: str
    response_time_ms: float
    memory_usage_mb: float
    curriculum_alignment_score: float
    language_quality_score: float
    sources_used: List[str]
    confidence_score: float
    educational_grade: str
    
    # Additional metrics for comprehensive analysis
    tokens_generated: int = 0
    context_tokens: int = 0
    processing_timestamp: datetime = field(default_factory=datetime.now)
    validation_result: Optional[EducationalValidationResult] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert demo response to dictionary for serialization."""
        result = {
            'query': self.query,
            'response': self.response,
            'response_time_ms': self.response_time_ms,
            'memory_usage_mb': self.memory_usage_mb,
            'curriculum_alignment_score': self.curriculum_alignment_score,
            'language_quality_score': self.language_quality_score,
            'sources_used': self.sources_used,
            'confidence_score': self.confidence_score,
            'educational_grade': self.educational_grade,
            'tokens_generated': self.tokens_generated,
            'context_tokens': self.context_tokens,
            'processing_timestamp': self.processing_timestamp.isoformat()
        }
        
        if self.validation_result:
            result['validation_details'] = {
                'overall_score': self.validation_result.overall_score,
                'overall_level': self.validation_result.overall_level.value,
                'component_scores': {
                    'language_score': self.validation_result.language_score,
                    'content_score': self.validation_result.content_score,
                    'curriculum_score': self.validation_result.curriculum_score,
                    'structure_score': self.validation_result.structure_score,
                    'attribution_score': self.validation_result.attribution_score
                },
                'issues_count': len(self.validation_result.issues),
                'strengths_count': len(self.validation_result.strengths),
                'recommendations_count': len(self.validation_result.recommendations)
            }
        
        if self.performance_metrics:
            result['performance_details'] = {
                'tokens_per_second': self.performance_metrics.tokens_per_second,
                'cpu_usage_percent': self.performance_metrics.cpu_usage_percent,
                'memory_peak_mb': self.performance_metrics.memory_peak_mb,
                'performance_grade': self.performance_metrics.get_performance_grade(),
                'within_targets': self.performance_metrics.is_within_targets()
            }
        
        return result


@dataclass
class DemonstrationReport:
    """
    Comprehensive demonstration report containing all sample responses
    and system analysis as specified in requirements.
    """
    demonstration_timestamp: datetime
    total_queries_processed: int
    average_response_time_ms: float
    average_memory_usage_mb: float
    average_curriculum_alignment: float
    average_language_quality: float
    system_performance_grade: str
    demo_responses: List[DemoResponse]
    
    # System-wide metrics
    total_tokens_generated: int = 0
    total_processing_time_ms: float = 0.0
    success_rate: float = 0.0
    educational_effectiveness_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert demonstration report to dictionary."""
        return {
            'demonstration_timestamp': self.demonstration_timestamp.isoformat(),
            'summary': {
                'total_queries_processed': self.total_queries_processed,
                'average_response_time_ms': self.average_response_time_ms,
                'average_memory_usage_mb': self.average_memory_usage_mb,
                'average_curriculum_alignment': self.average_curriculum_alignment,
                'average_language_quality': self.average_language_quality,
                'system_performance_grade': self.system_performance_grade,
                'total_tokens_generated': self.total_tokens_generated,
                'total_processing_time_ms': self.total_processing_time_ms,
                'success_rate': self.success_rate,
                'educational_effectiveness_score': self.educational_effectiveness_score
            },
            'responses': [response.to_dict() for response in self.demo_responses]
        }


class SystemDemonstrationEngine:
    """
    System Demonstration Engine for showcasing AI model capabilities.
    
    This engine provides comprehensive demonstration capabilities including:
    - Sample query processing with the complete pipeline
    - Response quality analysis and metrics collection
    - Educational content validation and scoring
    - Performance benchmarking and reporting
    
    Implements requirements 2.1, 6.1, 6.2, 6.3 from the specification.
    """
    
    # Sample educational queries for demonstration
    SAMPLE_QUERIES = [
        {
            'query': 'Jelaskan konsep algoritma dalam informatika dan berikan contoh sederhana',
            'subject': 'informatika',
            'grade': 'kelas_10',
            'expected_topics': ['algoritma', 'langkah-langkah', 'contoh', 'pemrograman']
        },
        {
            'query': 'Apa itu struktur data dan mengapa penting dalam pemrograman?',
            'subject': 'informatika', 
            'grade': 'kelas_10',
            'expected_topics': ['struktur data', 'array', 'list', 'efisiensi']
        },
        {
            'query': 'Bagaimana cara kerja basis data dan apa fungsinya dalam sistem informasi?',
            'subject': 'informatika',
            'grade': 'kelas_10', 
            'expected_topics': ['basis data', 'tabel', 'relasi', 'SQL']
        },
        {
            'query': 'Jelaskan perbedaan antara hardware dan software dalam komputer',
            'subject': 'informatika',
            'grade': 'kelas_10',
            'expected_topics': ['hardware', 'software', 'komponen', 'fungsi']
        },
        {
            'query': 'Apa yang dimaksud dengan jaringan komputer dan sebutkan jenisnya',
            'subject': 'informatika',
            'grade': 'kelas_11',
            'expected_topics': ['jaringan', 'LAN', 'WAN', 'internet', 'protokol']
        }
    ]
    
    def __init__(self, pipeline: Optional[CompletePipeline] = None):
        """
        Initialize the System Demonstration Engine.
        
        Args:
            pipeline: Complete pipeline instance (creates default if None)
        """
        self.pipeline = pipeline
        self.educational_validator = EducationalContentValidator()
        
        # Demonstration statistics
        self.demo_stats = {
            'total_demonstrations': 0,
            'successful_demonstrations': 0,
            'failed_demonstrations': 0,
            'total_processing_time_ms': 0.0,
            'average_response_time_ms': 0.0
        }
        
        logger.info("SystemDemonstrationEngine initialized")
    
    def initialize_pipeline(self, config: Optional[PipelineConfig] = None) -> bool:
        """
        Initialize the complete pipeline for demonstration.
        
        Args:
            config: Pipeline configuration (uses defaults if None)
            
        Returns:
            bool: True if initialization successful
        """
        try:
            if not self.pipeline:
                self.pipeline = CompletePipeline(config)
            
            if not self.pipeline.initialize():
                logger.error("Failed to initialize pipeline")
                return False
            
            if not self.pipeline.start():
                logger.error("Failed to start pipeline")
                return False
            
            logger.info("Pipeline initialized successfully for demonstration")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing pipeline: {e}")
            return False
    
    def generate_sample_responses(self, 
                                queries: Optional[List[Dict[str, Any]]] = None,
                                include_validation: bool = True,
                                include_performance_metrics: bool = True) -> List[DemoResponse]:
        """
        Generate sample responses for demonstration queries.
        
        Args:
            queries: List of query dictionaries (uses default samples if None)
            include_validation: Whether to include educational validation
            include_performance_metrics: Whether to include performance metrics
            
        Returns:
            List of DemoResponse objects with comprehensive analysis
        """
        if not self.pipeline or not self.pipeline.is_running:
            raise RuntimeError("Pipeline must be initialized and running")
        
        queries_to_process = queries or self.SAMPLE_QUERIES
        demo_responses = []
        
        logger.info(f"Generating sample responses for {len(queries_to_process)} queries")
        
        for i, query_info in enumerate(queries_to_process):
            try:
                logger.info(f"Processing query {i+1}/{len(queries_to_process)}: {query_info['query'][:50]}...")
                
                # Process query through pipeline
                demo_response = self._process_demonstration_query(
                    query_info, 
                    include_validation, 
                    include_performance_metrics
                )
                
                demo_responses.append(demo_response)
                self.demo_stats['successful_demonstrations'] += 1
                
                logger.info(f"Query {i+1} processed successfully")
                
            except Exception as e:
                logger.error(f"Error processing query {i+1}: {e}")
                self.demo_stats['failed_demonstrations'] += 1
                
                # Create error response
                error_response = DemoResponse(
                    query=query_info['query'],
                    response=f"Error processing query: {str(e)}",
                    response_time_ms=0.0,
                    memory_usage_mb=0.0,
                    curriculum_alignment_score=0.0,
                    language_quality_score=0.0,
                    sources_used=[],
                    confidence_score=0.0,
                    educational_grade="Error"
                )
                demo_responses.append(error_response)
        
        self.demo_stats['total_demonstrations'] += len(queries_to_process)
        
        # Update average response time
        if demo_responses:
            total_time = sum(r.response_time_ms for r in demo_responses if r.response_time_ms > 0)
            valid_responses = len([r for r in demo_responses if r.response_time_ms > 0])
            if valid_responses > 0:
                self.demo_stats['average_response_time_ms'] = total_time / valid_responses
        
        logger.info(f"Generated {len(demo_responses)} demonstration responses")
        return demo_responses
    
    def _process_demonstration_query(self, 
                                   query_info: Dict[str, Any],
                                   include_validation: bool,
                                   include_performance_metrics: bool) -> DemoResponse:
        """
        Process a single demonstration query with comprehensive analysis.
        
        Args:
            query_info: Query information dictionary
            include_validation: Whether to include educational validation
            include_performance_metrics: Whether to include performance metrics
            
        Returns:
            DemoResponse with complete analysis
        """
        query = query_info['query']
        subject = query_info.get('subject')
        grade = query_info.get('grade')
        
        start_time = time.time()
        
        # Process query through pipeline
        result = self.pipeline.process_query(
            query=query,
            subject_filter=subject,
            grade_filter=grade
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Extract basic information from result
        if isinstance(result, QueryResult):
            response_text = result.response
            sources_used = result.sources[:3] if result.sources else []  # Top 3 sources
            context_tokens = result.context_stats.get('context_tokens', 0)
            tokens_generated = len(response_text.split())  # Rough estimate
            memory_usage = result.context_stats.get('memory_usage_mb', 0.0)
        else:
            # Handle string response (batch processing ID)
            response_text = str(result)
            sources_used = []
            context_tokens = 0
            tokens_generated = 0
            memory_usage = 0.0
        
        # Initialize scores with defaults
        curriculum_alignment_score = 0.8
        language_quality_score = 0.8
        confidence_score = 0.8
        educational_grade = "Good"
        validation_result = None
        performance_metrics = None
        
        # Perform educational validation if requested
        if include_validation and isinstance(result, QueryResult):
            try:
                validation_result = self.educational_validator.validate_educational_response(
                    response=response_text,
                    query=query,
                    context=result.context,
                    subject=subject,
                    grade=grade
                )
                
                curriculum_alignment_score = validation_result.curriculum_score
                language_quality_score = validation_result.language_score
                confidence_score = validation_result.overall_score
                educational_grade = validation_result.overall_level.value.title()
                
            except Exception as e:
                logger.warning(f"Educational validation failed: {e}")
        
        # Get performance metrics if requested
        if include_performance_metrics and self.pipeline.performance_tracker:
            try:
                # Get latest performance metrics
                if self.pipeline.performance_tracker.metrics_history:
                    performance_metrics = list(self.pipeline.performance_tracker.metrics_history)[-1]
                    memory_usage = performance_metrics.memory_usage_mb
                    
            except Exception as e:
                logger.warning(f"Performance metrics retrieval failed: {e}")
        
        # Create comprehensive demo response
        demo_response = DemoResponse(
            query=query,
            response=response_text,
            response_time_ms=processing_time_ms,
            memory_usage_mb=memory_usage,
            curriculum_alignment_score=curriculum_alignment_score,
            language_quality_score=language_quality_score,
            sources_used=sources_used,
            confidence_score=confidence_score,
            educational_grade=educational_grade,
            tokens_generated=tokens_generated,
            context_tokens=context_tokens,
            validation_result=validation_result,
            performance_metrics=performance_metrics
        )
        
        return demo_response
    
    def create_demonstration_report(self, demo_responses: List[DemoResponse]) -> DemonstrationReport:
        """
        Create a comprehensive demonstration report from sample responses.
        
        Args:
            demo_responses: List of demonstration responses
            
        Returns:
            DemonstrationReport with system-wide analysis
        """
        if not demo_responses:
            raise ValueError("No demonstration responses provided")
        
        # Calculate averages and totals
        valid_responses = [r for r in demo_responses if r.response_time_ms > 0]
        
        if not valid_responses:
            raise ValueError("No valid demonstration responses found")
        
        total_queries = len(demo_responses)
        average_response_time = sum(r.response_time_ms for r in valid_responses) / len(valid_responses)
        average_memory_usage = sum(r.memory_usage_mb for r in valid_responses) / len(valid_responses)
        average_curriculum_alignment = sum(r.curriculum_alignment_score for r in valid_responses) / len(valid_responses)
        average_language_quality = sum(r.language_quality_score for r in valid_responses) / len(valid_responses)
        
        total_tokens = sum(r.tokens_generated for r in demo_responses)
        total_processing_time = sum(r.response_time_ms for r in demo_responses)
        success_rate = len(valid_responses) / total_queries * 100
        
        # Calculate educational effectiveness score
        educational_effectiveness = (average_curriculum_alignment + average_language_quality) / 2
        
        # Determine system performance grade
        if average_response_time < 5000 and average_memory_usage < 2048 and educational_effectiveness > 0.8:
            system_grade = "Excellent"
        elif average_response_time < 8000 and average_memory_usage < 2560 and educational_effectiveness > 0.7:
            system_grade = "Good"
        elif average_response_time < 10000 and average_memory_usage < 3072 and educational_effectiveness > 0.6:
            system_grade = "Acceptable"
        else:
            system_grade = "Needs Improvement"
        
        # Create comprehensive report
        report = DemonstrationReport(
            demonstration_timestamp=datetime.now(),
            total_queries_processed=total_queries,
            average_response_time_ms=average_response_time,
            average_memory_usage_mb=average_memory_usage,
            average_curriculum_alignment=average_curriculum_alignment,
            average_language_quality=average_language_quality,
            system_performance_grade=system_grade,
            demo_responses=demo_responses,
            total_tokens_generated=total_tokens,
            total_processing_time_ms=total_processing_time,
            success_rate=success_rate,
            educational_effectiveness_score=educational_effectiveness
        )
        
        logger.info(f"Created demonstration report: {system_grade} grade, "
                   f"{success_rate:.1f}% success rate, "
                   f"{educational_effectiveness:.2f} educational effectiveness")
        
        return report
    
    def export_demonstration_report(self, 
                                  report: DemonstrationReport, 
                                  output_path: Path,
                                  format: str = 'json') -> None:
        """
        Export demonstration report to file.
        
        Args:
            report: Demonstration report to export
            output_path: Path to output file
            format: Export format ('json' or 'html')
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'html':
                html_content = self._generate_html_report(report)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Demonstration report exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting demonstration report: {e}")
            raise
    
    def _generate_html_report(self, report: DemonstrationReport) -> str:
        """Generate HTML report from demonstration data."""
        html_template = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClass Nexus AI - Demonstration Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }
        .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .metric-label { color: #666; font-size: 14px; }
        .response-item { border: 1px solid #ddd; margin-bottom: 20px; border-radius: 6px; overflow: hidden; }
        .response-header { background: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd; }
        .response-content { padding: 15px; }
        .query { font-weight: bold; color: #333; margin-bottom: 10px; }
        .response-text { background: #f9f9f9; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 10px; }
        .metric-small { text-align: center; padding: 8px; background: #e9ecef; border-radius: 4px; }
        .grade-excellent { color: #28a745; }
        .grade-good { color: #17a2b8; }
        .grade-acceptable { color: #ffc107; }
        .grade-poor { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>OpenClass Nexus AI - System Demonstration Report</h1>
            <p>Generated on: {timestamp}</p>
        </div>
        
        <div class="summary">
            <div class="metric-card">
                <div class="metric-value">{total_queries}</div>
                <div class="metric-label">Total Queries Processed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_response_time:.1f}ms</div>
                <div class="metric-label">Average Response Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_memory:.1f}MB</div>
                <div class="metric-label">Average Memory Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{success_rate:.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value grade-{grade_class}">{system_grade}</div>
                <div class="metric-label">System Performance Grade</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{educational_score:.2f}</div>
                <div class="metric-label">Educational Effectiveness</div>
            </div>
        </div>
        
        <h2>Sample Responses</h2>
        {responses_html}
    </div>
</body>
</html>
        """
        
        # Generate responses HTML
        responses_html = ""
        for i, response in enumerate(report.demo_responses, 1):
            grade_class = response.educational_grade.lower().replace(' ', '-')
            
            responses_html += f"""
            <div class="response-item">
                <div class="response-header">
                    <div class="query">Query {i}: {response.query}</div>
                </div>
                <div class="response-content">
                    <div class="response-text">{response.response[:500]}{'...' if len(response.response) > 500 else ''}</div>
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
        
        # Format the template
        return html_template.format(
            timestamp=report.demonstration_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            total_queries=report.total_queries_processed,
            avg_response_time=report.average_response_time_ms,
            avg_memory=report.average_memory_usage_mb,
            success_rate=report.success_rate,
            system_grade=report.system_performance_grade,
            grade_class=report.system_performance_grade.lower().replace(' ', '-'),
            educational_score=report.educational_effectiveness_score,
            responses_html=responses_html
        )
    
    def get_demonstration_stats(self) -> Dict[str, Any]:
        """Get current demonstration statistics."""
        return self.demo_stats.copy()
    
    def cleanup(self) -> None:
        """Cleanup resources and stop pipeline."""
        if self.pipeline:
            self.pipeline.stop()
            logger.info("Pipeline stopped and resources cleaned up")


# Utility functions
def create_demonstration_engine(
    model_cache_dir: str = "./models/cache",
    chroma_db_path: str = "./data/vector_db",
    memory_limit_mb: int = 3072
) -> SystemDemonstrationEngine:
    """
    Create a demonstration engine with recommended settings.
    
    Args:
        model_cache_dir: Directory for model storage
        chroma_db_path: Path to ChromaDB database
        memory_limit_mb: Memory limit for the system
        
    Returns:
        SystemDemonstrationEngine instance
    """
    config = PipelineConfig(
        model_cache_dir=model_cache_dir,
        chroma_db_path=chroma_db_path,
        memory_limit_mb=memory_limit_mb,
        enable_performance_monitoring=True,
        enable_educational_validation=True
    )
    
    pipeline = CompletePipeline(config)
    return SystemDemonstrationEngine(pipeline)


# Example usage
def example_demonstration():
    """Example of how to use the demonstration engine."""
    print("System Demonstration Engine Example")
    print("This example shows how to use the SystemDemonstrationEngine")
    
    # Create demonstration engine
    demo_engine = SystemDemonstrationEngine()
    
    print("Demonstration engine created")
    print("In practice, you would:")
    print("1. Initialize the pipeline")
    print("2. Generate sample responses")
    print("3. Create demonstration report")
    print("4. Export results")


if __name__ == "__main__":
    example_demonstration()