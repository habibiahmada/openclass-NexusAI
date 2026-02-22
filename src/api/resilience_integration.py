"""
Resilience Integration for API Server

Integrates backup, health monitoring, and version management into the API server.
"""

import logging
from pathlib import Path
from typing import Optional

from src.resilience.backup_manager import BackupManager
from src.resilience.backup_scheduler import BackupScheduler
from src.resilience.health_monitor import HealthMonitor
from src.resilience.version_manager import VersionManager

logger = logging.getLogger(__name__)


class ResilienceService:
    """
    Service for managing resilience features:
    - Backup management
    - Health monitoring
    - Version management
    """
    
    def __init__(
        self,
        backup_dir: Optional[str] = None,
        chromadb_path: Optional[str] = None,
        config_path: Optional[str] = None,
        models_path: Optional[str] = None,
        version_file: Optional[str] = None
    ):
        """
        Initialize resilience service.
        
        Args:
            backup_dir: Directory for backups (default: ./backups)
            chromadb_path: Path to ChromaDB directory
            config_path: Path to config directory
            models_path: Path to models directory
            version_file: Path to version file
        """
        # Set default paths
        self.backup_dir = backup_dir or str(Path("./backups"))
        self.chromadb_path = chromadb_path or str(Path("./data/vector_db"))
        self.config_path = config_path or str(Path("./config"))
        self.models_path = models_path or str(Path("./models"))
        self.version_file = version_file or str(Path("./version.json"))
        
        # Initialize components
        self.backup_manager: Optional[BackupManager] = None
        self.backup_scheduler: Optional[BackupScheduler] = None
        self.health_monitor: Optional[HealthMonitor] = None
        self.version_manager: Optional[VersionManager] = None
        
        self._initialized = False
    
    def initialize(self):
        """Initialize all resilience components."""
        try:
            logger.info("Initializing resilience service...")
            
            # Initialize backup manager
            self.backup_manager = BackupManager(
                backup_dir=self.backup_dir,
                chromadb_path=self.chromadb_path,
                config_path=self.config_path,
                models_path=self.models_path
            )
            logger.info("Backup manager initialized")
            
            # Initialize backup scheduler
            self.backup_scheduler = BackupScheduler(
                backup_manager=self.backup_manager,
                retention_days=28
            )
            logger.info("Backup scheduler initialized")
            
            # Initialize health monitor
            self.health_monitor = HealthMonitor()
            logger.info("Health monitor initialized")
            
            # Initialize version manager
            self.version_manager = VersionManager(
                version_file=self.version_file
            )
            logger.info("Version manager initialized")
            
            self._initialized = True
            logger.info("Resilience service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize resilience service: {e}", exc_info=True)
            raise
    
    def get_health_status(self) -> dict:
        """
        Get current health status.
        
        Returns:
            dict: Health status information
        """
        if not self._initialized or not self.health_monitor:
            return {
                "status": "not_initialized",
                "message": "Resilience service not initialized"
            }
        
        try:
            health = self.health_monitor.run_health_checks()
            return {
                "status": "healthy" if health.overall_status.value == "healthy" else "degraded",
                "checks": {
                    "disk_space": health.disk_space.status.value,
                    "ram_usage": health.ram_usage.status.value,
                    "chromadb": health.chromadb.status.value,
                    "llm": health.llm.status.value
                },
                "details": {
                    "disk_space": health.disk_space.message,
                    "ram_usage": health.ram_usage.message,
                    "chromadb": health.chromadb.message,
                    "llm": health.llm.message
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_version_info(self) -> dict:
        """
        Get current version information.
        
        Returns:
            dict: Version information
        """
        if not self._initialized or not self.version_manager:
            return {
                "version": "unknown",
                "message": "Version manager not initialized"
            }
        
        try:
            current_version = self.version_manager.get_current_version()
            available_versions = self.version_manager.list_available_versions()
            
            return {
                "current_version": current_version,
                "available_versions": [
                    {
                        "version": v.version,
                        "timestamp": v.timestamp,
                        "description": v.description
                    }
                    for v in available_versions
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get version info: {e}", exc_info=True)
            return {
                "version": "unknown",
                "error": str(e)
            }
    
    def get_backup_info(self) -> dict:
        """
        Get backup schedule information.
        
        Returns:
            dict: Backup schedule information
        """
        if not self._initialized or not self.backup_scheduler:
            return {
                "status": "not_initialized",
                "message": "Backup scheduler not initialized"
            }
        
        try:
            schedule_info = self.backup_scheduler.get_backup_schedule_info()
            return {
                "status": "active",
                **schedule_info
            }
        except Exception as e:
            logger.error(f"Failed to get backup info: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def is_initialized(self) -> bool:
        """Check if resilience service is initialized."""
        return self._initialized
    
    def shutdown(self):
        """Shutdown resilience service."""
        logger.info("Shutting down resilience service...")
        self._initialized = False
        logger.info("Resilience service shutdown complete")
