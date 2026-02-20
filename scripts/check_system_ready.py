#!/usr/bin/env python3
"""
Script untuk mengecek apakah sistem siap digunakan
Checks:
1. Model GGUF sudah didownload
2. Vector database sudah ada dan berisi dokumen
3. Dependencies terinstall
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_model():
    """Check if model is downloaded"""
    try:
        from src.local_inference.model_config import ModelConfig
        from src.local_inference.model_downloader import ModelDownloader
        
        config = ModelConfig()
        downloader = ModelDownloader(cache_dir="./models")
        status = downloader.get_download_status(config)
        
        if status.get('file_valid', False):
            logger.info(f"✓ Model: {config.gguf_filename} ({status['local_size_mb']:.1f} MB)")
            return True
        else:
            logger.error("✗ Model belum didownload")
            logger.info("  Jalankan: python scripts/download_model.py")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error checking model: {e}")
        return False


def check_vector_db():
    """Check if vector database exists and has documents"""
    try:
        from src.embeddings.chroma_manager import ChromaDBManager
        
        db_path = Path("./data/vector_db")
        if not db_path.exists():
            logger.error("✗ Vector database tidak ditemukan")
            logger.info("  Jalankan: python scripts/run_etl_pipeline.py")
            return False
        
        try:
            db = ChromaDBManager(
                persist_directory=str(db_path)
            )
            
            db.get_collection("educational_content")
            doc_count = db.count_documents()
            if doc_count > 0:
                logger.info(f"✓ Vector database: {doc_count} dokumen")
                return True
            else:
                logger.error("✗ Vector database kosong")
                logger.info("  Jalankan: python scripts/run_etl_pipeline.py")
                return False
                
        except ValueError:
            logger.error("✗ Vector database collection tidak ditemukan")
            logger.info("  Jalankan: python scripts/run_etl_pipeline.py")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error checking vector database: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    required = [
        'fastapi',
        'uvicorn',
        'chromadb',
        'llama_cpp',
        'psutil'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"✗ Missing dependencies: {', '.join(missing)}")
        logger.info("  Jalankan: pip install -r requirements.txt")
        return False
    else:
        logger.info("✓ Dependencies terinstall")
        return True


def main():
    """Run all checks"""
    print("=" * 60)
    print("  OpenClass Nexus AI - System Readiness Check")
    print("=" * 60)
    print()
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Model GGUF", check_model),
        ("Vector Database", check_vector_db)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            logger.error(f"✗ {name}: {e}")
            results.append(False)
        print()
    
    print("=" * 60)
    if all(results):
        print("✓ Sistem siap digunakan!")
        print("  Jalankan: start_web_ui.bat")
        return 0
    else:
        print("✗ Sistem belum siap")
        print("\nLangkah-langkah setup:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Process dokumen: python scripts/run_etl_pipeline.py")
        print("3. Download model: python scripts/download_model.py")
        print("4. Check lagi: python scripts/check_system_ready.py")
        return 1


if __name__ == '__main__':
    sys.exit(main())
