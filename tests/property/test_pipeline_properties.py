"""Property-based tests for ETL pipeline.

Feature: phase2-backend-knowledge-engineering
"""

import pytest
import tempfile
import shutil
import gc
import time
import chromadb
from pathlib import Path
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, MagicMock

from src.data_processing.etl_pipeline import ETLPipeline, PipelineConfig
from src.data_processing.pdf_extractor import PDFExtractionError


# Helper function to create mock PDF files
def create_mock_pdf_files(directory: Path, num_files: int, fail_indices: list = None):
    """Create mock PDF files for testing.
    
    Args:
        directory: Directory to create files in (should be .../kelas_XX/subject/)
        num_files: Number of PDF files to create
        fail_indices: List of indices that should fail extraction
    """
    fail_indices = fail_indices or []
    
    # Create proper directory structure: kelas_10/informatika/
    proper_dir = directory / "kelas_10" / "informatika"
    proper_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(num_files):
        pdf_path = proper_dir / f"test_file_{i}.pdf"
        # Create a simple text file (we'll mock the extraction anyway)
        pdf_path.write_text(f"Mock PDF content {i}")


# Feature: phase2-backend-knowledge-engineering, Property 15: Pipeline Completeness
@settings(max_examples=100, deadline=None)
@given(
    num_files=st.integers(min_value=1, max_value=20),
    num_failures=st.integers(min_value=0, max_value=5)
)
def test_property_pipeline_completeness(num_files, num_failures):
    """Property 15: For any set of N PDF files in the input directory, 
    the pipeline should process all N files (successful or failed), 
    with total_files = successful_files + failed_files = N.
    
    Validates: Requirements 8.1
    """
    # Ensure failures don't exceed total files
    num_failures = min(num_failures, num_files)
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        input_dir = temp_path / "input"
        output_dir = temp_path / "output"
        vector_db_dir = temp_path / "vector_db"
        
        # Create mock PDF files in proper structure
        create_mock_pdf_files(input_dir, num_files)
        
        # Determine which files should fail
        fail_indices = list(range(num_failures))
        
        # Create pipeline config with proper path
        config = PipelineConfig(
            input_dir=str(input_dir / "kelas_10" / "informatika"),
            output_dir=str(output_dir),
            vector_db_dir=str(vector_db_dir),
            chunk_size=800,
            chunk_overlap=100,
            batch_size=25
        )
        
        # Mock ChromaDB manager completely to avoid file locking issues on Windows
        # This prevents any SQLite files from being created
        with patch('src.data_processing.etl_pipeline.ChromaDBManager') as MockChromaDB:
            mock_chroma_instance = Mock()
            mock_collection = Mock()
            mock_collection.count.return_value = 0
            
            mock_chroma_instance.collection = mock_collection
            mock_chroma_instance.create_collection = Mock(return_value=mock_collection)
            mock_chroma_instance.add_documents = Mock()
            mock_chroma_instance.count_documents = Mock(return_value=0)
            
            MockChromaDB.return_value = mock_chroma_instance
            
            pipeline = ETLPipeline(config)
            
            # Mock the PDF extraction to control success/failure
            original_extract = pipeline.pdf_extractor.extract_text
            
            def mock_extract(pdf_path):
                # Get file index from filename
                filename = Path(pdf_path).name
                if filename.startswith("test_file_"):
                    file_idx = int(filename.split("_")[2].split(".")[0])
                    if file_idx in fail_indices:
                        raise PDFExtractionError(f"Mock extraction failure for file {file_idx}")
                
                # Return mock text for successful extractions
                return f"Mock extracted text from {filename}. " * 100
            
            # Mock the Bedrock client to avoid actual API calls
            with patch.object(pipeline.pdf_extractor, 'extract_text', side_effect=mock_extract):
                with patch.object(pipeline.bedrock_client, 'generate_batch') as mock_bedrock:
                    # Mock embeddings generation
                    def mock_generate_batch(texts, batch_size=25):
                        return [[0.1] * 1024 for _ in texts]
                    
                    mock_bedrock.side_effect = mock_generate_batch
                    
                    # Mock token usage and cost
                    pipeline.bedrock_client.get_token_usage = Mock(return_value=10000)
                    pipeline.bedrock_client.calculate_cost = Mock(return_value=0.001)
                    
                    # Run the pipeline
                    result = pipeline.run()
                    
                    # Property: total_files should equal the number of PDF files
                    assert result.total_files == num_files, \
                        f"Expected {num_files} total files, got {result.total_files}"
                    
                    # Property: successful_files + failed_files should equal total_files
                    assert result.successful_files + result.failed_files == result.total_files, \
                        f"successful ({result.successful_files}) + failed ({result.failed_files}) " \
                        f"!= total ({result.total_files})"
                    
                    # Property: failed_files should match expected failures
                    assert result.failed_files == num_failures, \
                        f"Expected {num_failures} failures, got {result.failed_files}"
                    
                    # Property: successful_files should match expected successes
                    expected_successes = num_files - num_failures
                    assert result.successful_files == expected_successes, \
                        f"Expected {expected_successes} successes, got {result.successful_files}"


