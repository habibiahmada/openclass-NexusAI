"""
HealthMonitor - System health monitoring daemon
"""

import psutil
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class HealthLevel(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class HealthStatus:
    """Health status for a single check"""
    healthy: bool
    level: HealthLevel
    message: str
    critical: bool = False
    warning: bool = False
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        
        # Set level based on flags
        if self.critical:
            self.level = HealthLevel.CRITICAL
            self.healthy = False
        elif self.warning:
            self.level = HealthLevel.WARNING
        else:
            self.level = HealthLevel.HEALTHY


@dataclass
class SystemHealth:
    """Overall system health status"""
    healthy: bool
    checks: Dict[str, HealthStatus]
    critical_failures: List[str]
    warnings: List[str]
    timestamp: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'healthy': self.healthy,
            'checks': {k: asdict(v) for k, v in self.checks.items()},
            'critical_failures': self.critical_failures,
            'warnings': self.warnings,
            'timestamp': self.timestamp
        }


class HealthMonitor:
    """
    System health monitoring daemon that checks:
    - LLM model status
    - ChromaDB connection
    - PostgreSQL connection
    - Disk space (80% warning, 90% critical)
    - RAM usage (80% warning, 90% critical)
    """
    
    def __init__(
        self,
        disk_warning_threshold: float = 80.0,
        disk_critical_threshold: float = 90.0,
        ram_warning_threshold: float = 80.0,
        ram_critical_threshold: float = 90.0
    ):
        self.disk_warning_threshold = disk_warning_threshold
        self.disk_critical_threshold = disk_critical_threshold
        self.ram_warning_threshold = ram_warning_threshold
        self.ram_critical_threshold = ram_critical_threshold
        
        self.checks = [
            ('llm_status', self.check_llm_status),
            ('chromadb_connection', self.check_chromadb_connection),
            ('postgres_connection', self.check_postgres_connection),
            ('disk_space', self.check_disk_space),
            ('ram_usage', self.check_ram_usage)
        ]
        
        logger.info("HealthMonitor initialized")
    
    def run_health_checks(self) -> SystemHealth:
        """
        Execute all health checks and return overall system health.
        
        Returns:
            SystemHealth: Overall system health status
        """
        logger.info("Running health checks...")
        
        results = {}
        critical_failures = []
        warnings = []
        
        for check_name, check_func in self.checks:
            try:
                status = check_func()
                results[check_name] = status
                
                if status.critical:
                    critical_failures.append(check_name)
                elif status.warning:
                    warnings.append(check_name)
                    
            except Exception as e:
                logger.error(f"Health check failed: {check_name} - {e}", exc_info=True)
                results[check_name] = HealthStatus(
                    healthy=False,
                    level=HealthLevel.CRITICAL,
                    message=f"Check failed: {str(e)}",
                    critical=True
                )
                critical_failures.append(check_name)
        
        # Determine overall health
        all_healthy = all(r.healthy for r in results.values())
        
        system_health = SystemHealth(
            healthy=all_healthy,
            checks=results,
            critical_failures=critical_failures,
            warnings=warnings,
            timestamp=datetime.now().isoformat()
        )
        
        if critical_failures:
            logger.error(f"Critical failures detected: {critical_failures}")
        elif warnings:
            logger.warning(f"Warnings detected: {warnings}")
        else:
            logger.info("All health checks passed")
        
        return system_health
    
    def check_llm_status(self) -> HealthStatus:
        """
        Check LLM model status by attempting a test inference.
        
        Returns:
            HealthStatus: LLM health status
        """
        try:
            # Try to import and test LLM engine
            from src.edge_runtime.inference_engine import InferenceEngine
            
            # Create engine instance
            engine = InferenceEngine()
            
            # Test inference with minimal tokens
            response = engine.generate("test", max_tokens=5)
            
            if response and len(response) > 0:
                return HealthStatus(
                    healthy=True,
                    level=HealthLevel.HEALTHY,
                    message="LLM operational"
                )
            else:
                return HealthStatus(
                    healthy=False,
                    level=HealthLevel.CRITICAL,
                    message="LLM returned empty response",
                    critical=True
                )
                
        except ImportError:
            logger.warning("InferenceEngine not available, skipping LLM check")
            return HealthStatus(
                healthy=True,
                level=HealthLevel.WARNING,
                message="LLM check skipped (module not available)",
                warning=True
            )
        except Exception as e:
            return HealthStatus(
                healthy=False,
                level=HealthLevel.CRITICAL,
                message=f"LLM failure: {str(e)}",
                critical=True
            )
    
    def check_chromadb_connection(self) -> HealthStatus:
        """
        Check ChromaDB connection by attempting a health check query.
        
        Returns:
            HealthStatus: ChromaDB health status
        """
        try:
            # Try to import and test ChromaDB manager
            from src.embeddings.chroma_manager import ChromaManager
            
            # Create manager instance
            manager = ChromaManager()
            
            # Test connection
            manager.health_check()
            
            return HealthStatus(
                healthy=True,
                level=HealthLevel.HEALTHY,
                message="ChromaDB connected"
            )
                
        except ImportError:
            logger.warning("ChromaManager not available, skipping ChromaDB check")
            return HealthStatus(
                healthy=True,
                level=HealthLevel.WARNING,
                message="ChromaDB check skipped (module not available)",
                warning=True
            )
        except Exception as e:
            return HealthStatus(
                healthy=False,
                level=HealthLevel.CRITICAL,
                message=f"ChromaDB failure: {str(e)}",
                critical=True
            )
    
    def check_postgres_connection(self) -> HealthStatus:
        """
        Check PostgreSQL connection by attempting a test query.
        
        Returns:
            HealthStatus: PostgreSQL health status
        """
        try:
            # Try to import and test database manager
            from src.persistence.database_manager import DatabaseManager
            
            # Create manager instance
            manager = DatabaseManager()
            
            # Test connection
            if manager.health_check():
                return HealthStatus(
                    healthy=True,
                    level=HealthLevel.HEALTHY,
                    message="PostgreSQL connected"
                )
            else:
                return HealthStatus(
                    healthy=False,
                    level=HealthLevel.CRITICAL,
                    message="PostgreSQL health check failed",
                    critical=True
                )
                
        except ImportError:
            logger.warning("DatabaseManager not available, skipping PostgreSQL check")
            return HealthStatus(
                healthy=True,
                level=HealthLevel.WARNING,
                message="PostgreSQL check skipped (module not available)",
                warning=True
            )
        except Exception as e:
            return HealthStatus(
                healthy=False,
                level=HealthLevel.CRITICAL,
                message=f"PostgreSQL failure: {str(e)}",
                critical=True
            )
    
    def check_disk_space(self) -> HealthStatus:
        """
        Check disk space usage with thresholds (80% warning, 90% critical).
        
        Returns:
            HealthStatus: Disk space health status
        """
        try:
            usage = psutil.disk_usage('/')
            percent_used = usage.percent
            
            if percent_used >= self.disk_critical_threshold:
                return HealthStatus(
                    healthy=False,
                    level=HealthLevel.CRITICAL,
                    message=f"Disk usage critical: {percent_used:.1f}% "
                           f"(threshold: {self.disk_critical_threshold}%)",
                    critical=True
                )
            elif percent_used >= self.disk_warning_threshold:
                return HealthStatus(
                    healthy=True,
                    level=HealthLevel.WARNING,
                    message=f"Disk usage high: {percent_used:.1f}% "
                           f"(threshold: {self.disk_warning_threshold}%)",
                    warning=True
                )
            else:
                return HealthStatus(
                    healthy=True,
                    level=HealthLevel.HEALTHY,
                    message=f"Disk usage normal: {percent_used:.1f}%"
                )
                
        except Exception as e:
            return HealthStatus(
                healthy=False,
                level=HealthLevel.CRITICAL,
                message=f"Disk check failed: {str(e)}",
                critical=True
            )
    
    def check_ram_usage(self) -> HealthStatus:
        """
        Check RAM usage with thresholds (80% warning, 90% critical).
        
        Returns:
            HealthStatus: RAM usage health status
        """
        try:
            memory = psutil.virtual_memory()
            percent_used = memory.percent
            
            if percent_used >= self.ram_critical_threshold:
                return HealthStatus(
                    healthy=False,
                    level=HealthLevel.CRITICAL,
                    message=f"RAM usage critical: {percent_used:.1f}% "
                           f"(threshold: {self.ram_critical_threshold}%)",
                    critical=True
                )
            elif percent_used >= self.ram_warning_threshold:
                return HealthStatus(
                    healthy=True,
                    level=HealthLevel.WARNING,
                    message=f"RAM usage high: {percent_used:.1f}% "
                           f"(threshold: {self.ram_warning_threshold}%)",
                    warning=True
                )
            else:
                return HealthStatus(
                    healthy=True,
                    level=HealthLevel.HEALTHY,
                    message=f"RAM usage normal: {percent_used:.1f}%"
                )
                
        except Exception as e:
            return HealthStatus(
                healthy=False,
                level=HealthLevel.CRITICAL,
                message=f"RAM check failed: {str(e)}",
                critical=True
            )
    
    def get_detailed_system_info(self) -> dict:
        """
        Get detailed system information for diagnostics.
        
        Returns:
            dict: Detailed system information
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count(),
                    'count_logical': psutil.cpu_count(logical=True)
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'percent': disk.percent
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}", exc_info=True)
            return {'error': str(e)}
