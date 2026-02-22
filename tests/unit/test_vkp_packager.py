"""
Unit tests for VKP Packager

Tests VKP creation, checksum calculation, serialization/deserialization,
and edge cases.

Requirements: 6.1-6.6
"""

import pytest
import json
import hashlib
from datetime import datetime, timezone

from src.vkp.models import VKP, VKPChunk, VKPMetadata, ChunkMetadata
from src.vkp.packager import VKPPackager


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing."""
    return [
        VKPChunk(
            chunk_id="test_001",
            text="Sample text 1",
            embedding=[0.1, 0.2, 0.3],
            metadata=ChunkMetadata(page=1, section="Intro", topic="Test")
        ),
        VKPChunk(
            chunk_id="test_002",
            text="Sample text 2",
            embedding=[0.4, 0.5, 0.6],
            metadata=ChunkMetadata(page=2, section="Body", topic="Test")
        )
    ]


@pytest.fixture
def packager():
    """Create VKPPackager instance."""
    return VKPPackager()


class TestVKPCreation:
    """Test VKP package creation with various inputs."""
    
    def test_create_valid_package(self, packager, sample_chunks):
        """Test creating a valid VKP package."""
        vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        assert vkp.version == "1.0.0"
        assert vkp.subject == "matematika"
        assert vkp.grade == 10
        assert vkp.semester == 1
        assert vkp.embedding_model == "amazon.titan-embed-text-v1"
        assert vkp.chunk_config == {'chunk_size': 800, 'chunk_overlap': 100}
        assert len(vkp.chunks) == 2
        assert vkp.total_chunks == 2
        assert vkp.source_files == ["test.pdf"]
        assert vkp.checksum.startswith("sha256:")
        assert len(vkp.checksum) == 71
    
    def test_create_package_with_empty_chunks(self, packager):
        """Test creating VKP with empty chunks list."""
        vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=[],
            source_files=["test.pdf"]
        )
        
        assert vkp.total_chunks == 0
        assert len(vkp.chunks) == 0
    
    def test_create_package_invalid_version(self, packager, sample_chunks):
        """Test creating VKP with invalid version format."""
        with pytest.raises(ValueError, match="semantic versioning"):
            packager.create_package(
                version="1.0",  # Invalid: missing PATCH
                subject="matematika",
                grade=10,
                semester=1,
                embedding_model="amazon.titan-embed-text-v1",
                chunk_size=800,
                chunk_overlap=100,
                chunks=sample_chunks,
                source_files=["test.pdf"]
            )
    
    def test_create_package_invalid_grade(self, packager, sample_chunks):
        """Test creating VKP with invalid grade."""
        with pytest.raises(ValueError, match="grade must be an integer between 1 and 12"):
            packager.create_package(
                version="1.0.0",
                subject="matematika",
                grade=13,  # Invalid: > 12
                semester=1,
                embedding_model="amazon.titan-embed-text-v1",
                chunk_size=800,
                chunk_overlap=100,
                chunks=sample_chunks,
                source_files=["test.pdf"]
            )
    
    def test_create_package_invalid_semester(self, packager, sample_chunks):
        """Test creating VKP with invalid semester."""
        with pytest.raises(ValueError, match="semester must be 1 or 2"):
            packager.create_package(
                version="1.0.0",
                subject="matematika",
                grade=10,
                semester=3,  # Invalid: must be 1 or 2
                embedding_model="amazon.titan-embed-text-v1",
                chunk_size=800,
                chunk_overlap=100,
                chunks=sample_chunks,
                source_files=["test.pdf"]
            )
    
    def test_create_package_empty_subject(self, packager, sample_chunks):
        """Test creating VKP with empty subject."""
        with pytest.raises(ValueError, match="subject must be a non-empty string"):
            packager.create_package(
                version="1.0.0",
                subject="",  # Invalid: empty
                grade=10,
                semester=1,
                embedding_model="amazon.titan-embed-text-v1",
                chunk_size=800,
                chunk_overlap=100,
                chunks=sample_chunks,
                source_files=["test.pdf"]
            )


class TestChecksumCalculation:
    """Test checksum calculation and verification."""
    
    def test_checksum_deterministic(self, packager, sample_chunks):
        """Test that checksum calculation is deterministic."""
        vkp1 = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        # Calculate checksum multiple times
        checksum1 = packager.calculate_checksum(vkp1)
        checksum2 = packager.calculate_checksum(vkp1)
        checksum3 = packager.calculate_checksum(vkp1)
        
        assert checksum1 == checksum2 == checksum3
    
    def test_checksum_detects_changes(self, packager, sample_chunks):
        """Test that checksum changes when content changes."""
        vkp1 = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        # Modify a chunk
        modified_chunks = sample_chunks.copy()
        modified_chunks[0] = VKPChunk(
            chunk_id="test_001",
            text="Modified text",  # Changed
            embedding=[0.1, 0.2, 0.3],
            metadata=ChunkMetadata(page=1, section="Intro", topic="Test")
        )
        
        vkp2 = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=modified_chunks,
            source_files=["test.pdf"]
        )
        
        assert vkp1.checksum != vkp2.checksum
    
    def test_verify_checksum_valid(self, packager, sample_chunks):
        """Test verifying a valid checksum."""
        vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        assert packager.verify_checksum(vkp) is True
    
    def test_verify_checksum_corrupted(self, packager, sample_chunks):
        """Test verifying a corrupted checksum."""
        vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        # Corrupt the checksum
        vkp.checksum = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
        
        assert packager.verify_checksum(vkp) is False


class TestSerialization:
    """Test VKP serialization and deserialization."""
    
    def test_serialize_to_bytes(self, packager, sample_chunks):
        """Test serializing VKP to bytes."""
        vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        data = packager.serialize(vkp)
        
        assert isinstance(data, bytes)
        assert len(data) > 0
        
        # Verify it's valid JSON
        json_str = data.decode('utf-8')
        parsed = json.loads(json_str)
        assert parsed['version'] == "1.0.0"
        assert parsed['subject'] == "matematika"
    
    def test_deserialize_from_bytes(self, packager, sample_chunks):
        """Test deserializing VKP from bytes."""
        original_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        data = packager.serialize(original_vkp)
        deserialized_vkp = packager.deserialize(data)
        
        assert deserialized_vkp.version == original_vkp.version
        assert deserialized_vkp.subject == original_vkp.subject
        assert deserialized_vkp.grade == original_vkp.grade
        assert deserialized_vkp.semester == original_vkp.semester
        assert deserialized_vkp.checksum == original_vkp.checksum
        assert len(deserialized_vkp.chunks) == len(original_vkp.chunks)
    
    def test_serialization_roundtrip(self, packager, sample_chunks):
        """Test that serialization->deserialization preserves data."""
        original_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        # Serialize and deserialize
        data = packager.serialize(original_vkp)
        roundtrip_vkp = packager.deserialize(data)
        
        # Verify all fields match
        assert roundtrip_vkp.version == original_vkp.version
        assert roundtrip_vkp.subject == original_vkp.subject
        assert roundtrip_vkp.grade == original_vkp.grade
        assert roundtrip_vkp.semester == original_vkp.semester
        assert roundtrip_vkp.embedding_model == original_vkp.embedding_model
        assert roundtrip_vkp.chunk_config == original_vkp.chunk_config
        assert roundtrip_vkp.checksum == original_vkp.checksum
        assert roundtrip_vkp.total_chunks == original_vkp.total_chunks
        assert roundtrip_vkp.source_files == original_vkp.source_files
        
        # Verify chunks
        for i, (orig_chunk, rt_chunk) in enumerate(zip(original_vkp.chunks, roundtrip_vkp.chunks)):
            assert rt_chunk.chunk_id == orig_chunk.chunk_id
            assert rt_chunk.text == orig_chunk.text
            assert rt_chunk.embedding == orig_chunk.embedding
    
    def test_deserialize_invalid_json(self, packager):
        """Test deserializing invalid JSON."""
        invalid_data = b"not valid json"
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            packager.deserialize(invalid_data)
    
    def test_deserialize_missing_required_field(self, packager):
        """Test deserializing JSON with missing required field."""
        incomplete_json = json.dumps({
            "version": "1.0.0",
            "subject": "matematika"
            # Missing many required fields
        }).encode('utf-8')
        
        with pytest.raises(ValueError, match="Missing required field"):
            packager.deserialize(incomplete_json)
    
    def test_deserialize_invalid_checksum(self, packager, sample_chunks):
        """Test deserializing VKP with invalid checksum."""
        vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        # Serialize and corrupt checksum
        vkp_dict = vkp.to_dict()
        vkp_dict['checksum'] = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
        corrupted_data = json.dumps(vkp_dict).encode('utf-8')
        
        with pytest.raises(ValueError, match="checksum verification failed"):
            packager.deserialize(corrupted_data)


class TestFileOperations:
    """Test file serialization and deserialization."""
    
    def test_serialize_to_file(self, packager, sample_chunks, tmp_path):
        """Test serializing VKP to file."""
        vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        filepath = tmp_path / "test.vkp"
        packager.serialize_to_file(vkp, str(filepath))
        
        assert filepath.exists()
        assert filepath.stat().st_size > 0
    
    def test_deserialize_from_file(self, packager, sample_chunks, tmp_path):
        """Test deserializing VKP from file."""
        original_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        filepath = tmp_path / "test.vkp"
        packager.serialize_to_file(original_vkp, str(filepath))
        
        loaded_vkp = packager.deserialize_from_file(str(filepath))
        
        assert loaded_vkp.version == original_vkp.version
        assert loaded_vkp.checksum == original_vkp.checksum
    
    def test_deserialize_from_nonexistent_file(self, packager):
        """Test deserializing from non-existent file."""
        with pytest.raises(FileNotFoundError):
            packager.deserialize_from_file("nonexistent.vkp")


class TestFilenameGeneration:
    """Test VKP filename and S3 key generation."""
    
    def test_get_vkp_filename(self, packager, sample_chunks):
        """Test generating standard VKP filename."""
        vkp = packager.create_package(
            version="1.2.3",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        filename = packager.get_vkp_filename(vkp)
        
        assert filename == "matematika_10_1_v1.2.3.vkp"
    
    def test_get_s3_key(self, packager, sample_chunks):
        """Test generating S3 key."""
        vkp = packager.create_package(
            version="1.2.3",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["test.pdf"]
        )
        
        s3_key = packager.get_s3_key(vkp)
        
        assert s3_key == "matematika/kelas_10/v1.2.3.vkp"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_chunks_list(self, packager):
        """Test VKP with empty chunks list."""
        vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=[],
            source_files=["test.pdf"]
        )
        
        assert vkp.total_chunks == 0
        assert len(vkp.chunks) == 0
        assert vkp.checksum.startswith("sha256:")
    
    def test_large_embedding_dimensions(self, packager):
        """Test VKP with large embedding dimensions."""
        large_embedding = [0.1] * 1536  # Titan embedding size
        
        chunks = [
            VKPChunk(
                chunk_id="test_001",
                text="Sample text",
                embedding=large_embedding,
                metadata=ChunkMetadata()
            )
        ]
        
        vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks,
            source_files=["test.pdf"]
        )
        
        assert len(vkp.chunks[0].embedding) == 1536
    
    def test_unicode_text_in_chunks(self, packager):
        """Test VKP with Unicode text."""
        chunks = [
            VKPChunk(
                chunk_id="test_001",
                text="Teorema Pythagoras: a² + b² = c²",
                embedding=[0.1, 0.2, 0.3],
                metadata=ChunkMetadata()
            )
        ]
        
        vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks,
            source_files=["test.pdf"]
        )
        
        # Serialize and deserialize
        data = packager.serialize(vkp)
        roundtrip_vkp = packager.deserialize(data)
        
        assert roundtrip_vkp.chunks[0].text == "Teorema Pythagoras: a² + b² = c²"
    
    def test_multiple_source_files(self, packager, sample_chunks):
        """Test VKP with multiple source files."""
        vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=sample_chunks,
            source_files=["file1.pdf", "file2.pdf", "file3.pdf"]
        )
        
        assert len(vkp.source_files) == 3
        assert "file1.pdf" in vkp.source_files
