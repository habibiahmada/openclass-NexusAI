"""
VKP Data Models

This module defines the data structures for Versioned Knowledge Packages (VKP).

Requirements: 6.1, 6.2
"""

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class ChunkMetadata:
    """
    Metadata for a single chunk within a VKP.
    
    Attributes:
        page: Page number in source document
        section: Section name (e.g., "Geometri")
        topic: Topic name (e.g., "Pythagoras")
    """
    page: Optional[int] = None
    section: Optional[str] = None
    topic: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChunkMetadata':
        """Create ChunkMetadata from dictionary."""
        return cls(
            page=data.get('page'),
            section=data.get('section'),
            topic=data.get('topic')
        )


@dataclass
class VKPChunk:
    """
    A single chunk of text with its embedding and metadata.
    
    Attributes:
        chunk_id: Unique identifier for the chunk
        text: The actual text content
        embedding: Vector embedding (list of floats)
        metadata: Additional metadata about the chunk
    """
    chunk_id: str
    text: str
    embedding: List[float]
    metadata: ChunkMetadata = field(default_factory=ChunkMetadata)
    
    def validate(self) -> None:
        """
        Validate chunk data.
        
        Raises:
            ValueError: If validation fails
        """
        if not self.chunk_id:
            raise ValueError("chunk_id cannot be empty")
        
        if not self.text:
            raise ValueError("text cannot be empty")
        
        if not self.embedding:
            raise ValueError("embedding cannot be empty")
        
        if not isinstance(self.embedding, list):
            raise ValueError("embedding must be a list")
        
        if not all(isinstance(x, (int, float)) for x in self.embedding):
            raise ValueError("embedding must contain only numbers")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'chunk_id': self.chunk_id,
            'text': self.text,
            'embedding': self.embedding,
            'metadata': self.metadata.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VKPChunk':
        """Create VKPChunk from dictionary."""
        return cls(
            chunk_id=data['chunk_id'],
            text=data['text'],
            embedding=data['embedding'],
            metadata=ChunkMetadata.from_dict(data.get('metadata', {}))
        )


@dataclass
class VKPMetadata:
    """
    Metadata for a Versioned Knowledge Package.
    
    Attributes:
        version: Semantic version (MAJOR.MINOR.PATCH)
        subject: Subject name (e.g., "matematika")
        grade: Grade level (e.g., 10, 11, 12)
        semester: Semester number (1 or 2)
        created_at: ISO 8601 timestamp
        embedding_model: Model used for embeddings
        chunk_config: Configuration for chunking
        total_chunks: Total number of chunks
        source_files: List of source PDF filenames
    """
    version: str
    subject: str
    grade: int
    semester: int
    created_at: str
    embedding_model: str
    chunk_config: Dict[str, int]
    total_chunks: int
    source_files: List[str]
    
    def validate(self) -> None:
        """
        Validate metadata.
        
        Raises:
            ValueError: If validation fails
        """
        # Validate semantic versioning
        version_pattern = r'^\d+\.\d+\.\d+$'
        if not re.match(version_pattern, self.version):
            raise ValueError(
                f"version must follow semantic versioning (MAJOR.MINOR.PATCH): {self.version}"
            )
        
        # Validate subject
        if not self.subject or not isinstance(self.subject, str):
            raise ValueError("subject must be a non-empty string")
        
        # Validate grade
        if not isinstance(self.grade, int) or self.grade < 1 or self.grade > 12:
            raise ValueError("grade must be an integer between 1 and 12")
        
        # Validate semester
        if self.semester not in [1, 2]:
            raise ValueError("semester must be 1 or 2")
        
        # Validate created_at (ISO 8601 format)
        try:
            datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValueError(f"created_at must be valid ISO 8601 timestamp: {self.created_at}")
        
        # Validate embedding_model
        if not self.embedding_model or not isinstance(self.embedding_model, str):
            raise ValueError("embedding_model must be a non-empty string")
        
        # Validate chunk_config
        if not isinstance(self.chunk_config, dict):
            raise ValueError("chunk_config must be a dictionary")
        
        required_keys = {'chunk_size', 'chunk_overlap'}
        if not required_keys.issubset(self.chunk_config.keys()):
            raise ValueError(f"chunk_config must contain keys: {required_keys}")
        
        # Validate total_chunks
        if not isinstance(self.total_chunks, int) or self.total_chunks < 0:
            raise ValueError("total_chunks must be a non-negative integer")
        
        # Validate source_files
        if not isinstance(self.source_files, list) or not self.source_files:
            raise ValueError("source_files must be a non-empty list")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VKPMetadata':
        """Create VKPMetadata from dictionary."""
        return cls(
            version=data['version'],
            subject=data['subject'],
            grade=data['grade'],
            semester=data['semester'],
            created_at=data['created_at'],
            embedding_model=data['embedding_model'],
            chunk_config=data['chunk_config'],
            total_chunks=data['total_chunks'],
            source_files=data['source_files']
        )


