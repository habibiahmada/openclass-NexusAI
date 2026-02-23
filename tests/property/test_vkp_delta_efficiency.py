"""
Property Test: VKP Delta Update Efficiency

**Property 15: VKP Delta Update Efficiency**
**Validates: Requirements 6.3**

This test verifies that delta updates are smaller than full packages,
delta application produces correct results, and various modification
scenarios (add, remove, modify chunks) work correctly.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
import copy

from src.vkp.models import VKP, VKPChunk, ChunkMetadata
from src.vkp.packager import VKPPackager
from src.vkp.delta import DeltaCalculator


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


# Strategy for generating VKP chunks with unique IDs
@st.composite
def vkp_chunk_strategy(draw, chunk_index=None):
    """Generate VKPChunk with unique ID"""
    if chunk_index is not None:
        chunk_id = f"chunk_{chunk_index:04d}"
    else:
        chunk_id = f"chunk_{draw(st.integers(min_value=0, max_value=10000)):04d}"
    
    text = draw(st.text(min_size=10, max_size=500))
    embedding = draw(st.lists(
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=128,
        max_size=128
    ))
    metadata = draw(chunk_metadata_strategy())
    
    return VKPChunk(
        chunk_id=chunk_id,
        text=text,
        embedding=embedding,
        metadata=metadata
    )


# Strategy for generating complete VKP packages
@st.composite
def vkp_strategy(draw):
    """Generate complete VKP package with unique chunk IDs"""
    version = draw(semantic_version())
    subject = draw(st.sampled_from(['matematika', 'informatika', 'fisika']))
    grade = draw(st.integers(min_value=10, max_value=12))
    semester = draw(st.integers(min_value=1, max_value=2))
    embedding_model = 'amazon.titan-embed-text-v1'
    chunk_size = draw(st.integers(min_value=400, max_value=1200))
    chunk_overlap = draw(st.integers(min_value=50, max_value=200))
    
    # Generate chunks (at least 5 for meaningful delta tests) with unique IDs
    num_chunks = draw(st.integers(min_value=5, max_value=20))
    chunks = [draw(vkp_chunk_strategy(chunk_index=i)) for i in range(num_chunks)]
    
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


def increment_version(version: str) -> str:
    """Increment patch version"""
    parts = version.split('.')
    parts[2] = str(int(parts[2]) + 1)
    return '.'.join(parts)


class TestVKPDeltaEfficiency:
    """
    Property tests for VKP delta update efficiency.
    
    **Validates: Requirements 6.3**
    """
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.data_too_large, HealthCheck.large_base_example])
    def test_delta_is_smaller_than_full_package_when_few_changes(self, vkp):
        """
        Property: Delta update is smaller than full package when few chunks change.
        
        **Validates: Requirements 6.3**
        
        Verifies that when only a small percentage of chunks are modified,
        the delta package is significantly smaller than the full package.
        """
        calculator = DeltaCalculator()
        packager = VKPPackager()
        
        # Create modified version with only 20% of chunks changed
        new_vkp = copy.deepcopy(vkp)
        new_vkp.version = increment_version(vkp.version)
        
        # Modify approximately 20% of chunks
        num_to_modify = max(1, len(new_vkp.chunks) // 5)
        for i in range(num_to_modify):
            new_vkp.chunks[i].text = new_vkp.chunks[i].text + " MODIFIED"
        
        # Recalculate checksum
        new_vkp.checksum = packager.calculate_checksum(new_vkp)
        
        # Calculate delta
        delta = calculator.calculate_delta(vkp, new_vkp)
        
        # Delta should be smaller than full package
        delta_size = len(delta.added_chunks)
        full_size = len(new_vkp.chunks)
        
        assert delta_size < full_size, (
            f"Delta size ({delta_size}) should be smaller than full size ({full_size})"
        )
        
        # Delta should contain approximately the modified chunks
        assert delta_size <= num_to_modify + 1, (
            f"Delta size ({delta_size}) should be close to modified count ({num_to_modify})"
        )
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.data_too_large, HealthCheck.large_base_example])
    def test_delta_application_produces_correct_result(self, vkp):
        """
        Property: Applying delta produces the correct new VKP version.
        
        **Validates: Requirements 6.3**
        
        Verifies that applying a delta to an old VKP produces a new VKP
        that is identical to the target version.
        """
        calculator = DeltaCalculator()
        packager = VKPPackager()
        
        # Create modified version
        new_vkp = copy.deepcopy(vkp)
        new_vkp.version = increment_version(vkp.version)
        
        # Make some modifications
        if len(new_vkp.chunks) > 0:
            new_vkp.chunks[0].text = new_vkp.chunks[0].text + " MODIFIED"
        
        # Recalculate checksum
        new_vkp.checksum = packager.calculate_checksum(new_vkp)
        
        # Calculate delta
        delta = calculator.calculate_delta(vkp, new_vkp)
        
        # Apply delta
        result_vkp = calculator.apply_delta(vkp, delta)
        
        # Result should match new_vkp
        assert result_vkp.version == new_vkp.version
        assert result_vkp.subject == new_vkp.subject
        assert result_vkp.grade == new_vkp.grade
        assert result_vkp.semester == new_vkp.semester
        assert len(result_vkp.chunks) == len(new_vkp.chunks)
        
        # Verify chunk contents match
        result_chunk_map = {c.chunk_id: c for c in result_vkp.chunks}
        new_chunk_map = {c.chunk_id: c for c in new_vkp.chunks}
        
        assert set(result_chunk_map.keys()) == set(new_chunk_map.keys())
        
        for chunk_id in result_chunk_map:
            assert result_chunk_map[chunk_id].text == new_chunk_map[chunk_id].text
            assert result_chunk_map[chunk_id].embedding == new_chunk_map[chunk_id].embedding
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large, HealthCheck.large_base_example])
    def test_delta_handles_chunk_addition(self, vkp):
        """
        Property: Delta correctly handles adding new chunks.
        
        **Validates: Requirements 6.3**
        
        Verifies that when chunks are added, the delta contains only
        the new chunks and applying it produces the correct result.
        """
        calculator = DeltaCalculator()
        packager = VKPPackager()
        
        # Create modified version with added chunks
        new_vkp = copy.deepcopy(vkp)
        new_vkp.version = increment_version(vkp.version)
        
        # Add 2 new chunks
        new_chunk1 = VKPChunk(
            chunk_id="added_001",
            text="This is a new chunk",
            embedding=[0.5] * 128,
            metadata=ChunkMetadata()
        )
        new_chunk2 = VKPChunk(
            chunk_id="added_002",
            text="This is another new chunk",
            embedding=[0.6] * 128,
            metadata=ChunkMetadata()
        )
        new_vkp.chunks.extend([new_chunk1, new_chunk2])
        new_vkp.total_chunks = len(new_vkp.chunks)
        
        # Recalculate checksum
        new_vkp.checksum = packager.calculate_checksum(new_vkp)
        
        # Calculate delta
        delta = calculator.calculate_delta(vkp, new_vkp)
        
        # Delta should contain the 2 added chunks
        assert len(delta.added_chunks) == 2
        assert len(delta.removed_chunk_ids) == 0
        
        # Apply delta
        result_vkp = calculator.apply_delta(vkp, delta)
        
        # Result should have all chunks including new ones
        assert len(result_vkp.chunks) == len(new_vkp.chunks)
        assert "added_001" in [c.chunk_id for c in result_vkp.chunks]
        assert "added_002" in [c.chunk_id for c in result_vkp.chunks]
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large, HealthCheck.large_base_example])
    def test_delta_handles_chunk_removal(self, vkp):
        """
        Property: Delta correctly handles removing chunks.
        
        **Validates: Requirements 6.3**
        
        Verifies that when chunks are removed, the delta contains the
        removed chunk IDs and applying it produces the correct result.
        """
        # Need at least 3 chunks to remove some
        assume(len(vkp.chunks) >= 3)
        
        calculator = DeltaCalculator()
        packager = VKPPackager()
        
        # Create modified version with removed chunks
        new_vkp = copy.deepcopy(vkp)
        new_vkp.version = increment_version(vkp.version)
        
        # Remove last 2 chunks
        removed_ids = [new_vkp.chunks[-1].chunk_id, new_vkp.chunks[-2].chunk_id]
        new_vkp.chunks = new_vkp.chunks[:-2]
        new_vkp.total_chunks = len(new_vkp.chunks)
        
        # Recalculate checksum
        new_vkp.checksum = packager.calculate_checksum(new_vkp)
        
        # Calculate delta
        delta = calculator.calculate_delta(vkp, new_vkp)
        
        # Delta should contain the removed chunk IDs
        assert len(delta.removed_chunk_ids) == 2
        assert set(delta.removed_chunk_ids) == set(removed_ids)
        
        # Apply delta
        result_vkp = calculator.apply_delta(vkp, delta)
        
        # Result should not have removed chunks
        assert len(result_vkp.chunks) == len(new_vkp.chunks)
        result_ids = [c.chunk_id for c in result_vkp.chunks]
        for removed_id in removed_ids:
            assert removed_id not in result_ids
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large, HealthCheck.large_base_example])
    def test_delta_handles_chunk_modification(self, vkp):
        """
        Property: Delta correctly handles modifying existing chunks.
        
        **Validates: Requirements 6.3**
        
        Verifies that when chunks are modified (same ID, different content),
        the delta contains the modified chunks.
        """
        calculator = DeltaCalculator()
        packager = VKPPackager()
        
        # Create modified version with modified chunks
        new_vkp = copy.deepcopy(vkp)
        new_vkp.version = increment_version(vkp.version)
        
        # Modify first chunk
        original_text = new_vkp.chunks[0].text
        new_vkp.chunks[0].text = original_text + " MODIFIED"
        
        # Recalculate checksum
        new_vkp.checksum = packager.calculate_checksum(new_vkp)
        
        # Calculate delta
        delta = calculator.calculate_delta(vkp, new_vkp)
        
        # Delta should contain the modified chunk
        assert len(delta.added_chunks) >= 1
        modified_chunk_ids = [c.chunk_id for c in delta.added_chunks]
        assert new_vkp.chunks[0].chunk_id in modified_chunk_ids
        
        # Apply delta
        result_vkp = calculator.apply_delta(vkp, delta)
        
        # Result should have modified text
        result_chunk = next(c for c in result_vkp.chunks if c.chunk_id == new_vkp.chunks[0].chunk_id)
        assert result_chunk.text == new_vkp.chunks[0].text
        assert "MODIFIED" in result_chunk.text
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large, HealthCheck.large_base_example])
    def test_delta_handles_mixed_operations(self, vkp):
        """
        Property: Delta correctly handles mixed add/remove/modify operations.
        
        **Validates: Requirements 6.3**
        
        Verifies that a delta can handle multiple types of changes
        simultaneously (add, remove, modify).
        """
        # Need at least 3 chunks for meaningful test
        assume(len(vkp.chunks) >= 3)
        
        calculator = DeltaCalculator()
        packager = VKPPackager()
        
        # Create modified version with mixed changes
        new_vkp = copy.deepcopy(vkp)
        new_vkp.version = increment_version(vkp.version)
        
        # Modify first chunk
        new_vkp.chunks[0].text = new_vkp.chunks[0].text + " MODIFIED"
        
        # Remove last chunk
        removed_id = new_vkp.chunks[-1].chunk_id
        new_vkp.chunks = new_vkp.chunks[:-1]
        
        # Add new chunk
        new_chunk = VKPChunk(
            chunk_id="mixed_added",
            text="This is a new chunk in mixed operation",
            embedding=[0.7] * 128,
            metadata=ChunkMetadata()
        )
        new_vkp.chunks.append(new_chunk)
        new_vkp.total_chunks = len(new_vkp.chunks)
        
        # Recalculate checksum
        new_vkp.checksum = packager.calculate_checksum(new_vkp)
        
        # Calculate delta
        delta = calculator.calculate_delta(vkp, new_vkp)
        
        # Delta should reflect all changes
        assert len(delta.added_chunks) >= 2  # Modified + added
        assert len(delta.removed_chunk_ids) == 1
        assert removed_id in delta.removed_chunk_ids
        
        # Apply delta
        result_vkp = calculator.apply_delta(vkp, delta)
        
        # Verify result matches new_vkp
        assert len(result_vkp.chunks) == len(new_vkp.chunks)
        result_ids = set(c.chunk_id for c in result_vkp.chunks)
        new_ids = set(c.chunk_id for c in new_vkp.chunks)
        assert result_ids == new_ids
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large, HealthCheck.large_base_example])
    def test_delta_size_reduction_calculation(self, vkp):
        """
        Property: Delta size reduction is calculated correctly.
        
        **Validates: Requirements 6.3**
        
        Verifies that the delta size reduction statistics are accurate.
        """
        calculator = DeltaCalculator()
        packager = VKPPackager()
        
        # Create modified version with 30% changes
        new_vkp = copy.deepcopy(vkp)
        new_vkp.version = increment_version(vkp.version)
        
        num_to_modify = max(1, len(new_vkp.chunks) * 3 // 10)
        for i in range(num_to_modify):
            new_vkp.chunks[i].text = new_vkp.chunks[i].text + " MODIFIED"
        
        # Recalculate checksum
        new_vkp.checksum = packager.calculate_checksum(new_vkp)
        
        # Calculate delta size reduction
        stats = calculator.calculate_delta_size_reduction(vkp, new_vkp)
        
        # Verify statistics
        assert stats['full_size'] == len(new_vkp.chunks)
        assert stats['delta_size'] <= stats['full_size']
        assert stats['reduction'] == stats['full_size'] - stats['delta_size']
        assert 0 <= stats['reduction_percent'] <= 100
        
        # For 30% modification, delta should be significantly smaller
        assert stats['delta_size'] < stats['full_size']
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large, HealthCheck.large_base_example])
    def test_no_changes_produces_empty_delta(self, vkp):
        """
        Property: No changes produces a delta with no added/removed chunks.
        
        **Validates: Requirements 6.3**
        
        Verifies that when there are no changes between versions (except version number),
        the delta has no added or removed chunks.
        """
        calculator = DeltaCalculator()
        packager = VKPPackager()
        
        # Create "new" version with no actual chunk changes
        new_vkp = copy.deepcopy(vkp)
        new_vkp.version = increment_version(vkp.version)
        # Keep same created_at to avoid metadata changes
        new_vkp.created_at = vkp.created_at
        
        # Recalculate checksum (will be different due to version change)
        new_vkp.checksum = packager.calculate_checksum(new_vkp)
        
        # Calculate delta
        delta = calculator.calculate_delta(vkp, new_vkp)
        
        # Delta should have no added or removed chunks
        assert len(delta.added_chunks) == 0, f"Expected 0 added chunks, got {len(delta.added_chunks)}"
        assert len(delta.removed_chunk_ids) == 0, f"Expected 0 removed chunks, got {len(delta.removed_chunk_ids)}"
        
        # Applying delta should produce identical VKP (except version/checksum)
        result_vkp = calculator.apply_delta(vkp, delta)
        assert len(result_vkp.chunks) == len(vkp.chunks)
    
    @given(vkp=vkp_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.data_too_large, HealthCheck.large_base_example])
    def test_delta_preserves_unchanged_chunks(self, vkp):
        """
        Property: Delta application preserves unchanged chunks exactly.
        
        **Validates: Requirements 6.3**
        
        Verifies that chunks not included in the delta remain unchanged
        after delta application.
        """
        calculator = DeltaCalculator()
        packager = VKPPackager()
        
        # Create modified version with only first chunk changed
        new_vkp = copy.deepcopy(vkp)
        new_vkp.version = increment_version(vkp.version)
        
        if len(new_vkp.chunks) > 0:
            new_vkp.chunks[0].text = new_vkp.chunks[0].text + " MODIFIED"
        
        # Recalculate checksum
        new_vkp.checksum = packager.calculate_checksum(new_vkp)
        
        # Calculate and apply delta
        delta = calculator.calculate_delta(vkp, new_vkp)
        result_vkp = calculator.apply_delta(vkp, delta)
        
        # Verify unchanged chunks are identical
        for i in range(1, len(vkp.chunks)):
            original_chunk = vkp.chunks[i]
            result_chunk = next(c for c in result_vkp.chunks if c.chunk_id == original_chunk.chunk_id)
            
            assert result_chunk.text == original_chunk.text
            assert result_chunk.embedding == original_chunk.embedding
            assert result_chunk.metadata.page == original_chunk.metadata.page
