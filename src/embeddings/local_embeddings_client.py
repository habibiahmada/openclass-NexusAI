"""
Local embeddings client using sentence-transformers.
Alternative to AWS Bedrock for generating embeddings locally.
"""

import logging
from typing import List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class LocalEmbeddingsClient:
    """Client for generating embeddings using local sentence-transformers model"""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"):
        """Initialize local embeddings client.
        
        Args:
            model_name: HuggingFace model identifier
                - paraphrase-multilingual-mpnet-base-v2: 768-dim, supports Indonesian (278MB)
                - all-MiniLM-L6-v2: 384-dim, smaller but English-focused (80MB)
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
        
        self.model_name = model_name
        logger.info(f"Loading local embedding model: {model_name}")
        logger.info("This may take a few minutes on first run (downloading model)...")
        
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.total_texts_processed = 0
        
        logger.info(f"Model loaded successfully! Embedding dimension: {self.embedding_dim}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector (768-dim for multilingual model)
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")
        
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        self.total_texts_processed += 1
        
        return embedding.tolist()
    
    def generate_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts with batching.
        
        Args:
            texts: List of input texts
            batch_size: Number of texts per batch (default 32)
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        logger.info(f"Processing {len(texts)} texts locally...")
        
        # Process all texts at once (sentence-transformers handles batching internally)
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        self.total_texts_processed += len(texts)
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        
        return embeddings.tolist()
    
    def get_text_count(self) -> int:
        """Get total texts processed.
        
        Returns:
            Total number of texts processed
        """
        return self.total_texts_processed
    
    def estimate_cost(self, text_count: int = None) -> float:
        """Estimate cost (always $0 for local model).
        
        Args:
            text_count: Number of texts (ignored)
            
        Returns:
            Cost in USD (always 0.0)
        """
        return 0.0
    
    def reset_usage(self):
        """Reset usage counter"""
        self.total_texts_processed = 0
