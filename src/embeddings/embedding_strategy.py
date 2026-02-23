"""
Abstract base class for embedding strategies.
Defines the interface for generating embeddings using different backends.
"""

from abc import ABC, abstractmethod
from typing import List
import logging

logger = logging.getLogger(__name__)


class EmbeddingStrategy(ABC):
    """Abstract base class for embedding generation strategies"""
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            ValueError: If text is empty
            Exception: If embedding generation fails
        """
        pass
    
    @abstractmethod
    def batch_generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            ValueError: If texts list is empty
            Exception: If embedding generation fails
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimensionality of embeddings produced by this strategy.
        
        Returns:
            Number of dimensions in embedding vectors
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the embedding strategy is operational.
        
        Returns:
            True if strategy is healthy and can generate embeddings, False otherwise
        """
        pass
    
    def get_metrics(self):
        """Get performance metrics for this strategy.
        
        Returns:
            StrategyMetrics instance with current metrics, or None if not implemented
        """
        return None
