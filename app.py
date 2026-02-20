"""
OpenClass Nexus AI - Local Application (Phase 4)

Streamlit-based user interface for the offline AI tutor system.
This application integrates with existing Phase 1-3 components to provide
an interactive chat interface for Indonesian educational content.
"""

import logging
import streamlit as st

from src.ui.pipeline_manager import PipelineManager
from src.ui.chat_interface import render_chat_interface
from src.ui.status_dashboard import render_status_dashboard
from src.ui.subject_filter import render_subject_filter
from src.ui.models import ChatMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'pipeline_manager' not in st.session_state:
        st.session_state.pipeline_manager = PipelineManager()
    
    if 'current_subject_filter' not in st.session_state:
        st.session_state.current_subject_filter = "Semua"


def main():
    """Main application entry point."""
    # Set page configuration
    st.set_page_config(
        page_title="OpenClass Nexus AI - Tutor Offline",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Display application title
    st.title("OpenClass Nexus AI - Tutor Offline")
    st.caption("Asisten AI untuk pendidikan Indonesia - Bekerja sepenuhnya offline")
    
    # Render sidebar components
    with st.sidebar:
        # Status dashboard
        render_status_dashboard(st.session_state.pipeline_manager)
        
        # Subject filter
        st.header("Filter")
        selected_subject = render_subject_filter()
        st.session_state.current_subject_filter = selected_subject
        
        # Display active filter
        if selected_subject != "Semua":
            st.info(f"Filter aktif: {selected_subject}")
    
    # Render chat interface in main area
    render_chat_interface(
        chat_history=st.session_state.chat_history,
        pipeline_manager=st.session_state.pipeline_manager,
        subject_filter=st.session_state.current_subject_filter
    )


if __name__ == "__main__":
    main()
