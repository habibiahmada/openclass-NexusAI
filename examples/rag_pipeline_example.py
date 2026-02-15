"""
Example usage of RAG Pipeline Integration for Phase 3.

This example demonstrates how to use the RAG pipeline components
together for educational question answering in Indonesian.
"""

import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Example of RAG pipeline usage."""
    try:
        # Import components
        from src.embeddings.chroma_manager import ChromaDBManager
        from src.embeddings.bedrock_client import BedrockEmbeddingsClient
        from src.local_inference.inference_engine import InferenceEngine
        from src.local_inference.model_config import InferenceConfig, ModelConfig
        from src.local_inference.rag_pipeline import RAGPipeline
        from src.local_inference.context_manager import ContextManager
        from src.local_inference.fallback_handler import FallbackHandler, FallbackReason
        
        print("=== RAG Pipeline Integration Example ===\n")
        
        # 1. Initialize components
        print("1. Initializing components...")
        
        # Vector database
        vector_db = ChromaDBManager("data/vector_db")
        vector_db.create_collection()
        print(f"   - ChromaDB initialized with {vector_db.count_documents()} documents")
        
        # Model configuration
        model_config = ModelConfig()
        inference_config = InferenceConfig()
        print(f"   - Model config: {model_config.gguf_filename}")
        
        # Check if model exists
        model_path = model_config.get_model_path()
        if not model_path.exists():
            print(f"   - Model not found at {model_path}")
            print("   - Please run model download first")
            return
        
        # Inference engine
        inference_engine = InferenceEngine(str(model_path), inference_config)
        print("   - Inference engine initialized")
        
        # Embeddings client (optional for this example)
        embeddings_client = None
        try:
            embeddings_client = BedrockEmbeddingsClient()
            print("   - Bedrock embeddings client initialized")
        except Exception as e:
            print(f"   - Bedrock client not available: {e}")
        
        # Context manager
        context_manager = ContextManager(max_context_tokens=3000)
        print("   - Context manager initialized")
        
        # 2. Initialize RAG Pipeline
        print("\n2. Initializing RAG Pipeline...")
        rag_pipeline = RAGPipeline(
            vector_db=vector_db,
            inference_engine=inference_engine,
            embeddings_client=embeddings_client,
            context_manager=context_manager
        )
        
        # Get pipeline stats
        stats = rag_pipeline.get_pipeline_stats()
        print(f"   - Pipeline ready with {stats['vector_db_documents']} documents")
        
        # 3. Example queries
        print("\n3. Testing example queries...")
        
        example_queries = [
            "Apa itu algoritma dalam informatika?",
            "Jelaskan tentang fotosintesis",
            "Bagaimana cara menghitung luas lingkaran?",
            "",  # Empty query to test fallback
            "Mata pelajaran yang tidak ada"  # Non-existent subject
        ]
        
        for i, query in enumerate(example_queries, 1):
            print(f"\n   Query {i}: '{query}'")
            
            try:
                result = rag_pipeline.process_query(
                    query=query,
                    top_k=3,
                    max_tokens=256
                )
                
                print(f"   Response: {result.response[:100]}...")
                print(f"   Processing time: {result.processing_time_ms:.1f}ms")
                print(f"   Is fallback: {result.is_fallback}")
                
                if result.is_fallback:
                    print(f"   Fallback reason: {result.fallback_reason}")
                    print(f"   Suggestions: {len(result.suggestions)}")
                else:
                    print(f"   Sources used: {len(result.sources)}")
                    print(f"   Context stats: {result.context_stats}")
                
            except Exception as e:
                print(f"   Error: {e}")
        
        # 4. Demonstrate fallback handler directly
        print("\n4. Testing fallback handler...")
        
        fallback_handler = FallbackHandler()
        fallback_response = fallback_handler.generate_fallback_response(
            query="Pertanyaan tentang mata pelajaran yang tidak ada",
            reason=FallbackReason.SUBJECT_NOT_AVAILABLE,
            available_subjects=["matematika", "fisika", "informatika"]
        )
        
        print(f"   Fallback message: {fallback_response.message}")
        print(f"   Suggestions: {fallback_response.suggestions}")
        print(f"   Help resources: {len(fallback_response.help_resources)}")
        
        print("\n=== Example completed successfully! ===")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed")
    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Example failed")

if __name__ == "__main__":
    main()