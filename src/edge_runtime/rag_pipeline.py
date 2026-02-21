"""
RAG (Retrieval-Augmented Generation) Pipeline for OpenClass Nexus AI Phase 3.

This module integrates ChromaDB vector search with local Llama-3.2-3B-Instruct
inference to provide grounded educational responses in Indonesian language.
"""

import logging
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass
from datetime import datetime

from src.embeddings.chroma_manager import ChromaDBManager, SearchResult
from src.embeddings.bedrock_client import BedrockEmbeddingsClient
from src.edge_runtime.inference_engine import InferenceEngine
from src.edge_runtime.context_manager import ContextManager, Document
from src.edge_runtime.fallback_handler import FallbackHandler, FallbackReason
from src.edge_runtime.graceful_degradation import GracefulDegradationManager


logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result from RAG pipeline query processing."""
    query: str
    response: str
    context_used: str
    sources: List[Dict[str, Any]]
    processing_time_ms: float
    context_stats: Dict[str, Any]
    timestamp: datetime
    is_fallback: bool = False
    fallback_reason: Optional[str] = None
    suggestions: List[str] = None
    help_resources: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.suggestions is None:
            self.suggestions = []
        if self.help_resources is None:
            self.help_resources = []


class EducationalPromptTemplate:
    """Indonesian educational prompt templates for Llama-3.2-3B-Instruct."""
    
    SYSTEM_PROMPT = """Anda adalah asisten AI untuk pendidikan Indonesia. Jawab pertanyaan berdasarkan materi yang diberikan dengan bahasa yang mudah dipahami siswa SMA/SMK.

Aturan:
1. Gunakan bahasa Indonesia yang baik dan benar
2. Berikan penjelasan yang jelas dan terstruktur
3. Sertakan contoh jika membantu pemahaman
4. Jika tidak ada informasi yang relevan, katakan "Maaf, materi ini belum ada di database saya"
5. Selalu sertakan sumber referensi dari materi yang digunakan
6. Jawab dengan singkat dan fokus pada pertanyaan"""

    USER_TEMPLATE = """Konteks dari materi pembelajaran:
{context}

Pertanyaan siswa: {question}

Jawaban:"""
    
    FALLBACK_TEMPLATE = """Pertanyaan siswa: {question}

Maaf, saya tidak menemukan materi yang relevan dengan pertanyaan Anda di database saya. Silakan coba pertanyaan yang lebih spesifik atau hubungi guru Anda untuk bantuan lebih lanjut.

