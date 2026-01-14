"""Property-based tests for validation and quality control.

Feature: phase2-backend-knowledge-engineering
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings

from src.data_processing.validator import Validator
from src.data_processing.metadata_manager import EnrichedChunk


# Feature: phase2-backend-knowledge-engineering, Property 17: Validation Completeness
@settings(max_examples=100)
@given(
    num_pdfs=st.integers(min_value=1, max_value=20)
)
def test_property_validation_completeness(num_pdfs):
    """Property 17: For any PDF file processed, there should exist a corresponding text file.
    
    Validates: Requirements 9.1
    """
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_dir = temp_path / "pdfs"
        processed_dir = temp_path / "processed"
        
        pdf_dir.mkdir()
        processed_dir.mkdir()
        
        # Create PDF files (just empty files for testing)
        pdf_files = []
        for i in range(num_pdfs):
            pdf_file = pdf_dir / f"test_{i}.pdf"
            pdf_file.write_text(f"PDF content {i}")
            pdf_files.append(pdf_file)
        
        # Create corresponding text files
        for pdf_file in pdf_files:
            text_file = processed_dir / (pdf_file.stem + ".txt")
            text_file.write_text(f"Extracted text from {pdf_file.name}")
        
        # Validate extraction
        validator = Validator()
        result = validator.validate_extraction(pdf_files, str(processed_dir))
        
        # Property: All PDF files should have corresponding text files
        assert result.passed, f"Validation should pass when all text files exist: {result.message}"
        assert result.details["total_pdfs"] == num_pdfs
        assert result.details["found_text_files"] == num_pdfs
        assert len(result.details["missing_text_files"]) == 0


# Feature: phase2-backend-knowledge-engineering, Property 17: Validation Completeness (negative case)
@settings(max_examples=100)
@given(
    num_pdfs=st.integers(min_value=2, max_value=20),
    num_missing=st.integers(min_value=1, max_value=5)
)
def test_property_validation_completeness_missing_files(num_pdfs, num_missing):
    """Property 17: Validation should fail when text files are missing.
    
    Validates: Requirements 9.1
    """
    # Ensure we don't try to remove more files than we have
    num_missing = min(num_missing, num_pdfs)
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_dir = temp_path / "pdfs"
        processed_dir = temp_path / "processed"
        
        pdf_dir.mkdir()
        processed_dir.mkdir()
        
        # Create PDF files
        pdf_files = []
        for i in range(num_pdfs):
            pdf_file = pdf_dir / f"test_{i}.pdf"
            pdf_file.write_text(f"PDF content {i}")
            pdf_files.append(pdf_file)
        
        # Create text files, but skip some
        for i, pdf_file in enumerate(pdf_files):
            if i >= num_missing:  # Skip first num_missing files
                text_file = processed_dir / (pdf_file.stem + ".txt")
                text_file.write_text(f"Extracted text from {pdf_file.name}")
        
        # Validate extraction
        validator = Validator()
        result = validator.validate_extraction(pdf_files, str(processed_dir))
        
        # Property: Validation should fail when files are missing
        assert not result.passed, "Validation should fail when text files are missing"
        assert result.details["total_pdfs"] == num_pdfs
        assert len(result.details["missing_text_files"]) == num_missing


# Feature: phase2-backend-knowledge-engineering, Property 18: Embedding-Chunk Correspondence
@settings(max_examples=100)
@given(
    num_chunks=st.integers(min_value=1, max_value=100)
)
def test_property_embedding_chunk_correspondence(num_chunks):
    """Property 18: For any set of chunks, the number of embeddings should equal the number of chunks,
    and all embeddings should be 1024-dimensional.
    
    Validates: Requirements 9.3
    """
    # Create chunks
    chunks = [
        EnrichedChunk(
            chunk_id=f"chunk_{i}",
            text=f"This is chunk {i} with some text content",
            source_file="test.pdf",
            subject="informatika",
            grade="kelas_10",
            chunk_index=i,
            char_start=i * 100,
            char_end=(i + 1) * 100
        )
        for i in range(num_chunks)
    ]
    
    # Create embeddings (1024-dimensional)
    embeddings = [
        [0.1] * 1024
        for _ in range(num_chunks)
    ]
    
    # Validate embeddings
    validator = Validator()
    result = validator.validate_embeddings(
        embeddings=embeddings,
        expected_dimension=1024,
        expected_count=num_chunks
    )
    
    # Property: Number of embeddings should equal number of chunks
    assert result.passed, f"Validation should pass: {result.message}"
    assert result.details["embedding_count"] == num_chunks
    assert result.details["expected_dimension"] == 1024
    assert result.details["invalid_dimensions"] == 0


# Feature: phase2-backend-knowledge-engineering, Property 18: Embedding-Chunk Correspondence (dimension mismatch)
@settings(max_examples=100)
@given(
    num_chunks=st.integers(min_value=1, max_value=50),
    wrong_dimension=st.integers(min_value=1, max_value=2048).filter(lambda x: x != 1024)
)
def test_property_embedding_dimension_mismatch(num_chunks, wrong_dimension):
    """Property 18: Validation should fail when embeddings have wrong dimensions.
    
    Validates: Requirements 9.3
    """
    # Create embeddings with wrong dimension
    embeddings = [
        [0.1] * wrong_dimension
        for _ in range(num_chunks)
    ]
    
    # Validate embeddings
    validator = Validator()
    result = validator.validate_embeddings(
        embeddings=embeddings,
        expected_dimension=1024,
        expected_count=num_chunks
    )
    
    # Property: Validation should fail when dimensions are wrong
    assert not result.passed, "Validation should fail when embeddings have wrong dimensions"
    assert result.details["invalid_dimensions"] == num_chunks


# Feature: phase2-backend-knowledge-engineering, Property 18: Embedding-Chunk Correspondence (count mismatch)
@settings(max_examples=100)
@given(
    num_chunks=st.integers(min_value=2, max_value=50),
    num_embeddings=st.integers(min_value=1, max_value=50)
)
def test_property_embedding_count_mismatch(num_chunks, num_embeddings):
    """Property 18: Validation should fail when embedding count doesn't match chunk count.
    
    Validates: Requirements 9.3
    """
    # Skip if counts match (we want them to mismatch)
    if num_chunks == num_embeddings:
        pytest.skip("Counts match, skipping test")
    
    # Create embeddings with different count than chunks
    embeddings = [
        [0.1] * 1024
        for _ in range(num_embeddings)
    ]
    
    # Validate embeddings
    validator = Validator()
    result = validator.validate_embeddings(
        embeddings=embeddings,
        expected_dimension=1024,
        expected_count=num_chunks
    )
    
    # Property: Validation should fail when counts don't match
    assert not result.passed, "Validation should fail when embedding count doesn't match chunk count"
    assert result.details["embedding_count"] == num_embeddings
    assert result.details["expected_count"] == num_chunks
