"""
Subject filter module for Phase 4 Local Application.

Renders subject filter dropdown in sidebar for educational content filtering.
"""

import logging
from typing import Optional

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

logger = logging.getLogger(__name__)


# Available subjects for filtering
SUBJECTS = ["Semua", "Informatika"]


def render_subject_filter() -> str:
    """
    Render subject filter dropdown in sidebar.
    
    Returns:
        Selected subject as string
    """
    if not STREAMLIT_AVAILABLE:
        logger.warning("Streamlit not available, returning default subject")
        return "Semua"
    
    selected_subject = st.selectbox(
        "Pilih Mata Pelajaran:",
        SUBJECTS,
        index=0,
        help="Filter pertanyaan berdasarkan mata pelajaran"
    )
    
    return selected_subject


def map_subject_to_filter(subject: str) -> Optional[str]:
    """
    Map UI subject name to filter value for pipeline.
    
    Args:
        subject: Subject name from UI (e.g., "Semua", "Matematika")
        
    Returns:
        Filter value for pipeline: None for "Semua", lowercase subject name for specific subjects
    """
    if subject == "Semua":
        return None
    
    # Map Indonesian subject names to lowercase for pipeline
    subject_map = {
        "Matematika": "matematika",
        "IPA": "ipa",
        "Bahasa Indonesia": "bahasa_indonesia",
        "Informatika": "informatika"
    }
    
    return subject_map.get(subject, subject.lower())
