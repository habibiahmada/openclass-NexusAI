"""
VKP Delta Update Calculation

This module provides functionality for calculating delta updates between
VKP versions to minimize bandwidth usage during updates.

Requirements: 6.3
"""

import logging
from typing import List, Set, Dict, Any
from dataclasses import dataclass

from .models import VKP, VKPChunk

logger = logging.getLogger(__name__)


@dataclass
class VKPDelta:
    """
    Delta package containing only changes between VKP versions.
    
    Attributes:
        version: New version number
        base_version: Previous version this delta is based on
        subject: Subject name
        grade: Grade level
        semester: Semester number
        added_chunks: List of new or modified chunks
        removed_chunk_ids: List of chunk IDs that were removed
        metadata: Additional metadata from new version
    """
    version: str
    base_version: str
    subject: str
    grade: int
    semester: int
    added_chunks: List[VKPChunk]
    removed_chunk_ids: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'version': self.version,
            'base_version': self.base_version,
            'subject': self.subject,
            'grade': self.grade,
            'semester': self.semester,
            'added_chunks': [chunk.to_dict() for chunk in self.added_chunks],
            'removed_chunk_ids': self.removed_chunk_ids,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VKPDelta':
        """Create VKPDelta from dictionary."""
        return cls(
            version=data['version'],
            base_version=data['base_version'],
            subject=data['subject'],
            grade=data['grade'],
            semester=data['semester'],
            added_chunks=[VKPChunk.from_dict(c) for c in data['added_chunks']],
            removed_chunk_ids=data['removed_chunk_ids'],
            metadata=data['metadata']
        )


