"""
Error handler module for Phase 4 Local Application.

Provides Indonesian error messages and recovery suggestions for common failure scenarios.
"""

import logging
from typing import Optional

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

logger = logging.getLogger(__name__)


class ErrorMessages:
    """Indonesian error messages for common failure scenarios."""
    
    EMPTY_DATABASE = "Database kosong. Silakan jalankan pipeline ETL terlebih dahulu."
    MODEL_LOAD_FAILED = "Model gagal dimuat. Periksa file model di {path}."
    QUERY_FAILED = "Terjadi kesalahan. Silakan coba lagi."
    INSUFFICIENT_MEMORY = "Memori tidak cukup. Tutup aplikasi lain dan coba lagi."
    PIPELINE_INIT_FAILED = "Gagal menginisialisasi sistem: {error}"


def get_error_message(error_type: str, **kwargs) -> str:
    """
    Get formatted error message in Indonesian.
    
    Args:
        error_type: Type of error (e.g., 'empty_database', 'model_load_failed')
        **kwargs: Format parameters for the error message
        
    Returns:
        Formatted error message string
    """
    error_map = {
        'empty_database': ErrorMessages.EMPTY_DATABASE,
        'model_load_failed': ErrorMessages.MODEL_LOAD_FAILED,
        'query_failed': ErrorMessages.QUERY_FAILED,
        'insufficient_memory': ErrorMessages.INSUFFICIENT_MEMORY,
        'pipeline_init_failed': ErrorMessages.PIPELINE_INIT_FAILED
    }
    
    message_template = error_map.get(error_type, ErrorMessages.QUERY_FAILED)
    
    try:
        return message_template.format(**kwargs)
    except KeyError as e:
        logger.warning(f"Missing format parameter for error message: {e}")
        return message_template


def display_error(error_message: str, show_details: bool = False) -> None:
    """
    Display error in Streamlit UI with optional details.
    
    Args:
        error_message: Error message to display
        show_details: Whether to show detailed error information
    """
    if not STREAMLIT_AVAILABLE:
        logger.error(f"Error: {error_message}")
        return
    
    st.error(error_message)
    
    if show_details:
        with st.expander("Detail Kesalahan"):
            st.text(error_message)
    
    logger.error(f"Displayed error to user: {error_message}")
