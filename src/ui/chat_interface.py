"""
Chat interface module for Phase 4 Local Application.

Renders the chat UI with message history and input handling.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

from src.ui.pipeline_manager import PipelineManager
from src.ui.models import ChatMessage, SourceCitation
from src.ui.error_handler import display_error, get_error_message

logger = logging.getLogger(__name__)


def display_sources(sources: List[SourceCitation]) -> None:
    """
    Display source citations below a message.
    
    Args:
        sources: List of source citations
    """
    if not STREAMLIT_AVAILABLE or not sources:
        return
    
    st.markdown("**Sumber:**")
    for source in sources:
        st.caption(source.format_citation())


def display_message(message: ChatMessage) -> None:
    """
    Display a single chat message with role-based styling.
    
    Args:
        message: ChatMessage to display
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    if message.role == "user":
        with st.chat_message("user"):
            st.markdown(message.content)
    else:
        with st.chat_message("assistant"):
            st.markdown(message.content)
            
            # Display sources if available
            if message.sources:
                display_sources(message.sources)
            
            # Display processing time if available
            if message.processing_time_ms:
                st.caption(f"⏱️ Waktu proses: {message.processing_time_ms:.0f}ms")


def stream_response(
    query: str,
    pipeline_manager: PipelineManager,
    subject_filter: str
) -> ChatMessage:
    """
    Stream response from pipeline and return complete message.
    
    Args:
        query: User question
        pipeline_manager: Pipeline manager for query processing
        subject_filter: Current subject filter selection
        
    Returns:
        ChatMessage with complete response and filter info
    """
    start_time = time.time()
    
    try:
        # Map subject filter to pipeline format
        from src.ui.subject_filter import map_subject_to_filter
        filter_value = map_subject_to_filter(subject_filter)
        
        # Process query and collect response
        response_chunks = []
        for chunk in pipeline_manager.process_query(query, filter_value):
            response_chunks.append(chunk)
        
        response_text = ''.join(response_chunks)
        
        # Add filter info to response if not "Semua"
        if subject_filter != "Semua":
            response_text = f"*[Filter: {subject_filter}]*\n\n{response_text}"
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Extract sources from pipeline result
        # For now, we'll create a simple message without sources
        # In a full implementation, we'd extract sources from the QueryResult
        sources = []
        
        return ChatMessage(
            role="assistant",
            content=response_text,
            sources=sources,
            timestamp=datetime.now(),
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        logger.error(f"Error streaming response: {e}")
        error_msg = get_error_message('query_failed')
        return ChatMessage(
            role="assistant",
            content=error_msg,
            sources=[],
            timestamp=datetime.now(),
            processing_time_ms=(time.time() - start_time) * 1000
        )


def render_chat_interface(
    chat_history: List[ChatMessage],
    pipeline_manager: PipelineManager,
    subject_filter: str
) -> None:
    """
    Render the chat interface with message history and input.
    
    Args:
        chat_history: List of chat messages
        pipeline_manager: Pipeline manager for query processing
        subject_filter: Current subject filter selection
    """
    if not STREAMLIT_AVAILABLE:
        logger.warning("Streamlit not available, cannot render chat interface")
        return
    
    # Display chat history
    for message in chat_history:
        display_message(message)
    
    # Chat input
    if prompt := st.chat_input("Tanyakan sesuatu..."):
        # Display user message immediately
        user_message = ChatMessage(
            role="user",
            content=prompt,
            timestamp=datetime.now()
        )
        chat_history.append(user_message)
        display_message(user_message)
        
        # Check if pipeline is initialized
        if pipeline_manager.get_pipeline() is None:
            with st.spinner("Menginisialisasi sistem..."):
                if not pipeline_manager.initialize_pipeline():
                    error_msg = get_error_message(
                        'pipeline_init_failed',
                        error=pipeline_manager.initialization_error or "Unknown error"
                    )
                    display_error(error_msg)
                    return
        
        # Generate and display response
        with st.chat_message("assistant"):
            with st.spinner("Sedang berpikir..."):
                assistant_message = stream_response(prompt, pipeline_manager, subject_filter)
            
            st.markdown(assistant_message.content)
            
            if assistant_message.sources:
                display_sources(assistant_message.sources)
            
            if assistant_message.processing_time_ms:
                st.caption(f"⏱️ Waktu proses: {assistant_message.processing_time_ms:.0f}ms")
        
        # Add assistant message to history
        chat_history.append(assistant_message)
