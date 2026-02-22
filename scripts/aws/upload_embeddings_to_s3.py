#!/usr/bin/env python3
"""
Script untuk upload embeddings (vector DB) ke S3
Mengikuti struktur yang sudah ada di S3
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.aws_control_plane.s3_storage_manager import S3StorageManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Upload embeddings dan metadata ke S3"""
    
    # Load environment
    load_dotenv()
    
    logger.info("=" * 70)
    logger.info("Upload Embeddings to S3")
    logger.info("=" * 70)
    
    # Configuration
    subject = "informatika"
    grade = "kelas_10"
    
    # Paths
    vector_db_dir = "data/vector_db"
    metadata_dir = "data/processed/metadata"
    
    # Check if directories exist
    if not Path(vector_db_dir).exists():
        logger.error(f"Vector DB directory not found: {vector_db_dir}")
        logger.error("Run embedding generation first!")
        return 1
    
    try:
        # Initialize S3 manager
        logger.info("\nInitializing S3 storage manager...")
        s3_manager = S3StorageManager()
        logger.info(f"✓ Connected to bucket: {s3_manager.bucket_name}")
        
        # Upload ChromaDB (vector database)
        logger.info("\n" + "=" * 70)
        logger.info("1. Uploading Vector Database (ChromaDB)")
        logger.info("=" * 70)
        
        chromadb_result = s3_manager.upload_chromadb_files(
            chromadb_dir=vector_db_dir,
            subject=subject,
            grade=grade
        )
        
        logger.info(f"\nChromaDB Upload Results:")
        logger.info(f"  Successful: {chromadb_result.successful_uploads}")
        logger.info(f"  Failed: {chromadb_result.failed_uploads}")
        logger.info(f"  Total bytes: {chromadb_result.total_bytes_uploaded / (1024*1024):.2f} MB")
        
        if chromadb_result.errors:
            logger.warning(f"  Errors: {len(chromadb_result.errors)}")
            for error in chromadb_result.errors[:5]:  # Show first 5 errors
                logger.warning(f"    - {error}")
        
        # Upload metadata (progress, logs, etc)
        logger.info("\n" + "=" * 70)
        logger.info("2. Uploading Metadata Files")
        logger.info("=" * 70)
        
        if Path(metadata_dir).exists():
            metadata_result = s3_manager.upload_metadata(
                metadata_dir=metadata_dir,
                subject=subject,
                grade=grade
            )
            
            logger.info(f"\nMetadata Upload Results:")
            logger.info(f"  Successful: {metadata_result.successful_uploads}")
            logger.info(f"  Failed: {metadata_result.failed_uploads}")
            logger.info(f"  Total bytes: {metadata_result.total_bytes_uploaded / 1024:.2f} KB")
            
            if metadata_result.errors:
                logger.warning(f"  Errors: {len(metadata_result.errors)}")
                for error in metadata_result.errors[:5]:
                    logger.warning(f"    - {error}")
        else:
            logger.warning(f"Metadata directory not found: {metadata_dir}")
            metadata_result = None
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("UPLOAD SUMMARY")
        logger.info("=" * 70)
        
        total_successful = chromadb_result.successful_uploads
        total_failed = chromadb_result.failed_uploads
        total_bytes = chromadb_result.total_bytes_uploaded
        
        if metadata_result:
            total_successful += metadata_result.successful_uploads
            total_failed += metadata_result.failed_uploads
            total_bytes += metadata_result.total_bytes_uploaded
        
        logger.info(f"Total files uploaded: {total_successful}")
        logger.info(f"Total files failed: {total_failed}")
        logger.info(f"Total data uploaded: {total_bytes / (1024*1024):.2f} MB")
        
        # S3 structure
        logger.info("\n" + "=" * 70)
        logger.info("S3 STRUCTURE")
        logger.info("=" * 70)
        logger.info(f"Bucket: {s3_manager.bucket_name}")
        logger.info(f"Path: processed/{subject}/{grade}/")
        logger.info(f"  ├── chromadb/")
        logger.info(f"  │   └── [vector database files]")
        logger.info(f"  └── metadata/")
        logger.info(f"      ├── embedding_progress.json")
        logger.info(f"      └── [other metadata files]")
        
        # Verification
        logger.info("\n" + "=" * 70)
        logger.info("VERIFICATION")
        logger.info("=" * 70)
        
        # List uploaded files
        prefix = f"processed/{subject}/{grade}/"
        uploaded_files = s3_manager.list_uploaded_files(prefix)
        
        logger.info(f"Files in S3 with prefix '{prefix}': {len(uploaded_files)}")
        
        if uploaded_files:
            logger.info("\nSample files:")
            for file_info in uploaded_files[:10]:  # Show first 10
                size_mb = file_info['size'] / (1024*1024)
                logger.info(f"  - {file_info['key']} ({size_mb:.2f} MB)")
            
            if len(uploaded_files) > 10:
                logger.info(f"  ... and {len(uploaded_files) - 10} more files")
        
        # Final status
        logger.info("\n" + "=" * 70)
        
        if total_failed == 0:
            logger.info("✓ Upload selesai! Semua file berhasil di-upload ke S3")
            logger.info("=" * 70)
            
            logger.info("\n📊 View in AWS Console:")
            logger.info(f"S3: https://s3.console.aws.amazon.com/s3/buckets/{s3_manager.bucket_name}?prefix={prefix}")
            
            return 0
        else:
            logger.warning(f"⚠ Upload selesai dengan {total_failed} error(s)")
            logger.info("=" * 70)
            return 1
        
    except Exception as e:
        logger.error(f"\n✗ Error during upload: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
