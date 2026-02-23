"""
Property Test: VKP Checksum Verification Before Installation

**Property 20: VKP Checksum Verification Before Installation**
**Validates: Requirements 7.4**

This test verifies that VKP integrity is verified using checksums before
installation, and corrupted VKPs are rejected.

Test Strategy:
- Generate VKP packages with valid checksums
- Verify checksum validation detects any modifications
- Verify corrupted VKPs are rejected
- Verify checksum is deterministic (same VKP = same checksum)
"""

import pytest
import copy
from hypothesis import given, strategies as st, settings, HealthCheck
from src.vkp.models import VKP, VKPChunk, ChunkMetadata
from src.vkp.packager import VKPPackager
from src.vkp.puller import VKPPuller


# Strategy for generating VKP chunks
@st.composite
def vkp_chunk(draw, chunk_id=None):
    """Generate a VKPChunk with random data."""
    if chunk_id is None:
        chunk_id = f"chunk_{draw(st.integers(min_value=0, max_value=1000))}"
    
    text = draw(st.text(min_size=10, max_size=100))
    embedding = draw(st.lists(
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=128,
        max_size=128
    ))
    
    return VKPChunk(
        chunk_id=chunk_id,
        text=text,
        embedding=embedding,
        metadata=ChunkMetadata(page=1, section="Test", topic="Testing")
    )


@st.composite
def vkp_package(draw, num_chunks=None):
    """Generate a complete VKP package."""
    if num_chunks is None:
        num_chunks = draw(st.integers(min_value=5, max_value=15))
    
    chunks = [draw(vkp_chunk(chunk_id=f"chunk_{i}")) for i in range(num_chunks)]
    
    packager = VKPPackager()
    vkp = packager.create_package(
        version="1.0.0",
        subject="test",
        grade=10,
        semester=1,
        embedding_model="test-model",
        chunk_size=800,
        chunk_overlap=100,
        chunks=chunks,
        source_files=["test.pdf"]
    )
    
    return vkp


