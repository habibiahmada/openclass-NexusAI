"""
VKP Packager

This module provides the VKPPackager class for creating, serializing,
and deserializing Versioned Knowledge Packages with integrity verification.

Requirements: 6.1, 6.4, 6.5
"""

import hashlib
import json
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

from .models import VKP, VKPChunk, VKPMetadata

logger = logging.getLogger(__name__)


class VKPPackager:
    """
    Packager for creating and managing Versioned Knowledge Packages.
    
    Provides methods for creating VKP packages from embeddings, calculating
    checksums for integrity verification, and serializing/deserializing packages.
    """
    
    def __init__(self):
        """Initialize VKPPackager."""
        pass
    
    def create_package(
        self,
        version: str,
        subject: str,
        grade: int,
        semester: int,
        embedding_model: str,
        chunk_size: int,
        chunk_overlap: int,
        chunks: List[VKPChunk],
        source_files: List[str]
    ) -> VKP:
        """
        Create a VKP package from embeddings and metadata.
        
        Args:
            version: Semantic version (MAJOR.MINOR.PATCH)
            subject: Subject name (e.g., "matematika")
            grade: Grade level (10, 11, 12)
            semester: Semester number (1 or 2)
            embedding_model: Model used for embeddings
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            chunks: List of VKPChunk objects
            source_files: List of source PDF filenames
        
        Returns:
            VKP object with calculated checksum
        
        Raises:
            ValueError: If validation fails
        
        Example:
            packager = VKPPackager()
            vkp = packager.create_package(
                version="1.0.0",
                subject="matematika",
                grade=10,
                semester=1,
                embedding_model="amazon.titan-embed-text-v1",
                chunk_size=800,
                chunk_overlap=100,
                chunks=chunk_list,
                source_files=["Matematika_Kelas_10.pdf"]
            )
        """
        # Create VKP without checksum first
        vkp = VKP(
            version=version,
            subject=subject,
            grade=grade,
            semester=semester,
            created_at=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            embedding_model=embedding_model,
            chunk_config={
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap
            },
            chunks=chunks,
            checksum='',  # Will be calculated
            total_chunks=len(chunks),
            source_files=source_files
        )
        
        # Calculate and set checksum
        vkp.checksum = self.calculate_checksum(vkp)
        
        # Validate complete VKP
        vkp.validate()
        
        logger.info(
            f"Created VKP package: {subject} grade {grade} semester {semester} "
            f"v{version} ({len(chunks)} chunks)"
        )
        
        return vkp
    
    def calculate_checksum(self, vkp: VKP) -> str:
        """
        Calculate SHA256 checksum for VKP integrity verification.
        
        The checksum is calculated from the JSON representation with sorted keys,
        excluding the checksum field itself.
        
        Args:
            vkp: VKP object to calculate checksum for
        
        Returns:
            Checksum string in format 'sha256:HEXDIGEST'
        
        Example:
            checksum = packager.calculate_checksum(vkp)
            # Returns: 'sha256:abc123def456...'
        """
        # Convert to dict and remove checksum field
        vkp_dict = vkp.to_dict()
        vkp_dict.pop('checksum', None)
        
        # Serialize with sorted keys for deterministic output
        vkp_json = json.dumps(vkp_dict, sort_keys=True, ensure_ascii=False)
        
        # Calculate SHA256
        hash_obj = hashlib.sha256(vkp_json.encode('utf-8'))
        checksum = f"sha256:{hash_obj.hexdigest()}"
        
        return checksum
    
    def verify_checksum(self, vkp: VKP) -> bool:
        """
        Verify VKP checksum integrity.
        
        Args:
            vkp: VKP object to verify
        
        Returns:
            True if checksum is valid, False otherwise
        
        Example:
            if packager.verify_checksum(vkp):
                print("VKP integrity verified")
            else:
                print("VKP integrity check failed!")
        """
        stored_checksum = vkp.checksum
        calculated_checksum = self.calculate_checksum(vkp)
        
        is_valid = stored_checksum == calculated_checksum
        
        if is_valid:
            logger.info(f"VKP checksum verified: {stored_checksum}")
        else:
            logger.error(
                f"VKP checksum mismatch! Stored: {stored_checksum}, "
                f"Calculated: {calculated_checksum}"
            )
        
        return is_valid
    
    def serialize(self, vkp: VKP, indent: int = None) -> bytes:
        """
        Serialize VKP to JSON bytes.
        
        Args:
            vkp: VKP object to serialize
            indent: Number of spaces for indentation (None for compact)
        
        Returns:
            JSON bytes representation
        
        Example:
            data = packager.serialize(vkp)
            with open('package.vkp', 'wb') as f:
                f.write(data)
        """
        json_str = vkp.to_json(indent=indent)
        return json_str.encode('utf-8')
    
    def deserialize(self, data: bytes) -> VKP:
        """
        Deserialize VKP from JSON bytes.
        
        Args:
            data: JSON bytes representation
        
        Returns:
            VKP object
        
        Raises:
            ValueError: If deserialization or validation fails
        
        Example:
            with open('package.vkp', 'rb') as f:
                data = f.read()
            vkp = packager.deserialize(data)
        """
        try:
            json_str = data.decode('utf-8')
            vkp = VKP.from_json(json_str)
            
            # Verify checksum
            if not self.verify_checksum(vkp):
                raise ValueError("VKP checksum verification failed")
            
            logger.info(
                f"Deserialized VKP: {vkp.subject} grade {vkp.grade} "
                f"v{vkp.version} ({vkp.total_chunks} chunks)"
            )
            
            return vkp
        
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid UTF-8 encoding: {e}")
        except Exception as e:
            logger.error(f"Failed to deserialize VKP: {e}")
            raise
    
    def serialize_to_file(self, vkp: VKP, filepath: str, indent: int = 2) -> None:
        """
        Serialize VKP and save to file.
        
        Args:
            vkp: VKP object to serialize
            filepath: Path to save file
            indent: Number of spaces for indentation
        
        Example:
            packager.serialize_to_file(vkp, 'matematika_10_1_v1.0.0.vkp')
        """
        data = self.serialize(vkp, indent=indent)
        
        with open(filepath, 'wb') as f:
            f.write(data)
        
        logger.info(f"Saved VKP to {filepath} ({len(data)} bytes)")
    
    def deserialize_from_file(self, filepath: str) -> VKP:
        """
        Load and deserialize VKP from file.
        
        Args:
            filepath: Path to VKP file
        
        Returns:
            VKP object
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If deserialization or validation fails
        
        Example:
            vkp = packager.deserialize_from_file('matematika_10_1_v1.0.0.vkp')
        """
        with open(filepath, 'rb') as f:
            data = f.read()
        
        logger.info(f"Loaded VKP from {filepath} ({len(data)} bytes)")
        
        return self.deserialize(data)
    
    def get_vkp_filename(self, vkp: VKP) -> str:
        """
        Generate standard filename for VKP.
        
        Format: {subject}_{grade}_{semester}_v{version}.vkp
        
        Args:
            vkp: VKP object
        
        Returns:
            Standard filename
        
        Example:
            filename = packager.get_vkp_filename(vkp)
            # Returns: 'matematika_10_1_v1.0.0.vkp'
        """
        return f"{vkp.subject}_{vkp.grade}_{vkp.semester}_v{vkp.version}.vkp"
    
    def get_s3_key(self, vkp: VKP) -> str:
        """
        Generate S3 key for VKP storage.
        
        Format: {subject}/kelas_{grade}/v{version}.vkp
        
        Args:
            vkp: VKP object
        
        Returns:
            S3 key path
        
        Example:
            key = packager.get_s3_key(vkp)
            # Returns: 'matematika/kelas_10/v1.0.0.vkp'
        """
        return f"{vkp.subject}/kelas_{vkp.grade}/v{vkp.version}.vkp"
