"""
Local MiniLM embedding strategy using sentence-transformers.
Provides sovereign mode embedding generation without AWS dependency.
"""

import logging
from typing import List
import os
import time

from .embedding_strategy import EmbeddingStrategy
from .strategy_metrics import StrategyMetrics, MetricsTracker

logger = logging.getLogger(__name__)

# Check if sentence-transformers is available
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")


class LocalMiniLMEmbeddingStrategy(EmbeddingStrategy):
    """Embedding strategy using local quantized MiniLM model for sovereign mode"""
    
    def __init__(self, model_path: str = None, n_threads: int = 4, max_retries: int = 3):
        """Initialize local MiniLM embedding strategy.
        
        Args:
            model_path: Path to local model or HuggingFace model name
                       (default: sentence-transformers/all-MiniLM-L6-v2)
            n_threads: Number of CPU threads for inference (default: 4)
            max_retries: Maximum number of retries on failure (default: 3)
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
        
        # Default to MiniLM-L6-v2 (384 dimensions, optimized for CPU)
        self.model_path = model_path or "sentence-transformers/all-MiniLM-L6-v2"
        self.n_threads = n_threads
        self.max_retries = max_retries
        self.model = None
        self.embedding_dim = None
        self.metrics = StrategyMetrics()
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load the sentence-transformers model"""
        try:
            logger.info(f"Loading local embedding model: {self.model_path}")
            logger.info("This may take a few minutes on first run (downloading model)...")
            
            # Set number of threads for CPU inference
            os.environ['OMP_NUM_THREADS'] = str(self.n_threads)
            os.environ['MKL_NUM_THREADS'] = str(self.n_threads)
            
            self.model = SentenceTransformer(self.model_path)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            
            logger.info(f"Model loaded successfully! Embedding dimension: {self.embedding_dim}")
            logger.info(f"Using {self.n_threads} CPU threads for inference")
            
        except Exception as e:
            logger.error(f"Failed to load local embedding model: {e}")
            self.model = None
            self.embedding_dim = None
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text using local MiniLM with retry logic.
        
        Args:
            text: Input text to embed
            
        Returns:
            384-dimensional embedding vector (for MiniLM-L6-v2)
            
        Raises:
            ValueError: If text is empty
            Exception: If model is not loaded or embedding generation fails after retries
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")
        
        if not self.model:
            raise Exception("Local embedding model not loaded")
        
        # Track metrics
        with MetricsTracker(self.metrics):
            # Try with exponential backoff
            for attempt in range(self.max_retries):
                try:
                    # Generate embedding
                    embedding = self.model.encode(text, convert_to_numpy=True)
                    return embedding.tolist()
                    
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt  # 1, 2, 4 seconds
                        logger.warning(
                            f"Local embedding generation failed, retrying in {wait_time}s "
                            f"(attempt {attempt + 1}/{self.max_retries}): {e}"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Failed to generate embedding after {self.max_retries} retries")
                        raise Exception(f"Local embedding generation failed: {e}") from e
            
            raise Exception("Unexpected error: max retries reached without success")
    
    def batch_generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts with batching.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of 384-dimensional embedding vectors
            
        Raises:
            ValueError: If texts list is empty
            Exception: If model is not loaded or embedding generation fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        if not self.model:
            raise Exception("Local embedding model not loaded")
        
        try:
            logger.info(f"Processing {len(texts)} texts with local MiniLM")
            
            # Process all texts at once (sentence-transformers handles batching internally)
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=len(texts) > 10,  # Show progress for large batches
                convert_to_numpy=True
            )
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise Exception(f"Local batch embedding generation failed: {e}") from e
    
    def get_dimension(self) -> int:
        """Get the dimensionality of MiniLM embeddings.
        
        Returns:
            384 (MiniLM-L6-v2 embedding dimension)
        """
        if self.embedding_dim:
            return self.embedding_dim
        return 384  # Default for MiniLM-L6-v2
    
    def health_check(self) -> bool:
        """Check if local model is loaded and operational.
        
        Returns:
            True if model is loaded and can generate embeddings, False otherwise
        """
        if not self.model:
            logger.warning("Local embedding model not loaded")
            return False
        
        try:
            # Try to generate a test embedding
            test_text = "health check"
            embedding = self.generate_embedding(test_text)
            
            # Verify embedding has correct dimension
            expected_dim = self.get_dimension()
            if len(embedding) == expected_dim:
                logger.info("Local MiniLM health check passed")
                return True
            else:
                logger.warning(f"Local MiniLM health check failed: unexpected dimension {len(embedding)}")
                return False
                
        except Exception as e:
            logger.warning(f"Local MiniLM health check failed: {e}")
            return False
    
    def get_metrics(self) -> StrategyMetrics:
        """Get performance metrics for this strategy.
        
        Returns:
            StrategyMetrics instance with current metrics
        """
        return self.metrics
