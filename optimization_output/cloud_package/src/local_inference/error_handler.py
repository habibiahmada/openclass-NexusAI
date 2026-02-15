"""
Comprehensive error handling system for OpenClass Nexus AI Phase 3.

This module provides centralized error handling for network errors, model loading
errors, and inference errors with recovery mechanisms as specified in requirements
2.3, 4.4, and 5.4.
"""

import logging
import time
import traceback
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout, HTTPError

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors in the system."""
    NETWORK_ERROR = "network_error"
    MODEL_LOADING_ERROR = "model_loading_error"
    INFERENCE_ERROR = "inference_error"
    MEMORY_ERROR = "memory_error"
    STORAGE_ERROR = "storage_error"
    VALIDATION_ERROR = "validation_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    CRITICAL = "critical"      # System cannot continue
    HIGH = "high"             # Major functionality affected
    MEDIUM = "medium"         # Some functionality affected
    LOW = "low"              # Minor issues, system can continue
    INFO = "info"            # Informational, not really an error


@dataclass
class ErrorContext:
    """Context information for error handling."""
    operation: str
    component: str
    user_query: Optional[str] = None
    model_path: Optional[str] = None
    network_url: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    additional_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.additional_info is None:
            self.additional_info = {}


@dataclass
class ErrorRecoveryResult:
    """Result of error recovery attempt."""
    success: bool
    message: str
    recovery_action: str
    retry_recommended: bool = False
    fallback_available: bool = False
    user_action_required: bool = False
    additional_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.additional_info is None:
            self.additional_info = {}


class NetworkErrorHandler:
    """Handles network-related errors with recovery mechanisms."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize network error handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay for exponential backoff (seconds)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        
    def handle_download_error(
        self, 
        error: Exception, 
        context: ErrorContext,
        retry_count: int = 0
    ) -> ErrorRecoveryResult:
        """
        Handle download errors with automatic retry and recovery.
        
        Args:
            error: The exception that occurred
            context: Error context information
            retry_count: Current retry attempt number
            
        Returns:
            ErrorRecoveryResult with recovery information
        """
        logger.error(f"Download error in {context.operation}: {error}")
        
        # Determine error type and appropriate recovery
        if isinstance(error, ConnectionError):
            return self._handle_connection_error(error, context, retry_count)
        elif isinstance(error, Timeout):
            return self._handle_timeout_error(error, context, retry_count)
        elif isinstance(error, HTTPError):
            return self._handle_http_error(error, context, retry_count)
        elif isinstance(error, RequestException):
            return self._handle_request_error(error, context, retry_count)
        else:
            return self._handle_unknown_network_error(error, context, retry_count)
    
    def _handle_connection_error(
        self, 
        error: ConnectionError, 
        context: ErrorContext, 
        retry_count: int
    ) -> ErrorRecoveryResult:
        """Handle connection errors."""
        if retry_count < self.max_retries:
            delay = self.base_delay * (2 ** retry_count)  # Exponential backoff
            
            logger.info(f"Connection error, retrying in {delay} seconds (attempt {retry_count + 1}/{self.max_retries})")
            time.sleep(delay)
            
            return ErrorRecoveryResult(
                success=False,
                message=f"Koneksi terputus. Mencoba lagi dalam {delay} detik...",
                recovery_action="retry_with_backoff",
                retry_recommended=True,
                additional_info={"delay_seconds": delay, "retry_count": retry_count + 1}
            )
        else:
            return ErrorRecoveryResult(
                success=False,
                message="Tidak dapat terhubung ke server setelah beberapa percobaan. Periksa koneksi internet Anda.",
                recovery_action="manual_intervention_required",
                user_action_required=True,
                fallback_available=True,
                additional_info={"max_retries_exceeded": True}
            )
    
    def _handle_timeout_error(
        self, 
        error: Timeout, 
        context: ErrorContext, 
        retry_count: int
    ) -> ErrorRecoveryResult:
        """Handle timeout errors."""
        if retry_count < self.max_retries:
            # Increase timeout for retry
            delay = self.base_delay * (retry_count + 1)
            
            return ErrorRecoveryResult(
                success=False,
                message=f"Koneksi timeout. Mencoba lagi dengan timeout yang lebih lama...",
                recovery_action="retry_with_increased_timeout",
                retry_recommended=True,
                additional_info={"increased_timeout": True, "delay_seconds": delay}
            )
        else:
            return ErrorRecoveryResult(
                success=False,
                message="Server tidak merespons. Coba lagi nanti atau gunakan model yang sudah ada.",
                recovery_action="use_cached_model",
                fallback_available=True,
                user_action_required=True
            )
    
    def _handle_http_error(
        self, 
        error: HTTPError, 
        context: ErrorContext, 
        retry_count: int
    ) -> ErrorRecoveryResult:
        """Handle HTTP errors."""
        status_code = error.response.status_code if error.response else 0
        
        if status_code == 404:
            return ErrorRecoveryResult(
                success=False,
                message="Model tidak ditemukan di server. Periksa konfigurasi model.",
                recovery_action="check_model_configuration",
                user_action_required=True,
                additional_info={"status_code": status_code}
            )
        elif status_code == 403:
            return ErrorRecoveryResult(
                success=False,
                message="Akses ditolak. Periksa token HuggingFace atau izin akses.",
                recovery_action="check_authentication",
                user_action_required=True,
                additional_info={"status_code": status_code}
            )
        elif status_code == 429:
            # Rate limited
            if retry_count < self.max_retries:
                delay = self.base_delay * (2 ** (retry_count + 2))  # Longer delay for rate limits
                
                return ErrorRecoveryResult(
                    success=False,
                    message=f"Terlalu banyak permintaan. Menunggu {delay} detik sebelum mencoba lagi...",
                    recovery_action="retry_with_rate_limit_backoff",
                    retry_recommended=True,
                    additional_info={"delay_seconds": delay, "rate_limited": True}
                )
            else:
                return ErrorRecoveryResult(
                    success=False,
                    message="Server sibuk. Coba lagi nanti.",
                    recovery_action="try_later",
                    user_action_required=True,
                    additional_info={"status_code": status_code}
                )
        elif 500 <= status_code < 600:
            # Server error
            if retry_count < self.max_retries:
                delay = self.base_delay * (retry_count + 1)
                
                return ErrorRecoveryResult(
                    success=False,
                    message=f"Server error. Mencoba lagi dalam {delay} detik...",
                    recovery_action="retry_server_error",
                    retry_recommended=True,
                    additional_info={"delay_seconds": delay, "server_error": True}
                )
            else:
                return ErrorRecoveryResult(
                    success=False,
                    message="Server mengalami masalah. Coba lagi nanti.",
                    recovery_action="server_maintenance",
                    user_action_required=True,
                    fallback_available=True
                )
        else:
            return ErrorRecoveryResult(
                success=False,
                message=f"HTTP error {status_code}. Periksa koneksi dan coba lagi.",
                recovery_action="generic_http_error",
                retry_recommended=retry_count < self.max_retries,
                additional_info={"status_code": status_code}
            )
    
    def _handle_request_error(
        self, 
        error: RequestException, 
        context: ErrorContext, 
        retry_count: int
    ) -> ErrorRecoveryResult:
        """Handle general request errors."""
        return ErrorRecoveryResult(
            success=False,
            message=f"Error dalam permintaan jaringan: {str(error)}",
            recovery_action="generic_network_error",
            retry_recommended=retry_count < self.max_retries,
            additional_info={"error_type": type(error).__name__}
        )
    
    def _handle_unknown_network_error(
        self, 
        error: Exception, 
        context: ErrorContext, 
        retry_count: int
    ) -> ErrorRecoveryResult:
        """Handle unknown network errors."""
        logger.error(f"Unknown network error: {error}\n{traceback.format_exc()}")
        
        return ErrorRecoveryResult(
            success=False,
            message="Terjadi kesalahan jaringan yang tidak dikenal. Periksa koneksi internet.",
            recovery_action="unknown_network_error",
            retry_recommended=retry_count < 1,  # Only retry once for unknown errors
            user_action_required=True,
            additional_info={"error_type": type(error).__name__, "error_message": str(error)}
        )


