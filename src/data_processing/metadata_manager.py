"""Metadata management for text chunks.

This module provides functionality to extract metadata from file paths
and enrich text chunks with metadata for source attribution.
"""

import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.data_processing.text_chunker import TextChunk


@dataclass
class FileMetadata:
    """Metadata extracted from file path."""
    subject: str  # e.g., "informatika"
    grade: str    # e.g., "kelas_10"
    filename: str # e.g., "Informatika-BS-KLS-X.pdf"


@dataclass
class EnrichedChunk:
    """Text chunk enriched with metadata."""
    chunk_id: str          # UUID
    text: str              # Chunk text
    source_file: str       # Original filename
    subject: str           # Subject area
    grade: str             # Grade level
    chunk_index: int       # Position in document
    char_start: int        # Start position
    char_end: int          # End position


class MetadataManager:
    """Manages metadata extraction and chunk enrichment."""
    
    def parse_file_path(self, file_path: str) -> FileMetadata:
        """Extract metadata from file path structure.
        
        Expected path format: data/raw_dataset/{grade}/{subject}/filename.pdf
        Example: data/raw_dataset/kelas_10/informatika/Informatika-BS-KLS-X.pdf
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileMetadata with subject, grade, filename
            
        Raises:
            ValueError: If path doesn't match expected format
        """
        path = Path(file_path)
        filename = path.name
        
        # Get path parts
        parts = path.parts
        
        # Try to find grade and subject in path
        # Expected structure: .../kelas_XX/subject/filename
        grade = None
        subject = None
        
        # Look for grade pattern (kelas_XX)
        grade_pattern = re.compile(r'kelas_\d+')
        for part in parts:
            if grade_pattern.match(part):
                grade = part
                # Subject should be the next part
                idx = parts.index(part)
                if idx + 1 < len(parts) - 1:  # -1 because last part is filename
                    subject = parts[idx + 1]
                break
        
        if not grade or not subject:
            raise ValueError(
                f"Could not extract grade and subject from path: {file_path}. "
                f"Expected format: .../kelas_XX/subject/filename.pdf"
            )
        
        return FileMetadata(
            subject=subject,
            grade=grade,
            filename=filename
        )
    
    def enrich_chunk(self, chunk: TextChunk, file_metadata: FileMetadata) -> EnrichedChunk:
        """Add metadata to a text chunk.
        
        Args:
            chunk: Text chunk to enrich
            file_metadata: Metadata from file path
            
        Returns:
            EnrichedChunk with all metadata fields
        """
        return EnrichedChunk(
            chunk_id=str(uuid.uuid4()),
            text=chunk.text,
            source_file=file_metadata.filename,
            subject=file_metadata.subject,
            grade=file_metadata.grade,
            chunk_index=chunk.chunk_index,
            char_start=chunk.start_pos,
            char_end=chunk.end_pos
        )
