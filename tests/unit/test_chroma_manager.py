"""Unit tests for ChromaDB manager.

Tests collection creation, document addition, similarity search, and persistence.
"""

import pytest
import tempfile
import shutil
import time
from pathlib import Path

from src.embeddings.chroma_manager import ChromaDBManager, SearchResult
from src.data_processing.metadata_manager import EnrichedChunk


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for ChromaDB."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    time.sleep(0.1)  # Brief pause to allow file handles to close
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def chroma_manager(temp_db_dir):
    """Create a ChromaDB manager instance."""
    manager = ChromaDBManager(persist_directory=temp_db_dir)
    yield manager
    # Cleanup
    del manager


@pytest.fixture
def sample_chunks():
    """Create sample enriched chunks for testing."""
    chunks = [
        EnrichedChunk(
            chunk_id="chunk_1",
            text="Python is a high-level programming language.",
            source_file="python_intro.pdf",
            subject="informatika",
            grade="kelas_10",
            chunk_index=0,
            char_start=0,
            char_end=100
        ),
        EnrichedChunk(
            chunk_id="chunk_2",
            text="Java is an object-oriented programming language.",
            source_file="java_intro.pdf",
            subject="informatika",
            grade="kelas_10",
            chunk_index=1,
            char_start=100,
            char_end=200
        ),
        EnrichedChunk(
            chunk_id="chunk_3",
            text="Mathematics is the study of numbers and patterns.",
            source_file="math_intro.pdf",
            subject="matematika",
            grade="kelas_11",
            chunk_index=0,
            char_start=0,
            char_end=100
        )
    ]
    return chunks


@pytest.fixture
def sample_embeddings():
    """Create sample embeddings for testing."""
    return [
        [0.1] * 1024,  # Python embedding
        [0.2] * 1024,  # Java embedding
        [0.3] * 1024   # Math embedding
    ]


class TestCollectionCreation:
    """Tests for collection creation."""
    
    def test_create_collection_success(self, chroma_manager):
        """Test that collection is created successfully."""
        collection = chroma_manager.create_collection("test_collection")
        
        assert collection is not None
        assert collection.name == "test_collection"
        assert chroma_manager.collection is not None
    
    def test_create_collection_default_name(self, chroma_manager):
        """Test creating collection with default name."""
        collection = chroma_manager.create_collection()
        
        assert collection.name == "educational_content"
    
    def test_get_or_create_idempotent(self, chroma_manager):
        """Test that creating the same collection twice returns the same collection."""
        collection1 = chroma_manager.create_collection("test_collection")
        collection2 = chroma_manager.create_collection("test_collection")
        
        assert collection1.name == collection2.name
    
    def test_get_existing_collection(self, chroma_manager):
        """Test getting an existing collection."""
        # Create collection
        chroma_manager.create_collection("test_collection")
        
        # Get the collection
        collection = chroma_manager.get_collection("test_collection")
        
        assert collection is not None
        assert collection.name == "test_collection"
    
    def test_get_nonexistent_collection_raises_error(self, chroma_manager):
        """Test that getting a non-existent collection raises an error."""
        with pytest.raises(ValueError, match="does not exist"):
            chroma_manager.get_collection("nonexistent_collection")


class TestDocumentAddition:
    """Tests for adding documents to collection."""
    
    def test_add_documents_success(self, chroma_manager, sample_chunks, sample_embeddings):
        """Test adding documents successfully."""
        chroma_manager.create_collection("test_collection")
        
        # Add documents
        chroma_manager.add_documents(sample_chunks, sample_embeddings)
        
        # Verify documents were added
        count = chroma_manager.count_documents()
        assert count == len(sample_chunks)
    
    def test_add_documents_without_collection_raises_error(self, chroma_manager, sample_chunks, sample_embeddings):
        """Test that adding documents without creating collection raises error."""
        with pytest.raises(RuntimeError, match="Collection not created"):
            chroma_manager.add_documents(sample_chunks, sample_embeddings)
    
    def test_add_documents_mismatched_lengths_raises_error(self, chroma_manager, sample_chunks):
        """Test that mismatched chunks and embeddings lengths raises error."""
        chroma_manager.create_collection("test_collection")
        
        # Create embeddings with wrong length
        wrong_embeddings = [[0.1] * 1024, [0.2] * 1024]  # Only 2 embeddings for 3 chunks
        
        with pytest.raises(ValueError, match="must have the same length"):
            chroma_manager.add_documents(sample_chunks, wrong_embeddings)
    
    def test_add_empty_documents_list(self, chroma_manager):
        """Test adding empty list of documents."""
        chroma_manager.create_collection("test_collection")
        
        # Should not raise error
        chroma_manager.add_documents([], [])
        
        assert chroma_manager.count_documents() == 0
    
    def test_add_documents_preserves_metadata(self, chroma_manager, sample_chunks, sample_embeddings):
        """Test that metadata is preserved when adding documents."""
        chroma_manager.create_collection("test_collection")
        chroma_manager.add_documents(sample_chunks, sample_embeddings)
        
        # Query to get documents back
        results = chroma_manager.query(sample_embeddings[0], n_results=1)
        
        assert len(results) > 0
        result = results[0]
        
        # Verify metadata
        assert result.metadata['source_file'] == sample_chunks[0].source_file
        assert result.metadata['subject'] == sample_chunks[0].subject
        assert result.metadata['grade'] == sample_chunks[0].grade
        assert result.metadata['chunk_index'] == sample_chunks[0].chunk_index


