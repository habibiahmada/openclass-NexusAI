"""
Context management for RAG pipeline with token limit optimization.

This module provides functionality to manage context within token limits
for the Llama-3.2-3B-Instruct model, including document ranking for
educational relevance and intelligent context fitting.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from src.embeddings.chroma_manager import SearchResult
from .graceful_degradation import GracefulDegradationManager


logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Document representation for context management."""
    text: str
    metadata: Dict[str, Any]
    relevance_score: float
    token_count: int = 0
    
    def __post_init__(self):
        """Calculate token count after initialization."""
        if self.token_count == 0:
            self.token_count = self._estimate_tokens(self.text)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using simple heuristic."""
        # Rough approximation: 1 token ≈ 4 characters for Indonesian text
        return len(text) // 4


class ContextManager:
    """
    Manages context fitting within token limits for educational queries.
    
    This class is optimized for Llama-3.2-3B-Instruct with 4096 token context window,
    providing intelligent document ranking and context fitting for Indonesian
    educational content.
    """
    
    def __init__(self, max_context_tokens: int = 3000, 
                 degradation_manager: Optional[GracefulDegradationManager] = None):
        """
        Initialize context manager.
        
        Args:
            max_context_tokens: Maximum tokens for context (leaving room for query and response)
            degradation_manager: Optional graceful degradation manager for dynamic adjustments
        """
        self.base_max_context_tokens = max_context_tokens
        self.max_context_tokens = max_context_tokens
        self.degradation_manager = degradation_manager
        self.educational_keywords = self._load_educational_keywords()
        
        logger.info(f"Initialized ContextManager with max_context_tokens: {max_context_tokens}")
    
    def fit_context(self, documents: List[SearchResult], query: str) -> Tuple[str, List[Document]]:
        """
        Fit documents within token limit while preserving educational quality.
        
        Args:
            documents: List of search results from ChromaDB
            query: Original user query for relevance ranking
            
        Returns:
            Tuple of (formatted_context, selected_documents)
        """
        if not documents:
            return "", []
        
        # Update max context tokens based on degradation level
        self._update_context_limit()
        
        # Convert SearchResults to Documents
        doc_objects = []
        for doc in documents:
            doc_obj = Document(
                text=doc.text,
                metadata=doc.metadata,
                relevance_score=doc.similarity_score
            )
            doc_objects.append(doc_obj)
        
        # Rank documents by educational relevance
        ranked_docs = self.rank_documents(doc_objects, query)
        
        # Select documents that fit within token limit
        selected_docs = self._select_documents_by_tokens(ranked_docs)
        
        # Format context for educational prompt
        formatted_context = self._format_educational_context(selected_docs)
        
        logger.debug(f"Selected {len(selected_docs)} documents with {self._count_tokens(formatted_context)} tokens "
                    f"(limit: {self.max_context_tokens})")
        
        return formatted_context, selected_docs
    
    def rank_documents(self, documents: List[Document], query: str) -> List[Document]:
        """
        Rank documents by relevance for educational queries.
        
        Ranking considers:
        1. Similarity score from vector search
        2. Educational keyword relevance
        3. Subject matter alignment
        4. Grade level appropriateness
        
        Args:
            documents: List of documents to rank
            query: User query for context
            
        Returns:
            List of documents sorted by educational relevance
        """
        if not documents:
            return []
        
        # Calculate educational relevance scores
        for doc in documents:
            educational_score = self._calculate_educational_relevance(doc, query)
            # Combine similarity score with educational relevance
            doc.relevance_score = (doc.relevance_score * 0.7) + (educational_score * 0.3)
        
        # Sort by combined relevance score
        ranked = sorted(documents, key=lambda d: d.relevance_score, reverse=True)
        
        logger.debug(f"Ranked {len(ranked)} documents by educational relevance")
        return ranked
    
    def _calculate_educational_relevance(self, document: Document, query: str) -> float:
        """
        Calculate educational relevance score for a document.
        
        Args:
            document: Document to score
            query: User query
            
        Returns:
            Educational relevance score (0.0 to 1.0)
        """
        score = 0.0
        text_lower = document.text.lower()
        query_lower = query.lower()
        
        # Keyword matching bonus
        query_words = set(query_lower.split())
        text_words = set(text_lower.split())
        word_overlap = len(query_words.intersection(text_words))
        if len(query_words) > 0:
            score += (word_overlap / len(query_words)) * 0.3
        
        # Educational keyword bonus
        educational_matches = 0
        for keyword in self.educational_keywords:
            if keyword in text_lower:
                educational_matches += 1
        
        if educational_matches > 0:
            score += min(educational_matches / 10, 0.3)  # Cap at 0.3
        
        # Subject consistency bonus
        subject = document.metadata.get('subject', '').lower()
        if subject and subject in query_lower:
            score += 0.2
        
        # Grade level appropriateness (prefer current grade level)
        grade = document.metadata.get('grade', '')
        if 'kelas_10' in grade:  # Assuming target is grade 10
            score += 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _update_context_limit(self) -> None:
        """Update context limit based on degradation manager if available."""
        if self.degradation_manager:
            adjustments = self.degradation_manager.get_inference_config_adjustments()
            new_limit = adjustments.get('max_context_tokens', self.base_max_context_tokens)
            
            if new_limit != self.max_context_tokens:
                logger.info(f"Context limit adjusted due to degradation: "
                           f"{self.max_context_tokens} -> {new_limit} tokens")
                self.max_context_tokens = new_limit
    
    def _select_documents_by_tokens(self, documents: List[Document]) -> List[Document]:
        """
        Select documents that fit within token limit.
        
        Args:
            documents: Ranked documents
            
        Returns:
            List of selected documents within token limit
        """
        selected = []
        total_tokens = 0
        
        for doc in documents:
            if total_tokens + doc.token_count <= self.max_context_tokens:
                selected.append(doc)
                total_tokens += doc.token_count
            else:
                # Try to fit a truncated version
                remaining_tokens = self.max_context_tokens - total_tokens
                if remaining_tokens > 100:  # Only if we have meaningful space
                    truncated_text = self._truncate_text(doc.text, remaining_tokens)
                    if truncated_text:
                        truncated_doc = Document(
                            text=truncated_text,
                            metadata=doc.metadata,
                            relevance_score=doc.relevance_score
                        )
                        selected.append(truncated_doc)
                break
        
        return selected
    
    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """
        Intelligently truncate text to fit token limit.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens allowed
            
        Returns:
            Truncated text or empty string if too short
        """
        if max_tokens < 50:  # Not worth truncating for very small limits
            return ""
        
        # Estimate character limit (4 chars per token)
        max_chars = max_tokens * 4
        
        if len(text) <= max_chars:
            return text
        
        # Try to truncate at sentence boundary
        truncated = text[:max_chars]
        
        # Find last sentence ending
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        last_sentence_end = -1
        
        for ending in sentence_endings:
            pos = truncated.rfind(ending)
            if pos > last_sentence_end:
                last_sentence_end = pos + len(ending) - 1
        
        if last_sentence_end > max_chars * 0.7:  # If we found a good break point
            return truncated[:last_sentence_end + 1]
        else:
            # Fallback to word boundary
            words = truncated.split()
            return ' '.join(words[:-1]) + '...'
    
    def _format_educational_context(self, documents: List[Document]) -> str:
        """
        Format selected documents into educational context.
        
        Args:
            documents: Selected documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            # Add source attribution
            source = doc.metadata.get('source_file', 'Unknown')
            subject = doc.metadata.get('subject', 'Unknown')
            grade = doc.metadata.get('grade', 'Unknown')
            
            context_part = f"[Sumber {i}: {source} - {subject.title()} {grade.replace('_', ' ').title()}]\n"
            context_part += doc.text.strip()
            context_part += "\n"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text using simple estimation.
        
        Args:
            text: Text to count
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def _load_educational_keywords(self) -> List[str]:
        """
        Load educational keywords for relevance scoring.
        
        Returns:
            List of educational keywords in Indonesian
        """
        return [
            # General educational terms
            'pembelajaran', 'materi', 'pelajaran', 'bab', 'subbab',
            'definisi', 'pengertian', 'konsep', 'teori', 'prinsip',
            'contoh', 'latihan', 'soal', 'jawaban', 'penjelasan',
            'rumus', 'formula', 'metode', 'cara', 'langkah',
            
            # Subject-specific terms
            'matematika', 'fisika', 'kimia', 'biologi', 'informatika',
            'sejarah', 'geografi', 'ekonomi', 'sosiologi', 'bahasa',
            
            # Educational levels
            'sma', 'smk', 'kelas', 'semester', 'kurikulum',
            
            # Learning activities
            'diskusi', 'praktikum', 'eksperimen', 'observasi', 'analisis',
            'evaluasi', 'refleksi', 'presentasi', 'proyek', 'tugas'
        ]
    
    def get_context_stats(self, context: str, documents: List[Document]) -> Dict[str, Any]:
        """
        Get statistics about the context.
        
        Args:
            context: Formatted context string
            documents: Selected documents
            
        Returns:
            Dictionary with context statistics
        """
        return {
            'total_documents': len(documents),
            'total_tokens': self._count_tokens(context),
            'total_characters': len(context),
            'token_utilization': self._count_tokens(context) / self.max_context_tokens,
            'subjects': list(set(doc.metadata.get('subject', 'Unknown') for doc in documents)),
            'grades': list(set(doc.metadata.get('grade', 'Unknown') for doc in documents)),
            'average_relevance': sum(doc.relevance_score for doc in documents) / len(documents) if documents else 0.0
        }