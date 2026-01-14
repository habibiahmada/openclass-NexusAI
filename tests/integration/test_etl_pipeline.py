"""Integration tests for ETL pipeline.

Feature: phase2-backend-knowledge-engineering
"""

import pytest
import tempfile
import shutil
import gc
import time
from pathlib import Path
from unittest.mock import Mock, patch

from src.data_processing.etl_pipeline import ETLPipeline, PipelineConfig


@pytest.fixture
def sample_pdf_fixtures():
    """Create sample PDF fixtures for testing."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Create proper directory structure: kelas_10/informatika/
        input_dir = temp_path / "input" / "kelas_10" / "informatika"
        input_dir.mkdir(parents=True, exist_ok=True)
        
        # Create 3 sample PDF files with different content
        pdf_files = []
        for i in range(3):
            pdf_path = input_dir / f"sample_textbook_{i}.pdf"
            # Create mock PDF content (we'll mock extraction anyway)
            content = f"Sample educational content for file {i}. " * 50
            pdf_path.write_text(content)
            pdf_files.append(pdf_path)
        
        yield {
            "input_dir": str(input_dir),
            "temp_dir": temp_path,
            "pdf_files": pdf_files
        }
    finally:
        # Cleanup with retry logic for Windows file locking
        try:
            gc.collect()
            time.sleep(0.2)
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


def test_end_to_end_pipeline_with_sample_pdfs(sample_pdf_fixtures):
    """Integration test: Verify complete pipeline execution from PDFs to ChromaDB.
    
    This test validates:
    - All phases execute in sequence (extraction, chunking, embedding, storage)
    - ChromaDB contains expected documents
    - Summary report is generated
    - No errors occur during processing
    
    Validates: Requirements 8.1, 8.2, 8.4
    """
    fixtures = sample_pdf_fixtures
    
    # Setup output directories
    output_dir = fixtures["temp_dir"] / "output"
    vector_db_dir = fixtures["temp_dir"] / "vector_db"
    
    # Create pipeline configuration
    config = PipelineConfig(
        input_dir=fixtures["input_dir"],
        output_dir=str(output_dir),
        vector_db_dir=str(vector_db_dir),
        chunk_size=800,
        chunk_overlap=100,
        batch_size=25
    )
    
    pipeline = ETLPipeline(config)
    
    # Mock ChromaDB manager completely to avoid file locking issues on Windows
    # Replace the entire ChromaDB manager with a mock
    mock_chroma_manager = Mock()
    mock_collection = Mock()
    mock_collection.count.return_value = 0
    
    mock_chroma_manager.collection = mock_collection
    mock_chroma_manager.create_collection = Mock(return_value=mock_collection)
    pipeline.chroma_manager = mock_chroma_manager
    
    # Track documents added to ChromaDB
    added_documents = []
    
    def mock_add_documents(chunks, embeddings):
        """Mock add_documents to track what was stored."""
        added_documents.extend(chunks)
    
    mock_chroma_manager.add_documents = mock_add_documents
    mock_chroma_manager.count_documents = Mock(return_value=len(added_documents))
    
    # Mock PDF extraction to return realistic text
    def mock_extract(pdf_path):
        filename = Path(pdf_path).name
        # Return realistic educational content
        return (
            f"Chapter 1: Introduction to {filename}\n\n"
            "This chapter covers the fundamental concepts of computer science. "
            "We will explore algorithms, data structures, and programming paradigms. "
            "Understanding these concepts is essential for building robust software systems. "
            * 10  # Repeat to create enough content for multiple chunks
        )
    
    # Mock Bedrock client to avoid actual API calls
    with patch.object(pipeline.pdf_extractor, 'extract_text', side_effect=mock_extract):
        with patch.object(pipeline.bedrock_client, 'generate_batch') as mock_bedrock:
            # Mock embeddings generation
            def mock_generate_batch(texts, batch_size=25):
                return [[0.1 * (i % 10)] * 1024 for i in range(len(texts))]
            
            mock_bedrock.side_effect = mock_generate_batch
            
            # Mock token usage and cost
            pipeline.bedrock_client.get_token_usage = Mock(return_value=15000)
            pipeline.bedrock_client.calculate_cost = Mock(return_value=0.0015)
            
            # Run the complete pipeline
            result = pipeline.run()
            
            # Verify Phase 1: Extraction completed successfully
            assert result.total_files == 3, "Should process all 3 PDF files"
            assert result.successful_files == 3, "All files should be extracted successfully"
            assert result.failed_files == 0, "No files should fail"
            
            # Verify Phase 2: Chunking created chunks
            assert result.total_chunks > 0, "Should create chunks from extracted text"
            # Each file should produce multiple chunks given the content size
            assert result.total_chunks >= 3, "Should have at least 1 chunk per file"
            
            # Verify Phase 3: Embeddings generated
            assert result.total_embeddings > 0, "Should generate embeddings"
            assert result.total_embeddings == result.total_chunks, \
                "Number of embeddings should match number of chunks"
            
            # Verify Phase 4: Documents stored in ChromaDB
            assert len(added_documents) == result.total_chunks, \
                "All chunks should be stored in ChromaDB"
            
            # Verify all stored documents have required metadata
            for doc in added_documents:
                assert doc.chunk_id, "Each document should have a chunk_id"
                assert doc.text, "Each document should have text content"
                assert doc.source_file, "Each document should have source_file"
                assert doc.subject == "informatika", "Subject should be extracted from path"
                assert doc.grade == "kelas_10", "Grade should be extracted from path"
            
            # Verify summary report metrics
            assert result.processing_time > 0, "Should track processing time"
            assert result.estimated_cost > 0, "Should calculate estimated cost"
            assert len(result.errors) == 0, "Should have no errors"
            
            # Verify error handler generated report
            summary_report = pipeline.error_handler.generate_summary_report(
                pipeline_result=result,
                output_path=None  # Don't save to disk in test
            )
            
            assert summary_report.status == "completed", "Pipeline should complete successfully"
            assert summary_report.total_files == 3
            assert summary_report.successful_files == 3
            assert summary_report.failed_files == 0
            assert summary_report.total_chunks == result.total_chunks
            assert summary_report.total_embeddings == result.total_embeddings
            assert summary_report.total_errors == 0
    
    # Cleanup
    try:
        del mock_chroma_manager
        del pipeline
        gc.collect()
        time.sleep(0.1)
    except Exception:
        pass


def test_pipeline_with_mixed_success_and_failure():
    """Integration test: Verify pipeline handles mixed success/failure scenarios.
    
    This test validates:
    - Pipeline continues processing after individual file failures
    - Successful files are processed completely
    - Error report includes failure details
    - Summary report shows correct counts
    
    Validates: Requirements 8.3, 8.4
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create proper directory structure
        input_dir = temp_path / "input" / "kelas_10" / "informatika"
        input_dir.mkdir(parents=True, exist_ok=True)
        
        # Create 5 PDF files
        for i in range(5):
            pdf_path = input_dir / f"textbook_{i}.pdf"
            pdf_path.write_text(f"Content {i}")
        
        output_dir = temp_path / "output"
        vector_db_dir = temp_path / "vector_db"
        
        config = PipelineConfig(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            vector_db_dir=str(vector_db_dir)
        )
        
        # Mock extraction to fail on files 1 and 3
        def mock_extract(pdf_path):
            filename = Path(pdf_path).name
            if "textbook_1" in filename or "textbook_3" in filename:
                from src.data_processing.pdf_extractor import PDFExtractionError
                raise PDFExtractionError(f"Mock failure for {filename}")
            return "Educational content. " * 100
        
        # Use patch to mock ChromaDB at initialization time
        with patch('src.data_processing.etl_pipeline.ChromaDBManager') as MockChromaDB:
            # Setup mock ChromaDB manager
            mock_chroma_manager = Mock()
            mock_collection = Mock()
            mock_collection.count.return_value = 0
            mock_chroma_manager.collection = mock_collection
            mock_chroma_manager.create_collection = Mock(return_value=mock_collection)
            mock_chroma_manager.add_documents = Mock()
            mock_chroma_manager.count_documents = Mock(return_value=0)
            MockChromaDB.return_value = mock_chroma_manager
            
            # Create pipeline (will use mocked ChromaDB)
            pipeline = ETLPipeline(config)
            
            with patch.object(pipeline.pdf_extractor, 'extract_text', side_effect=mock_extract):
                with patch.object(pipeline.bedrock_client, 'generate_batch') as mock_bedrock:
                    mock_bedrock.return_value = [[0.1] * 1024 for _ in range(100)]
                    pipeline.bedrock_client.get_token_usage = Mock(return_value=10000)
                    pipeline.bedrock_client.calculate_cost = Mock(return_value=0.001)
                    
                    # Run pipeline
                    result = pipeline.run()
                    
                    # Verify mixed results
                    assert result.total_files == 5, "Should process all 5 files"
                    assert result.successful_files == 3, "3 files should succeed"
                    assert result.failed_files == 2, "2 files should fail"
                    
                    # Verify successful files produced chunks
                    assert result.total_chunks > 0, "Successful files should produce chunks"
                    
                    # Verify errors were recorded
                    assert len(result.errors) >= 2, "Should record errors for failed files"
                    
                    # Verify error handler tracked failures
                    assert pipeline.error_handler.get_error_count() >= 2
                    failed_files = pipeline.error_handler.get_failed_files()
                    assert len(failed_files) == 2
            
            # Cleanup
            try:
                del pipeline
                del mock_chroma_manager
                gc.collect()
                time.sleep(0.1)
            except Exception:
                pass