@dataclass
class VKP:
    """
    Versioned Knowledge Package containing embeddings and metadata.
    
    This is the complete package format for distributing curriculum embeddings.
    
    Attributes:
        version: Semantic version
        subject: Subject name
        grade: Grade level
        semester: Semester number
        created_at: ISO 8601 timestamp
        embedding_model: Model used for embeddings
        chunk_config: Chunking configuration
        chunks: List of VKPChunk objects
        checksum: SHA256 checksum for integrity verification
        total_chunks: Total number of chunks
        source_files: List of source PDF filenames
    """
    version: str
    subject: str
    grade: int
    semester: int
    created_at: str
    embedding_model: str
    chunk_config: Dict[str, int]
    chunks: List[VKPChunk]
    checksum: str
    total_chunks: int
    source_files: List[str]
    
    def validate(self) -> None:
        """
        Validate VKP structure.
        
        Raises:
            ValueError: If validation fails
        """
        # Create and validate metadata
        metadata = VKPMetadata(
            version=self.version,
            subject=self.subject,
            grade=self.grade,
            semester=self.semester,
            created_at=self.created_at,
            embedding_model=self.embedding_model,
            chunk_config=self.chunk_config,
            total_chunks=self.total_chunks,
            source_files=self.source_files
        )
        metadata.validate()
        
        # Validate chunks
        if not isinstance(self.chunks, list):
            raise ValueError("chunks must be a list")
        
        if len(self.chunks) != self.total_chunks:
            raise ValueError(
                f"chunks length ({len(self.chunks)}) does not match total_chunks ({self.total_chunks})"
            )
        
        # Validate each chunk
        for i, chunk in enumerate(self.chunks):
            try:
                chunk.validate()
            except ValueError as e:
                raise ValueError(f"Invalid chunk at index {i}: {e}")
        
        # Validate checksum format
        if not self.checksum or not self.checksum.startswith('sha256:'):
            raise ValueError("checksum must start with 'sha256:'")
        
        if len(self.checksum) != 71:  # 'sha256:' (7) + 64 hex chars
            raise ValueError("checksum must be 'sha256:' followed by 64 hex characters")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'version': self.version,
            'subject': self.subject,
            'grade': self.grade,
            'semester': self.semester,
            'created_at': self.created_at,
            'embedding_model': self.embedding_model,
            'chunk_config': self.chunk_config,
            'chunks': [chunk.to_dict() for chunk in self.chunks],
            'checksum': self.checksum,
            'total_chunks': self.total_chunks,
            'source_files': self.source_files
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VKP':
        """Create VKP from dictionary."""
        return cls(
            version=data['version'],
            subject=data['subject'],
            grade=data['grade'],
            semester=data['semester'],
            created_at=data['created_at'],
            embedding_model=data['embedding_model'],
            chunk_config=data['chunk_config'],
            chunks=[VKPChunk.from_dict(c) for c in data['chunks']],
            checksum=data['checksum'],
            total_chunks=data['total_chunks'],
            source_files=data['source_files']
        )
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Serialize VKP to JSON string.
        
        Args:
            indent: Number of spaces for indentation (None for compact)
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'VKP':
        """
        Deserialize VKP from JSON string.
        
        Args:
            json_str: JSON string representation
        
        Returns:
            VKP object
        
        Raises:
            ValueError: If JSON is invalid or VKP structure is invalid
        """
        try:
            data = json.loads(json_str)
            vkp = cls.from_dict(data)
            vkp.validate()
            return vkp
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")
