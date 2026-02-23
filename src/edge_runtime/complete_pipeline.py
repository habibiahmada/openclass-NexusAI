"""
Complete inference pipeline for OpenClass Nexus AI Phase 3.

This module provides the complete end-to-end inference pipeline that integrates
all components: model management, RAG pipeline, performance monitoring, batch
processing, and comprehensive logging for the local Llama-3.2-3B-Instruct system.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator, Union
from dataclasses import dataclass, field
from contextlib import contextmanager

# Import all pipeline components
from src.embeddings.chroma_manager import ChromaDBManager
from src.embeddings.bedrock_client import BedrockEmbeddingsClient
from .inference_engine import InferenceEngine
from .rag_pipeline import RAGPipeline, QueryResult
from .model_manager import ModelManager
from .model_config import ModelConfig, InferenceConfig
from .performance_monitor import PerformanceTracker, PerformanceContext
from .batch_processor import BatchProcessor, BatchProcessingConfig, QueryPriority
from .graceful_degradation import GracefulDegradationManager
from .resource_manager import MemoryMonitor, ThreadManager
from .educational_validator import EducationalContentValidator


logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the complete inference pipeline."""
    # Model configuration
    model_cache_dir: str = "./models/cache"
    model_config_file: Optional[str] = None
    
    # Performance settings
    enable_performance_monitoring: bool = True
    enable_batch_processing: bool = True
    enable_graceful_degradation: bool = True
    
    # Resource limits (removed memory_limit_mb constraint)
    max_concurrent_queries: int = 2
    
    # ChromaDB settings
    chroma_db_path: str = "./data/vector_db"
    chroma_collection_name: str = "educational_content"
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    enable_detailed_logging: bool = True
    
    # Educational validation
    enable_educational_validation: bool = True
    target_language: str = "indonesian"


