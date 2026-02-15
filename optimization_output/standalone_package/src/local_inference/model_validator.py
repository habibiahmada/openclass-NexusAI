"""
Model validator for GGUF format validation and integrity checking.

This module provides comprehensive validation capabilities for GGUF models
used in the OpenClass Nexus AI Phase 3 local inference system.
"""

import os
import struct
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json

from .model_config import ModelConfig

# Configure logging
logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Enumeration of validation results."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    """Represents a validation issue found during model checking."""
    level: ValidationResult
    category: str
    message: str
    details: Optional[Dict[str, Any]] = None


class GGUFHeader:
    """GGUF file format header parser."""
    
    # GGUF magic number and version
    GGUF_MAGIC = b'GGUF'
    SUPPORTED_VERSIONS = [3]  # GGUF v3 is current standard
    
    def __init__(self):
        self.magic = None
        self.version = None
        self.tensor_count = None
        self.metadata_kv_count = None
        self.metadata = {}
        self.is_valid = False
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'GGUFHeader':
        """
        Parse GGUF header from file.
        
        Args:
            file_path: Path to the GGUF file
            
        Returns:
            GGUFHeader instance with parsed information
        """
        header = cls()
        
        try:
            with open(file_path, 'rb') as f:
                # Read magic number (4 bytes)
                header.magic = f.read(4)
                if header.magic != cls.GGUF_MAGIC:
                    logger.error(f"Invalid GGUF magic number: {header.magic}")
                    return header
                
                # Read version (4 bytes, little-endian uint32)
                version_bytes = f.read(4)
                if len(version_bytes) != 4:
                    logger.error("Incomplete version field")
                    return header
                
                header.version = struct.unpack('<I', version_bytes)[0]
                if header.version not in cls.SUPPORTED_VERSIONS:
                    logger.warning(f"Unsupported GGUF version: {header.version}")
                
                # Read tensor count (8 bytes, little-endian uint64)
                tensor_count_bytes = f.read(8)
                if len(tensor_count_bytes) != 8:
                    logger.error("Incomplete tensor count field")
                    return header
                
                header.tensor_count = struct.unpack('<Q', tensor_count_bytes)[0]
                
                # Read metadata key-value count (8 bytes, little-endian uint64)
                kv_count_bytes = f.read(8)
                if len(kv_count_bytes) != 8:
                    logger.error("Incomplete metadata KV count field")
                    return header
                
                header.metadata_kv_count = struct.unpack('<Q', kv_count_bytes)[0]
                
                # Try to read some metadata (simplified parsing)
                try:
                    header.metadata = header._parse_metadata(f, header.metadata_kv_count)
                except Exception as e:
                    logger.warning(f"Could not parse metadata: {e}")
                    header.metadata = {}
                
                header.is_valid = True
                
        except Exception as e:
            logger.error(f"Error parsing GGUF header: {e}")
            header.is_valid = False
        
        return header
    
    def _parse_metadata(self, file_obj, kv_count: int) -> Dict[str, Any]:
        """
        Parse metadata key-value pairs (simplified implementation).
        
        Args:
            file_obj: Open file object
            kv_count: Number of key-value pairs to read
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # This is a simplified metadata parser
        # Full GGUF metadata parsing is complex and would require
        # handling various data types (strings, arrays, etc.)
        
        for i in range(min(kv_count, 50)):  # Limit to first 50 entries
            try:
                # Read key length (8 bytes)
                key_len_bytes = file_obj.read(8)
                if len(key_len_bytes) != 8:
                    break
                
                key_len = struct.unpack('<Q', key_len_bytes)[0]
                if key_len > 1000:  # Sanity check
                    break
                
                # Read key string
                key_bytes = file_obj.read(key_len)
                if len(key_bytes) != key_len:
                    break
                
                key = key_bytes.decode('utf-8', errors='ignore')
                
                # Read value type (4 bytes)
                value_type_bytes = file_obj.read(4)
                if len(value_type_bytes) != 4:
                    break
                
                value_type = struct.unpack('<I', value_type_bytes)[0]
                
                # Simplified value reading (only handle strings and numbers)
                if value_type == 8:  # String type
                    value_len_bytes = file_obj.read(8)
                    if len(value_len_bytes) != 8:
                        break
                    
                    value_len = struct.unpack('<Q', value_len_bytes)[0]
                    if value_len > 10000:  # Sanity check
                        break
                    
                    value_bytes = file_obj.read(value_len)
                    if len(value_bytes) == value_len:
                        metadata[key] = value_bytes.decode('utf-8', errors='ignore')
                
                elif value_type in [4, 5]:  # Int32, Int64
                    size = 4 if value_type == 4 else 8
                    value_bytes = file_obj.read(size)
                    if len(value_bytes) == size:
                        fmt = '<I' if value_type == 4 else '<Q'
                        metadata[key] = struct.unpack(fmt, value_bytes)[0]
                
                else:
                    # Skip unknown types
                    break
                    
            except Exception as e:
                logger.debug(f"Error parsing metadata entry {i}: {e}")
                break
        
        return metadata
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information from parsed metadata."""
        info = {
            'is_valid_gguf': self.is_valid,
            'version': self.version,
            'tensor_count': self.tensor_count,
            'metadata_count': self.metadata_kv_count
        }
        
        # Extract common metadata fields
        if self.metadata:
            info.update({
                'model_name': self.metadata.get('general.name', 'unknown'),
                'model_architecture': self.metadata.get('general.architecture', 'unknown'),
                'model_type': self.metadata.get('general.type', 'unknown'),
                'quantization': self.metadata.get('general.quantization_version', 'unknown'),
                'context_length': self.metadata.get('llama.context_length', 0),
                'embedding_length': self.metadata.get('llama.embedding_length', 0),
                'vocab_size': self.metadata.get('llama.vocab_size', 0)
            })
        
        return info


class ModelValidator:
    """
    Comprehensive model validator for GGUF format and integrity checking.
    
    This class provides validation capabilities for GGUF models including
    format validation, integrity checking, and compatibility verification.
    """
    
    def __init__(self):
        """Initialize the model validator."""
        self.validation_issues: List[ValidationIssue] = []
    
    def clear_issues(self) -> None:
        """Clear all validation issues."""
        self.validation_issues.clear()
    
    def add_issue(self, level: ValidationResult, category: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Add a validation issue."""
        issue = ValidationIssue(level, category, message, details)
        self.validation_issues.append(issue)
        
        # Log the issue
        log_level = {
            ValidationResult.ERROR: logging.ERROR,
            ValidationResult.INVALID: logging.ERROR,
            ValidationResult.WARNING: logging.WARNING,
            ValidationResult.VALID: logging.INFO
        }.get(level, logging.INFO)
        
        logger.log(log_level, f"[{category}] {message}")
    
    def validate_gguf_format(self, model_path: Path) -> bool:
        """
        Validate GGUF file format and structure.
        
        Args:
            model_path: Path to the GGUF model file
            
        Returns:
            bool: True if format is valid, False otherwise
        """
        if not model_path.exists():
            self.add_issue(ValidationResult.ERROR, "file", f"Model file does not exist: {model_path}")
            return False
        
        if not model_path.is_file():
            self.add_issue(ValidationResult.ERROR, "file", f"Path is not a file: {model_path}")
            return False
        
        # Check file size
        file_size = model_path.stat().st_size
        if file_size < 1024:  # Less than 1KB is definitely not a valid model
            self.add_issue(ValidationResult.ERROR, "file", f"File too small: {file_size} bytes")
            return False
        
        if file_size > 50 * 1024 * 1024 * 1024:  # Larger than 50GB is suspicious
            self.add_issue(ValidationResult.WARNING, "file", f"File very large: {file_size / (1024**3):.1f} GB")
        
        # Parse GGUF header
        try:
            header = GGUFHeader.from_file(model_path)
            
            if not header.is_valid:
                self.add_issue(ValidationResult.INVALID, "format", "Invalid GGUF header")
                return False
            
            # Validate header fields
            if header.version not in GGUFHeader.SUPPORTED_VERSIONS:
                self.add_issue(ValidationResult.WARNING, "format", f"Unsupported GGUF version: {header.version}")
            
            if header.tensor_count == 0:
                self.add_issue(ValidationResult.ERROR, "format", "No tensors found in model")
                return False
            
            if header.tensor_count > 1000:  # Sanity check
                self.add_issue(ValidationResult.WARNING, "format", f"Very high tensor count: {header.tensor_count}")
            
            # Log model information
            model_info = header.get_model_info()
            self.add_issue(ValidationResult.VALID, "format", f"Valid GGUF format detected", model_info)
            
            return True
            
        except Exception as e:
            self.add_issue(ValidationResult.ERROR, "format", f"Error validating GGUF format: {e}")
            return False
    
    def calculate_file_checksum(self, file_path: Path, algorithm: str = 'sha256', chunk_size: int = 8192) -> Optional[str]:
        """
        Calculate checksum of a file.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use
            chunk_size: Size of chunks to read
            
        Returns:
            Hexadecimal checksum string or None if error
        """
        try:
            hash_obj = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hash_obj.update(chunk)
            
            checksum = hash_obj.hexdigest()
            self.add_issue(ValidationResult.VALID, "checksum", f"Calculated {algorithm}: {checksum}")
            return checksum
            
        except Exception as e:
            self.add_issue(ValidationResult.ERROR, "checksum", f"Failed to calculate checksum: {e}")
            return None
    
    def verify_checksum(self, file_path: Path, expected_checksum: str, algorithm: str = 'sha256') -> bool:
        """
        Verify file checksum against expected value.
        
        Args:
            file_path: Path to the file
            expected_checksum: Expected checksum value
            algorithm: Hash algorithm to use
            
        Returns:
            bool: True if checksum matches, False otherwise
        """
        actual_checksum = self.calculate_file_checksum(file_path, algorithm)
        
        if actual_checksum is None:
            return False
        
        if actual_checksum.lower() == expected_checksum.lower():
            self.add_issue(ValidationResult.VALID, "checksum", "Checksum verification passed")
            return True
        else:
            self.add_issue(ValidationResult.INVALID, "checksum", 
                         f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}")
            return False
    
    def validate_model_compatibility(self, model_path: Path, model_config: ModelConfig) -> bool:
        """
        Validate model compatibility with configuration and system requirements.
        
        Args:
            model_path: Path to the model file
            model_config: Model configuration to validate against
            
        Returns:
            bool: True if compatible, False otherwise
        """
        try:
            # Parse GGUF header for model information
            header = GGUFHeader.from_file(model_path)
            
            if not header.is_valid:
                self.add_issue(ValidationResult.ERROR, "compatibility", "Cannot validate compatibility: invalid GGUF")
                return False
            
            model_info = header.get_model_info()
            
            # Check if this looks like the expected model
            expected_arch = "llama"  # Llama-3.2 uses llama architecture
            actual_arch = model_info.get('model_architecture', '').lower()
            
            if actual_arch and actual_arch != expected_arch:
                self.add_issue(ValidationResult.WARNING, "compatibility", 
                             f"Architecture mismatch: expected {expected_arch}, got {actual_arch}")
            
            # Check context length
            context_length = model_info.get('context_length', 0)
            if context_length > 0 and context_length < model_config.context_window:
                self.add_issue(ValidationResult.WARNING, "compatibility", 
                             f"Model context length ({context_length}) less than configured ({model_config.context_window})")
            
            # Check file size against expected
            file_size_mb = model_path.stat().st_size / (1024 * 1024)
            expected_size_mb = model_config.file_size_mb
            
            size_diff_percent = abs(file_size_mb - expected_size_mb) / expected_size_mb * 100
            if size_diff_percent > 20:  # More than 20% difference
                self.add_issue(ValidationResult.WARNING, "compatibility", 
                             f"File size differs significantly: {file_size_mb:.1f}MB vs expected {expected_size_mb}MB")
            
            # Check quantization format if available
            quantization = model_info.get('quantization', '')
            if quantization and model_config.quantization_format not in quantization:
                self.add_issue(ValidationResult.WARNING, "compatibility", 
                             f"Quantization format may not match: {quantization}")
            
            self.add_issue(ValidationResult.VALID, "compatibility", "Model compatibility check completed")
            return True
            
        except Exception as e:
            self.add_issue(ValidationResult.ERROR, "compatibility", f"Compatibility validation failed: {e}")
            return False
    
    def test_basic_inference(self, model_path: Path) -> Dict[str, Any]:
        """
        Test basic inference capability (without actually loading the full model).
        
        Args:
            model_path: Path to the model file
            
        Returns:
            Dict containing test results
        """
        test_results = {
            'can_open_file': False,
            'header_readable': False,
            'reasonable_size': False,
            'estimated_load_time': None,
            'memory_estimate_mb': None
        }
        
        try:
            # Test file access
            with open(model_path, 'rb') as f:
                # Try to read first few KB
                header_data = f.read(4096)
                if len(header_data) == 4096:
                    test_results['can_open_file'] = True
                    test_results['header_readable'] = header_data.startswith(b'GGUF')
            
            # Check file size reasonableness
            file_size_mb = model_path.stat().st_size / (1024 * 1024)
            test_results['reasonable_size'] = 100 <= file_size_mb <= 10000  # 100MB to 10GB
            
            # Estimate memory usage (rough approximation)
            # GGUF models typically use slightly more RAM than file size
            test_results['memory_estimate_mb'] = int(file_size_mb * 1.2)
            
            # Estimate load time (very rough, based on file size)
            # Assume ~100MB/s read speed for estimation
            test_results['estimated_load_time'] = file_size_mb / 100
            
            if all([test_results['can_open_file'], test_results['header_readable'], test_results['reasonable_size']]):
                self.add_issue(ValidationResult.VALID, "inference", "Basic inference test passed")
            else:
                self.add_issue(ValidationResult.WARNING, "inference", "Basic inference test had issues")
            
        except Exception as e:
            self.add_issue(ValidationResult.ERROR, "inference", f"Basic inference test failed: {e}")
        
        return test_results
    
    def validate_model(self, model_config: ModelConfig, expected_checksum: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive model validation.
        
        Args:
            model_config: Configuration for the model to validate
            expected_checksum: Optional expected checksum for verification
            
        Returns:
            Dict containing comprehensive validation results
        """
        self.clear_issues()
        
        model_path = model_config.get_model_path()
        
        validation_results = {
            'model_path': str(model_path),
            'format_valid': False,
            'checksum_valid': None,
            'compatibility_valid': False,
            'inference_test': {},
            'overall_valid': False,
            'issues': [],
            'recommendations': []
        }
        
        try:
            # 1. Validate GGUF format
            validation_results['format_valid'] = self.validate_gguf_format(model_path)
            
            # 2. Verify checksum if provided
            if expected_checksum:
                validation_results['checksum_valid'] = self.verify_checksum(model_path, expected_checksum)
            
            # 3. Validate compatibility
            validation_results['compatibility_valid'] = self.validate_model_compatibility(model_path, model_config)
            
            # 4. Test basic inference capability
            validation_results['inference_test'] = self.test_basic_inference(model_path)
            
            # 5. Determine overall validity
            format_ok = validation_results['format_valid']
            checksum_ok = validation_results['checksum_valid'] is not False  # None or True
            compatibility_ok = validation_results['compatibility_valid']
            
            validation_results['overall_valid'] = format_ok and checksum_ok and compatibility_ok
            
            # 6. Compile issues and recommendations
            validation_results['issues'] = [
                {
                    'level': issue.level.value,
                    'category': issue.category,
                    'message': issue.message,
                    'details': issue.details
                }
                for issue in self.validation_issues
            ]
            
            # Generate recommendations based on issues
            error_count = sum(1 for issue in self.validation_issues if issue.level in [ValidationResult.ERROR, ValidationResult.INVALID])
            warning_count = sum(1 for issue in self.validation_issues if issue.level == ValidationResult.WARNING)
            
            if error_count > 0:
                validation_results['recommendations'].append("Model has critical issues and should be re-downloaded")
            elif warning_count > 0:
                validation_results['recommendations'].append("Model has warnings but may still be usable")
            else:
                validation_results['recommendations'].append("Model validation passed successfully")
            
            # Memory and performance recommendations
            memory_estimate = validation_results['inference_test'].get('memory_estimate_mb', 0)
            if memory_estimate > 3000:
                validation_results['recommendations'].append("Model may require more than 3GB RAM - consider memory optimization")
            
        except Exception as e:
            self.add_issue(ValidationResult.ERROR, "validation", f"Validation process failed: {e}")
            validation_results['overall_valid'] = False
        
        return validation_results
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the last validation run.
        
        Returns:
            Dict containing validation summary
        """
        error_count = sum(1 for issue in self.validation_issues if issue.level in [ValidationResult.ERROR, ValidationResult.INVALID])
        warning_count = sum(1 for issue in self.validation_issues if issue.level == ValidationResult.WARNING)
        info_count = sum(1 for issue in self.validation_issues if issue.level == ValidationResult.VALID)
        
        return {
            'total_issues': len(self.validation_issues),
            'errors': error_count,
            'warnings': warning_count,
            'info': info_count,
            'has_errors': error_count > 0,
            'has_warnings': warning_count > 0,
            'status': 'error' if error_count > 0 else ('warning' if warning_count > 0 else 'valid')
        }


def validate_model_file(model_config: ModelConfig, expected_checksum: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to validate a model file.
    
    Args:
        model_config: Configuration for the model to validate
        expected_checksum: Optional expected checksum
        
    Returns:
        Dict containing validation results
    """
    validator = ModelValidator()
    return validator.validate_model(model_config, expected_checksum)


def quick_format_check(model_path: Path) -> bool:
    """
    Quick check if a file is a valid GGUF format.
    
    Args:
        model_path: Path to the model file
        
    Returns:
        bool: True if valid GGUF format, False otherwise
    """
    validator = ModelValidator()
    return validator.validate_gguf_format(model_path)