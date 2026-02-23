"""
AutoRestartService - Automatic service restart on failure detection
"""

import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RestartAttempt:
    """Record of a restart attempt"""
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


class AutoRestartService:
    """
    Automatic service restart on critical failure detection.
    
    Features:
    - Detects service failures
    - Attempts restart with max 3 attempts
    - Restart cooldown (5 minutes)
    - Escalates to manual intervention after max attempts
    """
    
    MAX_RESTART_ATTEMPTS = 3
    RESTART_COOLDOWN_SECONDS = 300  # 5 minutes
    
    def __init__(self):
        # Track restart history: service_name -> (last_restart_time, attempt_count, attempts_list)
        self.restart_history: Dict[str, Tuple[datetime, int, list]] = {}
        
        logger.info(f"AutoRestartService initialized "
                   f"(max_attempts={self.MAX_RESTART_ATTEMPTS}, "
                   f"cooldown={self.RESTART_COOLDOWN_SECONDS}s)")
    
    def detect_failure(self, service_name: str) -> bool:
        """
        Detect if a service has failed.
        
        Args:
            service_name: Name of the service to check
        
        Returns:
            bool: True if service has failed
        """
        try:
            # Check service status using systemctl
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Service is active if return code is 0
            is_active = result.returncode == 0
            
            if not is_active:
                logger.warning(f"Service failure detected: {service_name} "
                              f"(status: {result.stdout.strip()})")
            
            return not is_active
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout checking service status: {service_name}")
            return True  # Assume failure if check times out
        except FileNotFoundError:
            logger.warning(f"systemctl not found, cannot check service: {service_name}")
            return False  # Cannot determine, assume OK
        except Exception as e:
            logger.error(f"Error detecting failure for {service_name}: {e}", exc_info=True)
            return False  # Cannot determine, assume OK
    
    def attempt_restart(self, service_name: str) -> bool:
        """
        Attempt to restart a failed service.
        
        Args:
            service_name: Name of the service to restart
        
        Returns:
            bool: True if restart was successful
        """
        logger.info(f"Attempting to restart service: {service_name}")
        
        # Check restart history
        if service_name in self.restart_history:
            last_restart, attempt_count, attempts = self.restart_history[service_name]
            
            # Check cooldown
            time_since_last = (datetime.now() - last_restart).total_seconds()
            if time_since_last < self.RESTART_COOLDOWN_SECONDS:
                remaining = self.RESTART_COOLDOWN_SECONDS - time_since_last
                logger.warning(f"Restart cooldown active for {service_name} "
                              f"({remaining:.0f}s remaining)")
                return False
            
            # Check max attempts
            if attempt_count >= self.MAX_RESTART_ATTEMPTS:
                logger.error(f"Max restart attempts reached for {service_name} "
                            f"({attempt_count}/{self.MAX_RESTART_ATTEMPTS})")
                self.escalate_failure(service_name)
                return False
            
            # Reset attempt count if cooldown has passed
            if time_since_last > self.RESTART_COOLDOWN_SECONDS * 2:
                logger.info(f"Resetting restart attempt count for {service_name}")
                attempt_count = 0
                attempts = []
        else:
            attempt_count = 0
            attempts = []
        
        # Attempt restart
        try:
            result = subprocess.run(
                ['systemctl', 'restart', service_name],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            # Verify service is now active
            is_active = not self.detect_failure(service_name)
            
            if is_active:
                # Record successful restart
                attempt = RestartAttempt(
                    timestamp=datetime.now(),
                    success=True
                )
                attempts.append(attempt)
                
                self.restart_history[service_name] = (
                    datetime.now(),
                    attempt_count + 1,
                    attempts
                )
                
                logger.info(f"Successfully restarted {service_name} "
                           f"(attempt {attempt_count + 1}/{self.MAX_RESTART_ATTEMPTS})")
                return True
            else:
                # Restart command succeeded but service still not active
                error_msg = "Service not active after restart"
                logger.error(f"Restart failed for {service_name}: {error_msg}")
                
                attempt = RestartAttempt(
                    timestamp=datetime.now(),
                    success=False,
                    error_message=error_msg
                )
                attempts.append(attempt)
                
                self.restart_history[service_name] = (
                    datetime.now(),
                    attempt_count + 1,
                    attempts
                )
                
                return False
                
        except subprocess.CalledProcessError as e:
            error_msg = f"Restart command failed: {e.stderr}"
            logger.error(f"Failed to restart {service_name}: {error_msg}")
            
            attempt = RestartAttempt(
                timestamp=datetime.now(),
                success=False,
                error_message=error_msg
            )
            attempts.append(attempt)
            
            self.restart_history[service_name] = (
                datetime.now(),
                attempt_count + 1,
                attempts
            )
            
            return False
            
        except subprocess.TimeoutExpired:
            error_msg = "Restart command timed out"
            logger.error(f"Failed to restart {service_name}: {error_msg}")
            
            attempt = RestartAttempt(
                timestamp=datetime.now(),
                success=False,
                error_message=error_msg
            )
            attempts.append(attempt)
            
            self.restart_history[service_name] = (
                datetime.now(),
                attempt_count + 1,
                attempts
            )
            
            return False
            
        except FileNotFoundError:
            logger.error(f"systemctl not found, cannot restart service: {service_name}")
            return False
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error restarting {service_name}: {error_msg}", 
                        exc_info=True)
            
            attempt = RestartAttempt(
                timestamp=datetime.now(),
                success=False,
                error_message=error_msg
            )
            attempts.append(attempt)
            
            self.restart_history[service_name] = (
                datetime.now(),
                attempt_count + 1,
                attempts
            )
            
            return False
    
    def escalate_failure(self, service_name: str):
        """
        Escalate failure to manual intervention after max restart attempts.
        
        Args:
            service_name: Name of the failed service
        """
        logger.critical(f"CRITICAL: {service_name} failed after "
                       f"{self.MAX_RESTART_ATTEMPTS} restart attempts - "
                       f"MANUAL INTERVENTION REQUIRED")
        
        # Get restart history
        if service_name in self.restart_history:
            _, attempt_count, attempts = self.restart_history[service_name]
            
            logger.critical(f"Restart history for {service_name}:")
            for i, attempt in enumerate(attempts[-self.MAX_RESTART_ATTEMPTS:], 1):
                status = "SUCCESS" if attempt.success else "FAILED"
                logger.critical(f"  Attempt {i}: {status} at {attempt.timestamp.isoformat()}")
                if attempt.error_message:
                    logger.critical(f"    Error: {attempt.error_message}")
        
        # Optional: Send notification (email, SMS, etc.)
        self._send_admin_notification(service_name)
    
    def _send_admin_notification(self, service_name: str):
        """
        Send notification to administrators about critical failure.
        
        Args:
            service_name: Name of the failed service
        """
        # TODO: Implement notification system (email, SMS, Slack, etc.)
        # For now, just log
        logger.critical(f"ADMIN NOTIFICATION: Service {service_name} requires manual intervention")
        
        # Example: Send email
        # send_email(
        #     to=os.getenv('ADMIN_EMAIL'),
        #     subject=f"CRITICAL: {service_name} requires manual intervention",
        #     body=f"Service {service_name} has failed after {self.MAX_RESTART_ATTEMPTS} restart attempts."
        # )
    
    def get_restart_history(self, service_name: Optional[str] = None) -> dict:
        """
        Get restart history for a service or all services.
        
        Args:
            service_name: Name of the service (None for all services)
        
        Returns:
            dict: Restart history
        """
        if service_name:
            if service_name not in self.restart_history:
                return {
                    'service': service_name,
                    'attempts': 0,
                    'last_restart': None,
                    'history': []
                }
            
            last_restart, attempt_count, attempts = self.restart_history[service_name]
            
            return {
                'service': service_name,
                'attempts': attempt_count,
                'last_restart': last_restart.isoformat(),
                'history': [
                    {
                        'timestamp': a.timestamp.isoformat(),
                        'success': a.success,
                        'error_message': a.error_message
                    }
                    for a in attempts
                ]
            }
        else:
            # Return history for all services
            return {
                service: {
                    'attempts': attempt_count,
                    'last_restart': last_restart.isoformat(),
                    'history': [
                        {
                            'timestamp': a.timestamp.isoformat(),
                            'success': a.success,
                            'error_message': a.error_message
                        }
                        for a in attempts
                    ]
                }
                for service, (last_restart, attempt_count, attempts) in self.restart_history.items()
            }
    
    def reset_restart_history(self, service_name: str):
        """
        Reset restart history for a service (after manual intervention).
        
        Args:
            service_name: Name of the service
        """
        if service_name in self.restart_history:
            del self.restart_history[service_name]
            logger.info(f"Reset restart history for {service_name}")
        else:
            logger.warning(f"No restart history found for {service_name}")