class TestVKPChecksumVerification:
    """Property tests for VKP checksum verification."""
    
    # Suppress health checks for large VKP packages
    test_settings = settings(suppress_health_check=[HealthCheck.large_base_example, HealthCheck.data_too_large])
    
    @given(vkp=vkp_package())
    @test_settings
    def test_valid_checksum_passes_verification(self, vkp):
        """
        Property: A VKP with valid checksum passes verification.
        
        Any VKP created by VKPPackager should have a valid checksum.
        """
        packager = VKPPackager()
        
        # Verify checksum
        is_valid = packager.verify_checksum(vkp)
        
        assert is_valid, \
            f"VKP with valid checksum should pass verification"
    
    @given(vkp=vkp_package())
    @test_settings
    def test_modified_text_fails_verification(self, vkp):
        """
        Property: Modifying chunk text invalidates checksum.
        
        Any change to chunk text should cause checksum verification to fail.
        """
        packager = VKPPackager()
        
        # Store original checksum
        original_checksum = vkp.checksum
        
        # Modify chunk text
        vkp_modified = copy.deepcopy(vkp)
        if vkp_modified.chunks:
            vkp_modified.chunks[0].text = "MODIFIED TEXT"
        
        # Keep old checksum (simulate corruption)
        vkp_modified.checksum = original_checksum
        
        # Verify checksum fails
        is_valid = packager.verify_checksum(vkp_modified)
        
        assert not is_valid, \
            "Modified VKP should fail checksum verification"
    
    @given(vkp=vkp_package())
    @test_settings
    def test_modified_embedding_fails_verification(self, vkp):
        """
        Property: Modifying chunk embedding invalidates checksum.
        
        Any change to embeddings should cause checksum verification to fail.
        """
        packager = VKPPackager()
        
        # Store original checksum
        original_checksum = vkp.checksum
        
        # Modify embedding
        vkp_modified = copy.deepcopy(vkp)
        if vkp_modified.chunks:
            vkp_modified.chunks[0].embedding[0] = 999.0
        
        # Keep old checksum (simulate corruption)
        vkp_modified.checksum = original_checksum
        
        # Verify checksum fails
        is_valid = packager.verify_checksum(vkp_modified)
        
        assert not is_valid, \
            "Modified embedding should fail checksum verification"
    
    @given(vkp=vkp_package())
    @test_settings
    def test_modified_metadata_fails_verification(self, vkp):
        """
        Property: Modifying metadata invalidates checksum.
        
        Any change to VKP metadata should cause checksum verification to fail.
        """
        packager = VKPPackager()
        
        # Store original checksum
        original_checksum = vkp.checksum
        
        # Modify metadata
        vkp_modified = copy.deepcopy(vkp)
        vkp_modified.subject = "MODIFIED_SUBJECT"
        
        # Keep old checksum (simulate corruption)
        vkp_modified.checksum = original_checksum
        
        # Verify checksum fails
        is_valid = packager.verify_checksum(vkp_modified)
        
        assert not is_valid, \
            "Modified metadata should fail checksum verification"
    
    @given(vkp=vkp_package())
    @test_settings
    def test_checksum_is_deterministic(self, vkp):
        """
        Property: Checksum calculation is deterministic.
        
        Calculating checksum multiple times for the same VKP should
        produce the same result.
        """
        packager = VKPPackager()
        
        # Calculate checksum multiple times
        checksum1 = packager.calculate_checksum(vkp)
        checksum2 = packager.calculate_checksum(vkp)
        checksum3 = packager.calculate_checksum(vkp)
        
        assert checksum1 == checksum2 == checksum3, \
            "Checksum calculation should be deterministic"
    
    @given(vkp=vkp_package())
    @test_settings
    def test_serialization_preserves_checksum(self, vkp):
        """
        Property: Serialization and deserialization preserve checksum validity.
        
        A VKP that is serialized and then deserialized should still have
        a valid checksum.
        """
        packager = VKPPackager()
        
        # Serialize
        vkp_bytes = packager.serialize(vkp)
        
        # Deserialize
        vkp_restored = packager.deserialize(vkp_bytes)
        
        # Verify checksum is still valid
        is_valid = packager.verify_checksum(vkp_restored)
        
        assert is_valid, \
            "Deserialized VKP should have valid checksum"
        
        # Verify checksum matches original
        assert vkp_restored.checksum == vkp.checksum, \
            "Deserialized VKP should have same checksum as original"
    
    @given(vkp=vkp_package())
    @test_settings
    def test_puller_rejects_invalid_checksum(self, vkp):
        """
        Property: VKPPuller rejects VKPs with invalid checksums.
        
        The puller's verify_integrity method should return False for
        corrupted VKPs.
        """
        # Create puller
        puller = VKPPuller(
            bucket_name='test-bucket',
            version_manager=None,
            chroma_manager=None,
            book_repository=None
        )
        
        # Corrupt VKP
        vkp_corrupted = copy.deepcopy(vkp)
        if vkp_corrupted.chunks:
            vkp_corrupted.chunks[0].text = "CORRUPTED"
        # Don't recalculate checksum (simulate corruption)
        
        # Verify puller rejects it
        is_valid = puller.verify_integrity(vkp_corrupted)
        
        assert not is_valid, \
            "VKPPuller should reject VKP with invalid checksum"
    
    @given(vkp=vkp_package())
    @test_settings
    def test_puller_accepts_valid_checksum(self, vkp):
        """
        Property: VKPPuller accepts VKPs with valid checksums.
        
        The puller's verify_integrity method should return True for
        valid VKPs.
        """
        # Create puller
        puller = VKPPuller(
            bucket_name='test-bucket',
            version_manager=None,
            chroma_manager=None,
            book_repository=None
        )
        
        # Verify puller accepts it
        is_valid = puller.verify_integrity(vkp)
        
        assert is_valid, \
            "VKPPuller should accept VKP with valid checksum"
    
    def test_checksum_format_is_sha256(self):
        """
        Property: Checksum format is 'sha256:HEXDIGEST'.
        
        All checksums should start with 'sha256:' followed by 64 hex characters.
        """
        # Create a simple VKP
        chunks = [
            VKPChunk(
                chunk_id="chunk_0",
                text="Test text",
                embedding=[0.1] * 128,
                metadata=ChunkMetadata()
            )
        ]
        
        packager = VKPPackager()
        vkp = packager.create_package(
            version="1.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="test-model",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks,
            source_files=["test.pdf"]
        )
        
        # Verify checksum format
        assert vkp.checksum.startswith('sha256:'), \
            "Checksum should start with 'sha256:'"
        
        # Extract hex part
        hex_part = vkp.checksum[7:]  # Remove 'sha256:' prefix
        
        assert len(hex_part) == 64, \
            f"Checksum hex part should be 64 characters, got {len(hex_part)}"
        
        # Verify all characters are hex
        assert all(c in '0123456789abcdef' for c in hex_part), \
            "Checksum should contain only hex characters"
    
    @given(
        num_chunks=st.integers(min_value=5, max_value=10),
        modification_index=st.integers(min_value=0, max_value=4)
    )
    def test_any_chunk_modification_detected(self, num_chunks, modification_index):
        """
        Property: Modification to any chunk is detected.
        
        Modifying any chunk in the VKP should cause checksum verification to fail.
        """
        # Ensure modification_index is valid
        if modification_index >= num_chunks:
            modification_index = num_chunks - 1
        
        # Create VKP
        chunks = []
        for i in range(num_chunks):
            chunks.append(VKPChunk(
                chunk_id=f"chunk_{i}",
                text=f"Text {i}",
                embedding=[0.1] * 128,
                metadata=ChunkMetadata()
            ))
        
        packager = VKPPackager()
        vkp = packager.create_package(
            version="1.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="test-model",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks,
            source_files=["test.pdf"]
        )
        
        # Store original checksum
        original_checksum = vkp.checksum
        
        # Modify specific chunk
        vkp_modified = copy.deepcopy(vkp)
        vkp_modified.chunks[modification_index].text = "MODIFIED"
        vkp_modified.checksum = original_checksum  # Keep old checksum
        
        # Verify modification is detected
        is_valid = packager.verify_checksum(vkp_modified)
        
        assert not is_valid, \
            f"Modification to chunk {modification_index} should be detected"
    
    def test_checksum_different_for_different_vkps(self):
        """
        Property: Different VKPs have different checksums.
        
        Two VKPs with different content should have different checksums.
        """
        packager = VKPPackager()
        
        # Create VKP 1
        chunks1 = [
            VKPChunk(
                chunk_id="chunk_0",
                text="Text 1",
                embedding=[0.1] * 128,
                metadata=ChunkMetadata()
            )
        ]
        
        vkp1 = packager.create_package(
            version="1.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="test-model",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks1,
            source_files=["test.pdf"]
        )
        
        # Create VKP 2 (different content)
        chunks2 = [
            VKPChunk(
                chunk_id="chunk_0",
                text="Text 2",  # Different text
                embedding=[0.1] * 128,
                metadata=ChunkMetadata()
            )
        ]
        
        vkp2 = packager.create_package(
            version="1.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="test-model",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks2,
            source_files=["test.pdf"]
        )
        
        # Verify checksums are different
        assert vkp1.checksum != vkp2.checksum, \
            "Different VKPs should have different checksums"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
