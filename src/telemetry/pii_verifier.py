"""
PII Verifier Module

Verifies that telemetry data contains NO Personally Identifiable Information (PII).
Scans for patterns like NIK, email, phone, names, and suspicious keys.
"""

import re
import json
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class PIIMatch:
    """Represents a detected PII pattern match"""
    
    def __init__(self, pattern_name: str, matched_text: str, location: str):
        self.pattern_name = pattern_name
        self.matched_text = matched_text
        self.location = location
    
    def __repr__(self):
        return f"PIIMatch(pattern={self.pattern_name}, text={self.matched_text[:20]}..., location={self.location})"


class PIIVerifier:
    """
    Verifies that telemetry data contains NO PII.
    
    Privacy by architecture: This class enforces that sensitive data
    never leaves the school server.
    """
    
    # PII patterns to detect and reject
    PII_PATTERNS = {
        'nik': r'(?<![0-9.])\d{16}(?![0-9.])',  # Indonesian National ID (16 digits, not part of decimal)
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'(?<![0-9.])(\+62|0)\d{9,12}(?![0-9.])',  # Indonesian phone numbers (not part of decimal)
        'name_pattern': r'\b(?:Nama|Name|nama):\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
        'username_pattern': r'\b(?:Username|username|user):\s*\w+\b',
        'ip_address': r'(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)',  # IP address not part of larger number
        'session_token': r'\b[a-f0-9]{32,}\b',  # Long hex strings (likely tokens)
    }
    
    # Suspicious keys that might contain PII
    SUSPICIOUS_KEYS = [
        'username', 'user_name', 'userName', 'user_id', 'userId',
        'name', 'full_name', 'fullName', 'nama',
        'email', 'e_mail', 'eMail',
        'phone', 'phone_number', 'phoneNumber', 'telepon',
        'address', 'alamat',
        'nik', 'ktp',
        'password', 'pwd',
        'token', 'session_token', 'sessionToken',
        'chat', 'message', 'question', 'response', 'answer',
        'ip', 'ip_address', 'ipAddress',
        'student_id', 'studentId', 'teacher_id', 'teacherId'
    ]
    
    def verify_no_pii(self, data: dict) -> bool:
        """
        Verify that data contains NO PII.
        
        Args:
            data: Dictionary to verify
            
        Returns:
            True if no PII detected, False otherwise
        """
        # Convert to JSON string for pattern matching
        # Exclude school_id from PII scanning since it's already anonymized
        data_copy = data.copy()
        school_id = data_copy.pop('school_id', None)
        
        try:
            data_str = json.dumps(data_copy, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize data: {e}")
            return False
        
        # Check for PII patterns
        matches = self.scan_for_patterns(data_str)
        if matches:
            logger.error(f"PII patterns detected: {matches}")
            return False
        
        # Check for suspicious keys
        if self._has_suspicious_keys(data):
            logger.error("Suspicious keys detected in telemetry data")
            return False
        
        return True
    
    def scan_for_patterns(self, text: str) -> List[PIIMatch]:
        """
        Scan text for PII patterns.
        
        Args:
            text: Text to scan
            
        Returns:
            List of PIIMatch objects for detected patterns
        """
        matches = []
        
        for pattern_name, pattern in self.PII_PATTERNS.items():
            for match in re.finditer(pattern, text):
                matches.append(PIIMatch(
                    pattern_name=pattern_name,
                    matched_text=match.group(0),
                    location=f"position {match.start()}-{match.end()}"
                ))
        
        return matches
    
    def _has_suspicious_keys(self, data: dict, path: str = "") -> bool:
        """
        Check if dictionary contains suspicious keys.
        
        Args:
            data: Dictionary to check
            path: Current path in nested structure
            
        Returns:
            True if suspicious keys found
        """
        if not isinstance(data, dict):
            return False
        
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            # Check if key is suspicious
            if key.lower() in [k.lower() for k in self.SUSPICIOUS_KEYS]:
                logger.error(f"Suspicious key detected: {current_path}")
                return True
            
            # Recursively check nested dictionaries
            if isinstance(value, dict):
                if self._has_suspicious_keys(value, current_path):
                    return True
            
            # Check lists of dictionaries
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        if self._has_suspicious_keys(item, f"{current_path}[{i}]"):
                            return True
        
        return False
    
    def get_allowed_keys(self) -> List[str]:
        """
        Get list of allowed telemetry keys.
        
        Returns:
            List of allowed key names
        """
        return [
            'school_id',  # Anonymized
            'timestamp',
            'total_queries',
            'successful_queries',
            'failed_queries',
            'average_latency_ms',
            'p50_latency_ms',
            'p90_latency_ms',
            'p99_latency_ms',
            'model_version',
            'embedding_model',
            'chromadb_version',
            'error_rate',
            'error_types',
            'chromadb_size_mb',
            'postgres_size_mb',
            'disk_usage_percent'
        ]
    
    def validate_schema(self, data: dict) -> Tuple[bool, str]:
        """
        Validate that data only contains allowed keys.
        
        Args:
            data: Dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        allowed_keys = set(self.get_allowed_keys())
        actual_keys = set(data.keys())
        
        # Check for unexpected keys
        unexpected_keys = actual_keys - allowed_keys
        if unexpected_keys:
            return False, f"Unexpected keys: {unexpected_keys}"
        
        return True, ""
