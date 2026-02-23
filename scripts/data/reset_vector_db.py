#!/usr/bin/env python3
"""
Script untuk reset vector database dan progress tracking
Gunakan dengan hati-hati - akan menghapus semua data!
"""

import sys
import logging
from pathlib import Path
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.embeddings.chroma_manager import ChromaDBManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Reset vector database dan progress files"""
    
    logger.warning("=" * 70)
    logger.warning("PERINGATAN: Script ini akan menghapus semua data!")
    logger.warning("=" * 70)
    
    response = input("\nApakah Anda yakin ingin reset vector database? (yes/no): ")
    
    if response.lower() != 'yes':
        logger.info("Reset dibatalkan.")
        return 0
    
    try:
        # Reset ChromaDB
        logger.info("\n1. Resetting ChromaDB...")
        vector_db_dir = Path("data/vector_db")
        
        if vector_db_dir.exists():
            shutil.rmtree(vector_db_dir)
            logger.info(f"   ✓ Deleted: {vector_db_dir}")
        
        vector_db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"   ✓ Created fresh: {vector_db_dir}")
        
        # Delete progress file
        logger.info("\n2. Deleting progress tracking...")
        progress_file = Path("data/processed/metadata/embedding_progress.json")
        
        if progress_file.exists():
            progress_file.unlink()
            logger.info(f"   ✓ Deleted: {progress_file}")
        else:
            logger.info(f"   - Progress file tidak ada")
        
        # Delete log file
        log_file = Path("data/processed/metadata/embedding_log.txt")
        if log_file.exists():
            log_file.unlink()
            logger.info(f"   ✓ Deleted: {log_file}")
        
        logger.info("\n" + "=" * 70)
        logger.info("✓ Reset selesai!")
        logger.info("=" * 70)
        logger.info("\nAnda dapat menjalankan embedding dari awal dengan:")
        logger.info("  python scripts/run_cloud_embeddings.py")
        
        return 0
        
    except Exception as e:
        logger.error(f"\n✗ Error during reset: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