# Feature: phase2-backend-knowledge-engineering, Property 16: Error Isolation
@settings(max_examples=100, deadline=None)
@given(
    num_files=st.integers(min_value=3, max_value=15),
    fail_index=st.integers(min_value=0, max_value=14)
)
def test_property_error_isolation(num_files, fail_index):
    """Property 16: For any pipeline execution where file X fails, 
    all other files should still be processed successfully.
    
    Validates: Requirements 8.3
    """
    # Ensure fail_index is within bounds
    fail_index = fail_index % num_files
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        input_dir = temp_path / "input"
        output_dir = temp_path / "output"
        vector_db_dir = temp_path / "vector_db"
        
        # Create mock PDF files in proper structure
        create_mock_pdf_files(input_dir, num_files)
        
        # Create pipeline config with proper path
        config = PipelineConfig(
            input_dir=str(input_dir / "kelas_10" / "informatika"),
            output_dir=str(output_dir),
            vector_db_dir=str(vector_db_dir),
            chunk_size=800,
            chunk_overlap=100,
            batch_size=25
        )
        
        # Mock ChromaDB manager completely to avoid file locking issues on Windows
        # This prevents any SQLite files from being created
        with patch('src.data_processing.etl_pipeline.ChromaDBManager') as MockChromaDB:
            mock_chroma_instance = Mock()
            mock_collection = Mock()
            mock_collection.count.return_value = 0
            
            mock_chroma_instance.collection = mock_collection
            mock_chroma_instance.create_collection = Mock(return_value=mock_collection)
            mock_chroma_instance.add_documents = Mock()
            mock_chroma_instance.count_documents = Mock(return_value=0)
            
            MockChromaDB.return_value = mock_chroma_instance
            
            pipeline = ETLPipeline(config)
            
            # Mock the PDF extraction to make one file fail
            def mock_extract(pdf_path):
                filename = Path(pdf_path).name
                if filename.startswith("test_file_"):
                    file_idx = int(filename.split("_")[2].split(".")[0])
                    if file_idx == fail_index:
                        raise PDFExtractionError(f"Mock extraction failure for file {file_idx}")
                
                return f"Mock extracted text from {filename}. " * 100
            
            # Mock the Bedrock client
            with patch.object(pipeline.pdf_extractor, 'extract_text', side_effect=mock_extract):
                with patch.object(pipeline.bedrock_client, 'generate_batch') as mock_bedrock:
                    # Mock embeddings generation
                    def mock_generate_batch(texts, batch_size=25):
                        return [[0.1] * 1024 for _ in texts]
                    
                    mock_bedrock.side_effect = mock_generate_batch
                    
                    # Mock token usage and cost
                    pipeline.bedrock_client.get_token_usage = Mock(return_value=10000)
                    pipeline.bedrock_client.calculate_cost = Mock(return_value=0.001)
                    
                    # Run the pipeline
                    result = pipeline.run()
                    
                    # Property: Exactly one file should fail
                    assert result.failed_files == 1, \
                        f"Expected 1 failure, got {result.failed_files}"
                    
                    # Property: All other files should succeed
                    expected_successes = num_files - 1
                    assert result.successful_files == expected_successes, \
                        f"Expected {expected_successes} successes, got {result.successful_files}"
                    
                    # Property: Total files processed should still be N
                    assert result.total_files == num_files, \
                        f"Expected {num_files} total files, got {result.total_files}"
                    
                    # Property: Chunks should be created from successful files
                    # Each successful file should produce some chunks
                    assert result.total_chunks > 0, \
                        "No chunks created despite successful file processing"
                    
                    # Property: Embeddings should be created for successful chunks
                    assert result.total_embeddings == result.total_chunks, \
                        f"Embeddings ({result.total_embeddings}) don't match chunks ({result.total_chunks})"
