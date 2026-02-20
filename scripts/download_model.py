#!/usr/bin/env python3
"""
Script untuk download model GGUF untuk Fase 3

Model yang akan didownload:
- Llama 3.2 3B Instruct Q4_K_M (optimal untuk 4GB RAM)
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.local_inference.model_downloader import ModelDownloader
from src.local_inference.model_config import ModelConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Download model GGUF"""
    
    logger.info("=" * 60)
    logger.info("Fase 3: Download Model GGUF")
    logger.info("=" * 60)
    
    # Create model config
    logger.info("\nMenggunakan model: Llama 3.2 3B Instruct Q4_K_M")
    logger.info("Size: ~2.0 GB")
    logger.info("Optimal untuk: 4GB RAM laptops")
    
    try:
        config = ModelConfig()  # Use default config
        logger.info(f"Model ID: {config.model_id}")
        logger.info(f"Filename: {config.gguf_filename}")
        logger.info(f"Repo: {config.gguf_repo}")
        
    except Exception as e:
        logger.error(f"Error creating model config: {e}")
        return 1
    
    # Initialize downloader
    try:
        downloader = ModelDownloader(cache_dir="./models")
        
    except Exception as e:
        logger.error(f"Error initializing downloader: {e}")
        return 1
    
    # Check if model already exists
    logger.info("\nChecking existing model...")
    status = downloader.get_download_status(config)
    
    if status.get('file_valid', False):
        logger.info("✓ Model sudah ada dan valid!")
        logger.info(f"  Path: {status['local_path']}")
        logger.info(f"  Size: {status['local_size_mb']:.2f} MB")
        return 0
    
    # Download model
    logger.info("\nMemulai download model...")
    logger.info("⚠️  Download akan memakan waktu tergantung koneksi internet")
    logger.info("⚠️  File size: ~2.0 GB")
    
    try:
        model_path = downloader.download_with_progress_bar(
            model_config=config,
            force_redownload=False
        )
        
        logger.info(f"\n✓ Model berhasil didownload!")
        logger.info(f"  Path: {model_path}")
        
        # Verify download
        logger.info("\nMemverifikasi download...")
        if downloader.verify_download(config):
            logger.info("✓ Verifikasi berhasil!")
            logger.info("\n✓ Fase 3 selesai! Model siap digunakan.")
            return 0
        else:
            logger.error("✗ Verifikasi gagal!")
            return 1
        
    except Exception as e:
        logger.error(f"\n✗ Download gagal: {e}")
        logger.info("\nTroubleshooting:")
        logger.info("1. Pastikan koneksi internet stabil")
        logger.info("2. Pastikan ada space disk minimal 3GB")
        logger.info("3. Coba jalankan ulang script ini (support resume)")
        return 1


if __name__ == '__main__':
    sys.exit(main())
