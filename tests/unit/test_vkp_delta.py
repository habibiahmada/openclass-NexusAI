"""
Unit tests for VKP Delta Calculator

Tests delta calculation between VKP versions, including add/remove/modify scenarios.

Requirements: 6.3
"""

import pytest

from src.vkp.models import VKP, VKPChunk, ChunkMetadata
from src.vkp.packager import VKPPackager
from src.vkp.delta import DeltaCalculator, VKPDelta


@pytest.fixture
def packager():
    """Create VKPPackager instance."""
    return VKPPackager()


@pytest.fixture
def calculator():
    """Create DeltaCalculator instance."""
    return DeltaCalculator()


@pytest.fixture
def base_chunks():
    """Create base set of chunks."""
    return [
        VKPChunk(
            chunk_id="chunk_001",
            text="Original text 1",
            embedding=[0.1, 0.2, 0.3],
            metadata=ChunkMetadata(page=1, section="Intro")
        ),
        VKPChunk(
            chunk_id="chunk_002",
            text="Original text 2",
            embedding=[0.4, 0.5, 0.6],
            metadata=ChunkMetadata(page=2, section="Body")
        ),
        VKPChunk(
            chunk_id="chunk_003",
            text="Original text 3",
            embedding=[0.7, 0.8, 0.9],
            metadata=ChunkMetadata(page=3, section="Conclusion")
        )
    ]


