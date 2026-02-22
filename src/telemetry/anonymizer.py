"""
Anonymizer Module

Provides one-way anonymization for school IDs using SHA256 hashing.
Ensures school identity cannot be reversed from telemetry data.
"""

import hashlib
import os
import logging

logger = logging.getLogger(__name__)


class Anonymizer:
    """
    Anonymizes school IDs using one-way SHA256 hashing.
    
    Uses a salt from environment variable to ensure consistent
    hashing while preventing rainbow table attacks.
    """
    
    def __init__(self, salt: str = None):
        """
        Initialize anonymizer.
        
        Args:
            salt: Salt for hashing. If None, reads from SCHOOL_ID_SALT env var.
        """
        if salt is None:
            salt = os.getenv('SCHOOL_ID_SALT', 'nexusai-2026-default-salt')
            if salt == 'nexusai-2026-default-salt':
                logger.warning(
                    "Using default salt for school ID anonymization. "
                    "Set SCHOOL_ID_SALT environment variable for production."
                )
        
        self.salt = salt
    
    def anonymize_school_id(self, school_id: str) -> str:
        """
        Anonymize school ID using SHA256 hash.
        
        This is a one-way operation - the original school_id cannot
        be recovered from the hash.
        
        Args:
            school_id: Original school identifier
            
        Returns:
            Anonymized school ID (format: "school_<16-char-hash>")
        """
        if not school_id:
            raise ValueError("school_id cannot be empty")
        
        # Combine school_id with salt
        combined = f"{school_id}:{self.salt}"
        
        # Calculate SHA256 hash
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # Return first 16 characters with prefix
        return f"school_{hash_hex[:16]}"
    
    def verify_anonymization(self, school_id: str, anonymized_id: str) -> bool:
        """
        Verify that an anonymized ID matches a school ID.
        
        Args:
            school_id: Original school identifier
            anonymized_id: Anonymized school ID to verify
            
        Returns:
            True if anonymized_id matches school_id
        """
        expected = self.anonymize_school_id(school_id)
        return expected == anonymized_id


# Global singleton instance
_anonymizer_instance = None


def get_anonymizer() -> Anonymizer:
    """Get global anonymizer instance"""
    global _anonymizer_instance
    if _anonymizer_instance is None:
        _anonymizer_instance = Anonymizer()
    return _anonymizer_instance
