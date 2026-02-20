import chromadb
from chromadb.config import Settings
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import time

from src.data_processing.metadata_manager import EnrichedChunk

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Result from similarity search."""
    text: str
    metadata: Dict[str, Any]
    similarity_score: float


class ChromaDBManager:
    """Manages ChromaDB vector store operations."""
    
    def __init__(self, persist_directory: str = "data/vector_db"):
        """Initialize ChromaDB with persistence.
        
        Args:
            persist_directory: Directory for database files
        """
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        
        # Create directory if it doesn't exist
        try:
            Path(persist_directory).mkdir(parents=True, exist_ok=True)
            self._initialize_client()
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise RuntimeError(f"Could not initialize vector database: {e}")
    
    def _initialize_client(self):
        """Initialize the ChromaDB client with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                logger.info(f"ChromaDB client initialized successfully at {self.persist_directory}")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} to initialize ChromaDB failed: {e}. Retrying...")
                    time.sleep(1)
                else:
                    logger.error(f"All attempts to initialize ChromaDB failed: {e}")
                    raise

    def check_health(self) -> bool:
        """Check if the vector database is healthy and accessible.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            if self.client is None:
                return False
            # Perform a lightweight operation to verify connectivity
            self.client.heartbeat()
            return True
        except Exception as e:
            logger.error(f"Vector DB health check failed: {e}")
            return False

    def create_collection(self, name: str = "educational_content"):
        """Create or get existing collection.
        
        Args:
            name: Collection name
            
        Returns:
            ChromaDB collection object
        """
        if self.client is None:
            self._initialize_client()

        try:
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=name,
                metadata={"description": "Educational content embeddings"}
            )
            return self.collection
        except Exception as e:
            logger.error(f"Failed to create collection '{name}': {e}")
            raise

    def add_documents(
        self, 
        chunks: List[EnrichedChunk], 
        embeddings: List[List[float]]
    ):
        """Add documents with embeddings to collection.
        
        Args:
            chunks: List of enriched chunks
            embeddings: Corresponding embedding vectors
            
        Raises:
            ValueError: If chunks and embeddings lengths don't match
            RuntimeError: If collection hasn't been created
        """
        if self.collection is None:
            raise RuntimeError("Collection not created. Call create_collection() first.")
        
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) "
                f"must have the same length"
            )
        
        if not chunks:
            return  # Nothing to add
        
        try:
            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in chunks]
            documents = [chunk.text for chunk in chunks]
            metadatas = [
                {
                    "source_file": chunk.source_file,
                    "subject": chunk.subject,
                    "grade": chunk.grade,
                    "chunk_index": chunk.chunk_index,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end
                }
                for chunk in chunks
            ]
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        except Exception as e:
            logger.error(f"Failed to add documents to vector DB: {e}")
            raise RuntimeError(f"Database write error: {e}")

    def query(
        self, 
        query_embedding: List[float], 
        n_results: int = 5
    ) -> List[SearchResult]:
        """Search for similar documents using embedding.
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            
        Returns:
            List of search results with text and metadata
            
        Raises:
            RuntimeError: If collection hasn't been created
        """
        if self.collection is None:
            raise RuntimeError("Collection not created. Call create_collection() first.")
        
        try:
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Convert to SearchResult objects
            search_results = []
            
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    search_results.append(SearchResult(
                        text=results['documents'][0][i],
                        metadata=results['metadatas'][0][i],
                        similarity_score=1.0 - results['distances'][0][i]  # Convert distance to similarity
                    ))
            
            return search_results
        except Exception as e:
            logger.error(f"Query extraction failed: {e}")
            return []

    def get_collection(self, name: str = "educational_content"):
        """Get existing collection.
        
        Args:
            name: Collection name
            
        Returns:
            ChromaDB collection object
            
        Raises:
            ValueError: If collection doesn't exist
        """
        if self.client is None:
            self._initialize_client()

        try:
            self.collection = self.client.get_collection(name=name)
            return self.collection
        except Exception as e:
            raise ValueError(f"Collection '{name}' does not exist: {e}")
    
    def count_documents(self) -> int:
        """Get count of documents in collection.
        
        Returns:
            Number of documents in collection
            
        Raises:
            RuntimeError: If collection hasn't been created
        """
        if self.collection is None:
            raise RuntimeError("Collection not created. Call create_collection() first.")
        
        return self.collection.count()
    
    def reset(self):
        """Reset the ChromaDB client (delete all data).
        
        Warning: This will delete all collections and data.
        """
        if self.client:
            self.client.reset()
            self.collection = None
