"""
Pipeline manager module for Phase 4 Local Application.

Manages the Complete_Pipeline lifecycle with lazy loading and error handling.
"""

import logging
from typing import Optional, Dict, Any, Iterator
from datetime import datetime

from src.local_inference.complete_pipeline import CompletePipeline, PipelineConfig
from src.ui.models import PipelineStatus

logger = logging.getLogger(__name__)


class PipelineManager:
    """
    Manages the Complete_Pipeline lifecycle with lazy loading and error handling.
    """
    
    def __init__(self):
        """Initialize pipeline manager with no pipeline loaded."""
        self.pipeline: Optional[CompletePipeline] = None
        self.initialization_error: Optional[str] = None
    
    def initialize_pipeline(self) -> bool:
        """
        Lazy initialize the Complete_Pipeline.
        
        Returns:
            True if successful, False otherwise
        """
        if self.pipeline is not None:
            logger.info("Pipeline already initialized")
            return True
        
        try:
            logger.info("Initializing Complete Pipeline...")
            
            # Create pipeline configuration optimized for 4GB systems
            config = PipelineConfig(
                model_cache_dir="./models/cache",
                chroma_db_path="./data/vector_db",
                chroma_collection_name="educational_content",
                memory_limit_mb=3072,
                enable_batch_processing=False,  # Disable for simpler UI
                enable_performance_monitoring=True,
                enable_graceful_degradation=True,
                log_level="INFO"
            )
            
            # Create and initialize pipeline
            self.pipeline = CompletePipeline(config=config)
            
            if not self.pipeline.initialize():
                self.initialization_error = "Pipeline initialization failed"
                logger.error(self.initialization_error)
                return False
            
            if not self.pipeline.start():
                self.initialization_error = "Pipeline start failed"
                logger.error(self.initialization_error)
                return False
            
            logger.info("Pipeline initialized and started successfully")
            self.initialization_error = None
            return True
            
        except FileNotFoundError as e:
            from src.ui.error_handler import get_error_message
            # Extract model path from error if possible
            error_str = str(e)
            if "Model file not found:" in error_str:
                model_path = error_str.split("Model file not found:")[-1].strip()
                self.initialization_error = get_error_message('model_load_failed', path=model_path)
            else:
                self.initialization_error = get_error_message('model_load_failed', path=str(e))
            logger.error(f"Pipeline initialization failed: {e}")
            return False
        except Exception as e:
            from src.ui.error_handler import get_error_message
            self.initialization_error = get_error_message('pipeline_init_failed', error=str(e))
            logger.error(f"Pipeline initialization failed: {e}")
            return False
    
    def get_pipeline(self) -> Optional[CompletePipeline]:
        """
        Get the initialized pipeline or None if not ready.
        
        Returns:
            CompletePipeline instance or None
        """
        return self.pipeline
    
    def get_status(self) -> PipelineStatus:
        """
        Get pipeline status for dashboard display.
        
        Returns:
            PipelineStatus with current state
        """
        if self.pipeline is None:
            return PipelineStatus(
                database_loaded=False,
                database_document_count=0,
                model_loaded=False,
                memory_usage_mb=0.0,
                last_update=datetime.now(),
                error_message=self.initialization_error
            )
        
        try:
            # Get comprehensive pipeline status
            status_dict = self.pipeline.get_pipeline_status()
            
            # Extract relevant information
            components = status_dict.get('components', {})
            memory_info = status_dict.get('memory', {})
            
            # Get document count from vector DB
            doc_count = 0
            if self.pipeline.vector_db:
                try:
                    doc_count = self.pipeline.vector_db.count_documents()
                except Exception as e:
                    logger.warning(f"Could not get document count: {e}")
            
            # Check for empty database
            error_msg = None
            if components.get('vector_db', False) and doc_count == 0:
                from src.ui.error_handler import get_error_message
                error_msg = get_error_message('empty_database')
            
            return PipelineStatus(
                database_loaded=components.get('vector_db', False),
                database_document_count=doc_count,
                model_loaded=components.get('inference_engine', False),
                memory_usage_mb=memory_info.get('usage_mb', 0.0),
                last_update=datetime.now(),
                error_message=error_msg
            )
            
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return PipelineStatus(
                database_loaded=False,
                database_document_count=0,
                model_loaded=False,
                memory_usage_mb=0.0,
                last_update=datetime.now(),
                error_message=str(e)
            )
    
    def process_query(self, query: str, subject_filter: Optional[str]) -> Iterator[str]:
        """
        Process query and yield response tokens for streaming.
        
        Args:
            query: User question
            subject_filter: Optional subject filter
            
        Yields:
            Response text chunks
            
        Raises:
            RuntimeError: If pipeline not initialized
        """
        if self.pipeline is None:
            raise RuntimeError("Pipeline not initialized. Call initialize_pipeline() first.")
        
        try:
            # Process query through pipeline
            result = self.pipeline.process_query(
                query=query,
                subject_filter=subject_filter,
                use_batch_processing=False
            )
            
            # For now, yield the complete response
            # In a real streaming implementation, we would yield chunks
            yield result.response
            
        except MemoryError as e:
            logger.error(f"Memory error during query processing: {e}", exc_info=True)
            from src.ui.error_handler import get_error_message
            error_msg = get_error_message('insufficient_memory')
            yield error_msg
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            from src.ui.error_handler import get_error_message
            error_msg = get_error_message('query_failed')
            yield error_msg
