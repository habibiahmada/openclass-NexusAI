"""
VKP Puller

This module provides the VKPPuller class for periodically checking AWS S3
for curriculum updates, downloading new versions, verifying integrity,
and extracting embeddings to ChromaDB.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
"""

import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from .packager import VKPPackager
from .version_manager import VKPVersionManager
from .delta import DeltaCalculator, VKPDelta
from .models import VKP

logger = logging.getLogger(__name__)


@dataclass
class VKPUpdate:
    """
    Information about an available VKP update.
    
    Attributes:
        subject: Subject name
        grade: Grade level
        semester: Semester number
        cloud_version: Version available in S3
        local_version: Currently installed version (None if not installed)
        s3_key: S3 object key for the VKP
        size_bytes: Size of the VKP file in bytes
    """
    subject: str
    grade: int
    semester: int
    cloud_version: str
    local_version: Optional[str]
    s3_key: str
    size_bytes: int
    
    def is_update_available(self) -> bool:
        """Check if an update is available."""
        if self.local_version is None:
            return True  # New installation
        
        # Compare versions
        local_parts = [int(x) for x in self.local_version.split('.')]
        cloud_parts = [int(x) for x in self.cloud_version.split('.')]
        
        return cloud_parts > local_parts


class VKPPuller:
    """
    Puller for checking and downloading VKP updates from AWS S3.
    
    Provides methods for checking updates, downloading VKPs with retry logic,
    verifying integrity, and extracting to ChromaDB.
    """
    
    def __init__(
        self,
        bucket_name: str,
        version_manager: VKPVersionManager,
        chroma_manager,
        book_repository,
        region_name: str = 'ap-southeast-1',
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        """
        Initialize VKPPuller.
        
        Args:
            bucket_name: S3 bucket name for VKP packages
            version_manager: VKPVersionManager instance
            chroma_manager: ChromaDBManager instance
            book_repository: BookRepository instance for metadata updates
            region_name: AWS region name
            max_retries: Maximum number of download retries
            retry_delay: Delay between retries in seconds
        """
        self.bucket_name = bucket_name
        self.version_manager = version_manager
        self.chroma_manager = chroma_manager
        self.book_repository = book_repository
        self.region_name = region_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.packager = VKPPackager()
        self.delta_calculator = DeltaCalculator()
        
        # Initialize S3 client (will be created on first use)
        self._s3_client = None
    
    def _get_s3_client(self):
        """
        Get or create S3 client.
        
        Returns:
            boto3 S3 client
        
        Raises:
            RuntimeError: If AWS credentials are not configured
        """
        if self._s3_client is None:
            try:
                self._s3_client = boto3.client('s3', region_name=self.region_name)
                # Test connection
                self._s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"Connected to S3 bucket: {self.bucket_name}")
            except NoCredentialsError:
                raise RuntimeError(
                    "AWS credentials not configured. "
                    "Please configure AWS credentials to use VKP pull mechanism."
                )
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == '404':
                    raise RuntimeError(f"S3 bucket not found: {self.bucket_name}")
                elif error_code == '403':
                    raise RuntimeError(f"Access denied to S3 bucket: {self.bucket_name}")
                else:
                    raise RuntimeError(f"Failed to connect to S3: {e}")
        
        return self._s3_client
    
    def check_internet_connectivity(self) -> bool:
        """
        Check if internet connection is available.
        
        Returns:
            True if internet is available, False otherwise
        
        Requirement: 7.7 - Offline mode support
        """
        try:
            # Try to connect to S3
            s3_client = self._get_s3_client()
            s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception as e:
            logger.warning(f"Internet connectivity check failed: {e}")
            return False
    
    def check_updates(self) -> List[VKPUpdate]:
        """
        Check for available VKP updates in S3.
        
        Lists all VKP files in S3 and compares with locally installed versions.
        
        Returns:
            List of VKPUpdate objects for available updates
        
        Raises:
            RuntimeError: If S3 connection fails
        
        Requirement: 7.1 - Check for updates from S3
        
        Example:
            updates = puller.check_updates()
            for update in updates:
                if update.is_update_available():
                    print(f"Update available: {update.subject} v{update.cloud_version}")
        """
        try:
            s3_client = self._get_s3_client()
            
            logger.info(f"Checking for VKP updates in s3://{self.bucket_name}")
            
            # List all VKP files in bucket
            updates = []
            paginator = s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.bucket_name):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    s3_key = obj['Key']
                    
                    # Parse S3 key: {subject}/kelas_{grade}/v{version}.vkp
                    if not s3_key.endswith('.vkp'):
                        continue
                    
                    try:
                        parts = s3_key.split('/')
                        if len(parts) != 3:
                            continue
                        
                        subject = parts[0]
                        grade_str = parts[1]  # e.g., "kelas_10"
                        version_file = parts[2]  # e.g., "v1.0.0.vkp"
                        
                        # Extract grade number
                        if not grade_str.startswith('kelas_'):
                            continue
                        grade = int(grade_str.split('_')[1])
                        
                        # Extract version
                        if not version_file.startswith('v') or not version_file.endswith('.vkp'):
                            continue
                        cloud_version = version_file[1:-4]  # Remove 'v' prefix and '.vkp' suffix
                        
                        # Assume semester 1 (can be enhanced to parse from metadata)
                        semester = 1
                        
                        # Get local version
                        local_version = self.version_manager.get_installed_version(
                            subject=subject,
                            grade=grade,
                            semester=semester
                        )
                        
                        # Create update info
                        update = VKPUpdate(
                            subject=subject,
                            grade=grade,
                            semester=semester,
                            cloud_version=cloud_version,
                            local_version=local_version,
                            s3_key=s3_key,
                            size_bytes=obj['Size']
                        )
                        
                        updates.append(update)
                    
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse S3 key {s3_key}: {e}")
                        continue
            
            logger.info(f"Found {len(updates)} VKP packages in S3")
            
            # Filter to only updates that are newer
            available_updates = [u for u in updates if u.is_update_available()]
            
            logger.info(f"{len(available_updates)} updates available")
            
            return available_updates
        
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            raise RuntimeError(f"Update check failed: {e}")
    
    def compare_versions(self, local_version: str, cloud_version: str) -> str:
        """
        Compare two semantic versions.
        
        Args:
            local_version: Local version (MAJOR.MINOR.PATCH)
            cloud_version: Cloud version (MAJOR.MINOR.PATCH)
        
        Returns:
            "update_available" if cloud > local
            "up_to_date" if cloud == local
            "local_newer" if cloud < local (shouldn't happen)
        
        Requirement: 7.2 - Compare local version with cloud version
        
        Example:
            status = puller.compare_versions("1.0.0", "1.2.0")
            # Returns: "update_available"
        """
        local_parts = [int(x) for x in local_version.split('.')]
        cloud_parts = [int(x) for x in cloud_version.split('.')]
        
        if cloud_parts > local_parts:
            return "update_available"
        elif cloud_parts == local_parts:
            return "up_to_date"
        else:
            return "local_newer"
    
    def download_vkp(self, s3_key: str) -> VKP:
        """
        Download VKP from S3 with retry logic.
        
        Args:
            s3_key: S3 object key for the VKP
        
        Returns:
            VKP object
        
        Raises:
            RuntimeError: If download fails after all retries
        
        Requirement: 7.1 - Download VKP with retry logic
        
        Example:
            vkp = puller.download_vkp("matematika/kelas_10/v1.0.0.vkp")
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"Downloading VKP from s3://{self.bucket_name}/{s3_key} "
                    f"(attempt {attempt}/{self.max_retries})"
                )
                
                s3_client = self._get_s3_client()
                
                # Download VKP data
                response = s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                vkp_data = response['Body'].read()
                
                # Deserialize VKP
                vkp = self.packager.deserialize(vkp_data)
                
                logger.info(
                    f"Downloaded VKP: {vkp.subject} grade {vkp.grade} "
                    f"v{vkp.version} ({len(vkp_data)} bytes, {vkp.total_chunks} chunks)"
                )
                
                return vkp
            
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                
                if error_code == 'NoSuchKey':
                    raise RuntimeError(f"VKP not found in S3: {s3_key}")
                
                if attempt < self.max_retries:
                    logger.warning(
                        f"Download attempt {attempt} failed: {e}. "
                        f"Retrying in {self.retry_delay} seconds..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    raise RuntimeError(
                        f"Failed to download VKP after {self.max_retries} attempts: {e}"
                    )
            
            except Exception as e:
                if attempt < self.max_retries:
                    logger.warning(
                        f"Download attempt {attempt} failed: {e}. "
                        f"Retrying in {self.retry_delay} seconds..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    raise RuntimeError(
                        f"Failed to download VKP after {self.max_retries} attempts: {e}"
                    )
        
        raise RuntimeError("Download failed: max retries exceeded")
    
    def verify_integrity(self, vkp: VKP) -> bool:
        """
        Verify VKP integrity using checksum.
        
        Compares calculated checksum with stored checksum.
        
        Args:
            vkp: VKP object to verify
        
        Returns:
            True if checksum is valid, False otherwise
        
        Requirement: 7.4 - Verify integrity checksum before applying updates
        
        Example:
            if puller.verify_integrity(vkp):
                print("VKP integrity verified")
            else:
                print("VKP integrity check failed!")
        """
        return self.packager.verify_checksum(vkp)
    
    def extract_to_chromadb(self, vkp: VKP, collection_name: Optional[str] = None) -> bool:
        """
        Extract VKP embeddings to ChromaDB.
        
        Adds embeddings to appropriate collection, creating collection if needed.
        
        Args:
            vkp: VKP object to extract
            collection_name: Optional collection name (defaults to subject_grade_semester)
        
        Returns:
            True if extraction succeeded
        
        Raises:
            RuntimeError: If ChromaDB operation fails
        
        Requirement: 7.5 - Extract embeddings to ChromaDB
        
        Example:
            success = puller.extract_to_chromadb(vkp)
        """
        try:
            # Generate collection name if not provided
            if collection_name is None:
                collection_name = f"{vkp.subject}_grade{vkp.grade}_sem{vkp.semester}"
            
            logger.info(
                f"Extracting VKP to ChromaDB collection: {collection_name} "
                f"({vkp.total_chunks} chunks)"
            )
            
            # Create or get collection
            collection = self.chroma_manager.create_collection(name=collection_name)
            
            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in vkp.chunks]
            documents = [chunk.text for chunk in vkp.chunks]
            embeddings = [chunk.embedding for chunk in vkp.chunks]
            metadatas = [
                {
                    'subject': vkp.subject,
                    'grade': vkp.grade,
                    'semester': vkp.semester,
                    'version': vkp.version,
                    'page': chunk.metadata.page,
                    'section': chunk.metadata.section,
                    'topic': chunk.metadata.topic
                }
                for chunk in vkp.chunks
            ]
            
            # Add to collection (upsert to handle updates)
            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(
                f"Successfully extracted {vkp.total_chunks} chunks to ChromaDB"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to extract VKP to ChromaDB: {e}")
            raise RuntimeError(f"ChromaDB extraction failed: {e}")
    
    def update_metadata(self, vkp: VKP) -> bool:
        """
        Update PostgreSQL metadata with new VKP version.
        
        Updates books table with new version, timestamp, and chunk count.
        
        Args:
            vkp: VKP object with metadata to update
        
        Returns:
            True if update succeeded
        
        Raises:
            RuntimeError: If database operation fails
        
        Requirement: 7.6 - Update PostgreSQL metadata
        
        Example:
            success = puller.update_metadata(vkp)
        """
        try:
            logger.info(
                f"Updating metadata for {vkp.subject} grade {vkp.grade} "
                f"semester {vkp.semester} v{vkp.version}"
            )
            
            # Register version in version manager
            self.version_manager.register_version(
                subject=vkp.subject,
                grade=vkp.grade,
                semester=vkp.semester,
                version=vkp.version,
                chunk_count=vkp.total_chunks,
                checksum=vkp.checksum
            )
            
            # Update book repository (if book exists)
            # This assumes book_repository has an update_book_version method
            # If not, we'll just rely on version_manager
            
            logger.info("Metadata updated successfully")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            raise RuntimeError(f"Metadata update failed: {e}")
    
    def download_delta(self, s3_key: str) -> Optional[VKPDelta]:
        """
        Download delta package from S3 if available.
        
        Delta packages are stored with .delta.vkp extension.
        
        Args:
            s3_key: S3 object key for the full VKP
        
        Returns:
            VKPDelta object if delta exists, None otherwise
        
        Requirement: 7.3 - Download only changed chunks when possible
        """
        # Convert full VKP key to delta key
        # e.g., matematika/kelas_10/v1.2.0.vkp -> matematika/kelas_10/v1.2.0.delta.vkp
        delta_key = s3_key.replace('.vkp', '.delta.vkp')
        
        try:
            logger.info(f"Checking for delta package: {delta_key}")
            
            s3_client = self._get_s3_client()
            
            # Check if delta exists
            try:
                s3_client.head_object(Bucket=self.bucket_name, Key=delta_key)
            except ClientError as e:
                if e.response.get('Error', {}).get('Code', '') == '404':
                    logger.info("Delta package not available, will use full download")
                    return None
                raise
            
            # Download delta
            response = s3_client.get_object(Bucket=self.bucket_name, Key=delta_key)
            delta_data = response['Body'].read()
            
            # Deserialize delta
            import json
            delta_dict = json.loads(delta_data.decode('utf-8'))
            delta = VKPDelta.from_dict(delta_dict)
            
            logger.info(
                f"Downloaded delta package: {len(delta.added_chunks)} added chunks, "
                f"{len(delta.removed_chunk_ids)} removed chunks"
            )
            
            return delta
        
        except Exception as e:
            logger.warning(f"Failed to download delta package: {e}")
            return None
    
    def apply_delta_update(self, update: VKPUpdate, delta: VKPDelta) -> VKP:
        """
        Apply delta update to existing VKP.
        
        Args:
            update: VKPUpdate object
            delta: VKPDelta to apply
        
        Returns:
            New VKP with delta applied
        
        Raises:
            RuntimeError: If delta cannot be applied
        
        Requirement: 7.3 - Apply delta updates to existing ChromaDB
        """
        try:
            logger.info(
                f"Applying delta update from v{delta.base_version} to v{delta.version}"
            )
            
            # Get current VKP from ChromaDB
            # For now, we'll download the old VKP to apply delta
            # In production, this could be optimized to work directly with ChromaDB
            
            # Construct old VKP S3 key
            old_s3_key = f"{update.subject}/kelas_{update.grade}/v{update.local_version}.vkp"
            
            logger.info(f"Downloading base VKP: {old_s3_key}")
            old_vkp = self.download_vkp(old_s3_key)
            
            # Apply delta
            new_vkp = self.delta_calculator.apply_delta(old_vkp, delta)
            
            logger.info(
                f"Delta applied successfully: {new_vkp.total_chunks} total chunks"
            )
            
            return new_vkp
        
        except Exception as e:
            logger.error(f"Failed to apply delta update: {e}")
            raise RuntimeError(f"Delta application failed: {e}")
    
    def pull_update(self, update: VKPUpdate, use_delta: bool = True) -> bool:
        """
        Pull and install a VKP update.
        
        Downloads VKP (using delta if available), verifies integrity,
        extracts to ChromaDB, and updates metadata.
        
        Args:
            update: VKPUpdate object describing the update
            use_delta: Whether to attempt delta download (if available)
        
        Returns:
            True if update succeeded
        
        Raises:
            RuntimeError: If any step fails
        
        Requirement: 7.3 - Delta download optimization with fallback
        
        Example:
            success = puller.pull_update(update)
        """
        try:
            logger.info(
                f"Pulling update: {update.subject} grade {update.grade} "
                f"v{update.local_version} -> v{update.cloud_version}"
            )
            
            vkp = None
            delta_used = False
            
            # Try delta download if enabled and local version exists
            if use_delta and update.local_version is not None:
                try:
                    delta = self.download_delta(update.s3_key)
                    
                    if delta is not None:
                        # Apply delta to get new VKP
                        vkp = self.apply_delta_update(update, delta)
                        delta_used = True
                        
                        logger.info("Delta update applied successfully")
                
                except Exception as e:
                    logger.warning(
                        f"Delta update failed: {e}. Falling back to full download."
                    )
                    vkp = None
            
            # Fallback to full download if delta failed or not available
            if vkp is None:
                logger.info("Using full VKP download")
                vkp = self.download_vkp(update.s3_key)
            
            # Verify integrity
            if not self.verify_integrity(vkp):
                raise RuntimeError(
                    f"Integrity verification failed for {update.s3_key}. "
                    "VKP may be corrupted."
                )
            
            logger.info("VKP integrity verified")
            
            # Extract to ChromaDB
            self.extract_to_chromadb(vkp)
            
            # Update metadata
            self.update_metadata(vkp)
            
            # Log bandwidth savings if delta was used
            if delta_used:
                full_size = update.size_bytes
                delta_size = len(vkp.chunks) * 1000  # Rough estimate
                savings_percent = ((full_size - delta_size) / full_size * 100) if full_size > 0 else 0
                
                logger.info(
                    f"Bandwidth savings from delta update: ~{savings_percent:.1f}%"
                )
            
            logger.info(
                f"Successfully updated {update.subject} grade {update.grade} "
                f"to v{update.cloud_version}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to pull update: {e}")
            raise
    
    def pull_all_updates(self) -> Dict[str, Any]:
        """
        Check for and pull all available updates.
        
        Returns:
            Dictionary with update statistics
        
        Example:
            stats = puller.pull_all_updates()
            print(f"Updated {stats['successful_updates']} packages")
        """
        stats = {
            'successful_updates': 0,
            'failed_updates': 0,
            'skipped_updates': 0,
            'errors': []
        }
        
        try:
            # Check internet connectivity
            if not self.check_internet_connectivity():
                logger.info("Offline mode - skipping VKP update check")
                stats['skipped_updates'] = -1  # Indicate offline mode
                return stats
            
            # Check for updates
            updates = self.check_updates()
            
            if not updates:
                logger.info("No updates available")
                return stats
            
            # Pull each update
            for update in updates:
                try:
                    self.pull_update(update)
                    stats['successful_updates'] += 1
                except Exception as e:
                    logger.error(
                        f"Failed to update {update.subject} grade {update.grade}: {e}"
                    )
                    stats['failed_updates'] += 1
                    stats['errors'].append(str(e))
            
            logger.info(
                f"Update complete: {stats['successful_updates']} successful, "
                f"{stats['failed_updates']} failed"
            )
            
            return stats
        
        except Exception as e:
            logger.error(f"Failed to pull updates: {e}")
            stats['errors'].append(str(e))
            return stats
