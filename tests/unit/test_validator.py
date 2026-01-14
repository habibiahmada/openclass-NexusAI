"""Unit tests for validation and quality control.

Tests validation checks with complete data, missing files, invalid dimensions,
and missing metadata fields.
"""

import pytest
import tempfile
from pathlib import Path

from src.data_processing.validator import Validator, ValidationResult, QualityReport
from src.data_processing.metadata_manager import EnrichedChunk


class TestValidateExtraction:
    """Tests for validate_extraction method."""
    
    def test_validate_extraction_with_complete_data(self):
        """Test validation passes when all text files exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pdf_dir = temp_path / "pdfs"
            processed_dir = temp_path / "processed"
            
            pdf_dir.mkdir()
            processed_dir.mkdir()
            
            # Create PDF files
            pdf_files = [
                pdf_dir / "test1.pdf",
                pdf_dir / "test2.pdf",
                pdf_dir / "test3.pdf"
            ]
            for pdf_file in pdf_files:
                pdf_file.write_text("PDF content")
            
            # Create corresponding text files
            for pdf_file in pdf_files:
                text_file = processed_dir / (pdf_file.stem + ".txt")
                text_file.write_text("Extracted text")
            
            # Validate
            validator = Validator()
            result = validator.validate_extraction(pdf_files, str(processed_dir))
            
            assert result.passed
            assert result.details["total_pdfs"] == 3
            assert result.details["found_text_files"] == 3
            assert len(result.details["missing_text_files"]) == 0
    
    def test_validate_extraction_with_missing_files(self):
        """Test validation fails when text files are missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pdf_dir = temp_path / "pdfs"
            processed_dir = temp_path / "processed"
            
            pdf_dir.mkdir()
            processed_dir.mkdir()
            
            # Create PDF files
            pdf_files = [
                pdf_dir / "test1.pdf",
                pdf_dir / "test2.pdf",
                pdf_dir / "test3.pdf"
            ]
            for pdf_file in pdf_files:
                pdf_file.write_text("PDF content")
            
            # Create only some text files
            (processed_dir / "test1.txt").write_text("Extracted text")
            # test2.txt is missing
            (processed_dir / "test3.txt").write_text("Extracted text")
            
            # Validate
            validator = Validator()
            result = validator.validate_extraction(pdf_files, str(processed_dir))
            
            assert not result.passed
            assert result.details["total_pdfs"] == 3
            assert result.details["found_text_files"] == 2
            assert "test2.txt" in result.details["missing_text_files"]
    
    def test_validate_extraction_with_nonexistent_directory(self):
        """Test validation fails when processed directory doesn't exist."""
        pdf_files = [Path("test1.pdf"), Path("test2.pdf")]
        
        validator = Validator()
        result = validator.validate_extraction(pdf_files, "/nonexistent/directory")
        
        assert not result.passed
        assert "does not exist" in result.message