Jawaban:"""
    
    def format_prompt(self, context: str, question: str) -> str:
        """Format prompt with context and question."""
        if context.strip():
            return f"{self.SYSTEM_PROMPT}\n\n{self.USER_TEMPLATE.format(context=context, question=question)}"
        else:
            return f"{self.SYSTEM_PROMPT}\n\n{self.FALLBACK_TEMPLATE.format(question=question)}"


class RAGPipeline:
    """
    RAG Pipeline integrating ChromaDB retrieval with local inference.
    
    This pipeline provides educational question-answering capabilities
    by combining semantic search with local AI generation, optimized
    for Indonesian educational content.
    """
    
    def __init__(
        self,
        vector_db: ChromaDBManager,
        inference_engine: InferenceEngine,
        embeddings_client: Optional[BedrockEmbeddingsClient] = None,
        context_manager: Optional[ContextManager] = None,
        degradation_manager: Optional[GracefulDegradationManager] = None
    ):
        """
        Initialize RAG pipeline.
        
        Args:
            vector_db: ChromaDB manager for document retrieval
            inference_engine: Local inference engine for response generation
            embeddings_client: Client for generating query embeddings (optional)
            context_manager: Context manager for token optimization (optional)
            degradation_manager: Graceful degradation manager for performance optimization (optional)
        """
        self.vector_db = vector_db
        self.inference_engine = inference_engine
        self.embeddings_client = embeddings_client
        self.context_manager = context_manager or ContextManager()
        self.degradation_manager = degradation_manager
        self.prompt_template = EducationalPromptTemplate()
        self.fallback_handler = FallbackHandler()
        
        # Connect degradation manager to context manager if both are available
        if self.degradation_manager and hasattr(self.context_manager, 'degradation_manager'):
            self.context_manager.degradation_manager = self.degradation_manager
        
        # Ensure vector database collection is available
        try:
            self.vector_db.get_collection()
        except ValueError:
            logger.warning("ChromaDB collection not found, creating new collection")
            self.vector_db.create_collection()
        
        logger.info("Initialized RAGPipeline with all components")
    
    def process_query(
        self, 
        query: str, 
        subject_filter: Optional[str] = None,
        grade_filter: Optional[str] = None,
        top_k: int = 5,
        max_tokens: Optional[int] = None
    ) -> QueryResult:
        """
        Process educational query with context retrieval and generation.
        
        Args:
            query: User question in Indonesian
            subject_filter: Optional subject filter (e.g., "informatika")
            grade_filter: Optional grade filter (e.g., "kelas_10")
            top_k: Number of documents to retrieve
            max_tokens: Maximum tokens for response generation
            
        Returns:
            QueryResult with response and metadata
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
            # Check for empty query
            if not query or not query.strip():
                return self._generate_fallback_result(
                    query, FallbackReason.EMPTY_QUERY, start_time
                )
            
            # Step 1: Retrieve relevant context
            context, selected_docs = self.retrieve_context(
                query, 
                subject_filter=subject_filter,
                grade_filter=grade_filter,
                top_k=top_k
            )
            
            # Check if we have sufficient context
            if not context.strip():
                return self._generate_fallback_result(
                    query, FallbackReason.NO_RELEVANT_CONTENT, start_time
                )
            
            # Step 2: Construct educational prompt
            prompt = self.construct_prompt(query, context)
            
            # Step 3: Adjust generation parameters based on degradation level
            generation_params = {}
            if max_tokens:
                generation_params['max_tokens'] = max_tokens
            
            # Apply degradation-based adjustments
            if self.degradation_manager:
                adjustments = self.degradation_manager.get_inference_config_adjustments()
                degradation_level = adjustments.get('degradation_level', 'OPTIMAL')
                
                # Reduce max_tokens for higher degradation levels
                if degradation_level in ['HEAVY', 'CRITICAL'] and not max_tokens:
                    generation_params['max_tokens'] = 256  # Shorter responses under stress
                elif degradation_level in ['MODERATE'] and not max_tokens:
                    generation_params['max_tokens'] = 384  # Moderately shorter responses
                
                logger.debug(f"Applied degradation adjustments for level {degradation_level}")
            
            # Step 3: Generate response using local inference
            response = self.generate_response(prompt, **generation_params)
            
            # Check if response generation failed
            if not response or "terjadi kesalahan" in response.lower():
                return self._generate_fallback_result(
                    query, FallbackReason.TECHNICAL_ERROR, start_time
                )
            
            # Step 4: Extract source information
            sources = self._extract_sources(selected_docs)
            
            # Step 5: Get context statistics
            context_stats = self.context_manager.get_context_stats(context, selected_docs)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            result = QueryResult(
                query=query,
                response=response,
                context_used=context,
                sources=sources,
                processing_time_ms=processing_time,
                context_stats=context_stats,
                timestamp=start_time,
                is_fallback=False
            )
            
            logger.info(f"Query processed successfully in {processing_time:.1f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return self._generate_fallback_result(
                query, FallbackReason.TECHNICAL_ERROR, start_time
            )
    
    def retrieve_context(
        self, 
        query: str, 
        subject_filter: Optional[str] = None,
        grade_filter: Optional[str] = None,
        top_k: int = 5
    ) -> tuple[str, List[Document]]:
        """
        Retrieve relevant educational content from ChromaDB.
        
        Args:
            query: User query
            subject_filter: Optional subject filter
            grade_filter: Optional grade filter
            top_k: Number of documents to retrieve
            
        Returns:
            Tuple of (formatted_context, selected_documents)
        """
        try:
            # Generate query embedding if embeddings client is available
            if self.embeddings_client:
                query_embedding = self.embeddings_client.generate_embedding(query)
            else:
                # Fallback: use a dummy embedding or raise error
                logger.warning("No embeddings client available, using dummy embedding")
                query_embedding = [0.0] * 1024  # Titan embeddings are 1024-dimensional
            
            # Search in vector database
            search_results = self.vector_db.query(
                query_embedding=query_embedding,
                n_results=top_k
            )
            
            # Apply filters if specified
            if subject_filter or grade_filter:
                search_results = self._apply_filters(search_results, subject_filter, grade_filter)
            
            # Use context manager to fit within token limits
            context, selected_docs = self.context_manager.fit_context(search_results, query)
            
            logger.debug(f"Retrieved {len(selected_docs)} documents for context")
            return context, selected_docs
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return "", []
    
    def construct_prompt(self, query: str, context: str) -> str:
        """
        Build educational prompt with Indonesian context.
        
        Args:
            query: User question
            context: Retrieved context from documents
            
        Returns:
            Formatted prompt for the model
        """
        prompt = self.prompt_template.format_prompt(context, query)
        
        # Log prompt statistics
        prompt_length = len(prompt)
        estimated_tokens = prompt_length // 4
        logger.debug(f"Constructed prompt: {prompt_length} chars, ~{estimated_tokens} tokens")
        
        return prompt
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate response using local inference engine.
        
        Args:
            prompt: Formatted prompt
            **kwargs: Additional generation parameters (max_tokens, temperature, etc.)
            
        Returns:
            Generated response text
        """
        try:
            # Ensure model is loaded
            if not self.inference_engine.is_loaded:
                logger.info("Loading inference model...")
                if not self.inference_engine.load_model():
                    raise RuntimeError("Failed to load inference model")
            
            # Generate streaming response
            response_chunks = []
            for chunk in self.inference_engine.generate_response(prompt, **kwargs):
                response_chunks.append(chunk)
            
            response = ''.join(response_chunks).strip()
            
            # Clean up response (remove any prompt repetition)
            response = self._clean_response(response)
            
            logger.debug(f"Generated response: {len(response)} characters")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Maaf, terjadi kesalahan dalam menghasilkan jawaban. Silakan coba lagi."
    
    def _apply_filters(
        self, 
        search_results: List[SearchResult], 
        subject_filter: Optional[str], 
        grade_filter: Optional[str]
    ) -> List[SearchResult]:
        """
        Apply subject and grade filters to search results.
        
        Args:
            search_results: Original search results
            subject_filter: Subject to filter by
            grade_filter: Grade to filter by
            
        Returns:
            Filtered search results
        """
        filtered_results = []
        
        for result in search_results:
            metadata = result.metadata
            
            # Apply subject filter
            if subject_filter and metadata.get('subject', '').lower() != subject_filter.lower():
                continue
            
            # Apply grade filter
            if grade_filter and metadata.get('grade', '').lower() != grade_filter.lower():
                continue
            
            filtered_results.append(result)
        
        logger.debug(f"Filtered {len(search_results)} results to {len(filtered_results)}")
        return filtered_results
    
    def _extract_sources(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Extract source information from selected documents.
        
        Args:
            documents: Selected documents
            
        Returns:
            List of source information dictionaries
        """
        sources = []
        
        for doc in documents:
            source_info = {
                'filename': doc.metadata.get('source_file', 'Unknown'),
                'subject': doc.metadata.get('subject', 'Unknown'),
                'grade': doc.metadata.get('grade', 'Unknown'),
                'relevance_score': doc.relevance_score,
                'chunk_index': doc.metadata.get('chunk_index', 0)
            }
            sources.append(source_info)
        
        return sources
    
    def _clean_response(self, response: str) -> str:
        """
        Clean up generated response.
        
        Args:
            response: Raw response from model
            
        Returns:
            Cleaned response
        """
        # Remove any prompt repetition
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and lines that look like prompt repetition
            if line and not line.startswith('Konteks dari materi') and not line.startswith('Pertanyaan siswa:'):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get pipeline statistics and health information.
        
        Returns:
            Dictionary with pipeline statistics
        """
        return {
            'vector_db_documents': self.vector_db.count_documents(),
            'inference_engine_loaded': self.inference_engine.is_loaded,
            'inference_engine_metrics': self.inference_engine.get_metrics(),
            'context_manager_max_tokens': self.context_manager.max_context_tokens,
            'embeddings_client_available': self.embeddings_client is not None,
            'fallback_handler_stats': self.fallback_handler.get_fallback_stats()
        }
    
    def _generate_fallback_result(
        self, 
        query: str, 
        reason: FallbackReason, 
        start_time: datetime,
        available_subjects: Optional[List[str]] = None
    ) -> QueryResult:
        """
        Generate fallback result when normal processing fails.
        
        Args:
            query: Original query
            reason: Reason for fallback
            start_time: Processing start time
            available_subjects: Available subjects in database
            
        Returns:
            QueryResult with fallback response
        """
        # Get available subjects from database if not provided
        if available_subjects is None:
            try:
                # This would need to be implemented in ChromaDBManager
                available_subjects = []  # Placeholder
            except Exception:
                available_subjects = []
        
        # Generate fallback response
        fallback_response = self.fallback_handler.generate_fallback_response(
            query, reason, available_subjects
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        return QueryResult(
            query=query,
            response=fallback_response.message,
            context_used="",
            sources=[],
            processing_time_ms=processing_time,
            context_stats={},
            timestamp=start_time,
            is_fallback=True,
            fallback_reason=reason.value,
            suggestions=fallback_response.suggestions,
            help_resources=fallback_response.help_resources
        )