class TestSimilaritySearch:
    """Tests for similarity search."""
    
    def test_query_returns_results(self, chroma_manager, sample_chunks, sample_embeddings):
        """Test that query returns results."""
        chroma_manager.create_collection("test_collection")
        chroma_manager.add_documents(sample_chunks, sample_embeddings)
        
        # Query with first embedding
        results = chroma_manager.query(sample_embeddings[0], n_results=3)
        
        assert len(results) > 0
        assert len(results) <= 3
    
    def test_query_without_collection_raises_error(self, chroma_manager, sample_embeddings):
        """Test that querying without collection raises error."""
        with pytest.raises(RuntimeError, match="Collection not created"):
            chroma_manager.query(sample_embeddings[0])
    
    def test_query_returns_correct_document(self, chroma_manager, sample_chunks, sample_embeddings):
        """Test that query returns the most similar document."""
        chroma_manager.create_collection("test_collection")
        chroma_manager.add_documents(sample_chunks, sample_embeddings)
        
        # Query with first embedding should return first document
        results = chroma_manager.query(sample_embeddings[0], n_results=1)
        
        assert len(results) == 1
        assert results[0].text == sample_chunks[0].text
    
    def test_query_respects_n_results(self, chroma_manager, sample_chunks, sample_embeddings):
        """Test that query respects n_results parameter."""
        chroma_manager.create_collection("test_collection")
        chroma_manager.add_documents(sample_chunks, sample_embeddings)
        
        # Query with n_results=2
        results = chroma_manager.query(sample_embeddings[0], n_results=2)
        
        assert len(results) == 2
    
    def test_query_returns_search_result_objects(self, chroma_manager, sample_chunks, sample_embeddings):
        """Test that query returns SearchResult objects."""
        chroma_manager.create_collection("test_collection")
        chroma_manager.add_documents(sample_chunks, sample_embeddings)
        
        results = chroma_manager.query(sample_embeddings[0], n_results=1)
        
        assert len(results) > 0
        result = results[0]
        
        assert isinstance(result, SearchResult)
        assert hasattr(result, 'text')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'similarity_score')
    
    def test_query_empty_collection_returns_empty_list(self, chroma_manager):
        """Test that querying empty collection returns empty list."""
        chroma_manager.create_collection("test_collection")
        
        # Query empty collection
        results = chroma_manager.query([0.1] * 1024, n_results=5)
        
        assert len(results) == 0


class TestPersistence:
    """Tests for persistence across restarts."""
    
    def test_persistence_across_restarts(self, temp_db_dir, sample_chunks, sample_embeddings):
        """Test that data persists across manager restarts."""
        # Phase 1: Create and populate
        manager1 = ChromaDBManager(persist_directory=temp_db_dir)
        manager1.create_collection("test_collection")
        manager1.add_documents(sample_chunks, sample_embeddings)
        
        count_before = manager1.count_documents()
        assert count_before == len(sample_chunks)
        
        # Clean up first manager
        del manager1
        time.sleep(0.1)
        
        # Phase 2: Create new manager and load collection
        manager2 = ChromaDBManager(persist_directory=temp_db_dir)
        manager2.get_collection("test_collection")
        
        count_after = manager2.count_documents()
        assert count_after == count_before
        
        # Verify we can still query
        results = manager2.query(sample_embeddings[0], n_results=1)
        assert len(results) > 0
        assert results[0].text == sample_chunks[0].text
        
        # Clean up
        del manager2
    
    def test_persistence_directory_created(self, temp_db_dir):
        """Test that persistence directory is created."""
        # Remove the directory first
        shutil.rmtree(temp_db_dir, ignore_errors=True)
        
        # Create manager - should create directory
        manager = ChromaDBManager(persist_directory=temp_db_dir)
        
        assert Path(temp_db_dir).exists()
        assert Path(temp_db_dir).is_dir()
        
        del manager


class TestCountDocuments:
    """Tests for counting documents."""
    
    def test_count_documents_empty_collection(self, chroma_manager):
        """Test counting documents in empty collection."""
        chroma_manager.create_collection("test_collection")
        
        count = chroma_manager.count_documents()
        assert count == 0
    
    def test_count_documents_after_adding(self, chroma_manager, sample_chunks, sample_embeddings):
        """Test counting documents after adding."""
        chroma_manager.create_collection("test_collection")
        chroma_manager.add_documents(sample_chunks, sample_embeddings)
        
        count = chroma_manager.count_documents()
        assert count == len(sample_chunks)
    
    def test_count_documents_without_collection_raises_error(self, chroma_manager):
        """Test that counting without collection raises error."""
        with pytest.raises(RuntimeError, match="Collection not created"):
            chroma_manager.count_documents()


class TestReset:
    """Tests for resetting ChromaDB."""
    
    def test_reset_clears_all_data(self, chroma_manager, sample_chunks, sample_embeddings):
        """Test that reset clears all data."""
        chroma_manager.create_collection("test_collection")
        chroma_manager.add_documents(sample_chunks, sample_embeddings)
        
        assert chroma_manager.count_documents() > 0
        
        # Reset
        chroma_manager.reset()
        
        # Collection should be None after reset
        assert chroma_manager.collection is None
        
        # Creating new collection should start fresh
        chroma_manager.create_collection("test_collection")
        assert chroma_manager.count_documents() == 0
