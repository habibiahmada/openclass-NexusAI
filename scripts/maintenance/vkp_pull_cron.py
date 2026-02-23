import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.vkp.puller import VKPPuller
from src.vkp.version_manager import VKPVersionManager
from src.embeddings.chroma_manager import ChromaDBManager
from src.persistence.database_manager import DatabaseManager
from src.persistence.book_repository import BookRepository

# Configure logging
log_dir = project_root / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'vkp_pull.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def check_internet_connectivity() -> bool:
    """
    Check if internet connection is available.
    
    Returns:
        True if internet is available, False otherwise
    """
    import socket
    
    try:
        # Try to connect to AWS S3 endpoint
        socket.create_connection(("s3.amazonaws.com", 443), timeout=5)
        return True
    except OSError:
        return False


def main():
    """
    Main function for VKP pull cron job.
    
    Checks for updates, downloads new VKPs, and updates ChromaDB.
    """
    logger.info("=" * 80)
    logger.info("VKP Pull Cron Job Started")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 80)
    
    try:
        # Check internet connectivity first
        if not check_internet_connectivity():
            logger.info("No internet connection - skipping VKP update check (offline mode)")
            logger.info("System will continue operating with existing data")
            return 0
        
        logger.info("Internet connection available")
        
        # Load configuration
        from config.aws_config import aws_config
        bucket_name = os.getenv('VKP_BUCKET_NAME', aws_config.vkp_packages_bucket)
        db_connection_string = os.getenv(
            'DATABASE_URL',
            'postgresql://nexusai:nexusai@localhost:5432/nexusai'
        )
        chroma_persist_dir = os.getenv('CHROMA_PERSIST_DIR', 'data/vector_db')
        
        logger.info(f"Configuration:")
        logger.info(f"  S3 Bucket: {bucket_name}")
        logger.info(f"  ChromaDB: {chroma_persist_dir}")
        
        # Initialize components
        logger.info("Initializing components...")
        
        db_manager = DatabaseManager(db_connection_string)
        version_manager = VKPVersionManager(db_manager)
        chroma_manager = ChromaDBManager(persist_directory=chroma_persist_dir)
        book_repository = BookRepository(db_manager)
        
        # Initialize VKP puller
        puller = VKPPuller(
            bucket_name=bucket_name,
            version_manager=version_manager,
            chroma_manager=chroma_manager,
            book_repository=book_repository,
            region_name='ap-southeast-1',
            max_retries=3,
            retry_delay=5
        )
        
        logger.info("Components initialized successfully")
        
        # Pull all updates
        logger.info("Checking for VKP updates...")
        
        stats = puller.pull_all_updates()
        
        # Log results
        logger.info("=" * 80)
        logger.info("VKP Pull Results:")
        logger.info(f"  Successful updates: {stats['successful_updates']}")
        logger.info(f"  Failed updates: {stats['failed_updates']}")
        logger.info(f"  Skipped updates: {stats['skipped_updates']}")
        
        if stats['errors']:
            logger.error("Errors encountered:")
            for error in stats['errors']:
                logger.error(f"  - {error}")
        
        logger.info("=" * 80)
        logger.info("VKP Pull Cron Job Completed")
        logger.info("=" * 80)
        
        # Return exit code
        if stats['failed_updates'] > 0:
            return 1  # Partial failure
        else:
            return 0  # Success
    
    except Exception as e:
        logger.error(f"VKP pull cron job failed: {e}", exc_info=True)
        return 2  # Critical failure


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
