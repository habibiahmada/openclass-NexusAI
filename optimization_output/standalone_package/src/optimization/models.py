"""
Data Models for Optimization Module

This module defines all data models used throughout the optimization process,
including cleanup reports, demo responses, benchmarks, and documentation packages.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CleanupReport:
    """Report generated after project cleanup operations."""
    files_removed: int
    directories_cleaned: int
    cache_cleared_mb: float
    space_freed_mb: float
    cleanup_duration_seconds: float
    issues_encountered: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'files_removed': self.files_removed,
            'directories_cleaned': self.directories_cleaned,
            'cache_cleared_mb': self.cache_cleared_mb,
            'space_freed_mb': self.space_freed_mb,
            'cleanup_duration_seconds': self.cleanup_duration_seconds,
            'issues_encountered': self.issues_encountered,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class DemoResponse:
    """AI model response with comprehensive metrics for demonstration."""
    query: str
    response: str
    response_time_ms: float
    memory_usage_mb: float
    curriculum_alignment_score: float
    language_quality_score: float
    sources_used: List[str]
    confidence_score: float
    educational_grade: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'query': self.query,
            'response': self.response,
            'response_time_ms': self.response_time_ms,
            'memory_usage_mb': self.memory_usage_mb,
            'curriculum_alignment_score': self.curriculum_alignment_score,
            'language_quality_score': self.language_quality_score,
            'sources_used': self.sources_used,
            'confidence_score': self.confidence_score,
            'educational_grade': self.educational_grade,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class PerformanceBenchmark:
    """Comprehensive performance benchmark results."""
    average_response_time_ms: float
    peak_memory_usage_mb: float
    throughput_queries_per_minute: float
    concurrent_query_capacity: int
    curriculum_alignment_accuracy: float
    system_stability_score: float
    hardware_efficiency_score: float
    test_duration_seconds: float = 0.0
    total_queries_processed: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'average_response_time_ms': self.average_response_time_ms,
            'peak_memory_usage_mb': self.peak_memory_usage_mb,
            'throughput_queries_per_minute': self.throughput_queries_per_minute,
            'concurrent_query_capacity': self.concurrent_query_capacity,
            'curriculum_alignment_accuracy': self.curriculum_alignment_accuracy,
            'system_stability_score': self.system_stability_score,
            'hardware_efficiency_score': self.hardware_efficiency_score,
            'test_duration_seconds': self.test_duration_seconds,
            'total_queries_processed': self.total_queries_processed,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class DocumentationPackage:
    """Package containing all generated documentation."""
    user_guide_path: str
    api_documentation_path: str
    deployment_guide_path: str
    troubleshooting_guide_path: str
    examples_directory: str
    language_versions: List[str]
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'user_guide_path': self.user_guide_path,
            'api_documentation_path': self.api_documentation_path,
            'deployment_guide_path': self.deployment_guide_path,
            'troubleshooting_guide_path': self.troubleshooting_guide_path,
            'examples_directory': self.examples_directory,
            'language_versions': self.language_versions,
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class PerformanceValidation:
    """Results of performance requirement validation."""
    response_time_compliant: bool
    memory_usage_compliant: bool
    concurrent_processing_compliant: bool
    curriculum_alignment_compliant: bool
    system_stability_compliant: bool
    overall_score: float
    detailed_results: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'response_time_compliant': self.response_time_compliant,
            'memory_usage_compliant': self.memory_usage_compliant,
            'concurrent_processing_compliant': self.concurrent_processing_compliant,
            'curriculum_alignment_compliant': self.curriculum_alignment_compliant,
            'system_stability_compliant': self.system_stability_compliant,
            'overall_score': self.overall_score,
            'detailed_results': self.detailed_results,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class HealthCheckReport:
    """Comprehensive system health check report."""
    component_status: Dict[str, bool]
    overall_health: bool
    issues_found: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'component_status': self.component_status,
            'overall_health': self.overall_health,
            'issues_found': self.issues_found,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class DeploymentPackage:
    """Deployment package with all necessary components."""
    package_path: str
    dependencies_included: bool
    configuration_templates: List[str]
    installation_scripts: List[str]
    package_size_mb: float
    checksum: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'package_path': self.package_path,
            'dependencies_included': self.dependencies_included,
            'configuration_templates': self.configuration_templates,
            'installation_scripts': self.installation_scripts,
            'package_size_mb': self.package_size_mb,
            'checksum': self.checksum,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ConfigurationTemplates:
    """Environment-specific configuration templates."""
    development_config: str
    staging_config: str
    production_config: str
    docker_config: str
    environment_variables: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'development_config': self.development_config,
            'staging_config': self.staging_config,
            'production_config': self.production_config,
            'docker_config': self.docker_config,
            'environment_variables': self.environment_variables,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class DemonstrationReport:
    """Complete system demonstration report."""
    demo_responses: List[DemoResponse]
    performance_benchmark: PerformanceBenchmark
    validation_results: 'ValidationResults'
    summary: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'demo_responses': [response.to_dict() for response in self.demo_responses],
            'performance_benchmark': self.performance_benchmark.to_dict(),
            'validation_results': self.validation_results.to_dict(),
            'summary': self.summary,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ValidationResults:
    """Educational content validation results."""
    curriculum_alignment_score: float
    language_quality_score: float
    age_appropriateness_score: float
    source_attribution_accuracy: float
    overall_quality_score: float
    detailed_feedback: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'curriculum_alignment_score': self.curriculum_alignment_score,
            'language_quality_score': self.language_quality_score,
            'age_appropriateness_score': self.age_appropriateness_score,
            'source_attribution_accuracy': self.source_attribution_accuracy,
            'overall_quality_score': self.overall_quality_score,
            'detailed_feedback': self.detailed_feedback,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class UserGuide:
    """User guide documentation."""
    content: str
    language: str
    sections: List[str]
    examples_included: bool
    file_path: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'content': self.content,
            'language': self.language,
            'sections': self.sections,
            'examples_included': self.examples_included,
            'file_path': self.file_path,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class APIDocumentation:
    """API documentation with complete function references."""
    functions_documented: int
    coverage_percentage: float
    examples_included: bool
    file_path: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'functions_documented': self.functions_documented,
            'coverage_percentage': self.coverage_percentage,
            'examples_included': self.examples_included,
            'file_path': self.file_path,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class DeploymentGuide:
    """Production deployment guide."""
    content: str
    environments_covered: List[str]
    configuration_examples: List[str]
    file_path: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'content': self.content,
            'environments_covered': self.environments_covered,
            'configuration_examples': self.configuration_examples,
            'file_path': self.file_path,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class TroubleshootingGuide:
    """Troubleshooting guide with common issues and solutions."""
    content: str
    issues_covered: int
    solutions_provided: int
    file_path: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'content': self.content,
            'issues_covered': self.issues_covered,
            'solutions_provided': self.solutions_provided,
            'file_path': self.file_path,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class StructureReport:
    """Directory structure optimization report."""
    directories_reorganized: int
    files_moved: int
    structure_improvements: List[str]
    validation_passed: bool
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'directories_reorganized': self.directories_reorganized,
            'files_moved': self.files_moved,
            'structure_improvements': self.structure_improvements,
            'validation_passed': self.validation_passed,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ValidationReport:
    """Production readiness validation report."""
    components_validated: int
    validation_passed: bool
    issues_found: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    overall_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'components_validated': self.components_validated,
            'validation_passed': self.validation_passed,
            'issues_found': self.issues_found,
            'recommendations': self.recommendations,
            'overall_score': self.overall_score,
            'timestamp': self.timestamp.isoformat()
        }