"""
Data models for Phase 4 Local Application.

Defines dataclasses for chat messages, source citations, and pipeline status.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class SourceCitation:
    """Represents a source citation for an assistant response."""
    
    filename: str
    subject: str
    relevance_score: float
    chunk_index: int
    
    def format_citation(self) -> str:
        """
        Format as: 📚 [Subject] - [Filename] (Relevance: [Score])
        
        Returns:
            Formatted citation string
        """
        return f"📚 {self.subject} - {self.filename} (Relevance: {self.relevance_score:.2f})"


@dataclass
class ChatMessage:
    """Represents a single message in the chat history."""
    
    role: str  # "user" or "assistant"
    content: str
    sources: List[SourceCitation] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time_ms: Optional[float] = None


@dataclass
class PipelineStatus:
    """Represents the current status of the pipeline for dashboard display."""
    
    database_loaded: bool
    database_document_count: int
    model_loaded: bool
    memory_usage_mb: float
    last_update: datetime
    error_message: Optional[str] = None
    
    def get_database_status_text(self) -> str:
        """
        Returns: 'Database: Loaded (N documents)' or 'Database: Not Loaded'
        """
        if self.database_loaded:
            return f"Database: Loaded ({self.database_document_count} documents)"
        return "Database: Not Loaded"
    
    def get_model_status_text(self) -> str:
        """
        Returns: 'Model: Ready' or 'Model: Loading' or 'Model: Error'
        """
        if self.error_message:
            return "Model: Error"
        if self.model_loaded:
            return "Model: Ready"
        return "Model: Loading"
    
    def has_memory_warning(self) -> bool:
        """
        Returns True if memory usage > 2.5GB
        """
        return self.memory_usage_mb > 2500
