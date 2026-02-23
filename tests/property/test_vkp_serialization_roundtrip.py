"""
Property Test: VKP Serialization Round-Trip

**Property 17: VKP Serialization Round-Trip**
**Validates: Requirements 6.5**

This test verifies that VKP packages can be serialized to JSON/bytes and
deserialized back without any data loss. All fields including metadata,
chunks, embeddings, and checksum must be preserved exactly.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import json

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
    # Generate embedding (smaller size for testing)
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
    num_chunks = draw(st.integers(min_value=1, max_value=15))
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


class TestVKPSerializationRoundTrip:
    """
    Property tests for VKP serialization round-trip.
    
    **Validates: Requirements 6.5**
    """
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_json_serialization_round_trip_preserves_all_data(self, vkp):
        """
        Property: JSON serialization round-trip preserves all VKP data.
        
        **Validates: Requirements 6.5**
        
        Verifies that:
        - VKP can be serialized to JSON string
        - JSON can be deserialized back to VKP
        - All fields are preserved exactly (metadata, chunks, embeddings, checksum)
        - Deserialized VKP is valid and passes checksum verification
        """
        packager = VKPPackager()
        
        # Serialize to JSON string
        json_str = vkp.to_json()
        assert json_str is not None
        assert len(json_str) > 0
        
        # Deserialize from JSON string
        vkp_restored = VKP.from_json(json_str)
        
        # Verify all metadata fields preserved
        assert vkp_restored.version == vkp.version
        assert vkp_restored.subject == vkp.subject
        assert vkp_restored.grade == vkp.grade
        assert vkp_restored.semester == vkp.semester
        assert vkp_restored.created_at == vkp.created_at
        assert vkp_restored.embedding_model == vkp.embedding_model
        assert vkp_restored.chunk_config == vkp.chunk_config
        assert vkp_restored.total_chunks == vkp.total_chunks
        assert vkp_restored.source_files == vkp.source_files
        assert vkp_restored.checksum == vkp.checksum
        
        # Verify chunks preserved
        assert len(vkp_restored.chunks) == len(vkp.chunks)
        
        for i, (original_chunk, restored_chunk) in enumerate(zip(vkp.chunks, vkp_restored.chunks)):
            assert restored_chunk.chunk_id == original_chunk.chunk_id, f"Chunk {i} ID mismatch"
            assert restored_chunk.text == original_chunk.text, f"Chunk {i} text mismatch"
            assert restored_chunk.embedding == original_chunk.embedding, f"Chunk {i} embedding mismatch"
            assert restored_chunk.metadata.page == original_chunk.metadata.page, f"Chunk {i} page mismatch"
            assert restored_chunk.metadata.section == original_chunk.metadata.section, f"Chunk {i} section mismatch"
            assert restored_chunk.metadata.topic == original_chunk.metadata.topic, f"Chunk {i} topic mismatch"
        
        # Verify checksum is still valid
        assert packager.verify_checksum(vkp_restored) is True
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_bytes_serialization_round_trip_preserves_all_data(self, vkp):
        """
        Property: Bytes serialization round-trip preserves all VKP data.
        
        **Validates: Requirements 6.5**
        
        Verifies that:
        - VKP can be serialized to bytes
        - Bytes can be deserialized back to VKP
        - All fields are preserved exactly
        - Checksum verification passes
        """
        packager = VKPPackager()
        
        # Serialize to bytes
        data = packager.serialize(vkp)
        assert data is not None
        assert len(data) > 0
        assert isinstance(data, bytes)
        
        # Deserialize from bytes
        vkp_restored = packager.deserialize(data)
        
        # Verify all metadata fields preserved
        assert vkp_restored.version == vkp.version
        assert vkp_restored.subject == vkp.subject
        assert vkp_restored.grade == vkp.grade
        assert vkp_restored.semester == vkp.semester
        assert vkp_restored.created_at == vkp.created_at
        assert vkp_restored.embedding_model == vkp.embedding_model
        assert vkp_restored.chunk_config == vkp.chunk_config
        assert vkp_restored.total_chunks == vkp.total_chunks
        assert vkp_restored.source_files == vkp.source_files
        assert vkp_restored.checksum == vkp.checksum
        
        # Verify chunks preserved
        assert len(vkp_restored.chunks) == len(vkp.chunks)
        
        for original_chunk, restored_chunk in zip(vkp.chunks, vkp_restored.chunks):
            assert restored_chunk.chunk_id == original_chunk.chunk_id
            assert restored_chunk.text == original_chunk.text
            assert restored_chunk.embedding == original_chunk.embedding
            assert restored_chunk.metadata.page == original_chunk.metadata.page
            assert restored_chunk.metadata.section == original_chunk.metadata.section
            assert restored_chunk.metadata.topic == original_chunk.metadata.topic
        
        # Verify checksum is still valid
        assert packager.verify_checksum(vkp_restored) is True
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large, HealthCheck.function_scoped_fixture])
    def test_file_serialization_round_trip_preserves_all_data(self, vkp, tmp_path):
        """
        Property: File serialization round-trip preserves all VKP data.
        
        **Validates: Requirements 6.5**
        
        Verifies that:
        - VKP can be saved to file
        - VKP can be loaded from file
        - All fields are preserved exactly
        """
        packager = VKPPackager()
        
        # Create temporary file path
        filepath = tmp_path / "test_vkp.vkp"
        
        # Serialize to file
        packager.serialize_to_file(vkp, str(filepath))
        assert filepath.exists()
        
        # Deserialize from file
        vkp_restored = packager.deserialize_from_file(str(filepath))
        
        # Verify all fields preserved
        assert vkp_restored.version == vkp.version
        assert vkp_restored.subject == vkp.subject
        assert vkp_restored.grade == vkp.grade
        assert vkp_restored.semester == vkp.semester
        assert vkp_restored.checksum == vkp.checksum
        assert len(vkp_restored.chunks) == len(vkp.chunks)
        
        # Verify checksum is still valid
        assert packager.verify_checksum(vkp_restored) is True
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_multiple_round_trips_preserve_data(self, vkp):
        """
        Property: Multiple serialization round-trips preserve data.
        
        **Validates: Requirements 6.5**
        
        Verifies that serializing and deserializing multiple times
        doesn't cause data degradation.
        """
        packager = VKPPackager()
        
        current_vkp = vkp
        
        # Perform 3 round-trips
        for i in range(3):
            # Serialize
            data = packager.serialize(current_vkp)
            
            # Deserialize
            current_vkp = packager.deserialize(data)
            
            # Verify still matches original
            assert current_vkp.version == vkp.version
            assert current_vkp.subject == vkp.subject
            assert current_vkp.checksum == vkp.checksum
            assert len(current_vkp.chunks) == len(vkp.chunks)
            
            # Verify checksum still valid
            assert packager.verify_checksum(current_vkp) is True
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_embedding_precision_preserved(self, vkp):
        """
        Property: Embedding float precision is preserved in round-trip.
        
        **Validates: Requirements 6.5**
        
        Verifies that floating-point embedding values maintain their
        precision through serialization and deserialization.
        """
        packager = VKPPackager()
        
        # Serialize and deserialize
        data = packager.serialize(vkp)
        vkp_restored = packager.deserialize(data)
        
        # Check embedding precision for all chunks
        for original_chunk, restored_chunk in zip(vkp.chunks, vkp_restored.chunks):
            assert len(restored_chunk.embedding) == len(original_chunk.embedding)
            
            for j, (original_val, restored_val) in enumerate(
                zip(original_chunk.embedding, restored_chunk.embedding)
            ):
                # Floats should be exactly equal (JSON preserves precision)
                assert restored_val == original_val, (
                    f"Embedding value mismatch at position {j}: "
                    f"{restored_val} != {original_val}"
                )
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_unicode_text_preserved(self, vkp):
        """
        Property: Unicode text in chunks is preserved in round-trip.
        
        **Validates: Requirements 6.5**
        
        Verifies that text containing Unicode characters (Indonesian,
        mathematical symbols, etc.) is preserved correctly.
        """
        packager = VKPPackager()
        
        # Add some Unicode text to first chunk if it doesn't have any
        if len(vkp.chunks) > 0:
            # Add Indonesian and mathematical symbols
            vkp.chunks[0].text = "Teorema Pythagoras: a² + b² = c² 🔺"
            # Recalculate checksum
            vkp.checksum = packager.calculate_checksum(vkp)
        
        # Serialize and deserialize
        data = packager.serialize(vkp)
        vkp_restored = packager.deserialize(data)
        
        # Verify Unicode text preserved
        if len(vkp.chunks) > 0:
            assert vkp_restored.chunks[0].text == vkp.chunks[0].text
            assert "Pythagoras" in vkp_restored.chunks[0].text
            assert "²" in vkp_restored.chunks[0].text
            assert "🔺" in vkp_restored.chunks[0].text
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_chunk_order_preserved(self, vkp):
        """
        Property: Chunk order is preserved in round-trip.
        
        **Validates: Requirements 6.5**
        
        Verifies that the order of chunks is maintained exactly
        through serialization and deserialization.
        """
        packager = VKPPackager()
        
        # Get original chunk IDs in order
        original_chunk_ids = [chunk.chunk_id for chunk in vkp.chunks]
        
        # Serialize and deserialize
        data = packager.serialize(vkp)
        vkp_restored = packager.deserialize(data)
        
        # Get restored chunk IDs in order
        restored_chunk_ids = [chunk.chunk_id for chunk in vkp_restored.chunks]
        
        # Order must be preserved
        assert restored_chunk_ids == original_chunk_ids
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_metadata_fields_preserved(self, vkp):
        """
        Property: All metadata fields are preserved in round-trip.
        
        **Validates: Requirements 6.5**
        
        Verifies that chunk metadata (page, section, topic) is preserved,
        including None values.
        """
        packager = VKPPackager()
        
        # Serialize and deserialize
        data = packager.serialize(vkp)
        vkp_restored = packager.deserialize(data)
        
        # Check all chunk metadata
        for original_chunk, restored_chunk in zip(vkp.chunks, vkp_restored.chunks):
            # All metadata fields must match, including None values
            assert restored_chunk.metadata.page == original_chunk.metadata.page
            assert restored_chunk.metadata.section == original_chunk.metadata.section
            assert restored_chunk.metadata.topic == original_chunk.metadata.topic
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_deserialized_vkp_is_valid(self, vkp):
        """
        Property: Deserialized VKP passes all validation checks.
        
        **Validates: Requirements 6.5**
        
        Verifies that a deserialized VKP is structurally valid and
        passes all validation rules.
        """
        packager = VKPPackager()
        
        # Serialize and deserialize
        data = packager.serialize(vkp)
        vkp_restored = packager.deserialize(data)
        
        # Should not raise exception
        vkp_restored.validate()
        
        # Verify validation passes for all chunks
        for chunk in vkp_restored.chunks:
            chunk.validate()