class TestDeltaCalculation:
    """Test delta calculation between VKP versions."""
    
    def test_delta_with_added_chunks(self, packager, calculator, base_chunks):
        """Test delta calculation when chunks are added."""
        # Create old VKP
        old_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        # Create new VKP with additional chunk
        new_chunks = base_chunks + [
            VKPChunk(
                chunk_id="chunk_004",
                text="New text 4",
                embedding=[1.0, 1.1, 1.2],
                metadata=ChunkMetadata(page=4, section="Appendix")
            )
        ]
        
        new_vkp = packager.create_package(
            version="1.1.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=new_chunks,
            source_files=["test.pdf"]
        )
        
        # Calculate delta
        delta = calculator.calculate_delta(old_vkp, new_vkp)
        
        assert delta.version == "1.1.0"
        assert delta.base_version == "1.0.0"
        assert len(delta.added_chunks) == 1
        assert delta.added_chunks[0].chunk_id == "chunk_004"
        assert len(delta.removed_chunk_ids) == 0
    
    def test_delta_with_removed_chunks(self, packager, calculator, base_chunks):
        """Test delta calculation when chunks are removed."""
        # Create old VKP
        old_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        # Create new VKP with one chunk removed
        new_chunks = base_chunks[:2]  # Remove last chunk
        
        new_vkp = packager.create_package(
            version="1.1.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=new_chunks,
            source_files=["test.pdf"]
        )
        
        # Calculate delta
        delta = calculator.calculate_delta(old_vkp, new_vkp)
        
        assert delta.version == "1.1.0"
        assert delta.base_version == "1.0.0"
        assert len(delta.added_chunks) == 0
        assert len(delta.removed_chunk_ids) == 1
        assert "chunk_003" in delta.removed_chunk_ids
    
    def test_delta_with_modified_chunks(self, packager, calculator, base_chunks):
        """Test delta calculation when chunks are modified."""
        # Create old VKP
        old_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        # Create new VKP with modified chunk
        modified_chunks = [
            base_chunks[0],
            VKPChunk(
                chunk_id="chunk_002",  # Same ID
                text="Modified text 2",  # Different text
                embedding=[0.4, 0.5, 0.6],
                metadata=ChunkMetadata(page=2, section="Body")
            ),
            base_chunks[2]
        ]
        
        new_vkp = packager.create_package(
            version="1.1.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=modified_chunks,
            source_files=["test.pdf"]
        )
        
        # Calculate delta
        delta = calculator.calculate_delta(old_vkp, new_vkp)
        
        assert delta.version == "1.1.0"
        assert delta.base_version == "1.0.0"
        assert len(delta.added_chunks) == 1  # Modified chunk is in added
        assert delta.added_chunks[0].chunk_id == "chunk_002"
        assert delta.added_chunks[0].text == "Modified text 2"
        assert len(delta.removed_chunk_ids) == 0
    
    def test_delta_with_mixed_changes(self, packager, calculator, base_chunks):
        """Test delta calculation with add, remove, and modify."""
        # Create old VKP
        old_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        # Create new VKP with mixed changes
        new_chunks = [
            base_chunks[0],  # Unchanged
            VKPChunk(  # Modified
                chunk_id="chunk_002",
                text="Modified text 2",
                embedding=[0.4, 0.5, 0.6],
                metadata=ChunkMetadata(page=2, section="Body")
            ),
            # chunk_003 removed
            VKPChunk(  # Added
                chunk_id="chunk_004",
                text="New text 4",
                embedding=[1.0, 1.1, 1.2],
                metadata=ChunkMetadata(page=4, section="New")
            )
        ]
        
        new_vkp = packager.create_package(
            version="2.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=new_chunks,
            source_files=["test.pdf"]
        )
        
        # Calculate delta
        delta = calculator.calculate_delta(old_vkp, new_vkp)
        
        assert delta.version == "2.0.0"
        assert delta.base_version == "1.0.0"
        assert len(delta.added_chunks) == 2  # Modified + Added
        assert len(delta.removed_chunk_ids) == 1
        assert "chunk_003" in delta.removed_chunk_ids
        
        # Check added chunks
        added_ids = {chunk.chunk_id for chunk in delta.added_chunks}
        assert "chunk_002" in added_ids  # Modified
        assert "chunk_004" in added_ids  # Added
    
    def test_delta_no_changes(self, packager, calculator, base_chunks):
        """Test delta calculation when there are no changes."""
        # Create old VKP
        old_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        # Create new VKP with same chunks
        new_vkp = packager.create_package(
            version="1.0.1",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        # Calculate delta
        delta = calculator.calculate_delta(old_vkp, new_vkp)
        
        assert delta.version == "1.0.1"
        assert delta.base_version == "1.0.0"
        assert len(delta.added_chunks) == 0
        assert len(delta.removed_chunk_ids) == 0


class TestDeltaValidation:
    """Test delta validation and error handling."""
    
    def test_delta_mismatched_subject(self, packager, calculator, base_chunks):
        """Test delta calculation with mismatched subject."""
        old_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        new_vkp = packager.create_package(
            version="1.1.0",
            subject="fisika",  # Different subject
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        with pytest.raises(ValueError, match="Subject mismatch"):
            calculator.calculate_delta(old_vkp, new_vkp)
    
    def test_delta_mismatched_grade(self, packager, calculator, base_chunks):
        """Test delta calculation with mismatched grade."""
        old_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        new_vkp = packager.create_package(
            version="1.1.0",
            subject="matematika",
            grade=11,  # Different grade
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        with pytest.raises(ValueError, match="Grade mismatch"):
            calculator.calculate_delta(old_vkp, new_vkp)
    
    def test_delta_mismatched_semester(self, packager, calculator, base_chunks):
        """Test delta calculation with mismatched semester."""
        old_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        new_vkp = packager.create_package(
            version="1.1.0",
            subject="matematika",
            grade=10,
            semester=2,  # Different semester
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        with pytest.raises(ValueError, match="Semester mismatch"):
            calculator.calculate_delta(old_vkp, new_vkp)
    
    def test_delta_invalid_version_order(self, packager, calculator, base_chunks):
        """Test delta calculation with invalid version order."""
        old_vkp = packager.create_package(
            version="2.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        new_vkp = packager.create_package(
            version="1.0.0",  # Older version
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        with pytest.raises(ValueError, match="must be greater than"):
            calculator.calculate_delta(old_vkp, new_vkp)


class TestDeltaApplication:
    """Test applying delta updates."""
    
    def test_apply_delta_add_chunks(self, packager, calculator, base_chunks):
        """Test applying delta with added chunks."""
        # Create old VKP
        old_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        # Create new VKP with additional chunk
        new_chunks = base_chunks + [
            VKPChunk(
                chunk_id="chunk_004",
                text="New text 4",
                embedding=[1.0, 1.1, 1.2],
                metadata=ChunkMetadata(page=4)
            )
        ]
        
        new_vkp = packager.create_package(
            version="1.1.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=new_chunks,
            source_files=["test.pdf"]
        )
        
        # Calculate and apply delta
        delta = calculator.calculate_delta(old_vkp, new_vkp)
        result_vkp = calculator.apply_delta(old_vkp, delta)
        
        assert result_vkp.version == "1.1.0"
        assert len(result_vkp.chunks) == 4
        assert any(chunk.chunk_id == "chunk_004" for chunk in result_vkp.chunks)
    
    def test_apply_delta_remove_chunks(self, packager, calculator, base_chunks):
        """Test applying delta with removed chunks."""
        # Create old VKP
        old_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        # Create new VKP with removed chunk
        new_chunks = base_chunks[:2]
        
        new_vkp = packager.create_package(
            version="1.1.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=new_chunks,
            source_files=["test.pdf"]
        )
        
        # Calculate and apply delta
        delta = calculator.calculate_delta(old_vkp, new_vkp)
        result_vkp = calculator.apply_delta(old_vkp, delta)
        
        assert result_vkp.version == "1.1.0"
        assert len(result_vkp.chunks) == 2
        assert not any(chunk.chunk_id == "chunk_003" for chunk in result_vkp.chunks)
    
    def test_apply_delta_wrong_base_version(self, packager, calculator, base_chunks):
        """Test applying delta with wrong base version."""
        old_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        new_vkp = packager.create_package(
            version="1.1.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        delta = calculator.calculate_delta(old_vkp, new_vkp)
        
        # Try to apply to wrong version
        wrong_vkp = packager.create_package(
            version="0.9.0",  # Different version
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        with pytest.raises(ValueError, match="does not match"):
            calculator.apply_delta(wrong_vkp, delta)


class TestDeltaSizeReduction:
    """Test delta size reduction calculations."""
    
    def test_calculate_size_reduction(self, packager, calculator, base_chunks):
        """Test calculating delta size reduction."""
        # Create old VKP
        old_vkp = packager.create_package(
            version="1.0.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=base_chunks,
            source_files=["test.pdf"]
        )
        
        # Create new VKP with one added chunk
        new_chunks = base_chunks + [
            VKPChunk(
                chunk_id="chunk_004",
                text="New text 4",
                embedding=[1.0, 1.1, 1.2],
                metadata=ChunkMetadata()
            )
        ]
        
        new_vkp = packager.create_package(
            version="1.1.0",
            subject="matematika",
            grade=10,
            semester=1,
            embedding_model="amazon.titan-embed-text-v1",
            chunk_size=800,
            chunk_overlap=100,
            chunks=new_chunks,
            source_files=["test.pdf"]
        )
        
        # Calculate size reduction
        stats = calculator.calculate_delta_size_reduction(old_vkp, new_vkp)
        
        assert stats['full_size'] == 4
        assert stats['delta_size'] == 1
        assert stats['reduction'] == 3
        assert stats['reduction_percent'] == 75.0
