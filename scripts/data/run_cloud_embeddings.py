#!/usr/bin/env python3
"""
Script untuk menjalankan embedding di cloud menggunakan AWS Bedrock
dengan penanganan error yang lebih baik dan progress tracking
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.embeddings.bedrock_client import BedrockEmbeddingsClient
from src.embeddings.chroma_manager import ChromaDBManager
from src.data_processing.text_chunker import TextChunker
from src.data_processing.metadata_manager import MetadataManager, FileMetadata

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/metadata/embedding_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def save_progress(progress_data: dict, progress_file: Path):
    """Simpan progress ke file JSON"""
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, indent=2, ensure_ascii=False)


def load_progress(progress_file: Path) -> dict:
    """Load progress dari file JSON"""
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processed_files": [], "total_embeddings": 0, "total_cost": 0.0}


def main():
    """Generate embeddings menggunakan AWS Bedrock"""
    
    # Load environment
    load_dotenv()
    
    logger.info("=" * 70)
    logger.info("Cloud Embeddings Generation - AWS Bedrock")
    logger.info("=" * 70)
    
    # Setup paths
    text_dir = Path("data/processed/text")
    vector_db_dir = "data/vector_db"
    progress_file = Path("data/processed/metadata/embedding_progress.json")
    
    # Ensure directories exist
    Path("data/processed/metadata").mkdir(parents=True, exist_ok=True)
    
    if not text_dir.exists():
        logger.error(f"Text directory tidak ditemukan: {text_dir}")
        return 1
    
    # Load progress
    progress = load_progress(progress_file)
    processed_files = set(progress.get("processed_files", []))
    
    # Get all text files
    text_files = list(text_dir.glob("*.txt"))
    remaining_files = [f for f in text_files if f.name not in processed_files]
    
    logger.info(f"Total files: {len(text_files)}")
    logger.info(f"Already processed: {len(processed_files)}")
    logger.info(f"Remaining: {len(remaining_files)}")
    
    if len(remaining_files) == 0:
        logger.info("Semua file sudah diproses!")
        return 0
    
    # Initialize components
    try:
        logger.info("\nInisialisasi components...")
        bedrock_client = BedrockEmbeddingsClient()
        chroma_manager = ChromaDBManager(persist_directory=vector_db_dir)
        chroma_manager.create_collection("educational_content")
        text_chunker = TextChunker(chunk_size=800, overlap=100)
        metadata_manager = MetadataManager()
        
        logger.info("✓ Components berhasil diinisialisasi")
        
    except Exception as e:
        logger.error(f"✗ Gagal inisialisasi components: {e}")
        return 1
    
    # Process files
    total_chunks = progress.get("total_chunks", 0)
    total_embeddings = progress.get("total_embeddings", 0)
    failed_files = []
    
    for i, text_file in enumerate(remaining_files, 1):
        logger.info(f"\n{'='*70}")
        logger.info(f"[{i}/{len(remaining_files)}] Processing: {text_file.name}")
        logger.info(f"{'='*70}")
        
        try:
            # Read text
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if not text.strip():
                logger.warning(f"  ⚠ File kosong, skip: {text_file.name}")
                continue
            
            # Chunk text
            logger.info("  Chunking text...")
            chunks = text_chunker.chunk_text(text)
            logger.info(f"  ✓ Generated {len(chunks)} chunks")
            
            # Add metadata
            file_metadata = FileMetadata(
                subject="informatika",
                grade="kelas_10",
                filename=text_file.name
            )
            
            enriched_chunks = []
            for chunk in chunks:
                enriched_chunk = metadata_manager.enrich_chunk(
                    chunk=chunk,
                    file_metadata=file_metadata
                )
                enriched_chunks.append(enriched_chunk)
            
            # Generate embeddings dengan batch kecil
            batch_size = 3  # Batch kecil untuk menghindari rate limit
            embeddings = []
            
            logger.info(f"  Generating embeddings (batch size: {batch_size})...")
            
            for batch_start in range(0, len(chunks), batch_size):
                batch_end = min(batch_start + batch_size, len(chunks))
                batch_chunks = chunks[batch_start:batch_end]
                
                logger.info(f"    Batch {batch_start//batch_size + 1}: chunks {batch_start+1}-{batch_end}")
                
                try:
                    batch_texts = [chunk.text for chunk in batch_chunks]
                    batch_embeddings = bedrock_client.generate_batch(
                        texts=batch_texts,
                        batch_size=len(batch_texts)
                    )
                    embeddings.extend(batch_embeddings)
                    logger.info(f"    ✓ Generated {len(batch_embeddings)} embeddings")
                    
                except Exception as e:
                    logger.error(f"    ✗ Error generating embeddings: {e}")
                    logger.info(f"    Skipping batch...")
                    continue
            
            if len(embeddings) > 0:
                # Add to ChromaDB
                logger.info(f"  Adding {len(embeddings)} embeddings to vector DB...")
                chroma_manager.add_documents(
                    chunks=enriched_chunks[:len(embeddings)],
                    embeddings=embeddings
                )
                
                total_chunks += len(chunks)
                total_embeddings += len(embeddings)
                
                # Update progress
                processed_files.add(text_file.name)
                progress = {
                    "processed_files": list(processed_files),
                    "total_chunks": total_chunks,
                    "total_embeddings": total_embeddings,
                    "total_cost": bedrock_client.estimate_cost(),
                    "last_updated": datetime.now().isoformat()
                }
                save_progress(progress, progress_file)
                
                logger.info(f"  ✓ Successfully processed {text_file.name}")
                logger.info(f"  Progress: {len(processed_files)}/{len(text_files)} files")
            else:
                logger.warning(f"  ✗ No embeddings generated for {text_file.name}")
                failed_files.append(text_file.name)
            
        except Exception as e:
            logger.error(f"  ✗ Error processing {text_file.name}: {e}")
            failed_files.append(text_file.name)
            continue
    
    # Final summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total files: {len(text_files)}")
    logger.info(f"Successfully processed: {len(processed_files)}")
    logger.info(f"Failed: {len(failed_files)}")
    logger.info(f"Total chunks: {total_chunks}")
    logger.info(f"Total embeddings: {total_embeddings}")
    logger.info(f"Estimated cost: ${bedrock_client.estimate_cost():.4f}")
    
    if failed_files:
        logger.warning(f"\nFailed files: {', '.join(failed_files)}")
    
    # Verify vector DB
    doc_count = chroma_manager.count_documents()
    logger.info(f"\nDocuments in vector DB: {doc_count}")
    
    if doc_count > 0:
        logger.info("\n✓ Embedding generation selesai!")
        logger.info(f"Progress saved to: {progress_file}")
        return 0
    else:
        logger.error("\n✗ Vector database masih kosong!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
