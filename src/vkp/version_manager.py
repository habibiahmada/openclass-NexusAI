"""
VKP Version Manager

This module provides version tracking and management for VKP packages
using PostgreSQL for persistence.

Requirements: 6.1, 6.2
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class VKPVersionManager:
    """
    Manager for tracking VKP versions in PostgreSQL.
    
    Provides methods for version tracking, semantic version comparison,
    and rollback capability.
    """
    
    def __init__(self, db_manager):
        """
        Initialize VKPVersionManager with database manager.
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """
        Ensure vkp_versions table exists in database.
        
        Creates table if it doesn't exist.
        """
        create_table_query = """
            CREATE TABLE IF NOT EXISTS vkp_versions (
                id SERIAL PRIMARY KEY,
                subject VARCHAR(100) NOT NULL,
                grade INTEGER NOT NULL,
                semester INTEGER NOT NULL,
                version VARCHAR(20) NOT NULL,
                installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                chunk_count INTEGER DEFAULT 0,
                checksum VARCHAR(71),
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(subject, grade, semester, version)
            );
            
            CREATE INDEX IF NOT EXISTS idx_vkp_versions_subject_grade 
            ON vkp_versions(subject, grade, semester);
            
            CREATE INDEX IF NOT EXISTS idx_vkp_versions_active 
            ON vkp_versions(is_active);
        """
        
        try:
            self.db.execute_query(create_table_query)
            logger.info("VKP versions table ensured")
        except Exception as e:
            logger.error(f"Failed to create vkp_versions table: {e}")
            raise
    
    def register_version(
        self,
        subject: str,
        grade: int,
        semester: int,
        version: str,
        chunk_count: int = 0,
        checksum: Optional[str] = None
    ) -> bool:
        """
        Register a new VKP version in the database.
        
        Args:
            subject: Subject name
            grade: Grade level
            semester: Semester number
            version: Semantic version (MAJOR.MINOR.PATCH)
            chunk_count: Number of chunks in the VKP
            checksum: SHA256 checksum of the VKP
        
        Returns:
            True if registration succeeded
        
        Raises:
            ValueError: If version format is invalid
            Exception: If database operation fails
        
        Example:
            success = version_manager.register_version(
                subject="matematika",
                grade=10,
                semester=1,
                version="1.0.0",
                chunk_count=450,
                checksum="sha256:abc123..."
            )
        """
        # Validate version format
        if not self._validate_version_format(version):
            raise ValueError(
                f"Invalid version format: {version}. "
                "Must be semantic versioning (MAJOR.MINOR.PATCH)"
            )
        
        # Deactivate previous versions for this subject/grade/semester
        deactivate_query = """
            UPDATE vkp_versions
            SET is_active = FALSE
            WHERE subject = %(subject)s
              AND grade = %(grade)s
              AND semester = %(semester)s
              AND is_active = TRUE
        """
        
        deactivate_params = {
            'subject': subject,
            'grade': grade,
            'semester': semester
        }
        
        # Insert new version
        insert_query = """
            INSERT INTO vkp_versions 
            (subject, grade, semester, version, chunk_count, checksum, is_active)
            VALUES (%(subject)s, %(grade)s, %(semester)s, %(version)s, 
                    %(chunk_count)s, %(checksum)s, TRUE)
            ON CONFLICT (subject, grade, semester, version) 
            DO UPDATE SET 
                is_active = TRUE,
                installed_at = CURRENT_TIMESTAMP,
                chunk_count = %(chunk_count)s,
                checksum = %(checksum)s
            RETURNING id
        """
        
        insert_params = {
            'subject': subject,
            'grade': grade,
            'semester': semester,
            'version': version,
            'chunk_count': chunk_count,
            'checksum': checksum
        }
        
        try:
            # Execute in transaction
            self.db.execute_query(deactivate_query, deactivate_params)
            result = self.db.execute_query(insert_query, insert_params, fetch_one=True)
            
            if result:
                logger.info(
                    f"Registered VKP version: {subject} grade {grade} "
                    f"semester {semester} v{version}"
                )
                return True
            else:
                logger.error("Failed to register VKP version: no result returned")
                return False
        
        except Exception as e:
            logger.error(f"Failed to register VKP version: {e}")
            raise
    
    def get_installed_version(
        self,
        subject: str,
        grade: int,
        semester: int
    ) -> Optional[str]:
        """
        Get the currently installed (active) version for a subject/grade/semester.
        
        Args:
            subject: Subject name
            grade: Grade level
            semester: Semester number
        
        Returns:
            Version string if found, None otherwise
        
        Example:
            version = version_manager.get_installed_version(
                subject="matematika",
                grade=10,
                semester=1
            )
            # Returns: "1.2.0" or None
        """
        query = """
            SELECT version
            FROM vkp_versions
            WHERE subject = %(subject)s
              AND grade = %(grade)s
              AND semester = %(semester)s
              AND is_active = TRUE
            LIMIT 1
        """
        
        params = {
            'subject': subject,
            'grade': grade,
            'semester': semester
        }
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            
            if result:
                return result['version']
            
            return None
        
        except Exception as e:
            logger.error(
                f"Failed to get installed version for {subject} "
                f"grade {grade} semester {semester}: {e}"
            )
            raise
    
    def list_versions(
        self,
        subject: str,
        grade: int,
        semester: int
    ) -> List[Dict[str, Any]]:
        """
        List all versions for a subject/grade/semester.
        
        Args:
            subject: Subject name
            grade: Grade level
            semester: Semester number
        
        Returns:
            List of version records (newest first)
        
        Example:
            versions = version_manager.list_versions(
                subject="matematika",
                grade=10,
                semester=1
            )
            for v in versions:
                print(f"v{v['version']} - {v['installed_at']}")
        """
        query = """
            SELECT id, subject, grade, semester, version, installed_at,
                   chunk_count, checksum, is_active
            FROM vkp_versions
            WHERE subject = %(subject)s
              AND grade = %(grade)s
              AND semester = %(semester)s
            ORDER BY installed_at DESC
        """
        
        params = {
            'subject': subject,
            'grade': grade,
            'semester': semester
        }
        
        try:
            results = self.db.execute_query(query, params)
            return results if results else []
        
        except Exception as e:
            logger.error(
                f"Failed to list versions for {subject} "
                f"grade {grade} semester {semester}: {e}"
            )
            raise
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two semantic versions.
        
        Args:
            version1: First version (MAJOR.MINOR.PATCH)
            version2: Second version (MAJOR.MINOR.PATCH)
        
        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        
        Example:
            result = version_manager.compare_versions("1.0.0", "1.2.0")
            # Returns: -1 (1.0.0 < 1.2.0)
        """
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        if v1_parts < v2_parts:
            return -1
        elif v1_parts > v2_parts:
            return 1
        else:
            return 0
    
    def is_newer_version(self, current_version: str, new_version: str) -> bool:
        """
        Check if new_version is newer than current_version.
        
        Args:
            current_version: Current version
            new_version: New version to compare
        
        Returns:
            True if new_version > current_version
        
        Example:
            if version_manager.is_newer_version("1.0.0", "1.2.0"):
                print("Update available!")
        """
        return self.compare_versions(current_version, new_version) < 0
    
    def rollback_version(
        self,
        subject: str,
        grade: int,
        semester: int,
        target_version: str
    ) -> bool:
        """
        Rollback to a previous version.
        
        Deactivates current version and activates the target version.
        
        Args:
            subject: Subject name
            grade: Grade level
            semester: Semester number
            target_version: Version to rollback to
        
        Returns:
            True if rollback succeeded, False if target version not found
        
        Raises:
            Exception: If database operation fails
        
        Example:
            success = version_manager.rollback_version(
                subject="matematika",
                grade=10,
                semester=1,
                target_version="1.0.0"
            )
        """
        # Check if target version exists
        check_query = """
            SELECT id
            FROM vkp_versions
            WHERE subject = %(subject)s
              AND grade = %(grade)s
              AND semester = %(semester)s
              AND version = %(version)s
        """
        
        check_params = {
            'subject': subject,
            'grade': grade,
            'semester': semester,
            'version': target_version
        }
        
        # Deactivate all versions
        deactivate_query = """
            UPDATE vkp_versions
            SET is_active = FALSE
            WHERE subject = %(subject)s
              AND grade = %(grade)s
              AND semester = %(semester)s
        """
        
        deactivate_params = {
            'subject': subject,
            'grade': grade,
            'semester': semester
        }
        
        # Activate target version
        activate_query = """
            UPDATE vkp_versions
            SET is_active = TRUE
            WHERE subject = %(subject)s
              AND grade = %(grade)s
              AND semester = %(semester)s
              AND version = %(version)s
            RETURNING id
        """
        
        activate_params = {
            'subject': subject,
            'grade': grade,
            'semester': semester,
            'version': target_version
        }
        
        try:
            # Check if target version exists
            check_result = self.db.execute_query(check_query, check_params, fetch_one=True)
            
            if not check_result:
                logger.warning(
                    f"Target version {target_version} not found for rollback"
                )
                return False
            
            # Execute rollback in transaction
            self.db.execute_query(deactivate_query, deactivate_params)
            result = self.db.execute_query(activate_query, activate_params, fetch_one=True)
            
            if result:
                logger.info(
                    f"Rolled back to version {target_version} for {subject} "
                    f"grade {grade} semester {semester}"
                )
                return True
            else:
                logger.error("Failed to activate target version during rollback")
                return False
        
        except Exception as e:
            logger.error(f"Failed to rollback version: {e}")
            raise
    
    def get_version_info(
        self,
        subject: str,
        grade: int,
        semester: int,
        version: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific version.
        
        Args:
            subject: Subject name
            grade: Grade level
            semester: Semester number
            version: Version to query
        
        Returns:
            Version information dictionary or None if not found
        
        Example:
            info = version_manager.get_version_info(
                subject="matematika",
                grade=10,
                semester=1,
                version="1.0.0"
            )
        """
        query = """
            SELECT id, subject, grade, semester, version, installed_at,
                   chunk_count, checksum, is_active
            FROM vkp_versions
            WHERE subject = %(subject)s
              AND grade = %(grade)s
              AND semester = %(semester)s
              AND version = %(version)s
        """
        
        params = {
            'subject': subject,
            'grade': grade,
            'semester': semester,
            'version': version
        }
        
        try:
            result = self.db.execute_query(query, params, fetch_one=True)
            return result
        
        except Exception as e:
            logger.error(f"Failed to get version info: {e}")
            raise
    
    def _validate_version_format(self, version: str) -> bool:
        """
        Validate semantic version format.
        
        Args:
            version: Version string to validate
        
        Returns:
            True if valid, False otherwise
        """
        import re
        version_pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(version_pattern, version))
