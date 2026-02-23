"""
VKP (Versioned Knowledge Package) System

This module provides the VKP packaging system for versioning, distributing,
and managing curriculum embeddings with integrity verification.

Requirements: 6.1-6.6
"""

from .models import VKPMetadata, VKPChunk, ChunkMetadata, VKP
from .packager import VKPPackager
from .version_manager import VKPVersionManager
from .delta import VKPDelta, DeltaCalculator

__all__ = [
    'VKPMetadata',
    'VKPChunk',
    'ChunkMetadata',
    'VKP',
    'VKPPackager',
    'VKPVersionManager',
    'VKPDelta',
    'DeltaCalculator',
]
