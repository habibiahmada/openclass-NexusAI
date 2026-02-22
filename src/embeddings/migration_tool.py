"""
Embedding Migration Tool for migrating between different embedding dimensions.
Supports migrating ChromaDB collections when switching embedding strategies.
"""

import logging
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingMigrationTool:
    """Tool for migrating embeddings between different dimensions"""
    
    def __init__(self, chroma_client: chromadb.Client = None, persist_directory: str = "./chroma_db"):
        """Initialize migration tool.
        
        Args:
            chroma_client: Existing ChromaDB client (optional)
            persist_directory: Directory for ChromaDB persistence
        """
        if chroma_client:
            self.client = chroma_client
        else:
            self.client = chromadb.Client(Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            ))
        
        logger.info("Initialized EmbeddingMigrationTool")
    
    def migrate_collection(
        self,
        source_collection_name: str,
        target_collection_name: str,
        source_strategy,
        target_strategy,
        batch_size: int = 100
    ) -> bool:
        """Migrate a collection from one embedding strategy to another.
        
        Args:
            source_collection_name: Name of source collection
            target_collection_name: Name of target collection
            source_strategy: Source embedding strategy (for dimension info)
            target_strategy: Target embedding strategy (for re-embedding)
            batch_size: Number of documents to process at once
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            logger.info(
                f"Starting migration from {source_collection_name} "
                f"({source_strategy.get_dimension()}d) to {target_collection_name} "
                f"({target_strategy.get_dimension()}d)"
            )
            
            # Get source collection
            try:
                source_collection = self.client.get_collection(source_collection_name)
            except Exception as e:
                logger.error(f"Source collection not found: {e}")
                return False
            
            # Create target collection
            try:
                target_collection = self.client.create_collection(
                    name=target_collection_name,
                    metadata={"dimension": target_strategy.get_dimension()}
                )
            except Exception as e:
                logger.error(f"Failed to create target collection: {e}")
                return False
            
            # Get all documents from source
            source_data = source_collection.get(include=['documents', 'metadatas', 'embeddings'])
            
            if not source_data['ids']:
                logger.warning("Source collection is empty")
                return True
            
            total_docs = len(source_data['ids'])
            logger.info(f"Migrating {total_docs} documents...")
            
            # Process in batches
            for i in range(0, total_docs, batch_size):
                batch_end = min(i + batch_size, total_docs)
                
                batch_ids = source_data['ids'][i:batch_end]
                batch_documents = source_data['documents'][i:batch_end]
                batch_metadatas = source_data['metadatas'][i:batch_end]
                
                # Re-generate embeddings with target strategy
                logger.info(f"Processing batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}")
                
                try:
                    new_embeddings = target_strategy.batch_generate(batch_documents)
                except Exception as e:
                    logger.error(f"Failed to generate embeddings for batch: {e}")
                    return False
                
                # Add to target collection
                try:
                    target_collection.add(
                        ids=batch_ids,
                        documents=batch_documents,
                        metadatas=batch_metadatas,
                        embeddings=new_embeddings
                    )
                except Exception as e:
                    logger.error(f"Failed to add batch to target collection: {e}")
                    return False
            
            logger.info(f"Successfully migrated {total_docs} documents")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def verify_migration(
        self,
        source_collection_name: str,
        target_collection_name: str
    ) -> bool:
        """Verify that migration completed successfully.
        
        Args:
            source_collection_name: Name of source collection
            target_collection_name: Name of target collection
            
        Returns:
            True if verification passed, False otherwise
        """
        try:
            source_collection = self.client.get_collection(source_collection_name)
            target_collection = self.client.get_collection(target_collection_name)
            
            source_count = source_collection.count()
            target_count = target_collection.count()
            
            if source_count != target_count:
                logger.error(
                    f"Document count mismatch: source={source_count}, target={target_count}"
                )
                return False
            
            logger.info(f"Verification passed: {target_count} documents migrated")
            return True
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    def rollback_migration(self, target_collection_name: str) -> bool:
        """Rollback a migration by deleting the target collection.
        
        Args:
            target_collection_name: Name of target collection to delete
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            self.client.delete_collection(target_collection_name)
            logger.info(f"Rolled back migration: deleted {target_collection_name}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict]:
        """Get information about a collection.
        
        Args:
            collection_name: Name of collection
            
        Returns:
            Dictionary with collection info, or None if not found
        """
        try:
            collection = self.client.get_collection(collection_name)
            count = collection.count()
            metadata = collection.metadata
            
            return {
                'name': collection_name,
                'count': count,
                'metadata': metadata
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None
    
    def check_migration_needed(
        self,
        collection_name: str,
        target_strategy
    ) -> bool:
        """Check if migration is needed for a collection.
        
        Args:
            collection_name: Name of collection to check
            target_strategy: Target embedding strategy
            
        Returns:
            True if migration is needed, False otherwise
        """
        try:
            collection = self.client.get_collection(collection_name)
            
            # Get a sample embedding to check dimension
            sample = collection.get(limit=1, include=['embeddings'])
            
            if not sample['embeddings'] or len(sample['embeddings']) == 0:
                logger.info(f"Collection '{collection_name}' is empty, no migration needed")
                return False
            
            current_dim = len(sample['embeddings'][0])
            target_dim = target_strategy.get_dimension()
            
            if current_dim != target_dim:
                logger.info(
                    f"Migration needed: collection has {current_dim}d embeddings, "
                    f"target strategy produces {target_dim}d embeddings"
                )
                return True
            else:
                logger.info(f"No migration needed: dimensions match ({current_dim}d)")
                return False
                
        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return False
    
    def estimate_migration_time(
        self,
        collection_name: str,
        target_strategy,
        batch_size: int = 100
    ) -> Optional[float]:
        """Estimate time required for migration in seconds.
        
        Args:
            collection_name: Name of collection to migrate
            target_strategy: Target embedding strategy
            batch_size: Batch size for processing
            
        Returns:
            Estimated time in seconds, or None if estimation fails
        """
        try:
            collection = self.client.get_collection(collection_name)
            total_docs = collection.count()
            
            if total_docs == 0:
                return 0.0
            
            # Estimate based on strategy metrics if available
            if hasattr(target_strategy, 'get_metrics'):
                metrics = target_strategy.get_metrics()
                if metrics.total_calls > 0:
                    avg_time_per_doc = metrics.avg_time_ms / 1000  # Convert to seconds
                    estimated_time = (total_docs * avg_time_per_doc) * 1.2  # Add 20% buffer
                    
                    logger.info(
                        f"Estimated migration time: {estimated_time:.1f}s "
                        f"({total_docs} documents, {avg_time_per_doc*1000:.1f}ms per doc)"
                    )
                    return estimated_time
            
            # Fallback: rough estimate based on strategy type
            # Bedrock: ~100ms per doc, Local: ~50ms per doc
            time_per_doc = 0.1 if 'bedrock' in str(type(target_strategy)).lower() else 0.05
            estimated_time = (total_docs * time_per_doc) * 1.2  # Add 20% buffer
            
            logger.info(
                f"Estimated migration time (rough): {estimated_time:.1f}s "
                f"({total_docs} documents)"
            )
            return estimated_time
            
        except Exception as e:
            logger.error(f"Failed to estimate migration time: {e}")
            return None