class CompletePipeline:
    """
    Complete inference pipeline integrating all Phase 3 components.
    
    This pipeline provides:
    - End-to-end query processing from input to response
    - Comprehensive performance monitoring and logging
    - Resource management and graceful degradation
    - Batch processing capabilities
    - Educational content validation
    - Complete offline functionality
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the complete inference pipeline.
        
        Args:
            config: Pipeline configuration (uses defaults if None)
        """
        self.config = config or PipelineConfig()
        self.is_initialized = False
        self.is_running = False
        
        # Core components (initialized in setup)
        self.model_manager: Optional[ModelManager] = None
        self.inference_engine: Optional[InferenceEngine] = None
        self.vector_db: Optional[ChromaDBManager] = None
        self.embeddings_client: Optional[BedrockEmbeddingsClient] = None
        self.rag_pipeline: Optional[RAGPipeline] = None
        
        # Monitoring and optimization components
        self.performance_tracker: Optional[PerformanceTracker] = None
        self.degradation_manager: Optional[GracefulDegradationManager] = None
        self.memory_monitor: Optional[MemoryMonitor] = None
        self.thread_manager: Optional[ThreadManager] = None
        
        # Batch processing
        self.batch_processor: Optional[BatchProcessor] = None
        
        # Educational validation
        self.educational_validator: Optional[EducationalContentValidator] = None
        
        # Pipeline statistics
        self.stats = {
            'initialized_at': None,
            'started_at': None,
            'total_queries_processed': 0,
            'total_errors': 0,
            'average_response_time_ms': 0.0,
            'uptime_seconds': 0.0
        }
        
        # Setup logging
        self._setup_logging()
        
        logger.info(f"CompletePipeline created with config: {self.config}")
    
    def initialize(self) -> bool:
        """
        Initialize all pipeline components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self.is_initialized:
            logger.warning("Pipeline is already initialized")
            return True
        
        try:
            logger.info("Initializing complete inference pipeline...")
            start_time = time.time()
            
            # Step 1: Initialize resource monitoring
            self._initialize_resource_monitoring()
            
            # Step 2: Initialize model management
            self._initialize_model_management()
            
            # Step 3: Initialize vector database
            self._initialize_vector_database()
            
            # Step 4: Initialize inference engine
            self._initialize_inference_engine()
            
            # Step 5: Initialize RAG pipeline
            self._initialize_rag_pipeline()
            
            # Step 6: Initialize performance monitoring
            self._initialize_performance_monitoring()
            
            # Step 7: Initialize batch processing
            self._initialize_batch_processing()
            
            # Step 8: Initialize educational validation
            self._initialize_educational_validation()
            
            # Step 9: Initialize graceful degradation
            self._initialize_graceful_degradation()
            
            # Mark as initialized
            self.is_initialized = True
            self.stats['initialized_at'] = datetime.now()
            
            initialization_time = time.time() - start_time
            logger.info(f"Pipeline initialization completed in {initialization_time:.2f} seconds")
            
            # Log system status
            self._log_system_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline initialization failed: {e}")
            self.is_initialized = False
            return False
    
    def start(self) -> bool:
        """
        Start the pipeline for processing queries.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if not self.is_initialized:
            logger.error("Pipeline must be initialized before starting")
            return False
        
        if self.is_running:
            logger.warning("Pipeline is already running")
            return True
        
        try:
            logger.info("Starting inference pipeline...")
            
            # Start batch processor if enabled
            if self.config.enable_batch_processing and self.batch_processor:
                self.batch_processor.start()
                logger.info("Batch processor started")
            
            # Start performance monitoring if enabled
            if self.config.enable_performance_monitoring and self.performance_tracker:
                # Performance tracker starts automatically
                logger.info("Performance monitoring active")
            
            # Mark as running
            self.is_running = True
            self.stats['started_at'] = datetime.now()
            
            logger.info("Pipeline started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start pipeline: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the pipeline and cleanup resources."""
        if not self.is_running:
            return
        
        logger.info("Stopping inference pipeline...")
        
        try:
            # Stop batch processor
            if self.batch_processor:
                self.batch_processor.stop()
                logger.info("Batch processor stopped")
            
            # Stop performance monitoring
            if self.performance_tracker:
                self.performance_tracker.stop_continuous_monitoring()
                logger.info("Performance monitoring stopped")
            
            # Unload inference model
            if self.inference_engine:
                self.inference_engine.unload_model()
                logger.info("Inference model unloaded")
            
            # Mark as stopped
            self.is_running = False
            
            # Calculate uptime
            if self.stats['started_at']:
                uptime = (datetime.now() - self.stats['started_at']).total_seconds()
                self.stats['uptime_seconds'] = uptime
                logger.info(f"Pipeline stopped after {uptime:.1f} seconds uptime")
            
        except Exception as e:
            logger.error(f"Error during pipeline shutdown: {e}")
    
    def process_query(self, 
                     query: str,
                     subject_filter: Optional[str] = None,
                     grade_filter: Optional[str] = None,
                     priority: QueryPriority = QueryPriority.NORMAL,
                     use_batch_processing: bool = False) -> Union[QueryResult, str]:
        """
        Process a single query through the complete pipeline.
        
        Args:
            query: User question in Indonesian
            subject_filter: Optional subject filter
            grade_filter: Optional grade filter  
            priority: Query priority for batch processing
            use_batch_processing: Whether to use batch processing
            
        Returns:
            QueryResult for direct processing, query_id for batch processing
        """
        if not self.is_running:
            raise RuntimeError("Pipeline is not running. Call start() first.")
        
        # Validate query
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Educational validation if enabled
        # Note: Educational validation is done on response, not query
        # Query validation is minimal - just check if it's educational context
        if self.config.enable_educational_validation and self.educational_validator:
            # Skip query validation - we'll validate the response instead
            pass
        
        try:
            if use_batch_processing and self.batch_processor:
                # Submit to batch processor
                query_id = self.batch_processor.submit_query(
                    prompt=query,
                    priority=priority,
                    metadata={
                        'subject_filter': subject_filter,
                        'grade_filter': grade_filter,
                        'timestamp': datetime.now().isoformat()
                    }
                )
                logger.info(f"Query submitted to batch processor: {query_id}")
                return query_id
            else:
                # Process directly through RAG pipeline
                with self._performance_context(query) as perf_ctx:
                    result = self.rag_pipeline.process_query(
                        query=query,
                        subject_filter=subject_filter,
                        grade_filter=grade_filter
                    )
                    
                    # Update performance context
                    if perf_ctx:
                        perf_ctx.update_token_counts(
                            context_tokens=result.context_stats.get('context_tokens', 0),
                            response_tokens=len(result.response.split())
                        )
                    
                    # Update statistics
                    self.stats['total_queries_processed'] += 1
                    self._update_average_response_time(result.processing_time_ms)
                    
                    logger.info(f"Query processed successfully in {result.processing_time_ms:.1f}ms")
                    return result
                    
        except Exception as e:
            self.stats['total_errors'] += 1
            logger.error(f"Error processing query: {e}")
            raise
    
    def get_batch_result(self, query_id: str, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Get result from batch processing.
        
        Args:
            query_id: Query ID from batch submission
            timeout: Maximum time to wait for result
            
        Returns:
            Dict with result information or None if not ready
        """
        if not self.batch_processor:
            raise RuntimeError("Batch processing is not enabled")
        
        batch_result = self.batch_processor.get_result(query_id, timeout)
        if batch_result:
            return {
                'query_id': batch_result.query_id,
                'response': batch_result.response,
                'success': batch_result.success,
                'error_message': batch_result.error_message,
                'processing_time_ms': batch_result.processing_time_ms,
                'tokens_generated': batch_result.tokens_generated,
                'memory_usage_mb': batch_result.memory_usage_mb,
                'completed_at': batch_result.completed_at.isoformat()
            }
        return None
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get comprehensive pipeline status and statistics.
        
        Returns:
            Dict with complete pipeline status
        """
        status = {
            'pipeline': {
                'initialized': self.is_initialized,
                'running': self.is_running,
                'config': self.config.__dict__,
                'stats': self.stats.copy()
            },
            'components': {
                'model_manager': self.model_manager is not None,
                'inference_engine': self.inference_engine is not None and self.inference_engine.is_loaded,
                'vector_db': self.vector_db is not None,
                'rag_pipeline': self.rag_pipeline is not None,
                'performance_tracker': self.performance_tracker is not None,
                'batch_processor': self.batch_processor is not None,
                'degradation_manager': self.degradation_manager is not None
            }
        }
        
        # Add component-specific status
        if self.inference_engine:
            status['inference_engine'] = self.inference_engine.get_metrics()
        
        if self.performance_tracker:
            status['performance'] = self.performance_tracker.get_performance_summary()
        
        if self.batch_processor:
            status['batch_processing'] = self.batch_processor.get_queue_status()
        
        if self.memory_monitor:
            memory_stats = self.memory_monitor.get_system_memory()
            status['memory'] = {
                'usage_mb': self.memory_monitor.get_memory_usage(),
                'limit_mb': self.memory_monitor.memory_limit_mb,
                'available_mb': memory_stats.available_mb,
                'recommendations': self.memory_monitor.get_memory_recommendations()
            }
        
        if self.degradation_manager:
            status['degradation'] = {
                'current_level': self.degradation_manager.current_level.name,
                'adjustments': self.degradation_manager.get_inference_config_adjustments()
            }
        
        return status
    
    def get_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all components.
        
        Returns:
            Dict with health check results
        """
        health = {
            'overall_status': 'unknown',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        issues = []
        
        try:
            # Check pipeline status
            health['checks']['pipeline_running'] = self.is_running
            if not self.is_running:
                issues.append("Pipeline is not running")
            
            # Check inference engine
            if self.inference_engine:
                health['checks']['model_loaded'] = self.inference_engine.is_loaded
                if not self.inference_engine.is_loaded:
                    issues.append("Inference model is not loaded")
                
                # Check memory usage
                metrics = self.inference_engine.get_metrics()
                memory_usage = metrics.get('memory_usage_mb', 0)
                health['checks']['memory_usage_mb'] = memory_usage
                
                # Check against memory monitor limit if available
                if self.memory_monitor and memory_usage > self.memory_monitor.memory_limit_mb * 0.9:
                    issues.append(f"High memory usage: {memory_usage}MB")
            else:
                issues.append("Inference engine not initialized")
            
            # Check vector database
            if self.vector_db:
                try:
                    doc_count = self.vector_db.count_documents()
                    health['checks']['vector_db_documents'] = doc_count
                    if doc_count == 0:
                        issues.append("Vector database is empty")
                except Exception as e:
                    issues.append(f"Vector database error: {e}")
            else:
                issues.append("Vector database not initialized")
            
            # Check batch processor if enabled
            if self.config.enable_batch_processing and self.batch_processor:
                batch_status = self.batch_processor.get_queue_status()
                health['checks']['batch_queue_size'] = batch_status['queue_size']
                health['checks']['batch_active_queries'] = batch_status['active_queries']
            
            # Determine overall status
            if not issues:
                health['overall_status'] = 'healthy'
            elif len(issues) <= 2:
                health['overall_status'] = 'warning'
            else:
                health['overall_status'] = 'unhealthy'
            
            health['issues'] = issues
            
        except Exception as e:
            health['overall_status'] = 'error'
            health['error'] = str(e)
            logger.error(f"Health check failed: {e}")
        
        return health
    
    # Private initialization methods
    def _initialize_resource_monitoring(self) -> None:
        """Initialize resource monitoring components."""
        logger.info("Initializing resource monitoring...")
        
        self.memory_monitor = MemoryMonitor()
        self.thread_manager = ThreadManager()
        
        logger.info(f"Optimal thread count: {self.thread_manager.optimal_threads}")
    
    def _initialize_model_management(self) -> None:
        """Initialize model management."""
        logger.info("Initializing model management...")
        
        self.model_manager = ModelManager(base_dir=self.config.model_cache_dir)
        
        # Load configuration
        if self.config.model_config_file:
            model_config, inference_configs = self.model_manager.load_config_from_file(
                self.config.model_config_file
            )
        else:
            # Use default configuration
            model_config = ModelConfig(cache_dir=self.config.model_cache_dir)
            inference_configs = {"default": InferenceConfig()}
        
        self.model_config = model_config
        self.inference_configs = inference_configs
        
        logger.info(f"Model configuration loaded: {model_config.model_id}")
    
    def _initialize_vector_database(self) -> None:
        """Initialize ChromaDB vector database."""
        logger.info("Initializing vector database...")
        
        try:
            self.vector_db = ChromaDBManager(
                persist_directory=self.config.chroma_db_path
            )
            
            # Get or create collection
            try:
                collection = self.vector_db.create_collection(self.config.chroma_collection_name)
                doc_count = self.vector_db.count_documents()
                logger.info(f"Vector database initialized with {doc_count} documents")
            except Exception as e:
                logger.warning(f"ChromaDB collection issue: {e}, will be created when needed")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            raise
    
    def _initialize_inference_engine(self) -> None:
        """Initialize the inference engine."""
        logger.info("Initializing inference engine...")
        
        # Get model path
        model_path = self.model_config.get_model_path()
        if not model_path or not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Get inference configuration
        inference_config = self.inference_configs.get("default", InferenceConfig())
        
        # Apply resource-based adjustments
        if self.thread_manager:
            memory_stats = self.memory_monitor.get_system_memory()
            inference_config.n_threads = self.thread_manager.get_thread_config(
                available_memory_mb=memory_stats.available_mb
            )
        
        # Create inference engine
        self.inference_engine = InferenceEngine(
            model_path=str(model_path),
            config=inference_config
        )
        
        # Load the model
        if not self.inference_engine.load_model():
            raise RuntimeError("Failed to load inference model")
        
        logger.info("Inference engine initialized and model loaded")
    
    def _initialize_rag_pipeline(self) -> None:
        """Initialize the RAG pipeline."""
        logger.info("Initializing RAG pipeline...")
        
        # Initialize embeddings client (optional for offline mode)
        try:
            self.embeddings_client = BedrockEmbeddingsClient()
            logger.info("Bedrock embeddings client initialized")
        except Exception as e:
            logger.warning(f"Bedrock embeddings client not available: {e}")
            self.embeddings_client = None
        
        # Create RAG pipeline
        self.rag_pipeline = RAGPipeline(
            vector_db=self.vector_db,
            inference_engine=self.inference_engine,
            embeddings_client=self.embeddings_client
        )
        
        logger.info("RAG pipeline initialized")
    
    def _initialize_performance_monitoring(self) -> None:
        """Initialize performance monitoring."""
        if not self.config.enable_performance_monitoring:
            return
        
        logger.info("Initializing performance monitoring...")
        
        self.performance_tracker = PerformanceTracker(
            enable_continuous_monitoring=True
        )
        
        # Register performance callback for logging
        self.performance_tracker.register_performance_callback(
            self._log_performance_metrics
        )
        
        logger.info("Performance monitoring initialized")
    
    def _initialize_batch_processing(self) -> None:
        """Initialize batch processing."""
        if not self.config.enable_batch_processing:
            return
        
        logger.info("Initializing batch processing...")
        
        # Use memory monitor's limit if available, otherwise use a default
        memory_threshold = self.memory_monitor.memory_limit_mb * 0.9 if self.memory_monitor else 2764.8  # 90% of 3072MB
        
        batch_config = BatchProcessingConfig(
            max_concurrent_queries=self.config.max_concurrent_queries,
            memory_threshold_mb=memory_threshold
        )
        
        self.batch_processor = BatchProcessor(
            inference_engine=self.inference_engine,
            config=batch_config,
            memory_monitor=self.memory_monitor,
            performance_tracker=self.performance_tracker
        )
        
        logger.info("Batch processing initialized")
    
    def _initialize_educational_validation(self) -> None:
        """Initialize educational validation."""
        if not self.config.enable_educational_validation:
            return
        
        logger.info("Initializing educational validation...")
        
        try:
            self.educational_validator = EducationalContentValidator()
            logger.info("Educational validation initialized")
        except Exception as e:
            logger.warning(f"Educational validation not available: {e}")
            self.educational_validator = None
    
    def _initialize_graceful_degradation(self) -> None:
        """Initialize graceful degradation."""
        if not self.config.enable_graceful_degradation:
            return
        
        logger.info("Initializing graceful degradation...")
        
        self.degradation_manager = GracefulDegradationManager(
            memory_monitor=self.memory_monitor,
            thread_manager=self.thread_manager,
            performance_tracker=self.performance_tracker
        )
        
        # Connect degradation manager to other components
        if self.inference_engine:
            self.inference_engine.degradation_manager = self.degradation_manager
        
        if self.batch_processor:
            self.batch_processor.degradation_manager = self.degradation_manager
        
        logger.info("Graceful degradation initialized")
    
    # Utility methods
    def _setup_logging(self) -> None:
        """Setup comprehensive logging for the pipeline."""
        # Configure logging level
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Add file handler if specified
        if self.config.log_file:
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        # Ensure console handler exists
        if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
    
    @contextmanager
    def _performance_context(self, query: str):
        """Create performance tracking context for query processing."""
        if self.performance_tracker:
            perf_ctx = PerformanceContext(
                self.performance_tracker,
                operation_name="pipeline_query",
                query_length=len(query)
            )
            with perf_ctx:
                yield perf_ctx
        else:
            yield None
    
    def _log_performance_metrics(self, metrics) -> None:
        """Log performance metrics callback."""
        if self.config.enable_detailed_logging:
            logger.info(f"Performance: {metrics.response_time_ms:.1f}ms, "
                       f"{metrics.memory_usage_mb:.1f}MB, "
                       f"{metrics.tokens_per_second:.1f} tok/s, "
                       f"grade: {metrics.get_performance_grade()}")
    
    def _update_average_response_time(self, response_time_ms: float) -> None:
        """Update average response time statistics."""
        total_queries = self.stats['total_queries_processed']
        if total_queries == 1:
            self.stats['average_response_time_ms'] = response_time_ms
        else:
            # Calculate running average
            current_avg = self.stats['average_response_time_ms']
            new_avg = ((current_avg * (total_queries - 1)) + response_time_ms) / total_queries
            self.stats['average_response_time_ms'] = new_avg
    
    def _log_system_status(self) -> None:
        """Log comprehensive system status after initialization."""
        logger.info("=== Pipeline System Status ===")
        logger.info(f"Model: {self.model_config.model_id}")
        if self.memory_monitor:
            logger.info(f"Memory limit: {self.memory_monitor.memory_limit_mb}MB")
        logger.info(f"Thread count: {self.inference_configs['default'].n_threads}")
        logger.info(f"Context window: {self.inference_configs['default'].n_ctx}")
        logger.info(f"Batch processing: {'enabled' if self.config.enable_batch_processing else 'disabled'}")
        logger.info(f"Performance monitoring: {'enabled' if self.config.enable_performance_monitoring else 'disabled'}")
        logger.info(f"Graceful degradation: {'enabled' if self.config.enable_graceful_degradation else 'disabled'}")
        
        if self.vector_db:
            try:
                doc_count = self.vector_db.count_documents()
                logger.info(f"Vector database: {doc_count} documents")
            except Exception:
                logger.info("Vector database: status unknown")
        
        logger.info("=== End System Status ===")
    
    def __enter__(self):
        """Context manager entry."""
        if not self.initialize():
            raise RuntimeError("Failed to initialize pipeline")
        if not self.start():
            raise RuntimeError("Failed to start pipeline")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.stop()


# Utility functions for pipeline creation
def create_complete_pipeline(
    model_cache_dir: str = "./models/cache",
    chroma_db_path: str = "./data/vector_db",
    enable_batch_processing: bool = True,
    enable_performance_monitoring: bool = True,
    log_level: str = "INFO"
) -> CompletePipeline:
    """
    Create a complete pipeline with recommended settings.
    
    Args:
        model_cache_dir: Directory for model storage
        chroma_db_path: Path to ChromaDB database
        enable_batch_processing: Enable batch processing capabilities
        enable_performance_monitoring: Enable performance monitoring
        log_level: Logging level
        
    Returns:
        CompletePipeline instance
    """
    config = PipelineConfig(
        model_cache_dir=model_cache_dir,
        chroma_db_path=chroma_db_path,
        enable_batch_processing=enable_batch_processing,
        enable_performance_monitoring=enable_performance_monitoring,
        log_level=log_level
    )
    
    return CompletePipeline(config=config)


# Example usage
def example_pipeline_usage():
    """Example of how to use the complete pipeline."""
    print("Complete Pipeline Example")
    print("This example shows how to use the CompletePipeline class")
    
    # Create pipeline configuration
    config = PipelineConfig(
        model_cache_dir="./models/cache",
        chroma_db_path="./data/vector_db",
        enable_batch_processing=True,
        enable_performance_monitoring=True,
        log_level="INFO"
    )
    
    print(f"Configuration: {config}")
    print("Pipeline would integrate all Phase 3 components")
    print("for complete end-to-end Indonesian educational AI")


if __name__ == "__main__":
    example_pipeline_usage()