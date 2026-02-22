#!/usr/bin/env python3
"""
Script untuk download embeddings (vector DB) dari S3
Berguna untuk sync ke komputer lain atau restore
"""

import sys
import logging
import gzip
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from config.aws_config import aws_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def decompress_file(compressed_path: str, output_path: str):
    """Decompress gzip file"""
    with gzip.open(compressed_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def main():
    """Download embeddings dari S3"""
    
    # Load environment
    load_dotenv()
    
    logger.info("=" * 70)
    logger.info("Download Embeddings from S3")
    logger.info("=" * 70)
    
    # Configuration
    subject = "informatika"
    grade = "kelas_10"
    bucket_name = aws_config.s3_bucket
    
    if not bucket_name:
        logger.error("S3 bucket name not configured in .env")
        return 1
    
    # S3 prefix
    prefix = f"processed/{subject}/{grade}/"
    
    # Local paths
    vector_db_dir = Path("data/vector_db")
    metadata_dir = Path("data/processed/metadata")
    
    # Create directories
    vector_db_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize S3 client
        logger.info(f"\nConnecting to S3 bucket: {bucket_name}")
        s3_client = aws_config.get_s3_client()
        
        # List files in S3
        logger.info(f"Listing files with prefix: {prefix}")
        
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            logger.error(f"No files found in S3 with prefix: {prefix}")
            logger.error("Upload embeddings first using: python scripts/upload_embeddings_to_s3.py")
            return 1
        
        files_to_download = response['Contents']
        logger.info(f"Found {len(files_to_download)} files to download")
        
        # Download files
        downloaded = 0
        failed = 0
        total_bytes = 0
        
        for obj in files_to_download:
            s3_key = obj['Key']
            file_size = obj['Size']
            
            # Determine local path
            # Remove prefix to get relative path
            rel_path = s3_key.replace(prefix, '')
            
            if rel_path.startswith('chromadb/'):
                # ChromaDB file
                local_path = vector_db_dir / rel_path.replace('chromadb/', '')
            elif rel_path.startswith('metadata/'):
                # Metadata file
                local_path = metadata_dir / rel_path.replace('metadata/', '')
            else:
                logger.warning(f"Unknown file type: {s3_key}, skipping")
                continue
            
            # Create parent directory
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            logger.info(f"Downloading: {s3_key}")
            
            try:
                # Check if file is compressed
                is_compressed = s3_key.endswith('.gz')
                
                if is_compressed:
                    # Download to temporary file
                    temp_path = str(local_path) + '.tmp.gz'
                    s3_client.download_file(bucket_name, s3_key, temp_path)
                    
                    # Decompress
                    final_path = str(local_path).replace('.gz', '') if str(local_path).endswith('.gz') else str(local_path)
                    decompress_file(temp_path, final_path)
                    
                    # Remove temp file
                    Path(temp_path).unlink()
                    
                    logger.info(f"  ✓ Downloaded and decompressed to: {final_path}")
                else:
                    # Download directly
                    s3_client.download_file(bucket_name, s3_key, str(local_path))
                    logger.info(f"  ✓ Downloaded to: {local_path}")
                
                downloaded += 1
                total_bytes += file_size
                
            except Exception as e:
                logger.error(f"  ✗ Failed to download {s3_key}: {e}")
                failed += 1
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Files downloaded: {downloaded}")
        logger.info(f"Files failed: {failed}")
        logger.info(f"Total data downloaded: {total_bytes / (1024*1024):.2f} MB")
        
        logger.info(f"\nLocal paths:")
        logger.info(f"  Vector DB: {vector_db_dir}")
        logger.info(f"  Metadata: {metadata_dir}")
        
        # Verify
        logger.info("\n" + "=" * 70)
        logger.info("VERIFICATION")
        logger.info("=" * 70)
        
        # Check ChromaDB
        try:
            from src.embeddings.chroma_manager import ChromaDBManager
            
            chroma = ChromaDBManager()
            chroma.get_collection("educational_content")
            doc_count = chroma.count_documents()
            
            logger.info(f"✓ ChromaDB collection loaded")
            logger.info(f"✓ Total documents: {doc_count}")
            
        except Exception as e:
            logger.warning(f"⚠ Could not verify ChromaDB: {e}")
        
        logger.info("\n" + "=" * 70)
        
        if failed == 0:
            logger.info("✓ Download selesai! Embeddings berhasil di-download dari S3")
            logger.info("=" * 70)
            return 0
        else:
            logger.warning(f"⚠ Download selesai dengan {failed} error(s)")
            logger.info("=" * 70)
            return 1
        
    except Exception as e:
        logger.error(f"\n✗ Error during download: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