class TestValidateChunks:
    """Tests for validate_chunks method."""
    
    def test_validate_chunks_with_valid_data(self):
        """Test validation passes with valid chunks."""
        chunks = [
            EnrichedChunk(
                chunk_id=f"chunk_{i}",
                text=f"This is chunk {i}",
                source_file="test.pdf",
                subject="informatika",
                grade="kelas_10",
                chunk_index=i,
                char_start=i * 100,
                char_end=(i + 1) * 100
            )
            for i in range(10)
        ]
        
        validator = Validator()
        result = validator.validate_chunks(chunks)
        
        assert result.passed
        assert result.details["chunk_count"] == 10
        assert result.details["invalid_chunks"] == 0
    
    def test_validate_chunks_with_empty_list(self):
        """Test validation fails with empty chunk list."""
        validator = Validator()
        result = validator.validate_chunks([])
        
        assert not result.passed
        assert "No chunks found" in result.message
    
    def test_validate_chunks_with_invalid_positions(self):
        """Test validation fails when chunk positions are invalid."""
        chunks = [
            EnrichedChunk(
                chunk_id="chunk_1",
                text="Valid chunk",
                source_file="test.pdf",
                subject="informatika",
                grade="kelas_10",
                chunk_index=0,
                char_start=100,
                char_end=50  # Invalid: start > end
            )
        ]
        
        validator = Validator()
        result = validator.validate_chunks(chunks)
        
        assert not result.passed
        assert result.details["invalid_chunks"] > 0
    
    def test_validate_chunks_with_empty_text(self):
        """Test validation fails when chunk text is empty."""
        chunks = [
            EnrichedChunk(
                chunk_id="chunk_1",
                text="",  # Empty text
                source_file="test.pdf",
                subject="informatika",
                grade="kelas_10",
                chunk_index=0,
                char_start=0,
                char_end=100
            )
        ]
        
        validator = Validator()
        result = validator.validate_chunks(chunks)
        
        assert not result.passed
        assert result.details["invalid_chunks"] > 0
    
    def test_validate_chunks_with_count_range(self):
        """Test validation with expected chunk count range."""
        chunks = [
            EnrichedChunk(
                chunk_id=f"chunk_{i}",
                text=f"Chunk {i}",
                source_file="test.pdf",
                subject="informatika",
                grade="kelas_10",
                chunk_index=i,
                char_start=i * 100,
                char_end=(i + 1) * 100
            )
            for i in range(5)
        ]
        
        validator = Validator()
        
        # Should pass: 5 chunks within range [3, 10]
        result = validator.validate_chunks(chunks, expected_min_chunks=3, expected_max_chunks=10)
        assert result.passed
        
        # Should fail: 5 chunks below minimum 10
        result = validator.validate_chunks(chunks, expected_min_chunks=10)
        assert not result.passed
        
        # Should fail: 5 chunks above maximum 3
        result = validator.validate_chunks(chunks, expected_max_chunks=3)
        assert not result.passed


class TestValidateEmbeddings:
    """Tests for validate_embeddings method."""
    
    def test_validate_embeddings_with_correct_dimensions(self):
        """Test validation passes with correct embedding dimensions."""
        embeddings = [
            [0.1] * 1024
            for _ in range(10)
        ]
        
        validator = Validator()
        result = validator.validate_embeddings(embeddings, expected_dimension=1024)
        
        assert result.passed
        assert result.details["embedding_count"] == 10
        assert result.details["invalid_dimensions"] == 0
    
    def test_validate_embeddings_with_invalid_dimensions(self):
        """Test validation fails with wrong embedding dimensions."""
        embeddings = [
            [0.1] * 512  # Wrong dimension
            for _ in range(5)
        ]
        
        validator = Validator()
        result = validator.validate_embeddings(embeddings, expected_dimension=1024)
        
        assert not result.passed
        assert result.details["invalid_dimensions"] == 5
    
    def test_validate_embeddings_with_mixed_dimensions(self):
        """Test validation fails when embeddings have mixed dimensions."""
        embeddings = [
            [0.1] * 1024,  # Correct
            [0.1] * 512,   # Wrong
            [0.1] * 1024,  # Correct
            [0.1] * 768    # Wrong
        ]
        
        validator = Validator()
        result = validator.validate_embeddings(embeddings, expected_dimension=1024)
        
        assert not result.passed
        assert result.details["invalid_dimensions"] == 2
    
    def test_validate_embeddings_with_count_mismatch(self):
        """Test validation fails when embedding count doesn't match expected."""
        embeddings = [
            [0.1] * 1024
            for _ in range(5)
        ]
        
        validator = Validator()
        result = validator.validate_embeddings(
            embeddings, 
            expected_dimension=1024,
            expected_count=10  # Expected 10, got 5
        )
        
        assert not result.passed
        assert "count" in result.message.lower()
    
    def test_validate_embeddings_with_empty_list(self):
        """Test validation fails with empty embedding list."""
        validator = Validator()
        result = validator.validate_embeddings([])
        
        assert not result.passed
        assert "No embeddings found" in result.message


