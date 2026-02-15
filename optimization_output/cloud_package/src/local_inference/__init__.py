"""
Local inference module for OpenClass Nexus AI Phase 3.

This module provides local AI inference capabilities using optimized models
that can run offline on resource-constrained hardware (4GB RAM systems).
The module includes model management, configuration, and inference components.
"""

from .model_config import (
    ModelConfig,
    InferenceConfig,
    DEFAULT_MODEL_CONFIG,
    PERFORMANCE_INFERENCE_CONFIG,
    QUALITY_INFERENCE_CONFIG,
    MEMORY_OPTIMIZED_CONFIG
)

from .hf_client import (
    HuggingFaceClient,
    get_hf_client,
    setup_hf_environment
)

from .model_manager import (
    ModelManager,
    setup_model_management
)

from .model_downloader import (
    ModelDownloader,
    DownloadProgress
)

from .model_validator import (
    ModelValidator,
    ValidationResult,
    ValidationIssue,
    GGUFHeader,
    validate_model_file,
    quick_format_check
)

from .inference_engine import (
    InferenceEngine,
    InferenceMetrics
)

from .resource_manager import (
    MemoryMonitor,
    ThreadManager,
    MemoryStats,
    setup_resource_monitoring,
    get_system_info
)

from .performance_monitor import (
    PerformanceMetrics,
    PerformanceTargets,
    PerformanceTracker,
    PerformanceContext,
    create_performance_tracker
)

from .graceful_degradation import (
    GracefulDegradationManager,
    DegradationLevel,
    DegradationConfig,
    DegradationState,
    create_degradation_manager,
    get_degradation_status_summary
)

from .batch_processor import (
    BatchProcessor,
    BatchQuery,
    BatchResult,
    BatchProcessingConfig,
    QueryPriority,
    create_batch_processor
)

from .context_manager import (
    ContextManager,
    Document
)

from .rag_pipeline import (
    RAGPipeline,
    QueryResult,
    EducationalPromptTemplate
)

from .educational_validator import (
    EducationalContentValidator,
    IndonesianLanguageValidator,
    ResponseQualityAssessor,
    CurriculumAlignmentValidator,
    EducationalValidationResult,
    ValidationIssue as EducationalValidationIssue,
    ValidationLevel,
    ValidationCategory
)

from .error_handler import (
    ComprehensiveErrorHandler,
    NetworkErrorHandler,
    ModelLoadingErrorHandler,
    InferenceErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    ErrorRecoveryResult,
    handle_network_error,
    handle_model_error,
    handle_inference_error
)

__all__ = [
    # Model configuration
    'ModelConfig',
    'InferenceConfig',
    'DEFAULT_MODEL_CONFIG',
    'PERFORMANCE_INFERENCE_CONFIG',
    'QUALITY_INFERENCE_CONFIG',
    'MEMORY_OPTIMIZED_CONFIG',
    
    # HuggingFace client
    'HuggingFaceClient',
    'get_hf_client',
    'setup_hf_environment',
    
    # Model management
    'ModelManager',
    'setup_model_management',
    
    # Model downloading
    'ModelDownloader',
    'DownloadProgress',
    
    # Model validation
    'ModelValidator',
    'ValidationResult',
    'ValidationIssue',
    'GGUFHeader',
    'validate_model_file',
    'quick_format_check',
    
    # Inference engine
    'InferenceEngine',
    'InferenceMetrics',
    
    # Resource management
    'MemoryMonitor',
    'ThreadManager',
    'MemoryStats',
    'setup_resource_monitoring',
    'get_system_info',
    
    # Performance monitoring
    'PerformanceMetrics',
    'PerformanceTargets',
    'PerformanceTracker',
    'PerformanceContext',
    'create_performance_tracker',
    
    # Graceful degradation
    'GracefulDegradationManager',
    'DegradationLevel',
    'DegradationConfig',
    'DegradationState',
    'create_degradation_manager',
    'get_degradation_status_summary',
    
    # Batch processing
    'BatchProcessor',
    'BatchQuery',
    'BatchResult',
    'BatchProcessingConfig',
    'QueryPriority',
    'create_batch_processor',
    
    # Context management
    'ContextManager',
    'Document',
    
    # RAG pipeline
    'RAGPipeline',
    'QueryResult',
    'EducationalPromptTemplate',
    
    # Educational content validation
    'EducationalContentValidator',
    'IndonesianLanguageValidator',
    'ResponseQualityAssessor',
    'CurriculumAlignmentValidator',
    'EducationalValidationResult',
    'EducationalValidationIssue',
    'ValidationLevel',
    'ValidationCategory',
    
    # Error handling
    'ComprehensiveErrorHandler',
    'NetworkErrorHandler',
    'ModelLoadingErrorHandler',
    'InferenceErrorHandler',
    'ErrorCategory',
    'ErrorSeverity',
    'ErrorContext',
    'ErrorRecoveryResult',
    'handle_network_error',
    'handle_model_error',
    'handle_inference_error'
]

# Version information
__version__ = "0.1.0"
__author__ = "OpenClass Nexus AI Team"
__description__ = "Local inference module for offline AI capabilities"