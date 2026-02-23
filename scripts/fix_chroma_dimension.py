#!/usr/bin/env python3
"""
Fix ChromaDB Embedding Dimension Mismatch

This script recreates the ChromaDB collection to match the current
embedding model dimension (1024 for Bedrock Titan v2).
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import chromadb
from chromadb.config import Settings


def fix_chroma_dimension():
    """Recreate ChromaDB collection with correct dimension."""
    
    chroma_path = "./data/vector_db"
    collection_name = "educational_content"
    
    print("=" * 60)
    print("ChromaDB Dimension Fix")
    print("=" * 60)
    print()
    
    print(f"ChromaDB Path: {chroma_path}")
    print(f"Collection: {collection_name}")
    print()
    
    try:
        # Initialize client
        print("[1/3] Connecting to ChromaDB...")
        client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )
        print("✓ Connected")
        print()
        
        # Check existing collection
        print("[2/3] Checking existing collection...")
        try:
            collection = client.get_collection(collection_name)
            doc_count = collection.count()
            print(f"✓ Found collection with {doc_count} documents")
            print()
            
            # Ask for confirmation
            print("⚠️  WARNING: This will delete the existing collection!")
            print(f"   {doc_count} documents will be lost.")
            print()
            response = input("Continue? (yes/no): ").strip().lower()
            
            if response != 'yes':
                print("\nOperation cancelled.")
                return False
            
            # Delete collection
            print("\nDeleting old collection...")
            client.delete_collection(collection_name)
            print("✓ Deleted")
            
        except Exception as e:
            print(f"Collection not found or error: {e}")
            print("Will create new collection...")
        
        print()
        
        # Create new collection
        print("[3/3] Creating new collection...")
        new_collection = client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": "Educational content embeddings",
                "embedding_dimension": 1024,
                "model": "amazon.titan-embed-text-v2:0"
            }
        )
        print("✓ Created new collection")
        print()
        
        print("=" * 60)
        print("✓ ChromaDB dimension fix complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Re-run the ETL pipeline to populate the collection:")
        print("   python scripts/data/run_etl_pipeline.py")
        print()
        print("2. Or restart the application - it will work with empty collection")
        print("   (fallback responses will be used until data is loaded)")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fix_chroma_dimension()
    sys.exit(0 if success else 1)
