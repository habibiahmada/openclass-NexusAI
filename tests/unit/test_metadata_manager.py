"""Unit tests for metadata manager."""

import pytest

from src.data_processing.metadata_manager import MetadataManager, FileMetadata
from src.data_processing.text_chunker import TextChunk


class TestMetadataManager:
    """Unit tests for MetadataManager class."""
    
    def test_parse_valid_path_standard_format(self):
        """Test parsing a valid path with standard format.
        
        Requirements: 3.1, 3.2
        """
        manager = MetadataManager()
        path = "data/raw_dataset/kelas_10/informatika/Informatika-BS-KLS-X.pdf"
        
        metadata = manager.parse_file_path(path)
        
        assert metadata.grade == "kelas_10"
        assert metadata.subject == "informatika"
        assert metadata.filename == "Informatika-BS-KLS-X.pdf"
    
    def test_parse_valid_path_different_grade(self):
        """Test parsing with different grade level.
        
        Requirements: 3.1, 3.2
        """
        manager = MetadataManager()
        path = "data/raw_dataset/kelas_12/matematika/Math-Book.pdf"
        
        metadata = manager.parse_file_path(path)
        
        assert metadata.grade == "kelas_12"
        assert metadata.subject == "matematika"
        assert metadata.filename == "Math-Book.pdf"
    
    def test_parse_valid_path_absolute(self):
        """Test parsing an absolute path.
        
        Requirements: 3.1, 3.2
        """
        manager = MetadataManager()
        path = "/home/user/data/raw_dataset/kelas_11/fisika/Physics.pdf"
        
        metadata = manager.parse_file_path(path)
        
        assert metadata.grade == "kelas_11"
        assert metadata.subject == "fisika"
        assert metadata.filename == "Physics.pdf"
    
    def test_parse_invalid_path_no_grade(self):
        """Test parsing fails when grade pattern is missing.
        
        Requirements: 3.1, 3.2
        """
        manager = MetadataManager()
        path = "data/raw_dataset/informatika/file.pdf"
        
        with pytest.raises(ValueError) as exc_info:
            manager.parse_file_path(path)
        
        assert "Could not extract grade and subject" in str(exc_info.value)
    
    def test_parse_invalid_path_no_subject(self):
        """Test parsing fails when subject is missing.
        
        Requirements: 3.1, 3.2
        """
        manager = MetadataManager()
        path = "data/raw_dataset/kelas_10/file.pdf"
        
        with pytest.raises(ValueError) as exc_info:
            manager.parse_file_path(path)
        
        assert "Could not extract grade and subject" in str(exc_info.value)
    
    def test_parse_invalid_path_wrong_format(self):
        """Test parsing fails with completely wrong format.
        
        Requirements: 3.1, 3.2
        """
        manager = MetadataManager()
        path = "some/random/path/file.pdf"
        
        with pytest.raises(ValueError) as exc_info:
            manager.parse_file_path(path)
        
        assert "Could not extract grade and subject" in str(exc_info.value)
    
    def test_enrich_chunk_basic(self):
        """Test basic chunk enrichment.
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
        """
        manager = MetadataManager()
        
        chunk = TextChunk(
            text="This is a test chunk",
            start_pos=0,
            end_pos=20,
            chunk_index=0
        )
        
        file_metadata = FileMetadata(
            subject="informatika",
            grade="kelas_10",
            filename="test.pdf"
        )
        
        enriched = manager.enrich_chunk(chunk, file_metadata)
        
        assert enriched.text == "This is a test chunk"
        assert enriched.source_file == "test.pdf"
        assert enriched.subject == "informatika"
        assert enriched.grade == "kelas_10"
        assert enriched.chunk_index == 0
        assert enriched.char_start == 0
        assert enriched.char_end == 20
        assert enriched.chunk_id  # Should have a UUID
        assert len(enriched.chunk_id) == 36  # UUID format
    
    def test_enrich_chunk_preserves_metadata(self):
        """Test that enrichment preserves all metadata fields.
        
        Requirements: 3.3, 3.5
        """
        manager = MetadataManager()
        
        chunk = TextChunk(
            text="Another chunk",
            start_pos=100,
            end_pos=113,
            chunk_index=5
        )
        
        file_metadata = FileMetadata(
            subject="matematika",
            grade="kelas_11",
            filename="math-book.pdf"
        )
        
        enriched = manager.enrich_chunk(chunk, file_metadata)
        
        # Verify all fields are preserved
        assert enriched.text == chunk.text
        assert enriched.chunk_index == chunk.chunk_index
        assert enriched.char_start == chunk.start_pos
        assert enriched.char_end == chunk.end_pos
        assert enriched.source_file == file_metadata.filename
        assert enriched.subject == file_metadata.subject
        assert enriched.grade == file_metadata.grade
    
    def test_enrich_multiple_chunks_unique_ids(self):
        """Test that multiple chunks get unique IDs.
        
        Requirements: 3.4
        """
        manager = MetadataManager()
        
        file_metadata = FileMetadata(
            subject="informatika",
            grade="kelas_10",
            filename="test.pdf"
        )
        
        chunks = [
            TextChunk(text=f"chunk {i}", start_pos=i*10, end_pos=(i+1)*10, chunk_index=i)
            for i in range(10)
        ]
        
        enriched_chunks = [
            manager.enrich_chunk(chunk, file_metadata)
            for chunk in chunks
        ]
        
        # Extract all chunk IDs
        chunk_ids = [e.chunk_id for e in enriched_chunks]
        
        # Verify all are unique
        assert len(chunk_ids) == len(set(chunk_ids))
