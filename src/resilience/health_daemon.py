#!/usr/bin/env python3
"""
Health Monitoring Daemon

Runs health checks every 5 minutes and attempts auto-restart on critical failures.
Logs all health check results and sends alerts on repeated failures.
"""

import os
import sys
import time
import logging
import signal
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.resilience.health_monitor import HealthMonitor, HealthLevel
from src.resilience.auto_restart_service import AutoRestartService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/nexusai/health_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class HealthDaemon:
    """
    Health monitoring daemon that runs continuously.
    
    Features:
    - Runs health checks every 5 minutes
    - Attempts auto-restart on critical failures
    - Logs all health check results
    - Sends alerts on repeated failures
    """
    
    CHECK_INTERVAL_SECONDS = 300  # 5 minutes
    
    # Service name mapping for auto-restart
    SERVICE_MAPPING = {
        'llm_status': 'nexusai-api',
        'chromadb_connection': 'chromadb',
        'postgres_connection': 'postgresql'
    }
    
    def __init__(self):
        self.health_monitor = HealthMonitor()
        self.auto_restart = AutoRestartService()
        self.running = False
        self.consecutive_failures = {}
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info("Health daemon initialized")
    
    def start(self):
        """Start the health monitoring daemon"""
        logger.info("Starting health monitoring daemon...")
        logger.info(f"Check interval: {self.CHECK_INTERVAL_SECONDS} seconds")
        
        self.running = True
        
        try:
            while self.running:
                self._run_health_check_cycle()
                
                # Sleep until next check
                if self.running:
                    logger.debug(f"Sleeping for {self.CHECK_INTERVAL_SECONDS} seconds...")
                    time.sleep(self.CHECK_INTERVAL_SECONDS)
                    
        except Exception as e:
            logger.error(f"Health daemon error: {e}", exc_info=True)
            raise
        finally:
            logger.info("Health daemon stopped")
    
    def stop(self):
        """Stop the health monitoring daemon"""
        logger.info("Stopping health daemon...")
        self.running = False
    
    def _run_health_check_cycle(self):
        """Run a single health check cycle"""
        logger.info("=" * 60)
        logger.info("Running health check cycle...")
        
        try:
            # Run all health checks
            system_health = self.health_monitor.run_health_checks()
            
            # Log overall status
            if system_health.healthy:
                logger.info("✓ System health: HEALTHY")
            else:
                logger.warning("✗ System health: UNHEALTHY")
            
            # Log individual check results
            for check_name, status in system_health.checks.items():
                level_symbol = {
                    HealthLevel.HEALTHY: "✓",
                    HealthLevel.WARNING: "⚠",
                    HealthLevel.CRITICAL: "✗"
                }.get(status.level, "?")
                
                logger.info(f"  {level_symbol} {check_name}: {status.message}")
            
            # Handle critical failures
            if system_health.critical_failures:
                logger.error(f"Critical failures detected: {system_health.critical_failures}")
                self._handle_critical_failures(system_health.critical_failures)
            
            # Handle warnings
            if system_health.warnings:
                logger.warning(f"Warnings detected: {system_health.warnings}")
                self._handle_warnings(system_health.warnings)
            
            # Reset consecutive failures for healthy checks
            for check_name, status in system_health.checks.items():
                if status.healthy and check_name in self.consecutive_failures:
                    logger.info(f"Resetting consecutive failures for {check_name}")
                    del self.consecutive_failures[check_name]
            
            # Log system info periodically
            if datetime.now().minute % 15 == 0:  # Every 15 minutes
                self._log_system_info()
            
        except Exception as e:
            logger.error(f"Health check cycle failed: {e}", exc_info=True)
    
    def _handle_critical_failures(self, failures: list):
        """
        Handle critical failures by attempting auto-restart.
        
        Args:
            failures: List of failed check names
        """
        for check_name in failures:
            # Track consecutive failures
            if check_name not in self.consecutive_failures:
                self.consecutive_failures[check_name] = 0
            self.consecutive_failures[check_name] += 1
            
            failure_count = self.consecutive_failures[check_name]
            logger.error(f"Critical failure: {check_name} "
                        f"(consecutive failures: {failure_count})")
            
            # Attempt auto-restart for service failures
            if check_name in self.SERVICE_MAPPING:
                service_name = self.SERVICE_MAPPING[check_name]
                logger.info(f"Attempting auto-restart for {service_name}...")
                
                success = self.auto_restart.attempt_restart(service_name)
                
                if success:
                    logger.info(f"Auto-restart successful for {service_name}")
                    # Reset consecutive failures on successful restart
                    self.consecutive_failures[check_name] = 0
                else:
                    logger.error(f"Auto-restart failed for {service_name}")
            
            # Send alert on repeated failures
            if failure_count >= 3:
                self._send_alert(check_name, failure_count)
    
    def _handle_warnings(self, warnings: list):
        """
        Handle warnings by logging and monitoring.
        
        Args:
            warnings: List of warning check names
        """
        for check_name in warnings:
            # Track consecutive warnings
            if check_name not in self.consecutive_failures:
                self.consecutive_failures[check_name] = 0
            self.consecutive_failures[check_name] += 1
            
            warning_count = self.consecutive_failures[check_name]
            
            # Send alert if warning persists
            if warning_count >= 6:  # 30 minutes of warnings
                logger.warning(f"Persistent warning: {check_name} "
                              f"(consecutive warnings: {warning_count})")
                self._send_alert(check_name, warning_count, level='warning')
    
    def _send_alert(self, check_name: str, failure_count: int, level: str = 'critical'):
        """
        Send alert about repeated failures.
        
        Args:
            check_name: Name of the failed check
            failure_count: Number of consecutive failures
            level: Alert level ('critical' or 'warning')
        """
        logger.critical(f"ALERT: {check_name} has failed {failure_count} times consecutively")
        
        # TODO: Implement alert system (email, SMS, Slack, etc.)
        # For now, just log
        
        # Example: Send email
        # send_email(
        #     to=os.getenv('ADMIN_EMAIL'),
        #     subject=f"{level.upper()}: {check_name} repeated failures",
        #     body=f"{check_name} has failed {failure_count} times consecutively."
        # )
    
    def _log_system_info(self):
        """Log detailed system information"""
        logger.info("System information:")
        
        try:
            system_info = self.health_monitor.get_detailed_system_info()
            
            logger.info(f"  CPU: {system_info['cpu']['percent']:.1f}% "
                       f"({system_info['cpu']['count']} cores)")
            logger.info(f"  Memory: {system_info['memory']['used_gb']:.1f}GB / "
                       f"{system_info['memory']['total_gb']:.1f}GB "
                       f"({system_info['memory']['percent']:.1f}%)")
            logger.info(f"  Disk: {system_info['disk']['used_gb']:.1f}GB / "
                       f"{system_info['disk']['total_gb']:.1f}GB "
                       f"({system_info['disk']['percent']:.1f}%)")
        except Exception as e:
            logger.error(f"Failed to log system info: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()


def main():
    """Main entry point for the health daemon"""
    logger.info("=" * 60)
    logger.info("NexusAI Health Monitoring Daemon")
    logger.info("=" * 60)
    
    # Create log directory if it doesn't exist
    log_dir = Path('/var/log/nexusai')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create and start daemon
    daemon = HealthDaemon()
    
    try:
        daemon.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        daemon.stop()
    except Exception as e:
        logger.error(f"Daemon failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