class ModelLoadingErrorHandler:
    """Handles model loading errors with recovery mechanisms."""
    
    def handle_model_loading_error(
        self, 
        error: Exception, 
        context: ErrorContext
    ) -> ErrorRecoveryResult:
        """
        Handle model loading errors.
        
        Args:
            error: The exception that occurred
            context: Error context information
            
        Returns:
            ErrorRecoveryResult with recovery information
        """
        logger.error(f"Model loading error in {context.operation}: {error}")
        
        # Check error type and provide appropriate recovery
        if "memory" in str(error).lower() or "oom" in str(error).lower():
            return self._handle_memory_error(error, context)
        elif "file not found" in str(error).lower() or "no such file" in str(error).lower():
            return self._handle_file_not_found_error(error, context)
        elif "corrupted" in str(error).lower() or "invalid" in str(error).lower():
            return self._handle_corrupted_model_error(error, context)
        elif "permission" in str(error).lower() or "access" in str(error).lower():
            return self._handle_permission_error(error, context)
        else:
            return self._handle_unknown_model_error(error, context)
    
    def _handle_memory_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle memory-related model loading errors."""
        return ErrorRecoveryResult(
            success=False,
            message="Tidak cukup memori untuk memuat model. Sistem akan mengoptimalkan penggunaan memori.",
            recovery_action="optimize_memory_usage",
            retry_recommended=True,
            additional_info={
                "memory_optimization_needed": True,
                "suggested_actions": [
                    "Tutup aplikasi lain yang tidak diperlukan",
                    "Gunakan konfigurasi model yang lebih ringan",
                    "Restart aplikasi untuk membersihkan memori"
                ]
            }
        )
    
    def _handle_file_not_found_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle file not found errors."""
        model_path = context.model_path or "unknown"
        
        return ErrorRecoveryResult(
            success=False,
            message=f"File model tidak ditemukan: {model_path}. Model perlu diunduh ulang.",
            recovery_action="redownload_model",
            retry_recommended=True,
            user_action_required=True,
            additional_info={
                "missing_file": model_path,
                "suggested_actions": [
                    "Download model dari HuggingFace",
                    "Periksa path konfigurasi model",
                    "Pastikan model sudah selesai diunduh"
                ]
            }
        )
    
    def _handle_corrupted_model_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle corrupted model file errors."""
        model_path = context.model_path or "unknown"
        
        return ErrorRecoveryResult(
            success=False,
            message=f"File model rusak atau tidak valid: {model_path}. Model perlu diunduh ulang.",
            recovery_action="redownload_corrupted_model",
            retry_recommended=True,
            user_action_required=True,
            additional_info={
                "corrupted_file": model_path,
                "suggested_actions": [
                    "Hapus file model yang rusak",
                    "Download ulang model dari sumber resmi",
                    "Verifikasi checksum file model"
                ]
            }
        )
    
    def _handle_permission_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle permission errors."""
        return ErrorRecoveryResult(
            success=False,
            message="Tidak memiliki izin untuk mengakses file model. Periksa izin file dan folder.",
            recovery_action="fix_file_permissions",
            user_action_required=True,
            additional_info={
                "permission_issue": True,
                "suggested_actions": [
                    "Periksa izin folder models/",
                    "Jalankan aplikasi dengan izin yang sesuai",
                    "Pastikan file tidak sedang digunakan aplikasi lain"
                ]
            }
        )
    
    def _handle_unknown_model_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle unknown model loading errors."""
        logger.error(f"Unknown model loading error: {error}\n{traceback.format_exc()}")
        
        return ErrorRecoveryResult(
            success=False,
            message=f"Terjadi kesalahan saat memuat model: {str(error)}",
            recovery_action="unknown_model_error",
            retry_recommended=False,
            user_action_required=True,
            additional_info={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "suggested_actions": [
                    "Periksa log aplikasi untuk detail error",
                    "Coba restart aplikasi",
                    "Hubungi support jika masalah berlanjut"
                ]
            }
        )


class InferenceErrorHandler:
    """Handles inference errors with recovery mechanisms."""
    
    def handle_inference_error(
        self, 
        error: Exception, 
        context: ErrorContext
    ) -> ErrorRecoveryResult:
        """
        Handle inference errors.
        
        Args:
            error: The exception that occurred
            context: Error context information
            
        Returns:
            ErrorRecoveryResult with recovery information
        """
        logger.error(f"Inference error in {context.operation}: {error}")
        
        # Check error type and provide appropriate recovery
        if "memory" in str(error).lower() or "oom" in str(error).lower():
            return self._handle_inference_memory_error(error, context)
        elif "timeout" in str(error).lower():
            return self._handle_inference_timeout_error(error, context)
        elif "context" in str(error).lower() and "too long" in str(error).lower():
            return self._handle_context_overflow_error(error, context)
        elif "model not loaded" in str(error).lower():
            return self._handle_model_not_loaded_error(error, context)
        else:
            return self._handle_unknown_inference_error(error, context)
    
    def _handle_inference_memory_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle memory errors during inference."""
        return ErrorRecoveryResult(
            success=False,
            message="Tidak cukup memori untuk menghasilkan respons. Mengurangi panjang konteks.",
            recovery_action="reduce_context_length",
            retry_recommended=True,
            additional_info={
                "memory_optimization": True,
                "context_reduction_needed": True,
                "suggested_actions": [
                    "Kurangi panjang pertanyaan",
                    "Gunakan konteks yang lebih pendek",
                    "Restart aplikasi jika diperlukan"
                ]
            }
        )
    
    def _handle_inference_timeout_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle timeout errors during inference."""
        return ErrorRecoveryResult(
            success=False,
            message="Waktu pemrosesan terlalu lama. Mencoba dengan pengaturan yang lebih cepat.",
            recovery_action="optimize_inference_speed",
            retry_recommended=True,
            additional_info={
                "timeout_occurred": True,
                "speed_optimization_needed": True,
                "suggested_actions": [
                    "Gunakan pertanyaan yang lebih sederhana",
                    "Kurangi panjang respons maksimum",
                    "Periksa beban sistem"
                ]
            }
        )
    
    def _handle_context_overflow_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle context window overflow errors."""
        return ErrorRecoveryResult(
            success=False,
            message="Konteks terlalu panjang untuk model. Memotong konteks secara otomatis.",
            recovery_action="truncate_context",
            retry_recommended=True,
            additional_info={
                "context_overflow": True,
                "truncation_needed": True,
                "suggested_actions": [
                    "Gunakan pertanyaan yang lebih spesifik",
                    "Kurangi jumlah dokumen referensi",
                    "Fokus pada topik yang lebih sempit"
                ]
            }
        )
    
    def _handle_model_not_loaded_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle model not loaded errors."""
        return ErrorRecoveryResult(
            success=False,
            message="Model belum dimuat. Memuat model secara otomatis.",
            recovery_action="load_model",
            retry_recommended=True,
            additional_info={
                "model_loading_needed": True,
                "suggested_actions": [
                    "Tunggu proses loading model selesai",
                    "Pastikan model tersedia di sistem",
                    "Periksa konfigurasi model"
                ]
            }
        )
    
    def _handle_unknown_inference_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle unknown inference errors."""
        logger.error(f"Unknown inference error: {error}\n{traceback.format_exc()}")
        
        return ErrorRecoveryResult(
            success=False,
            message="Terjadi kesalahan saat menghasilkan respons. Menggunakan respons fallback.",
            recovery_action="use_fallback_response",
            retry_recommended=False,
            fallback_available=True,
            additional_info={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "fallback_response": "Maaf, saya tidak dapat memproses pertanyaan Anda saat ini. Silakan coba lagi atau hubungi guru untuk bantuan."
            }
        )


