"""
Property Test: VKP Checksum Integrity

**Property 16: VKP Checksum Integrity**
**Validates: Requirements 6.4**

This test verifies that VKP checksums correctly detect any modifications
to the package content, ensuring integrity verification works properly.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import copy

from src.vkp.models import VKP, VKPChunk, ChunkMetadata
from src.vkp.packager import VKPPackager


# Reuse strategies from test_vkp_structure
@st.composite
def semantic_version(draw):
    """Generate semantic version (MAJOR.MINOR.PATCH)"""
    major = draw(st.integers(min_value=0, max_value=10))
    minor = draw(st.integers(min_value=0, max_value=20))
    patch = draw(st.integers(min_value=0, max_value=50))
    return f"{major}.{minor}.{patch}"


@st.composite
def chunk_metadata_strategy(draw):
    """Generate ChunkMetadata"""
    return ChunkMetadata(
        page=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=500))),
        section=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        topic=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    )


@st.composite
def vkp_chunk_strategy(draw, chunk_id_prefix="chunk"):
    """Generate VKPChunk"""
    chunk_id = draw(st.integers(min_value=0, max_value=1000))
    text = draw(st.text(min_size=10, max_size=500))
    embedding = draw(st.lists(
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=128,
        max_size=128
    ))
    metadata = draw(chunk_metadata_strategy())
    
    return VKPChunk(
        chunk_id=f"{chunk_id_prefix}_{chunk_id:04d}",
        text=text,
        embedding=embedding,
        metadata=metadata
    )


@st.composite
def vkp_strategy(draw):
    """Generate complete VKP package"""
    version = draw(semantic_version())
    subject = draw(st.sampled_from(['matematika', 'informatika', 'fisika']))
    grade = draw(st.integers(min_value=10, max_value=12))
    semester = draw(st.integers(min_value=1, max_value=2))
    embedding_model = 'amazon.titan-embed-text-v1'
    chunk_size = draw(st.integers(min_value=400, max_value=1200))
    chunk_overlap = draw(st.integers(min_value=50, max_value=200))
    
    num_chunks = draw(st.integers(min_value=2, max_value=10))
    chunks = [draw(vkp_chunk_strategy()) for _ in range(num_chunks)]
    
    source_files = draw(st.lists(
        st.text(min_size=5, max_size=50),
        min_size=1,
        max_size=3
    ))
    
    packager = VKPPackager()
    vkp = packager.create_package(
        version=version,
        subject=subject,
        grade=grade,
        semester=semester,
        embedding_model=embedding_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunks=chunks,
        source_files=source_files
    )
    
    return vkp


class TestVKPChecksumIntegrity:
    """
    Property tests for VKP checksum integrity verification.
    
    **Validates: Requirements 6.4**
    """
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_checksum_is_deterministic(self, vkp):
        """
        Property: Checksum calculation is deterministic.
        
        **Validates: Requirements 6.4**
        
        Verifies that calculating checksum multiple times for the same
        VKP always produces the same result.
        """
        packager = VKPPackager()
        
        # Calculate checksum multiple times
        checksum1 = packager.calculate_checksum(vkp)
        checksum2 = packager.calculate_checksum(vkp)
        checksum3 = packager.calculate_checksum(vkp)
        
        # All checksums should be identical
        assert checksum1 == checksum2
        assert checksum2 == checksum3
        assert checksum1 == vkp.checksum
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_checksum_verification_succeeds_for_unmodified_vkp(self, vkp):
        """
        Property: Checksum verification succeeds for unmodified VKP.
        
        **Validates: Requirements 6.4**
        
        Verifies that a VKP with correct checksum passes verification.
        """
        packager = VKPPackager()
        
        # Verification should succeed
        assert packager.verify_checksum(vkp) is True
    
    @given(vkp=vkp_strategy(), new_text=st.text(min_size=5, max_size=100))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_checksum_detects_chunk_text_modification(self, vkp, new_text):
        """
        Property: Checksum detects modifications to chunk text.
        
        **Validates: Requirements 6.4**
        
        Verifies that modifying any chunk's text causes checksum
        verification to fail.
        """
        packager = VKPPackager()
        
        # Make a copy and modify first chunk's text
        vkp_modified = copy.deepcopy(vkp)
        if len(vkp_modified.chunks) > 0:
            original_text = vkp_modified.chunks[0].text
            vkp_modified.chunks[0].text = new_text
            
            # Only test if we actually changed something
            if original_text != new_text:
                # Verification should fail
                assert packager.verify_checksum(vkp_modified) is False
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_checksum_detects_chunk_embedding_modification(self, vkp):
        """
        Property: Checksum detects modifications to chunk embeddings.
        
        **Validates: Requirements 6.4**
        
        Verifies that modifying any chunk's embedding causes checksum
        verification to fail.
        """
        packager = VKPPackager()
        
        # Make a copy and modify first chunk's embedding
        vkp_modified = copy.deepcopy(vkp)
        if len(vkp_modified.chunks) > 0 and len(vkp_modified.chunks[0].embedding) > 0:
            # Flip the sign of first embedding value
            vkp_modified.chunks[0].embedding[0] = -vkp_modified.chunks[0].embedding[0]
            
            # Verification should fail
            assert packager.verify_checksum(vkp_modified) is False
    
    @given(vkp=vkp_strategy(), new_version=semantic_version())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_checksum_detects_metadata_modification(self, vkp, new_version):
        """
        Property: Checksum detects modifications to metadata.
        
        **Validates: Requirements 6.4**
        
        Verifies that modifying metadata (version, subject, etc.) causes
        checksum verification to fail.
        """
        packager = VKPPackager()
        
        # Make a copy and modify version
        vkp_modified = copy.deepcopy(vkp)
        original_version = vkp_modified.version
        vkp_modified.version = new_version
        
        # Only test if we actually changed something
        if original_version != new_version:
            # Verification should fail
            assert packager.verify_checksum(vkp_modified) is False
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_checksum_detects_chunk_removal(self, vkp):
        """
        Property: Checksum detects removal of chunks.
        
        **Validates: Requirements 6.4**
        
        Verifies that removing chunks causes checksum verification to fail.
        """
        packager = VKPPackager()
        
        # Make a copy and remove last chunk
        vkp_modified = copy.deepcopy(vkp)
        if len(vkp_modified.chunks) > 1:
            vkp_modified.chunks.pop()
            vkp_modified.total_chunks = len(vkp_modified.chunks)
            
            # Verification should fail
            assert packager.verify_checksum(vkp_modified) is False
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_checksum_detects_chunk_addition(self, vkp):
        """
        Property: Checksum detects addition of chunks.
        
        **Validates: Requirements 6.4**
        
        Verifies that adding chunks causes checksum verification to fail.
        """
        packager = VKPPackager()
        
        # Make a copy and add a new chunk
        vkp_modified = copy.deepcopy(vkp)
        new_chunk = VKPChunk(
            chunk_id="added_chunk",
            text="This is an added chunk",
            embedding=[0.5] * 128,
            metadata=ChunkMetadata()
        )
        vkp_modified.chunks.append(new_chunk)
        vkp_modified.total_chunks = len(vkp_modified.chunks)
        
        # Verification should fail
        assert packager.verify_checksum(vkp_modified) is False
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_checksum_detects_chunk_reordering(self, vkp):
        """
        Property: Checksum detects reordering of chunks.
        
        **Validates: Requirements 6.4**
        
        Verifies that changing the order of chunks causes checksum
        verification to fail (unless chunks form a palindrome).
        """
        packager = VKPPackager()
        
        # Make a copy and reverse chunk order
        vkp_modified = copy.deepcopy(vkp)
        if len(vkp_modified.chunks) > 1:
            # Check if chunks form a palindrome (same forward and backward)
            chunks_forward = [chunk.to_dict() for chunk in vkp_modified.chunks]
            chunks_backward = list(reversed(chunks_forward))
            is_palindrome = chunks_forward == chunks_backward
            
            # Only test if not a palindrome
            if not is_palindrome:
                vkp_modified.chunks.reverse()
                
                # Verification should fail
                assert packager.verify_checksum(vkp_modified) is False
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_serialization_preserves_checksum_validity(self, vkp):
        """
        Property: Serialization and deserialization preserve checksum validity.
        
        **Validates: Requirements 6.4, 6.5**
        
        Verifies that a VKP can be serialized and deserialized while
        maintaining checksum validity.
        """
        packager = VKPPackager()
        
        # Serialize
        data = packager.serialize(vkp)
        
        # Deserialize
        vkp_restored = packager.deserialize(data)
        
        # Checksum should still be valid
        assert packager.verify_checksum(vkp_restored) is True
        
        # Checksums should match
        assert vkp_restored.checksum == vkp.checksum
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_different_vkps_have_different_checksums(self, vkp):
        """
        Property: Different VKPs have different checksums.
        
        **Validates: Requirements 6.4**
        
        Verifies that modifying a VKP produces a different checksum.
        """
        packager = VKPPackager()
        
        # Create a modified version
        vkp_modified = copy.deepcopy(vkp)
        if len(vkp_modified.chunks) > 0:
            # Modify first chunk text
            vkp_modified.chunks[0].text = vkp_modified.chunks[0].text + " MODIFIED"
            
            # Recalculate checksum
            new_checksum = packager.calculate_checksum(vkp_modified)
            
            # Checksums should be different
            assert new_checksum != vkp.checksum
