"""
Status dashboard module for Phase 4 Local Application.

Displays system status in the sidebar showing database, model, and memory status.
"""

import logging
from typing import Optional

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

from src.ui.pipeline_manager import PipelineManager

logger = logging.getLogger(__name__)


def get_status_indicator(status: str) -> str:
    """
    Get emoji indicator for status.
    
    Args:
        status: Status string ('ready', 'loading', 'error')
        
    Returns:
        Emoji indicator: "🟢" for ready, "🟡" for loading, "🔴" for error
    """
    status_map = {
        'ready': '🟢',
        'loading': '🟡',
        'error': '🔴'
    }
    return status_map.get(status.lower(), '⚪')


def format_memory_usage(memory_mb: float) -> str:
    """
    Format memory usage with warning if > 2.5GB.
    
    Args:
        memory_mb: Memory usage in MB
        
    Returns:
        Formatted memory string with warning if needed
    """
    if memory_mb > 2500:
        return f"⚠️ {memory_mb:.0f} MB (Tinggi)"
    return f"{memory_mb:.0f} MB"


def render_status_dashboard(pipeline_manager: PipelineManager) -> None:
    """
    Render status dashboard in sidebar showing:
    - Database status (loaded/not loaded, document count)
    - Model status (ready/loading/error)
    - Memory usage
    - Last update timestamp
    
    Args:
        pipeline_manager: Pipeline manager instance
    """
    if not STREAMLIT_AVAILABLE:
        logger.warning("Streamlit not available, cannot render dashboard")
        return
    
    st.sidebar.header("Status Sistem")
    
    # Get current pipeline status
    status = pipeline_manager.get_status()
    
    # Display database status
    if status.database_loaded:
        db_indicator = get_status_indicator('ready')
        st.sidebar.markdown(f"{db_indicator} **{status.get_database_status_text()}**")
    else:
        db_indicator = get_status_indicator('error')
        st.sidebar.markdown(f"{db_indicator} **Database: Tidak Dimuat**")
    
    # Display model status
    if status.model_loaded:
        model_indicator = get_status_indicator('ready')
        st.sidebar.markdown(f"{model_indicator} **Model: Siap**")
    elif status.error_message:
        model_indicator = get_status_indicator('error')
        st.sidebar.markdown(f"{model_indicator} **Model: Error**")
        with st.sidebar.expander("Detail Error"):
            st.text(status.error_message)
    else:
        model_indicator = get_status_indicator('loading')
        st.sidebar.markdown(f"{model_indicator} **Model: Memuat...**")
    
    # Display memory usage
    memory_text = format_memory_usage(status.memory_usage_mb)
    st.sidebar.markdown(f"💾 **Memori:** {memory_text}")
    
    # Display last update
    st.sidebar.caption(f"Terakhir diperbarui: {status.last_update.strftime('%H:%M:%S')}")
    
    # Add divider
    st.sidebar.divider()