class ComprehensiveErrorHandler:
    """
    Comprehensive error handler combining all error handling capabilities.
    
    This class provides centralized error handling for the entire local inference
    system with automatic recovery mechanisms and user-friendly error messages.
    """
    
    def __init__(self):
        """Initialize the comprehensive error handler."""
        self.network_handler = NetworkErrorHandler()
        self.model_handler = ModelLoadingErrorHandler()
        self.inference_handler = InferenceErrorHandler()
        
        # Error statistics
        self.error_counts = {category.value: 0 for category in ErrorCategory}
        self.recovery_success_counts = {category.value: 0 for category in ErrorCategory}
        
        logger.info("Initialized ComprehensiveErrorHandler")
    
    def handle_error(
        self, 
        error: Exception, 
        category: ErrorCategory, 
        context: ErrorContext,
        retry_count: int = 0
    ) -> ErrorRecoveryResult:
        """
        Handle any error with appropriate recovery mechanism.
        
        Args:
            error: The exception that occurred
            category: Category of the error
            context: Error context information
            retry_count: Current retry attempt number
            
        Returns:
            ErrorRecoveryResult with recovery information
        """
        # Update error statistics
        self.error_counts[category.value] += 1
        
        logger.error(f"Handling {category.value} error: {error}")
        
        try:
            # Route to appropriate handler
            if category == ErrorCategory.NETWORK_ERROR:
                result = self.network_handler.handle_download_error(error, context, retry_count)
            elif category == ErrorCategory.MODEL_LOADING_ERROR:
                result = self.model_handler.handle_model_loading_error(error, context)
            elif category == ErrorCategory.INFERENCE_ERROR:
                result = self.inference_handler.handle_inference_error(error, context)
            elif category == ErrorCategory.MEMORY_ERROR:
                result = self._handle_memory_error(error, context)
            elif category == ErrorCategory.STORAGE_ERROR:
                result = self._handle_storage_error(error, context)
            elif category == ErrorCategory.VALIDATION_ERROR:
                result = self._handle_validation_error(error, context)
            elif category == ErrorCategory.CONFIGURATION_ERROR:
                result = self._handle_configuration_error(error, context)
            else:
                result = self._handle_unknown_error(error, context)
            
            # Update recovery statistics
            if result.success:
                self.recovery_success_counts[category.value] += 1
            
            return result
            
        except Exception as handler_error:
            logger.error(f"Error in error handler: {handler_error}\n{traceback.format_exc()}")
            
            # Return a safe fallback result
            return ErrorRecoveryResult(
                success=False,
                message="Terjadi kesalahan sistem. Silakan restart aplikasi.",
                recovery_action="system_restart_required",
                user_action_required=True,
                additional_info={
                    "handler_error": str(handler_error),
                    "original_error": str(error)
                }
            )
    
    def _handle_memory_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle memory-related errors."""
        return ErrorRecoveryResult(
            success=False,
            message="Sistem kehabisan memori. Mengoptimalkan penggunaan memori.",
            recovery_action="memory_cleanup",
            retry_recommended=True,
            additional_info={
                "memory_cleanup_needed": True,
                "current_memory_mb": context.memory_usage_mb,
                "suggested_actions": [
                    "Tutup aplikasi lain",
                    "Restart aplikasi",
                    "Gunakan konfigurasi yang lebih ringan"
                ]
            }
        )
    
    def _handle_storage_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle storage-related errors."""
        return ErrorRecoveryResult(
            success=False,
            message="Masalah dengan penyimpanan file. Periksa ruang disk dan izin akses.",
            recovery_action="check_storage",
            user_action_required=True,
            additional_info={
                "storage_issue": True,
                "suggested_actions": [
                    "Periksa ruang disk tersedia",
                    "Periksa izin folder",
                    "Bersihkan file temporary"
                ]
            }
        )
    
    def _handle_validation_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle validation errors."""
        return ErrorRecoveryResult(
            success=False,
            message=f"Error validasi: {str(error)}",
            recovery_action="fix_validation_issue",
            user_action_required=True,
            additional_info={
                "validation_failed": True,
                "error_details": str(error)
            }
        )
    
    def _handle_configuration_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle configuration errors."""
        return ErrorRecoveryResult(
            success=False,
            message="Masalah konfigurasi sistem. Periksa pengaturan aplikasi.",
            recovery_action="check_configuration",
            user_action_required=True,
            additional_info={
                "configuration_issue": True,
                "suggested_actions": [
                    "Periksa file konfigurasi",
                    "Reset ke pengaturan default",
                    "Periksa variabel environment"
                ]
            }
        )
    
    def _handle_unknown_error(self, error: Exception, context: ErrorContext) -> ErrorRecoveryResult:
        """Handle unknown errors."""
        logger.error(f"Unknown error: {error}\n{traceback.format_exc()}")
        
        return ErrorRecoveryResult(
            success=False,
            message="Terjadi kesalahan yang tidak dikenal. Silakan coba lagi atau hubungi support.",
            recovery_action="unknown_error_fallback",
            user_action_required=True,
            fallback_available=True,
            additional_info={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stack_trace": traceback.format_exc()
            }
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error handling statistics.
        
        Returns:
            Dictionary with error statistics
        """
        total_errors = sum(self.error_counts.values())
        total_recoveries = sum(self.recovery_success_counts.values())
        
        return {
            'total_errors': total_errors,
            'total_successful_recoveries': total_recoveries,
            'recovery_rate': total_recoveries / total_errors if total_errors > 0 else 0.0,
            'errors_by_category': self.error_counts.copy(),
            'recoveries_by_category': self.recovery_success_counts.copy(),
            'most_common_error': max(self.error_counts, key=self.error_counts.get) if total_errors > 0 else None
        }
    
    def reset_statistics(self) -> None:
        """Reset error handling statistics."""
        self.error_counts = {category.value: 0 for category in ErrorCategory}
        self.recovery_success_counts = {category.value: 0 for category in ErrorCategory}
        logger.info("Reset error handling statistics")


# Convenience functions for common error handling scenarios

def handle_network_error(
    error: Exception, 
    operation: str, 
    url: Optional[str] = None,
    retry_count: int = 0
) -> ErrorRecoveryResult:
    """
    Convenience function for handling network errors.
    
    Args:
        error: The network error
        operation: Description of the operation that failed
        url: URL that caused the error (optional)
        retry_count: Current retry count
        
    Returns:
        ErrorRecoveryResult with recovery information
    """
    handler = ComprehensiveErrorHandler()
    context = ErrorContext(
        operation=operation,
        component="network",
        network_url=url
    )
    
    return handler.handle_error(error, ErrorCategory.NETWORK_ERROR, context, retry_count)


def handle_model_error(
    error: Exception, 
    operation: str, 
    model_path: Optional[str] = None
) -> ErrorRecoveryResult:
    """
    Convenience function for handling model loading errors.
    
    Args:
        error: The model loading error
        operation: Description of the operation that failed
        model_path: Path to the model file (optional)
        
    Returns:
        ErrorRecoveryResult with recovery information
    """
    handler = ComprehensiveErrorHandler()
    context = ErrorContext(
        operation=operation,
        component="model_loader",
        model_path=model_path
    )
    
    return handler.handle_error(error, ErrorCategory.MODEL_LOADING_ERROR, context)


def handle_inference_error(
    error: Exception, 
    operation: str, 
    query: Optional[str] = None,
    memory_usage: Optional[float] = None
) -> ErrorRecoveryResult:
    """
    Convenience function for handling inference errors.
    
    Args:
        error: The inference error
        operation: Description of the operation that failed
        query: User query that caused the error (optional)
        memory_usage: Current memory usage in MB (optional)
        
    Returns:
        ErrorRecoveryResult with recovery information
    """
    handler = ComprehensiveErrorHandler()
    context = ErrorContext(
        operation=operation,
        component="inference_engine",
        user_query=query,
        memory_usage_mb=memory_usage
    )
    
    return handler.handle_error(error, ErrorCategory.INFERENCE_ERROR, context)