class DeltaCalculator:
    """
    Calculator for VKP delta updates.
    
    Compares two VKP versions and generates a delta package containing
    only the changes (added, modified, removed chunks).
    """
    
    def __init__(self):
        """Initialize DeltaCalculator."""
        pass
    
    def calculate_delta(self, old_vkp: VKP, new_vkp: VKP) -> VKPDelta:
        """
        Calculate delta between two VKP versions.
        
        Compares chunk_ids between versions and identifies:
        - Added chunks (new chunk_ids in new version)
        - Modified chunks (same chunk_id but different content)
        - Removed chunks (chunk_ids present in old but not in new)
        
        Args:
            old_vkp: Previous VKP version
            new_vkp: New VKP version
        
        Returns:
            VKPDelta object containing only changes
        
        Raises:
            ValueError: If VKPs are not compatible (different subject/grade/semester)
        
        Example:
            calculator = DeltaCalculator()
            delta = calculator.calculate_delta(old_vkp, new_vkp)
            print(f"Added: {len(delta.added_chunks)}, Removed: {len(delta.removed_chunk_ids)}")
        """
        # Validate compatibility
        self._validate_compatibility(old_vkp, new_vkp)
        
        # Build chunk maps for efficient lookup
        old_chunks_map = {chunk.chunk_id: chunk for chunk in old_vkp.chunks}
        new_chunks_map = {chunk.chunk_id: chunk for chunk in new_vkp.chunks}
        
        # Get chunk ID sets
        old_ids = set(old_chunks_map.keys())
        new_ids = set(new_chunks_map.keys())
        
        # Identify changes
        added_ids = new_ids - old_ids
        removed_ids = old_ids - new_ids
        common_ids = old_ids & new_ids
        
        # Check for modified chunks (same ID but different content)
        modified_ids = set()
        for chunk_id in common_ids:
            old_chunk = old_chunks_map[chunk_id]
            new_chunk = new_chunks_map[chunk_id]
            
            # Compare text and embedding
            if (old_chunk.text != new_chunk.text or 
                old_chunk.embedding != new_chunk.embedding):
                modified_ids.add(chunk_id)
        
        # Collect added and modified chunks
        changed_ids = added_ids | modified_ids
        added_chunks = [new_chunks_map[chunk_id] for chunk_id in changed_ids]
        
        # Create delta
        delta = VKPDelta(
            version=new_vkp.version,
            base_version=old_vkp.version,
            subject=new_vkp.subject,
            grade=new_vkp.grade,
            semester=new_vkp.semester,
            added_chunks=added_chunks,
            removed_chunk_ids=list(removed_ids),
            metadata={
                'embedding_model': new_vkp.embedding_model,
                'chunk_config': new_vkp.chunk_config,
                'created_at': new_vkp.created_at,
                'total_chunks': new_vkp.total_chunks,
                'source_files': new_vkp.source_files
            }
        )
        
        logger.info(
            f"Calculated delta from v{old_vkp.version} to v{new_vkp.version}: "
            f"{len(added_ids)} added, {len(modified_ids)} modified, "
            f"{len(removed_ids)} removed"
        )
        
        return delta
    
    def _validate_compatibility(self, old_vkp: VKP, new_vkp: VKP) -> None:
        """
        Validate that two VKPs are compatible for delta calculation.
        
        Args:
            old_vkp: Previous VKP version
            new_vkp: New VKP version
        
        Raises:
            ValueError: If VKPs are not compatible
        """
        if old_vkp.subject != new_vkp.subject:
            raise ValueError(
                f"Subject mismatch: {old_vkp.subject} != {new_vkp.subject}"
            )
        
        if old_vkp.grade != new_vkp.grade:
            raise ValueError(
                f"Grade mismatch: {old_vkp.grade} != {new_vkp.grade}"
            )
        
        if old_vkp.semester != new_vkp.semester:
            raise ValueError(
                f"Semester mismatch: {old_vkp.semester} != {new_vkp.semester}"
            )
        
        # Validate version ordering
        if not self._is_newer_version(old_vkp.version, new_vkp.version):
            raise ValueError(
                f"New version ({new_vkp.version}) must be greater than "
                f"old version ({old_vkp.version})"
            )
    
    def _is_newer_version(self, old_version: str, new_version: str) -> bool:
        """
        Check if new_version is newer than old_version.
        
        Args:
            old_version: Old semantic version (MAJOR.MINOR.PATCH)
            new_version: New semantic version (MAJOR.MINOR.PATCH)
        
        Returns:
            True if new_version > old_version
        """
        old_parts = [int(x) for x in old_version.split('.')]
        new_parts = [int(x) for x in new_version.split('.')]
        
        return new_parts > old_parts
    
    def calculate_delta_size_reduction(self, old_vkp: VKP, new_vkp: VKP) -> Dict[str, Any]:
        """
        Calculate size reduction achieved by using delta update.
        
        Args:
            old_vkp: Previous VKP version
            new_vkp: New VKP version
        
        Returns:
            Dictionary with size statistics
        
        Example:
            stats = calculator.calculate_delta_size_reduction(old_vkp, new_vkp)
            print(f"Reduction: {stats['reduction_percent']:.1f}%")
        """
        delta = self.calculate_delta(old_vkp, new_vkp)
        
        full_size = len(new_vkp.chunks)
        delta_size = len(delta.added_chunks)
        reduction = full_size - delta_size
        reduction_percent = (reduction / full_size * 100) if full_size > 0 else 0
        
        return {
            'full_size': full_size,
            'delta_size': delta_size,
            'reduction': reduction,
            'reduction_percent': reduction_percent,
            'removed_chunks': len(delta.removed_chunk_ids)
        }
    
    def apply_delta(self, old_vkp: VKP, delta: VKPDelta) -> VKP:
        """
        Apply delta update to create new VKP version.
        
        Args:
            old_vkp: Previous VKP version
            delta: Delta package to apply
        
        Returns:
            New VKP version with delta applied
        
        Raises:
            ValueError: If delta cannot be applied
        
        Example:
            new_vkp = calculator.apply_delta(old_vkp, delta)
        """
        # Validate delta can be applied
        if old_vkp.version != delta.base_version:
            raise ValueError(
                f"Delta base version ({delta.base_version}) does not match "
                f"old VKP version ({old_vkp.version})"
            )
        
        # Build chunk map from old VKP
        chunks_map = {chunk.chunk_id: chunk for chunk in old_vkp.chunks}
        
        # Remove deleted chunks
        for chunk_id in delta.removed_chunk_ids:
            chunks_map.pop(chunk_id, None)
        
        # Add/update chunks from delta
        for chunk in delta.added_chunks:
            chunks_map[chunk.chunk_id] = chunk
        
        # Create new VKP
        new_chunks = list(chunks_map.values())
        
        from .packager import VKPPackager
        packager = VKPPackager()
        
        new_vkp = packager.create_package(
            version=delta.version,
            subject=delta.subject,
            grade=delta.grade,
            semester=delta.semester,
            embedding_model=delta.metadata['embedding_model'],
            chunk_size=delta.metadata['chunk_config']['chunk_size'],
            chunk_overlap=delta.metadata['chunk_config']['chunk_overlap'],
            chunks=new_chunks,
            source_files=delta.metadata['source_files']
        )
        
        logger.info(
            f"Applied delta to create v{new_vkp.version} "
            f"({len(new_chunks)} total chunks)"
        )
        
        return new_vkp
