"""
VKP End-to-End Checkpoint Test

This test simulates the complete VKP workflow:
1. Mock PDF upload to S3
2. Mock Lambda processing (PDF -> text -> chunks -> embeddings -> VKP)
3. Verify VKP creation and integrity
4. Verify VKP serialization/deserialization
5. Test delta updates

Since AWS resources may not be available, this uses local simulation with mocks.

Requirements: 8.5, 8.6
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.vkp.models import VKP, VKPChunk, ChunkMetadata
from src.vkp.packager import VKPPackager
from src.vkp.delta import DeltaCalculator


class TestVKPEndToEnd:
    """End-to-end VKP workflow tests."""
    
    def test_complete_vkp_workflow(self):
        """
        Test complete VKP workflow from PDF to packaged VKP.
        
        Simulates:
        1. PDF upload (mocked)
        2. Text extraction (mocked)
        3. Chunking (mocked)
        4. Embedding generation (mocked)
        5. VKP packaging
        6. Checksum verification
        7. Serialization
        8. Deserialization
        """
        # Step 1: Mock PDF upload
        pdf_filename = "Matematika_Kelas_10_Semester_1.pdf"
        
        # Step 2: Mock text extraction
        extracted_text = """
        Bab 1: Persamaan Linear
        
        Persamaan linear adalah persamaan yang variabelnya berpangkat satu.
        Bentuk umum: ax + b = 0
        
        Contoh:
        2x + 5 = 0
        x = -5/2
        
        Bab 2: Teorema Pythagoras
        
        Dalam segitiga siku-siku, kuadrat sisi miring sama dengan 
        jumlah kuadrat kedua sisi lainnya.
        a² + b² = c²
        """
        
        # Step 3: Mock chunking (simulate 800 token chunks with 100 overlap)
        chunks_data = [
            {
                "text": "Bab 1: Persamaan Linear\n\nPersamaan linear adalah persamaan yang variabelnya berpangkat satu.\nBentuk umum: ax + b = 0",
                "page": 1,
                "section": "Bab 1",
                "topic": "Persamaan Linear"
            },
            {
                "text": "Contoh:\n2x + 5 = 0\nx = -5/2",
                "page": 1,
                "section": "Bab 1",
                "topic": "Persamaan Linear"
            },
            {
                "text": "Bab 2: Teorema Pythagoras\n\nDalam segitiga siku-siku, kuadrat sisi miring sama dengan jumlah kuadrat kedua sisi lainnya.\na² + b² = c²",
                "page": 2,
                "section": "Bab 2",
                "topic": "Teorema Pythagoras"
            }
        ]
        
        # Step 4: Mock embedding generation (simulate Bedrock Titan embeddings)
        # Titan produces 1536-dimensional embeddings
        def mock_generate_embedding(text):
            # Simple mock: hash text to generate deterministic embedding
            import hashlib
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            # Generate 1536 floats between -1 and 1
            embedding = [(hash_val * (i + 1) % 1000) / 500 - 1 for i in range(1536)]
            return embedding
        
        # Create VKP chunks with mock embeddings
        vkp_chunks = []
        for i, chunk_data in enumerate(chunks_data):
            chunk = VKPChunk(
                chunk_id=f"mat_10_s1_{i+1:03d}",
                text=chunk_data["text"],
                embedding=mock_generate_embedding(chunk_data["text"]),
                metadata=ChunkMetadata(
                    page=chunk_data["page"],
                    section=chunk_data["section"],
                    topic=chunk_data["topic"]
                )
            )
            vkp_chunks.append(chunk)
        
        # Step 5: Create VKP package
        packager = VKPPackager()
        vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=vkp_chunks,
            source_files=[pdf_filename]
        )
        
        # Step 6: Verify VKP structure
        assert vkp.version == "1.0.0"
        assert vkp.subject == "matematika"
        assert vkp.grade == 10
        assert vkp.semester == 1
        assert vkp.total_chunks == 3
        assert len(vkp.chunks) == 3
        assert vkp.source_files == [pdf_filename]
        
        # Step 7: Verify checksum
        assert vkp.checksum.startswith("sha256:")
        assert len(vkp.checksum) == 71
        assert packager.verify_checksum(vkp) is True
        
        # Step 8: Verify embeddings
        for chunk in vkp.chunks:
            assert len(chunk.embedding) == 1536
            assert all(isinstance(x, (int, float)) for x in chunk.embedding)
        
        # Step 9: Serialize VKP
        serialized_data = packager.serialize(vkp)
        assert isinstance(serialized_data, bytes)
        assert len(serialized_data) > 0
        
        # Step 10: Deserialize VKP
        deserialized_vkp = packager.deserialize(serialized_data)
        
        # Step 11: Verify deserialized VKP matches original
        assert deserialized_vkp.version == vkp.version
        assert deserialized_vkp.subject == vkp.subject
        assert deserialized_vkp.grade == vkp.grade
        assert deserialized_vkp.semester == vkp.semester
        assert deserialized_vkp.checksum == vkp.checksum
        assert len(deserialized_vkp.chunks) == len(vkp.chunks)
        
        # Step 12: Verify checksum after deserialization
        assert packager.verify_checksum(deserialized_vkp) is True
        
        print("✓ Complete VKP workflow test passed")
    
    def test_vkp_file_operations(self, tmp_path):
        """
        Test VKP file save and load operations.
        """
        # Create sample VKP
        packager = VKPPackager()
        
        chunks = [
            VKPChunk(
                chunk_id="test_001",
                text="Sample text for testing",
                embedding=[0.1] * 1536,
                metadata=ChunkMetadata(page=1, section="Test")
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
        
        # Save to file
        filepath = tmp_path / "test_package.vkp"
        packager.serialize_to_file(vkp, str(filepath))
        
        # Verify file exists
        assert filepath.exists()
        assert filepath.stat().st_size > 0
        
        # Load from file
        loaded_vkp = packager.deserialize_from_file(str(filepath))
        
        # Verify loaded VKP
        assert loaded_vkp.version == vkp.version
        assert loaded_vkp.checksum == vkp.checksum
        assert packager.verify_checksum(loaded_vkp) is True
        
        print("✓ VKP file operations test passed")
    
    def test_vkp_delta_workflow(self):
        """
        Test VKP delta update workflow.
        
        Simulates:
        1. Create initial VKP v1.0.0
        2. Create updated VKP v1.1.0 with changes
        3. Calculate delta
        4. Verify delta efficiency
        5. Apply delta to recreate v1.1.0
        """
        packager = VKPPackager()
        calculator = DeltaCalculator()
        
        # Step 1: Create initial VKP v1.0.0
        initial_chunks = [
            VKPChunk(
                chunk_id="chunk_001",
                text="Original content 1",
                embedding=[0.1] * 1536,
                metadata=ChunkMetadata(page=1, section="Intro")
            ),
            VKPChunk(
                chunk_id="chunk_002",
                text="Original content 2",
                embedding=[0.2] * 1536,
                metadata=ChunkMetadata(page=2, section="Body")
            ),
            VKPChunk(
                chunk_id="chunk_003",
                text="Original content 3",
                embedding=[0.3] * 1536,
                metadata=ChunkMetadata(page=3, section="Conclusion")
            )
        ]
        
        vkp_v1 = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=initial_chunks,
            source_files=["matematika_v1.pdf"]
        )
        
        # Step 2: Create updated VKP v1.1.0 with changes
        # - Keep chunk_001 unchanged
        # - Modify chunk_002
        # - Remove chunk_003
        # - Add chunk_004
        updated_chunks = [
            initial_chunks[0],  # Unchanged
            VKPChunk(
                chunk_id="chunk_002",
                text="Modified content 2",  # Changed
                embedding=[0.25] * 1536,
                metadata=ChunkMetadata(page=2, section="Body")
            ),
            # chunk_003 removed
            VKPChunk(
                chunk_id="chunk_004",
                text="New content 4",  # Added
                embedding=[0.4] * 1536,
                metadata=ChunkMetadata(page=4, section="Appendix")
            )
        ]
        
        vkp_v1_1 = packager.create_package(
            version="1.1.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=updated_chunks,
            source_files=["matematika_v1.1.pdf"]
        )
        
        # Step 3: Calculate delta
        delta = calculator.calculate_delta(vkp_v1, vkp_v1_1)
        
        # Step 4: Verify delta structure
        assert delta.version == "1.1.0"
        assert delta.base_version == "1.0.0"
        assert delta.subject == "matematika"
        assert delta.grade == 10
        assert delta.semester == 1
        
        # Verify changes detected
        assert len(delta.added_chunks) == 2  # Modified + Added
        assert len(delta.removed_chunk_ids) == 1  # Removed
        assert "chunk_003" in delta.removed_chunk_ids
        
        # Verify added chunks
        added_ids = {chunk.chunk_id for chunk in delta.added_chunks}
        assert "chunk_002" in added_ids  # Modified
        assert "chunk_004" in added_ids  # Added
        
        # Step 5: Verify delta efficiency
        stats = calculator.calculate_delta_size_reduction(vkp_v1, vkp_v1_1)
        assert stats['full_size'] == 3
        assert stats['delta_size'] == 2
        assert stats['reduction'] == 1
        assert stats['reduction_percent'] > 0
        
        # Step 6: Apply delta to recreate v1.1.0
        recreated_vkp = calculator.apply_delta(vkp_v1, delta)
        
        # Step 7: Verify recreated VKP
        assert recreated_vkp.version == "1.1.0"
        assert len(recreated_vkp.chunks) == 3
        
        # Verify chunk IDs
        recreated_ids = {chunk.chunk_id for chunk in recreated_vkp.chunks}
        assert "chunk_001" in recreated_ids
        assert "chunk_002" in recreated_ids
        assert "chunk_004" in recreated_ids
        assert "chunk_003" not in recreated_ids
        
        # Verify modified chunk has new content
        chunk_002 = next(c for c in recreated_vkp.chunks if c.chunk_id == "chunk_002")
        assert chunk_002.text == "Modified content 2"
        
        print("✓ VKP delta workflow test passed")
    
    def test_lambda_handler_simulation(self):
        """
        Simulate Lambda handler processing a PDF and creating VKP.
        
        This simulates what the Lambda function would do:
        1. Receive S3 event
        2. Download PDF (mocked)
        3. Extract text (mocked)
        4. Chunk text (mocked)
        5. Generate embeddings (mocked)
        6. Create VKP
        7. Upload to S3 (mocked)
        """
        # Mock S3 event
        s3_event = {
            "Records": [{
                "s3": {
                    "bucket": {"name": "nexusai-curriculum-raw"},
                    "object": {"key": "raw/Matematika_Kelas_10_Semester_1.pdf"}
                }
            }]
        }
        
        # Extract metadata from filename
        filename = "Matematika_Kelas_10_Semester_1.pdf"
        parts = filename.replace(".pdf", "").split("_")
        subject = parts[0].lower()
        grade = int(parts[2])
        semester = int(parts[4])
        
        # Mock PDF processing
        mock_text = "Sample curriculum content for testing"
        mock_chunks = [
            {
                "text": mock_text,
                "page": 1,
                "section": "Test",
                "topic": "Testing"
            }
        ]
        
        # Mock embedding generation
        def mock_bedrock_embedding(text):
            return [0.1] * 1536
        
        # Create VKP chunks
        vkp_chunks = []
        for i, chunk_data in enumerate(mock_chunks):
            chunk = VKPChunk(
                chunk_id=f"{subject}_{grade}_s{semester}_{i+1:03d}",
                text=chunk_data["text"],
                embedding=mock_bedrock_embedding(chunk_data["text"]),
                metadata=ChunkMetadata(
                    page=chunk_data["page"],
                    section=chunk_data["section"],
                    topic=chunk_data["topic"]
                )
            )
            vkp_chunks.append(chunk)
        
        # Create VKP
        packager = VKPPackager()
        vkp = packager.create_package(
            version="1.0.0",
            subject=subject,
            grade=grade,
            semester=semester,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=vkp_chunks,
            source_files=[filename]
        )
        
        # Verify VKP
        assert vkp.subject == "matematika"
        assert vkp.grade == 10
        assert vkp.semester == 1
        assert packager.verify_checksum(vkp) is True
        
        # Mock S3 upload
        s3_key = packager.get_s3_key(vkp)
        assert s3_key == "matematika/kelas_10/v1.0.0.vkp"
        
        # Serialize for upload
        vkp_data = packager.serialize(vkp)
        assert len(vkp_data) > 0
        
        print("✓ Lambda handler simulation test passed")
    
    def test_checksum_corruption_detection(self):
        """
        Test that checksum corruption is detected.
        """
        packager = VKPPackager()
        
        # Create VKP
        chunks = [
            VKPChunk(
                chunk_id="test_001",
                text="Original text",
                embedding=[0.1] * 1536,
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
        
        # Verify original checksum is valid
        assert packager.verify_checksum(vkp) is True
        
        # Serialize
        data = packager.serialize(vkp)
        
        # Corrupt the data (modify a byte)
        corrupted_data = bytearray(data)
        corrupted_data[100] = (corrupted_data[100] + 1) % 256
        corrupted_data = bytes(corrupted_data)
        
        # Try to deserialize corrupted data
        with pytest.raises(ValueError, match="checksum verification failed"):
            packager.deserialize(corrupted_data)
        
        print("✓ Checksum corruption detection test passed")


def test_all_vkp_tests_pass():
    """
    Run all VKP property tests to ensure they pass.
    """
    import subprocess
    
    result = subprocess.run(
        ["pytest", "tests/property/test_vkp_structure.py", 
         "tests/property/test_vkp_checksum.py",
         "tests/property/test_vkp_serialization_roundtrip.py",
         "tests/property/test_vkp_delta_efficiency.py",
         "-v"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"VKP property tests failed:\n{result.stdout}\n{result.stderr}"
    print("✓ All VKP property tests passed")


if __name__ == "__main__":
    # Run tests
    test = TestVKPEndToEnd()
    
    print("\n=== VKP End-to-End Checkpoint Tests ===\n")
    
    test.test_complete_vkp_workflow()
    test.test_vkp_file_operations(Path(tempfile.mkdtemp()))
    test.test_vkp_delta_workflow()
    test.test_lambda_handler_simulation()
    test.test_checksum_corruption_detection()
    
    print("\n=== Running VKP Property Tests ===\n")
    test_all_vkp_tests_pass()
    
    print("\n✅ All VKP end-to-end checkpoint tests passed!")