class TestValidateMetadata:
    """Tests for validate_metadata method."""
    
    def test_validate_metadata_with_complete_fields(self):
        """Test validation passes when all metadata fields are present."""
        chunks = [
            EnrichedChunk(
                chunk_id=f"chunk_{i}",
                text=f"Chunk text {i}",
                source_file="test.pdf",
                subject="informatika",
                grade="kelas_10",
                chunk_index=i,
                char_start=i * 100,
                char_end=(i + 1) * 100
            )
            for i in range(5)
        ]
        
        validator = Validator()
        result = validator.validate_metadata(chunks)
        
        assert result.passed
        assert result.details["chunk_count"] == 5
        assert len(result.details["missing_fields"]) == 0
        assert len(result.details["empty_fields"]) == 0
    
    def test_validate_metadata_with_empty_fields(self):
        """Test validation fails when metadata fields are empty."""
        chunks = [
            EnrichedChunk(
                chunk_id="",  # Empty
                text="Valid text",
                source_file="",  # Empty
                subject="informatika",
                grade="kelas_10",
                chunk_index=0,
                char_start=0,
                char_end=100
            )
        ]
        
        validator = Validator()
        result = validator.validate_metadata(chunks)
        
        assert not result.passed
        assert len(result.details["empty_fields"]) > 0
    
    def test_validate_metadata_with_empty_chunk_list(self):
        """Test validation fails with empty chunk list."""
        validator = Validator()
        result = validator.validate_metadata([])
        
        assert not result.passed
        assert "No chunks to validate" in result.message


class TestQualityReport:
    """Tests for quality report generation."""
    
    def test_generate_quality_report_all_pass(self):
        """Test quality report generation when all checks pass."""
        validator = Validator()
        
        # Add some passing validation results
        validator.validation_results = [
            ValidationResult(
                check_name="test1",
                passed=True,
                message="Test 1 passed"
            ),
            ValidationResult(
                check_name="test2",
                passed=True,
                message="Test 2 passed"
            )
        ]
        
        report = validator.generate_quality_report()
        
        assert report.total_checks == 2
        assert report.passed_checks == 2
        assert report.failed_checks == 0
        assert report.overall_status == "PASS"
    
    def test_generate_quality_report_with_failures(self):
        """Test quality report generation when some checks fail."""
        validator = Validator()
        
        # Add mixed validation results
        validator.validation_results = [
            ValidationResult(
                check_name="test1",
                passed=True,
                message="Test 1 passed"
            ),
            ValidationResult(
                check_name="test2",
                passed=False,
                message="Test 2 failed"
            ),
            ValidationResult(
                check_name="test3",
                passed=True,
                message="Test 3 passed"
            )
        ]
        
        report = validator.generate_quality_report()
        
        assert report.total_checks == 3
        assert report.passed_checks == 2
        assert report.failed_checks == 1
        assert report.overall_status == "FAIL"
    
    def test_generate_quality_report_saves_to_file(self):
        """Test quality report is saved to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.json"
            
            validator = Validator()
            validator.validation_results = [
                ValidationResult(
                    check_name="test1",
                    passed=True,
                    message="Test passed"
                )
            ]
            
            report = validator.generate_quality_report(output_path=str(output_path))
            
            assert output_path.exists()
            
            # Verify file content
            import json
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["total_checks"] == 1
            assert data["overall_status"] == "PASS"


class TestValidatorReset:
    """Tests for validator reset functionality."""
    
    def test_reset_clears_validation_results(self):
        """Test reset clears all validation results."""
        validator = Validator()
        
        # Add some validation results
        validator.validation_results = [
            ValidationResult(
                check_name="test1",
                passed=True,
                message="Test passed"
            )
        ]
        
        assert len(validator.validation_results) == 1
        
        # Reset
        validator.reset()
        
        assert len(validator.validation_results) == 0
