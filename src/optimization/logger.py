"""
Optimization Logging Utilities

This module provides centralized logging utilities for optimization processes,
ensuring consistent logging across all optimization components.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_optimization_logger(
    name: str = "optimization",
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    Setup a logger for optimization processes.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file name
        log_dir: Optional log directory path
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"optimization.{name}")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file and log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / log_file
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_optimization_logger(name: str) -> logging.Logger:
    """
    Get an optimization logger with consistent configuration.
    
    Args:
        name: Logger name suffix
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f"optimization.{name}")


class OptimizationLoggerMixin:
    """Mixin class to add logging capabilities to optimization components."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_optimization_logger(self.__class__.__name__.lower())
    
    def log_info(self, message: str, **kwargs):
        """Log info message with optional context."""
        if kwargs:
            message = f"{message} - Context: {kwargs}"
        self.logger.info(message)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with optional context."""
        if kwargs:
            message = f"{message} - Context: {kwargs}"
        self.logger.warning(message)
    
    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception and context."""
        if kwargs:
            message = f"{message} - Context: {kwargs}"
        if exception:
            self.logger.error(message, exc_info=exception)
        else:
            self.logger.error(message)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with optional context."""
        if kwargs:
            message = f"{message} - Context: {kwargs}"
        self.logger.debug(message)
    
    def log_operation_start(self, operation: str, **kwargs):
        """Log the start of an operation."""
        context = f" with {kwargs}" if kwargs else ""
        self.logger.info(f"Starting {operation}{context}")
    
    def log_operation_complete(self, operation: str, duration: Optional[float] = None, **kwargs):
        """Log the completion of an operation."""
        duration_str = f" in {duration:.2f}s" if duration else ""
        context = f" - Results: {kwargs}" if kwargs else ""
        self.logger.info(f"Completed {operation}{duration_str}{context}")
    
    def log_operation_error(self, operation: str, error: Exception, **kwargs):
        """Log an operation error."""
        context = f" - Context: {kwargs}" if kwargs else ""
        self.logger.error(f"Failed {operation}{context}", exc_info=error)