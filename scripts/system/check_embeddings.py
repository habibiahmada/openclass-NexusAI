#!/usr/bin/env python3
"""
Script untuk cek status embeddings lokal
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.embeddings.chroma_manager import ChromaDBManager

def main():
    print("=" * 70)
    print("Checking Local Embeddings Status")
    print("=" * 70)
    
    # Check vector DB directory
    vector_db_dir = Path("data/vector_db")
    print(f"\n1. Vector DB Directory: {vector_db_dir}")
    
    if vector_db_dir.exists():
        print(f"   ✓ Directory exists")
        
        # List files
        files = list(vector_db_dir.rglob("*"))
        print(f"   ✓ Total files: {len(files)}")
        
        # Check size
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        print(f"   ✓ Total size: {total_size / (1024*1024):.2f} MB")
    else:
        print(f"   ✗ Directory not found!")
        return 1
    
    # Check ChromaDB
    print(f"\n2. ChromaDB Status:")
    try:
        chroma = ChromaDBManager()
        chroma.get_collection("educational_content")
        
        doc_count = chroma.count_documents()
        print(f"   ✓ Collection exists")
        print(f"   ✓ Total documents: {doc_count}")
        
        if doc_count > 0:
            print(f"\n   🎉 SUCCESS! Embeddings tersimpan dengan baik!")
        else:
            print(f"\n   ⚠ WARNING: Collection kosong, embeddings belum selesai")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return 1
    
    # Check progress file
    print(f"\n3. Progress File:")
    progress_file = Path("data/processed/metadata/embedding_progress.json")
    
    if progress_file.exists():
        import json
        with open(progress_file, 'r') as f:
            progress = json.load(f)
        
        print(f"   ✓ Progress file exists")
        print(f"   ✓ Files processed: {len(progress.get('processed_files', []))}")
        print(f"   ✓ Total embeddings: {progress.get('total_embeddings', 0)}")
        print(f"   ✓ Total cost: ${progress.get('total_cost', 0):.4f}")
    else:
        print(f"   ⚠ Progress file not found")
    
    print("\n" + "=" * 70)
    print("✓ Check complete!")
    print("=" * 70)
    
    print("\nNote: Embeddings disimpan LOKAL, tidak di AWS!")
    print("AWS hanya digunakan untuk generate embeddings.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