def test_pipeline_generates_summary_report():
    """Integration test: Verify pipeline generates comprehensive summary report.
    
    This test validates:
    - Summary report contains all required metrics
    - Report includes processing time and cost estimates
    - Report can be saved to disk
    - Report format is correct
    
    Validates: Requirements 8.4, 10.4
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test structure
        input_dir = temp_path / "input" / "kelas_10" / "informatika"
        input_dir.mkdir(parents=True, exist_ok=True)
        
        # Create 2 PDF files
        for i in range(2):
            (input_dir / f"test_{i}.pdf").write_text(f"Content {i}")
        
        output_dir = temp_path / "output"
        vector_db_dir = temp_path / "vector_db"
        
        config = PipelineConfig(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            vector_db_dir=str(vector_db_dir)
        )
        
        # Use patch to mock ChromaDB at initialization time
        with patch('src.data_processing.etl_pipeline.ChromaDBManager') as MockChromaDB:
            # Setup mock ChromaDB manager
            mock_chroma_manager = Mock()
            mock_collection = Mock()
            mock_collection.count.return_value = 0
            mock_chroma_manager.collection = mock_collection
            mock_chroma_manager.create_collection = Mock(return_value=mock_collection)
            mock_chroma_manager.add_documents = Mock()
            mock_chroma_manager.count_documents = Mock(return_value=0)
            MockChromaDB.return_value = mock_chroma_manager
            
            # Create pipeline (will use mocked ChromaDB)
            pipeline = ETLPipeline(config)
            
            with patch.object(pipeline.pdf_extractor, 'extract_text', return_value="Text " * 100):
                with patch.object(pipeline.bedrock_client, 'generate_batch', return_value=[[0.1] * 1024] * 10):
                    pipeline.bedrock_client.get_token_usage = Mock(return_value=5000)
                    pipeline.bedrock_client.calculate_cost = Mock(return_value=0.0005)
                    
                    # Run pipeline
                    result = pipeline.run()
                    
                    # Generate summary report with file output
                    report_path = output_dir / "metadata" / "test_report.json"
                    summary_report = pipeline.error_handler.generate_summary_report(
                        pipeline_result=result,
                        output_path=str(report_path)
                    )
                    
                    # Verify report structure
                    assert summary_report.pipeline_run_id
                    assert summary_report.start_time
                    assert summary_report.end_time
                    assert summary_report.processing_time_seconds > 0
                    assert summary_report.total_files == 2
                    assert summary_report.successful_files == 2
                    assert summary_report.failed_files == 0
                    assert summary_report.total_chunks > 0
                    assert summary_report.total_embeddings > 0
                    assert summary_report.estimated_cost_usd > 0
                    assert summary_report.status == "completed"
                    
                    # Verify report was saved to disk
                    assert report_path.exists(), "Report should be saved to disk"
                    
                    # Verify report can be read back
                    import json
                    with open(report_path, 'r') as f:
                        report_data = json.load(f)
                    
                    assert report_data["total_files"] == 2
                    assert report_data["status"] == "completed"
            
            # Cleanup
            try:
                del pipeline
                del mock_chroma_manager
                gc.collect()
                time.sleep(0.1)
            except Exception:
                pass
