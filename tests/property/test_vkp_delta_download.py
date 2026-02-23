"""
Property Test: VKP Delta Download Only

**Property 19: VKP Delta Download Only**
**Validates: Requirements 7.3**

This test verifies that delta downloads only transfer changed chunks,
not the entire VKP package.

Test Strategy:
- Generate two VKP versions with some overlapping chunks
- Calculate delta between versions
- Verify delta contains only added/modified chunks
- Verify delta size is smaller than full VKP
- Verify applying delta produces correct result
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.vkp.models import VKP, VKPChunk, ChunkMetadata
from src.vkp.delta import DeltaCalculator, VKPDelta
from src.vkp.packager import VKPPackager


# Strategy for generating VKP chunks
@st.composite
def vkp_chunk(draw, chunk_id_prefix="chunk"):
    """Generate a VKPChunk with random data."""
    chunk_id = f"{chunk_id_prefix}_{draw(st.integers(min_value=0, max_value=1000))}"
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
def vkp_package(draw, version="1.0.0", subject="test", grade=10, num_chunks=None):
    """Generate a complete VKP package."""
    if num_chunks is None:
        num_chunks = draw(st.integers(min_value=5, max_value=20))
    
    chunks = [draw(vkp_chunk(chunk_id_prefix=f"chunk_{i}")) for i in range(num_chunks)]
    
    packager = VKPPackager()
    vkp = packager.create_package(
        version=version,
        subject=subject,
        grade=grade,
        semester=1,
        embedding_model="test-model",
        chunk_size=800,
        chunk_overlap=100,
        chunks=chunks,
        source_files=["test.pdf"]
    )
    
    return vkp


class TestVKPDeltaDownloadOnly:
    """Property tests for VKP delta download optimization."""
    
    @given(
        num_chunks_v1=st.integers(min_value=10, max_value=30),
        num_chunks_v2=st.integers(min_value=10, max_value=30),
        overlap_ratio=st.floats(min_value=0.3, max_value=0.9)
    )
    def test_delta_smaller_than_full(self, num_chunks_v1, num_chunks_v2, overlap_ratio):
        """
        Property: Delta package is smaller than full VKP when there's overlap.
        
        When versions share common chunks, delta should contain fewer chunks
        than the full new version.
        """
        # Calculate number of overlapping chunks
        num_overlap = int(min(num_chunks_v1, num_chunks_v2) * overlap_ratio)
        assume(num_overlap > 0)
        
        # Create v1 chunks
        chunks_v1 = []
        for i in range(num_chunks_v1):
            chunks_v1.append(VKPChunk(
                chunk_id=f"chunk_{i}",
                text=f"Text for chunk {i}",
                embedding=[0.1] * 128,
                metadata=ChunkMetadata()
            ))
        
        # Create v2 chunks (with overlap)
        chunks_v2 = []
        # Keep some chunks from v1 (overlap)
        for i in range(num_overlap):
            chunks_v2.append(chunks_v1[i])
        
        # Add new chunks
        for i in range(num_overlap, num_chunks_v2):
            chunks_v2.append(VKPChunk(
                chunk_id=f"chunk_{i}",
                text=f"New text for chunk {i}",
                embedding=[0.2] * 128,
                metadata=ChunkMetadata()
            ))
        
        # Create VKPs
        packager = VKPPackager()
        vkp_v1 = packager.create_package(
            version="1.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="test-model",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks_v1,
            source_files=["test.pdf"]
        )
        
        vkp_v2 = packager.create_package(
            version="2.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="test-model",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks_v2,
            source_files=["test.pdf"]
        )
        
        # Calculate delta
        calculator = DeltaCalculator()
        delta = calculator.calculate_delta(vkp_v1, vkp_v2)
        
        # Verify delta is smaller than full VKP
        delta_size = len(delta.added_chunks)
        full_size = len(vkp_v2.chunks)
        
        assert delta_size < full_size, \
            f"Delta size ({delta_size}) should be smaller than full VKP ({full_size})"
        
        # Verify delta contains only new/modified chunks
        expected_new_chunks = num_chunks_v2 - num_overlap
        assert delta_size == expected_new_chunks, \
            f"Delta should contain {expected_new_chunks} new chunks, got {delta_size}"
    
    @given(
        num_chunks=st.integers(min_value=10, max_value=20),
        num_modified=st.integers(min_value=1, max_value=5)
    )
    def test_delta_contains_only_changes(self, num_chunks, num_modified):
        """
        Property: Delta contains only added/modified chunks, not unchanged ones.
        
        When only a few chunks are modified, delta should contain only those chunks.
        """
        assume(num_modified < num_chunks)
        
        # Create v1 chunks
        chunks_v1 = []
        for i in range(num_chunks):
            chunks_v1.append(VKPChunk(
                chunk_id=f"chunk_{i}",
                text=f"Original text {i}",
                embedding=[0.1] * 128,
                metadata=ChunkMetadata()
            ))
        
        # Create v2 chunks (modify some)
        chunks_v2 = []
        for i in range(num_chunks):
            if i < num_modified:
                # Modified chunk
                chunks_v2.append(VKPChunk(
                    chunk_id=f"chunk_{i}",
                    text=f"Modified text {i}",  # Changed text
                    embedding=[0.2] * 128,  # Changed embedding
                    metadata=ChunkMetadata()
                ))
            else:
                # Unchanged chunk
                chunks_v2.append(chunks_v1[i])
        
        # Create VKPs
        packager = VKPPackager()
        vkp_v1 = packager.create_package(
            version="1.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="test-model",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks_v1,
            source_files=["test.pdf"]
        )
        
        vkp_v2 = packager.create_package(
            version="2.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="test-model",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks_v2,
            source_files=["test.pdf"]
        )
        
        # Calculate delta
        calculator = DeltaCalculator()
        delta = calculator.calculate_delta(vkp_v1, vkp_v2)
        
        # Verify delta contains only modified chunks
        assert len(delta.added_chunks) == num_modified, \
            f"Delta should contain {num_modified} modified chunks, got {len(delta.added_chunks)}"
        
        # Verify modified chunk IDs are correct
        modified_ids = {f"chunk_{i}" for i in range(num_modified)}
        delta_ids = {chunk.chunk_id for chunk in delta.added_chunks}
        
        assert delta_ids == modified_ids, \
            f"Delta chunk IDs {delta_ids} should match modified IDs {modified_ids}"
    
    @given(num_chunks=st.integers(min_value=5, max_value=15))
    def test_delta_apply_produces_correct_result(self, num_chunks):
        """
        Property: Applying delta to old VKP produces the new VKP.
        
        old_vkp + delta = new_vkp
        """
        # Create v1 chunks
        chunks_v1 = []
        for i in range(num_chunks):
            chunks_v1.append(VKPChunk(
                chunk_id=f"chunk_{i}",
                text=f"Text v1 {i}",
                embedding=[0.1] * 128,
                metadata=ChunkMetadata()
            ))
        
        # Create v2 chunks (modify half, keep half)
        chunks_v2 = []
        for i in range(num_chunks):
            if i % 2 == 0:
                # Keep chunk
                chunks_v2.append(chunks_v1[i])
            else:
                # Modify chunk
                chunks_v2.append(VKPChunk(
                    chunk_id=f"chunk_{i}",
                    text=f"Text v2 {i}",
                    embedding=[0.2] * 128,
                    metadata=ChunkMetadata()
                ))
        
        # Create VKPs
        packager = VKPPackager()
        vkp_v1 = packager.create_package(
            version="1.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="test-model",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks_v1,
            source_files=["test.pdf"]
        )
        
        vkp_v2 = packager.create_package(
            version="2.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="test-model",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks_v2,
            source_files=["test.pdf"]
        )
        
        # Calculate and apply delta
        calculator = DeltaCalculator()
        delta = calculator.calculate_delta(vkp_v1, vkp_v2)
        vkp_result = calculator.apply_delta(vkp_v1, delta)
        
        # Verify result matches v2
        assert vkp_result.version == vkp_v2.version
        assert vkp_result.total_chunks == vkp_v2.total_chunks
        assert len(vkp_result.chunks) == len(vkp_v2.chunks)
        
        # Verify chunk contents match
        result_chunks = {c.chunk_id: c for c in vkp_result.chunks}
        v2_chunks = {c.chunk_id: c for c in vkp_v2.chunks}
        
        assert set(result_chunks.keys()) == set(v2_chunks.keys()), \
            "Result chunk IDs should match v2 chunk IDs"
        
        for chunk_id in result_chunks:
            assert result_chunks[chunk_id].text == v2_chunks[chunk_id].text, \
                f"Chunk {chunk_id} text mismatch"
            assert result_chunks[chunk_id].embedding == v2_chunks[chunk_id].embedding, \
                f"Chunk {chunk_id} embedding mismatch"
    
    def test_delta_bandwidth_savings(self):
        """
        Property: Delta download saves bandwidth compared to full download.
        
        When 80% of chunks are unchanged, delta should be ~20% of full size.
        """
        num_chunks = 100
        num_changed = 20  # 20% changed
        
        # Create v1 chunks
        chunks_v1 = []
        for i in range(num_chunks):
            chunks_v1.append(VKPChunk(
                chunk_id=f"chunk_{i}",
                text=f"Text {i}" * 10,  # Make text larger
                embedding=[0.1] * 1536,  # Titan embedding size
                metadata=ChunkMetadata()
            ))
        
        # Create v2 chunks (change 20%)
        chunks_v2 = []
        for i in range(num_chunks):
            if i < num_changed:
                chunks_v2.append(VKPChunk(
                    chunk_id=f"chunk_{i}",
                    text=f"New text {i}" * 10,
                    embedding=[0.2] * 1536,
                    metadata=ChunkMetadata()
                ))
            else:
                chunks_v2.append(chunks_v1[i])
        
        # Create VKPs
        packager = VKPPackager()
        vkp_v1 = packager.create_package(
            version="1.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks_v1,
            source_files=["test.pdf"]
        )
        
        vkp_v2 = packager.create_package(
            version="2.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks_v2,
            source_files=["test.pdf"]
        )
        
        # Calculate delta
        calculator = DeltaCalculator()
        delta = calculator.calculate_delta(vkp_v1, vkp_v2)
        
        # Calculate sizes
        full_vkp_bytes = len(packager.serialize(vkp_v2))
        
        # Serialize delta (approximate)
        import json
        delta_bytes = len(json.dumps(delta.to_dict()).encode('utf-8'))
        
        # Verify bandwidth savings
        savings_ratio = 1 - (delta_bytes / full_vkp_bytes)
        
        assert savings_ratio > 0.5, \
            f"Delta should save >50% bandwidth, got {savings_ratio:.1%} savings"
        
        assert len(delta.added_chunks) == num_changed, \
            f"Delta should contain {num_changed} chunks, got {len(delta.added_chunks)}"
    
    def test_delta_with_removed_chunks(self):
        """
        Property: Delta correctly handles removed chunks.
        
        When chunks are removed in new version, delta should list them.
        """
        # Create v1 with 10 chunks
        chunks_v1 = []
        for i in range(10):
            chunks_v1.append(VKPChunk(
                chunk_id=f"chunk_{i}",
                text=f"Text {i}",
                embedding=[0.1] * 128,
                metadata=ChunkMetadata()
            ))
        
        # Create v2 with only 5 chunks (remove last 5)
        chunks_v2 = chunks_v1[:5]
        
        # Create VKPs
        packager = VKPPackager()
        vkp_v1 = packager.create_package(
            version="1.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="test-model",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks_v1,
            source_files=["test.pdf"]
        )
        
        vkp_v2 = packager.create_package(
            version="2.0.0",
            subject="test",
            grade=10,
            semester=1,
            embedding_model="test-model",
            chunk_size=800,
            chunk_overlap=100,
            chunks=chunks_v2,
            source_files=["test.pdf"]
        )
        
        # Calculate delta
        calculator = DeltaCalculator()
        delta = calculator.calculate_delta(vkp_v1, vkp_v2)
        
        # Verify removed chunks are listed
        assert len(delta.removed_chunk_ids) == 5, \
            f"Delta should list 5 removed chunks, got {len(delta.removed_chunk_ids)}"
        
        expected_removed = {f"chunk_{i}" for i in range(5, 10)}
        assert set(delta.removed_chunk_ids) == expected_removed, \
            f"Removed chunk IDs should be {expected_removed}, got {set(delta.removed_chunk_ids)}"
        
        # Verify no added chunks (all kept chunks are unchanged)
        assert len(delta.added_chunks) == 0, \
            f"Delta should have no added chunks, got {len(delta.added_chunks)}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
