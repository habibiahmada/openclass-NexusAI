"""Property-based tests for ChromaDB vector store.

Feature: phase2-backend-knowledge-engineering
"""

import pytest
import tempfile
import shutil
import time
from hypothesis import given, strategies as st, settings
from pathlib import Path

from src.embeddings.chroma_manager import ChromaDBManager
from src.data_processing.metadata_manager import EnrichedChunk


# Feature: phase2-backend-knowledge-engineering, Property 11: Vector-Text-Metadata Integrity
@settings(max_examples=100)
@given(
    num_docs=st.integers(min_value=1, max_value=20),
    text_size=st.integers(min_value=10, max_value=500),
    embedding_dim=st.just(1024)  # Fixed dimension for Titan embeddings
)
def test_property_vector_text_metadata_integrity(num_docs, text_size, embedding_dim):
    """Property 11: For any document stored in ChromaDB, retrieving it should return 
    the original text, embedding vector, and metadata together.
    
    Validates: Requirements 5.2
    """
    # Create temporary directory for this test
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize ChromaDB manager
        manager = ChromaDBManager(persist_directory=temp_dir)
        manager.create_collection("test_collection")
        
        # Generate test data
        chunks = []
        embeddings = []
        
        for i in range(num_docs):
            # Create enriched chunk
            chunk = EnrichedChunk(
                chunk_id=f"test_chunk_{i}",
                text=f"Sample text {i} " * (text_size // 20),  # Generate text of approximate size
                source_file=f"test_file_{i % 3}.pdf",  # Vary source files
                subject="informatika",
                grade="kelas_10",
                chunk_index=i,
                char_start=i * 1000,
                char_end=(i + 1) * 1000
            )
            chunks.append(chunk)
            
            # Create embedding vector
            embedding = [float(i) / 100.0] * embedding_dim
            embeddings.append(embedding)
        
        # Add documents to ChromaDB
        manager.add_documents(chunks, embeddings)
        
        # Verify all documents were stored
        assert manager.count_documents() == num_docs, \
            f"Expected {num_docs} documents, found {manager.count_documents()}"
        
        # Query with each embedding and verify we get the correct document back
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            results = manager.query(embedding, n_results=1)
            
            # Should get at least one result
            assert len(results) > 0, f"No results for document {i}"
            
            # The top result should be the document we stored
            top_result = results[0]
            
            # Verify text is preserved
            assert top_result.text == chunk.text, \
                f"Text mismatch for document {i}"
            
            # Verify metadata is preserved
            assert top_result.metadata['source_file'] == chunk.source_file, \
                f"source_file mismatch for document {i}"
            assert top_result.metadata['subject'] == chunk.subject, \
                f"subject mismatch for document {i}"
            assert top_result.metadata['grade'] == chunk.grade, \
                f"grade mismatch for document {i}"
            assert top_result.metadata['chunk_index'] == chunk.chunk_index, \
                f"chunk_index mismatch for document {i}"
            assert top_result.metadata['char_start'] == chunk.char_start, \
                f"char_start mismatch for document {i}"
            assert top_result.metadata['char_end'] == chunk.char_end, \
                f"char_end mismatch for document {i}"
            
            # Verify similarity score is high (should be very close to 1.0 for exact match)
            assert top_result.similarity_score > 0.99, \
                f"Similarity score too low for exact match: {top_result.similarity_score}"
    
    finally:
        # Clean up: explicitly delete manager to close ChromaDB connections
        if 'manager' in locals():
            del manager
        
        # Clean up temporary directory
        import time
        time.sleep(0.1)  # Brief pause to allow file handles to close
        shutil.rmtree(temp_dir, ignore_errors=True)


# Feature: phase2-backend-knowledge-engineering, Property 12: Persistence Round-Trip
@settings(max_examples=100)
@given(
    num_docs=st.integers(min_value=1, max_value=20),
    embedding_dim=st.just(1024)
)
def test_property_persistence_round_trip(num_docs, embedding_dim):
    """Property 12: For any ChromaDB collection with documents, restarting the application 
    and loading the collection should retrieve all previously stored documents.
    
    Validates: Requirements 5.4
    """
    # Create temporary directory for this test
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Phase 1: Create and populate collection
        manager1 = ChromaDBManager(persist_directory=temp_dir)
        manager1.create_collection("test_collection")
        
        # Generate test data
        chunks = []
        embeddings = []
        
        for i in range(num_docs):
            chunk = EnrichedChunk(
                chunk_id=f"persist_chunk_{i}",
                text=f"Persistence test text {i}",
                source_file=f"persist_file_{i}.pdf",
                subject="matematika",
                grade="kelas_11",
                chunk_index=i,
                char_start=i * 500,
                char_end=(i + 1) * 500
            )
            chunks.append(chunk)
            
            # Create unique embedding for each document
            embedding = [float(i + 1) / 10.0] * embedding_dim
            embeddings.append(embedding)
        
        # Add documents
        manager1.add_documents(chunks, embeddings)
        
        # Verify documents were added
        count_before = manager1.count_documents()
        assert count_before == num_docs, \
            f"Expected {num_docs} documents before restart, found {count_before}"
        
        # Store original data for comparison
        original_texts = [chunk.text for chunk in chunks]
        original_metadata = [
            {
                'source_file': chunk.source_file,
                'subject': chunk.subject,
                'grade': chunk.grade,
                'chunk_index': chunk.chunk_index
            }
            for chunk in chunks
        ]
        
        # Clean up first manager to release file handles
        del manager1
        
        # Phase 2: Simulate restart by creating new manager instance
        # (This simulates application restart - new manager, same persist directory)
        manager2 = ChromaDBManager(persist_directory=temp_dir)
        manager2.get_collection("test_collection")
        
        # Verify all documents are still there after "restart"
        count_after = manager2.count_documents()
        assert count_after == num_docs, \
            f"Expected {num_docs} documents after restart, found {count_after}"
        
        # Verify we can query and retrieve the same documents
        for i, embedding in enumerate(embeddings):
            results = manager2.query(embedding, n_results=1)
            
            assert len(results) > 0, \
                f"No results for document {i} after restart"
            
            top_result = results[0]
            
            # Verify text persisted correctly
            assert top_result.text == original_texts[i], \
                f"Text mismatch after restart for document {i}"
            
            # Verify metadata persisted correctly
            assert top_result.metadata['source_file'] == original_metadata[i]['source_file'], \
                f"source_file mismatch after restart for document {i}"
            assert top_result.metadata['subject'] == original_metadata[i]['subject'], \
                f"subject mismatch after restart for document {i}"
            assert top_result.metadata['grade'] == original_metadata[i]['grade'], \
                f"grade mismatch after restart for document {i}"
            assert top_result.metadata['chunk_index'] == original_metadata[i]['chunk_index'], \
                f"chunk_index mismatch after restart for document {i}"
        
        # Clean up second manager
        del manager2
    
    finally:
        # Clean up temporary directory
        import time
        time.sleep(0.1)  # Brief pause to allow file handles to close
        shutil.rmtree(temp_dir, ignore_errors=True)
