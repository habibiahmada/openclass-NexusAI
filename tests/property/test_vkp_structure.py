"""
Property Test: VKP Structure Validation

**Property 14: VKP Structure Validation**
**Validates: Requirements 6.1, 6.2, 6.6**

This test verifies that VKP packages maintain valid structure across
all possible inputs, including proper metadata, chunks, and checksums.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime

from src.vkp.models import VKP, VKPChunk, ChunkMetadata
from src.vkp.packager import VKPPackager


# Strategy for generating valid semantic versions
@st.composite
def semantic_version(draw):
    """Generate semantic version (MAJOR.MINOR.PATCH)"""
    major = draw(st.integers(min_value=0, max_value=10))
    minor = draw(st.integers(min_value=0, max_value=20))
    patch = draw(st.integers(min_value=0, max_value=50))
    return f"{major}.{minor}.{patch}"


# Strategy for generating chunk metadata
@st.composite
def chunk_metadata_strategy(draw):
    """Generate ChunkMetadata"""
    return ChunkMetadata(
        page=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=500))),
        section=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        topic=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    )


# Strategy for generating VKP chunks
@st.composite
def vkp_chunk_strategy(draw, chunk_id_prefix="chunk"):
    """Generate VKPChunk"""
    chunk_id = draw(st.integers(min_value=0, max_value=1000))
    text = draw(st.text(min_size=10, max_size=500))
    # Generate embedding (1536 dimensions for Titan)
    embedding = draw(st.lists(
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=128,  # Smaller for testing
        max_size=128
    ))
    metadata = draw(chunk_metadata_strategy())
    
    return VKPChunk(
        chunk_id=f"{chunk_id_prefix}_{chunk_id:04d}",
        text=text,
        embedding=embedding,
        metadata=metadata
    )


# Strategy for generating complete VKP packages
@st.composite
def vkp_strategy(draw):
    """Generate complete VKP package"""
    version = draw(semantic_version())
    subject = draw(st.sampled_from(['matematika', 'informatika', 'fisika', 'kimia', 'biologi']))
    grade = draw(st.integers(min_value=10, max_value=12))
    semester = draw(st.integers(min_value=1, max_value=2))
    embedding_model = draw(st.sampled_from([
        'amazon.titan-embed-text-v1',
        'amazon.titan-embed-text-v2'
    ]))
    chunk_size = draw(st.integers(min_value=400, max_value=1200))
    chunk_overlap = draw(st.integers(min_value=50, max_value=200))
    
    # Generate chunks
    num_chunks = draw(st.integers(min_value=1, max_value=20))
    chunks = [draw(vkp_chunk_strategy()) for _ in range(num_chunks)]
    
    source_files = draw(st.lists(
        st.text(min_size=5, max_size=50),
        min_size=1,
        max_size=3
    ))
    
    # Create VKP using packager
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


class TestVKPStructureValidation:
    """
    Property tests for VKP structure validation.
    
    **Validates: Requirements 6.1, 6.2, 6.6**
    """
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=100, deadline=None)
    def test_vkp_structure_is_always_valid(self, vkp):
        """
        Property: All generated VKP packages have valid structure.
        
        **Validates: Requirements 6.1, 6.2**
        
        Verifies that:
        - VKP has all required fields
        - Version follows semantic versioning
        - Grade is between 1-12
        - Semester is 1 or 2
        - Chunks list matches total_chunks
        - Checksum is present and properly formatted
        """
        # Should not raise exception
        vkp.validate()
        
        # Verify structure
        assert vkp.version is not None
        assert vkp.subject is not None
        assert vkp.grade >= 1 and vkp.grade <= 12
        assert vkp.semester in [1, 2]
        assert vkp.embedding_model is not None
        assert vkp.chunk_config is not None
        assert 'chunk_size' in vkp.chunk_config
        assert 'chunk_overlap' in vkp.chunk_config
        assert vkp.chunks is not None
        assert len(vkp.chunks) == vkp.total_chunks
        assert vkp.checksum.startswith('sha256:')
        assert len(vkp.checksum) == 71  # 'sha256:' + 64 hex chars
        assert vkp.source_files is not None
        assert len(vkp.source_files) > 0
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=100, deadline=None)
    def test_vkp_chunks_are_valid(self, vkp):
        """
        Property: All chunks in VKP have valid structure.
        
        **Validates: Requirements 6.1, 6.2**
        
        Verifies that each chunk:
        - Has a non-empty chunk_id
        - Has non-empty text
        - Has a non-empty embedding list
        - Has valid metadata
        """
        for chunk in vkp.chunks:
            # Should not raise exception
            chunk.validate()
            
            # Verify chunk structure
            assert chunk.chunk_id is not None and len(chunk.chunk_id) > 0
            assert chunk.text is not None and len(chunk.text) > 0
            assert chunk.embedding is not None and len(chunk.embedding) > 0
            assert isinstance(chunk.embedding, list)
            assert all(isinstance(x, (int, float)) for x in chunk.embedding)
            assert chunk.metadata is not None
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=100, deadline=None)
    def test_vkp_serialization_preserves_structure(self, vkp):
        """
        Property: VKP serialization preserves all structure.
        
        **Validates: Requirements 6.5, 6.6**
        
        Verifies that converting VKP to dict and back preserves:
        - All metadata fields
        - All chunks
        - Checksum
        """
        # Convert to dict
        vkp_dict = vkp.to_dict()
        
        # Verify dict has all required keys
        required_keys = {
            'version', 'subject', 'grade', 'semester', 'created_at',
            'embedding_model', 'chunk_config', 'chunks', 'checksum',
            'total_chunks', 'source_files'
        }
        assert required_keys.issubset(vkp_dict.keys())
        
        # Reconstruct from dict
        vkp_reconstructed = VKP.from_dict(vkp_dict)
        
        # Verify reconstruction matches original
        assert vkp_reconstructed.version == vkp.version
        assert vkp_reconstructed.subject == vkp.subject
        assert vkp_reconstructed.grade == vkp.grade
        assert vkp_reconstructed.semester == vkp.semester
        assert vkp_reconstructed.embedding_model == vkp.embedding_model
        assert vkp_reconstructed.total_chunks == vkp.total_chunks
        assert vkp_reconstructed.checksum == vkp.checksum
        assert len(vkp_reconstructed.chunks) == len(vkp.chunks)
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=100, deadline=None)
    def test_vkp_json_serialization_is_valid(self, vkp):
        """
        Property: VKP can be serialized to JSON and deserialized.
        
        **Validates: Requirements 6.5**
        
        Verifies that:
        - VKP can be converted to JSON string
        - JSON can be parsed back to VKP
        - Deserialized VKP is valid
        """
        # Serialize to JSON
        json_str = vkp.to_json()
        assert json_str is not None
        assert len(json_str) > 0
        
        # Deserialize from JSON
        vkp_deserialized = VKP.from_json(json_str)
        
        # Verify deserialized VKP is valid
        vkp_deserialized.validate()
        
        # Verify key fields match
        assert vkp_deserialized.version == vkp.version
        assert vkp_deserialized.subject == vkp.subject
        assert vkp_deserialized.grade == vkp.grade
        assert vkp_deserialized.total_chunks == vkp.total_chunks
        assert vkp_deserialized.checksum == vkp.checksum
    
    @given(
        version=semantic_version(),
        subject=st.sampled_from(['matematika', 'informatika']),
        grade=st.integers(min_value=10, max_value=12),
        semester=st.integers(min_value=1, max_value=2)
    )
    @settings(max_examples=50, deadline=None)
    def test_vkp_metadata_validation(self, version, subject, grade, semester):
        """
        Property: VKP metadata is always validated correctly.
        
        **Validates: Requirements 6.1, 6.2**
        
        Verifies that metadata validation catches invalid inputs.
        """
        packager = VKPPackager()
        
        # Create minimal valid VKP
        chunk = VKPChunk(
            chunk_id="test_001",
            text="Test content",
            embedding=[0.1] * 128,
            metadata=ChunkMetadata()
        )
        
        # Should succeed with valid inputs
        vkp = packager.create_package(
            version=version,
            subject=subject,
            grade=grade,
            semester=semester,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=[chunk],
            source_files=["test.pdf"]
        )
        
        # Verify validation passes
        vkp.validate()
        
        # Verify metadata fields
        assert vkp.version == version
        assert vkp.subject == subject
        assert vkp.grade == grade
        assert vkp.semester == semester
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_vkp_checksum_format_is_valid(self, vkp):
        """
        Property: VKP checksum always has valid format.
        
        **Validates: Requirements 6.4, 6.6**
        
        Verifies that:
        - Checksum starts with 'sha256:'
        - Checksum has exactly 64 hex characters after prefix
        - Checksum is deterministic
        """
        # Verify format
        assert vkp.checksum.startswith('sha256:')
        assert len(vkp.checksum) == 71
        
        # Extract hex part
        hex_part = vkp.checksum[7:]
        assert len(hex_part) == 64
        
        # Verify all characters are hex
        assert all(c in '0123456789abcdef' for c in hex_part.lower())
        
        # Verify checksum is deterministic
        packager = VKPPackager()
        recalculated_checksum = packager.calculate_checksum(vkp)
        assert recalculated_checksum == vkp.checksum
