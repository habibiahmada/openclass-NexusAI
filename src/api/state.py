"""
Application State Management
Manages global application state and initialization
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AppState:
    """Global application state"""
    
    def __init__(self):
        # Core components
        self.pipeline = None
        self.is_initialized = False
        
        # Database components
        self.db_manager = None
        self.session_repo = None
        self.chat_history_repo = None
        self.user_repo = None
        self.subject_repo = None
        self.db_initialized = False
        
        # Pedagogical engine
        self.pedagogical_integration = None
        self.pedagogy_initialized = False
        
        # Concurrency management
        self.concurrency_manager = None
        self.token_streamer = None
        self.concurrency_initialized = False
        
        # Telemetry
        self.telemetry_collector = None
        self.telemetry_initialized = False
        
        # Resilience
        self.resilience_service = None
        self.resilience_initialized = False
    
    def initialize_database(self) -> bool:
        """Initialize database connection and repositories"""
        try:
            from src.persistence.database_manager import DatabaseManager
            from src.persistence.session_repository import SessionRepository
            from src.persistence.chat_history_repository import ChatHistoryRepository
            from src.persistence.user_repository import UserRepository
            from src.persistence.subject_repository import SubjectRepository
        except ImportError as e:
            logger.warning(f"Database components not available: {e}")
            return False
        
        try:
            database_url = os.getenv('DATABASE_URL')
            
            if not database_url:
                logger.warning("DATABASE_URL not set - database features disabled")
                return False
            
            logger.info("Initializing database connection...")
            
            # Create database manager
            self.db_manager = DatabaseManager(database_url)
            
            # Test connection
            if not self.db_manager.health_check():
                logger.error("Database health check failed")
                return False
            
            # Initialize repositories
            self.session_repo = SessionRepository(self.db_manager)
            self.chat_history_repo = ChatHistoryRepository(self.db_manager)
            self.user_repo = UserRepository(self.db_manager)
            self.subject_repo = SubjectRepository(self.db_manager)
            
            self.db_initialized = True
            logger.info("Database initialized successfully")
            
            # Initialize pedagogical engine
            self._initialize_pedagogy()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            self.db_initialized = False
            return False
    
    def _initialize_pedagogy(self):
        """Initialize pedagogical engine"""
        try:
            from src.pedagogy.integration import create_pedagogical_integration
            
            self.pedagogical_integration = create_pedagogical_integration(self.db_manager)
            self.pedagogy_initialized = True
            logger.info("Pedagogical engine initialized successfully")
        except ImportError:
            logger.warning("Pedagogical engine not available")
        except Exception as e:
            logger.error(f"Failed to initialize pedagogical engine: {e}", exc_info=True)
    
    def initialize_concurrency(self) -> bool:
        """Initialize concurrency manager"""
        try:
            from src.concurrency.concurrency_manager import ConcurrencyManager
            from src.concurrency.token_streamer import TokenStreamer
            from .config import config
            
            logger.info("Initializing concurrency manager...")
            self.concurrency_manager = ConcurrencyManager(
                max_concurrent=config.MAX_CONCURRENT_REQUESTS
            )
            self.token_streamer = TokenStreamer()
            self.concurrency_manager.start_processing()
            self.concurrency_initialized = True
            logger.info("Concurrency manager initialized successfully")
            return True
            
        except ImportError:
            logger.warning("Concurrency management not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize concurrency manager: {e}", exc_info=True)
            return False
    
    def initialize_telemetry(self) -> bool:
        """Initialize telemetry collector"""
        try:
            from src.telemetry.collector import get_collector
            
            self.telemetry_collector = get_collector()
            self.telemetry_initialized = True
            logger.info("Telemetry collector initialized successfully")
            return True
            
        except ImportError:
            logger.warning("Telemetry components not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize telemetry: {e}", exc_info=True)
            return False
    
    def initialize_resilience(self) -> bool:
        """Initialize resilience service"""
        try:
            from src.api.resilience_integration import ResilienceService
            
            logger.info("Initializing resilience service...")
            self.resilience_service = ResilienceService()
            self.resilience_service.initialize()
            self.resilience_initialized = True
            logger.info("Resilience service initialized successfully")
            return True
            
        except ImportError:
            logger.warning("Resilience components not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize resilience service: {e}", exc_info=True)
            return False
    
    def initialize_pipeline(self) -> bool:
        """Initialize RAG pipeline"""
        try:
            from src.edge_runtime.complete_pipeline import CompletePipeline, PipelineConfig
            from .config import config
            
            logger.info("Initializing complete inference pipeline...")
            
            # Create pipeline configuration
            pipeline_config = PipelineConfig(
                model_cache_dir=config.MODEL_CACHE_DIR,
                chroma_db_path=config.CHROMA_DB_PATH,
                chroma_collection_name=config.CHROMA_COLLECTION_NAME,
                enable_performance_monitoring=True,
                enable_batch_processing=False,
                enable_graceful_degradation=True,
                memory_limit_mb=config.MEMORY_LIMIT_MB,
                log_level=config.LOG_LEVEL
            )
            
            # Initialize pipeline
            self.pipeline = CompletePipeline(pipeline_config)
            
            if self.pipeline.initialize():
                if self.pipeline.start():
                    self.is_initialized = True
                    logger.info("Pipeline initialized and started successfully")
                    return True
                else:
                    logger.error("Failed to start pipeline")
                    return False
            else:
                logger.error("Failed to initialize pipeline")
                return False
                
        except ImportError as e:
            logger.warning(f"RAG components not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}", exc_info=True)
            return False
    
    def initialize(self):
        """Initialize all components"""
        logger.info("Starting application initialization...")
        
        # Initialize database first
        self.initialize_database()
        
        # Initialize concurrency manager
        self.initialize_concurrency()
        
        # Initialize telemetry
        self.initialize_telemetry()
        
        # Initialize resilience service
        self.initialize_resilience()
        
        # Initialize RAG pipeline
        self.initialize_pipeline()
        
        logger.info("Application initialization complete")
        logger.info(f"Database: {'✓' if self.db_initialized else '✗'}")
        logger.info(f"Concurrency: {'✓' if self.concurrency_initialized else '✗'}")
        logger.info(f"Telemetry: {'✓' if self.telemetry_initialized else '✗'}")
        logger.info(f"Resilience: {'✓' if self.resilience_initialized else '✗'}")
        logger.info(f"Pipeline: {'✓' if self.is_initialized else '✗'}")
    
    def shutdown(self):
        """Shutdown all components"""
        logger.info("Shutting down application...")
        
        if self.concurrency_manager:
            try:
                self.concurrency_manager.stop_processing()
                logger.info("Concurrency manager stopped")
            except Exception as e:
                logger.error(f"Error stopping concurrency manager: {e}")
        
        if self.resilience_service:
            try:
                self.resilience_service.shutdown()
                logger.info("Resilience service stopped")
            except Exception as e:
                logger.error(f"Error stopping resilience service: {e}")
        
        if self.pipeline:
            try:
                self.pipeline.stop()
                logger.info("Pipeline stopped")
            except Exception as e:
                logger.error(f"Error stopping pipeline: {e}")
        
        if self.db_manager:
            try:
                self.db_manager.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database: {e}")
        
        logger.info("Application shutdown complete")


# Global state instance
app_state = AppState()
