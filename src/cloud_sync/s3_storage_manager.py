"""S3 Storage Manager

This module handles uploading processed knowledge base files to S3
with compression, encryption, and proper path structure.
"""

import gzip
import json
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

from config.aws_config import aws_config

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result from S3 upload operation."""
    successful_uploads: int = 0
    failed_uploads: int = 0
    total_bytes_uploaded: int = 0
    uploaded_files: List[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.uploaded_files is None:
            self.uploaded_files = []
        if self.errors is None:
            self.errors = []


class S3StorageManager:
    """Manages uploading knowledge base files to S3 with optimization."""
    
    def __init__(self, bucket_name: Optional[str] = None):
        """Initialize S3 storage manager.
        
        Args:
            bucket_name: S3 bucket name (defaults to config)
        """
        self.bucket_name = bucket_name or aws_config.s3_bucket
        self.s3_client = aws_config.get_s3_client()
        
        if not self.bucket_name:
            raise ValueError("S3 bucket name not configured")
        
        logger.info(f"Initialized S3StorageManager for bucket: {self.bucket_name}")
    
    def _build_s3_path(self, subject: str, grade: str, filename: str) -> str:
        """Build S3 path following the required structure.
        
        Args:
            subject: Subject area (e.g., "informatika")
            grade: Grade level (e.g., "kelas_10")
            filename: File name
            
        Returns:
            S3 path: processed/{subject}/{grade}/{filename}
        """
        # Normalize subject and grade
        subject = subject.lower().replace(" ", "_")
        grade = grade.lower().replace(" ", "_")
        
        # Build path: processed/{subject}/{grade}/{filename}
        s3_path = f"processed/{subject}/{grade}/{filename}"
        
        return s3_path
    
    def _compress_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """Compress file using gzip.
        
        Args:
            file_path: Path to file to compress
            output_path: Optional output path (defaults to file_path + .gz)
            
        Returns:
            Path to compressed file
        """
        if output_path is None:
            output_path = f"{file_path}.gz"
        
        logger.debug(f"Compressing {file_path} to {output_path}")
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Log compression ratio
        original_size = os.path.getsize(file_path)
        compressed_size = os.path.getsize(output_path)
        ratio = (1 - compressed_size / original_size) * 100
        
        logger.debug(
            f"Compressed {original_size} bytes to {compressed_size} bytes "
            f"({ratio:.1f}% reduction)"
        )
        
        return output_path

    def upload_file(
        self,
        local_path: str,
        s3_key: str,
        compress: bool = True,
        storage_class: str = "STANDARD_IA",
        encryption: str = "AES256"
    ) -> bool:
        """Upload a single file to S3 with compression and encryption.
        
        Args:
            local_path: Path to local file
            s3_key: S3 object key (path in bucket)
            compress: Whether to compress file with gzip
            storage_class: S3 storage class (STANDARD_IA for infrequent access)
            encryption: Server-side encryption algorithm (AES256)
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(local_path):
                logger.error(f"Local file not found: {local_path}")
                return False
            
            # Compress file if requested
            upload_path = local_path
            content_encoding = None
            
            if compress:
                # Create temporary compressed file
                compressed_path = f"{local_path}.tmp.gz"
                upload_path = self._compress_file(local_path, compressed_path)
                content_encoding = "gzip"
                
                # Update S3 key to include .gz extension if not already present
                if not s3_key.endswith('.gz'):
                    s3_key = f"{s3_key}.gz"
            
            # Prepare extra args for upload
            extra_args = {
                'StorageClass': storage_class,
                'ServerSideEncryption': encryption,
                'Metadata': {
                    'project': 'OpenClassNexusAI',
                    'content-type': 'knowledge-base',
                    'original-file': os.path.basename(local_path)
                }
            }
            
            if content_encoding:
                extra_args['ContentEncoding'] = content_encoding
            
            # Upload to S3
            logger.info(f"Uploading {local_path} to s3://{self.bucket_name}/{s3_key}")
            
            self.s3_client.upload_file(
                upload_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Clean up temporary compressed file
            if compress and os.path.exists(upload_path) and upload_path != local_path:
                os.remove(upload_path)
            
            # Get uploaded file size
            file_size = os.path.getsize(upload_path) if os.path.exists(upload_path) else 0
            
            logger.info(
                f"✓ Uploaded {s3_key} ({file_size / 1024:.1f} KB) "
                f"[{storage_class}, {encryption}]"
            )
            
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upload {local_path} to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading {local_path}: {e}")
            return False
    
    def upload_chromadb_files(
        self,
        chromadb_dir: str,
        subject: str,
        grade: str
    ) -> UploadResult:
        """Upload ChromaDB database files to S3.
        
        Args:
            chromadb_dir: Path to ChromaDB persistence directory
            subject: Subject area for path structure
            grade: Grade level for path structure
            
        Returns:
            UploadResult with upload statistics
        """
        result = UploadResult()
        
        chromadb_path = Path(chromadb_dir)
        
        if not chromadb_path.exists():
            error_msg = f"ChromaDB directory not found: {chromadb_dir}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        logger.info(f"Uploading ChromaDB files from {chromadb_dir}")
        
        # Find all files in ChromaDB directory
        files_to_upload = []
        for root, dirs, files in os.walk(chromadb_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Get relative path from chromadb_dir
                rel_path = os.path.relpath(file_path, chromadb_dir)
                files_to_upload.append((file_path, rel_path))
        
        logger.info(f"Found {len(files_to_upload)} files to upload")
        
        # Upload each file
        for file_path, rel_path in files_to_upload:
            # Build S3 key with proper structure
            filename = f"chromadb/{rel_path}".replace("\\", "/")
            s3_key = self._build_s3_path(subject, grade, filename)
            
            # Upload file
            success = self.upload_file(
                local_path=file_path,
                s3_key=s3_key,
                compress=True,
                storage_class="STANDARD_IA",
                encryption="AES256"
            )
            
            if success:
                result.successful_uploads += 1
                result.uploaded_files.append(s3_key)
                result.total_bytes_uploaded += os.path.getsize(file_path)
            else:
                result.failed_uploads += 1
                result.errors.append(f"Failed to upload {file_path}")
        
        logger.info(
            f"Upload complete: {result.successful_uploads} successful, "
            f"{result.failed_uploads} failed"
        )
        
        return result
    
    def upload_processed_text(
        self,
        text_dir: str,
        subject: str,
        grade: str
    ) -> UploadResult:
        """Upload processed text files to S3.
        
        Args:
            text_dir: Path to processed text directory
            subject: Subject area for path structure
            grade: Grade level for path structure
            
        Returns:
            UploadResult with upload statistics
        """
        result = UploadResult()
        
        text_path = Path(text_dir)
        
        if not text_path.exists():
            error_msg = f"Text directory not found: {text_dir}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        logger.info(f"Uploading processed text files from {text_dir}")
        
        # Find all text files
        text_files = list(text_path.glob("*.txt"))
        
        logger.info(f"Found {len(text_files)} text files to upload")
        
        # Upload each file
        for text_file in text_files:
            # Build S3 key
            filename = f"text/{text_file.name}"
            s3_key = self._build_s3_path(subject, grade, filename)
            
            # Upload file
            success = self.upload_file(
                local_path=str(text_file),
                s3_key=s3_key,
                compress=True,
                storage_class="STANDARD_IA",
                encryption="AES256"
            )
            
            if success:
                result.successful_uploads += 1
                result.uploaded_files.append(s3_key)
                result.total_bytes_uploaded += text_file.stat().st_size
            else:
                result.failed_uploads += 1
                result.errors.append(f"Failed to upload {text_file}")
        
        logger.info(
            f"Upload complete: {result.successful_uploads} successful, "
            f"{result.failed_uploads} failed"
        )
        
        return result
    
    def upload_metadata(
        self,
        metadata_dir: str,
        subject: str,
        grade: str
    ) -> UploadResult:
        """Upload metadata files to S3.
        
        Args:
            metadata_dir: Path to metadata directory
            subject: Subject area for path structure
            grade: Grade level for path structure
            
        Returns:
            UploadResult with upload statistics
        """
        result = UploadResult()
        
        metadata_path = Path(metadata_dir)
        
        if not metadata_path.exists():
            error_msg = f"Metadata directory not found: {metadata_dir}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        logger.info(f"Uploading metadata files from {metadata_dir}")
        
        # Find all JSON files
        json_files = list(metadata_path.glob("*.json"))
        
        logger.info(f"Found {len(json_files)} metadata files to upload")
        
        # Upload each file
        for json_file in json_files:
            # Build S3 key
            filename = f"metadata/{json_file.name}"
            s3_key = self._build_s3_path(subject, grade, filename)
            
            # Upload file (don't compress JSON files as they're already small)
            success = self.upload_file(
                local_path=str(json_file),
                s3_key=s3_key,
                compress=False,
                storage_class="STANDARD_IA",
                encryption="AES256"
            )
            
            if success:
                result.successful_uploads += 1
                result.uploaded_files.append(s3_key)
                result.total_bytes_uploaded += json_file.stat().st_size
            else:
                result.failed_uploads += 1
                result.errors.append(f"Failed to upload {json_file}")
        
        logger.info(
            f"Upload complete: {result.successful_uploads} successful, "
            f"{result.failed_uploads} failed"
        )
        
        return result
    
    def verify_upload(self, s3_key: str) -> bool:
        """Verify that a file exists in S3.
        
        Args:
            s3_key: S3 object key to verify
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False
    
    def list_uploaded_files(self, prefix: str) -> List[Dict[str, Any]]:
        """List files uploaded to S3 with a given prefix.
        
        Args:
            prefix: S3 key prefix to filter by
            
        Returns:
            List of file information dictionaries
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            files = []
            for obj in response['Contents']:
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                })
            
            return files
            
        except ClientError as e:
            logger.error(f"Failed to list files with prefix {prefix}: {e}")
            return []
