import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.data_processing.pdf_extractor import PDFExtractor, PDFExtractionError
from src.data_processing.text_chunker import TextChunker
from src.data_processing.metadata_manager import MetadataManager, EnrichedChunk
from src.data_processing.error_handler import ErrorHandler, SummaryReport
from src.data_processing.cost_tracker import CostTracker
from src.embeddings.bedrock_client import BedrockEmbeddingsClient, BedrockAPIError
from src.embeddings.chroma_manager import ChromaDBManager

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for ETL pipeline."""
    input_dir: str = "data/raw_dataset/kelas_10/informatika"
    output_dir: str = "data/processed"
    vector_db_dir: str = "data/vector_db"
    chunk_size: int = 800
    chunk_overlap: int = 100
    batch_size: int = 25
    budget_limit: float = 1.0  # Budget limit in USD


@dataclass
class ExtractionResult:
    """Result from extraction phase."""
    successful_files: int = 0
    failed_files: int = 0
    extracted_texts: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class ChunkingResult:
    """Result from chunking phase."""
    total_chunks: int = 0
    enriched_chunks: List[EnrichedChunk] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class EmbeddingResult:
    """Result from embedding phase."""
    total_embeddings: int = 0
    embeddings: List[List[float]] = field(default_factory=list)
    tokens_processed: int = 0
    estimated_cost: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class StorageResult:
    """Result from storage phase."""
    documents_stored: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_chunks: int = 0
    total_embeddings: int = 0
    processing_time: float = 0.0
    estimated_cost: float = 0.0
    errors: List[str] = field(default_factory=list)


class ETLPipeline:
    """Orchestrates the complete ETL pipeline from PDFs to ChromaDB."""
    
    def __init__(self, config: PipelineConfig):
        """Initialize pipeline with configuration.
        
        Args:
            config: Pipeline configuration object
        """
        self.config = config
        
        # Initialize components
        self.pdf_extractor = PDFExtractor(
            output_dir=f"{config.output_dir}/text"
        )
        self.text_chunker = TextChunker(
            chunk_size=config.chunk_size,
            overlap=config.chunk_overlap
        )
        self.metadata_manager = MetadataManager()
        self.bedrock_client = BedrockEmbeddingsClient()
        self.chroma_manager = ChromaDBManager(
            persist_directory=config.vector_db_dir
        )
        
        # Initialize error handler
        self.error_handler = ErrorHandler()
        
        # Initialize cost tracker
        self.cost_tracker = CostTracker(
            log_path=f"{config.output_dir}/metadata/cost_log.json",
            budget_limit=config.budget_limit
        )
        
        # Track results
        self.extraction_result: Optional[ExtractionResult] = None
        self.chunking_result: Optional[ChunkingResult] = None
        self.embedding_result: Optional[EmbeddingResult] = None
        self.storage_result: Optional[StorageResult] = None
        
        logger.info(f"Initialized ETL Pipeline with config: {config}")
    
    def run(self) -> PipelineResult:
        """Execute the complete ETL pipeline.
        
        Returns:
            PipelineResult with success/failure counts and metrics
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("Starting ETL Pipeline")
        logger.info("=" * 60)
        
        try:
            # Phase 1: Extract text from PDFs
            logger.info("\n[Phase 1/4] PDF Text Extraction")
            self.extraction_result = self.run_extraction()
            logger.info(
                f"Extraction complete: {self.extraction_result.successful_files} successful, "
                f"{self.extraction_result.failed_files} failed"
            )
            
            # Phase 2: Chunk text and enrich with metadata
            logger.info("\n[Phase 2/4] Text Chunking and Metadata Enrichment")
            self.chunking_result = self.run_chunking()
            logger.info(f"Chunking complete: {self.chunking_result.total_chunks} chunks created")
            
            # Phase 3: Generate embeddings
            logger.info("\n[Phase 3/4] Embedding Generation")
            self.embedding_result = self.run_embedding()
            logger.info(
                f"Embedding complete: {self.embedding_result.total_embeddings} embeddings generated, "
                f"estimated cost: ${self.embedding_result.estimated_cost:.4f}"
            )
            
            # Track Bedrock token usage in cost tracker
            self.cost_tracker.track_bedrock_tokens(self.embedding_result.tokens_processed)
            
            # Phase 4: Store in ChromaDB
            logger.info("\n[Phase 4/4] ChromaDB Storage")
            self.storage_result = self.run_storage()
            logger.info(f"Storage complete: {self.storage_result.documents_stored} documents stored")
            
            # Record pipeline run in cost tracker
            self.cost_tracker.record_pipeline_run(
                files_processed=self.extraction_result.successful_files,
                chunks_processed=self.chunking_result.total_chunks
            )
            
            # Calculate final results
            processing_time = time.time() - start_time
            
            # Collect all errors
            all_errors = []
            if self.extraction_result:
                all_errors.extend(self.extraction_result.errors)
            if self.chunking_result:
                all_errors.extend(self.chunking_result.errors)
            if self.embedding_result:
                all_errors.extend(self.embedding_result.errors)
            if self.storage_result:
                all_errors.extend(self.storage_result.errors)
            
            result = PipelineResult(
                total_files=self.extraction_result.successful_files + self.extraction_result.failed_files,
                successful_files=self.extraction_result.successful_files,
                failed_files=self.extraction_result.failed_files,
                total_chunks=self.chunking_result.total_chunks,
                total_embeddings=self.embedding_result.total_embeddings,
                processing_time=processing_time,
                estimated_cost=self.embedding_result.estimated_cost,
                errors=all_errors
            )
            
            logger.info("\n" + "=" * 60)
            logger.info("Pipeline Complete!")
            logger.info("=" * 60)
            logger.info(f"Total files processed: {result.total_files}")
            logger.info(f"Successful: {result.successful_files}")
            logger.info(f"Failed: {result.failed_files}")
            logger.info(f"Total chunks: {result.total_chunks}")
            logger.info(f"Total embeddings: {result.total_embeddings}")
            logger.info(f"Processing time: {result.processing_time:.2f}s")
            logger.info(f"Estimated cost: ${result.estimated_cost:.4f}")
            if result.errors:
                logger.warning(f"Total errors: {len(result.errors)}")
            
            # Generate summary report
            summary_report = self.error_handler.generate_summary_report(
                pipeline_result=result,
                output_path=f"{self.config.output_dir}/metadata/pipeline_report.json"
            )
            self.error_handler.print_summary(summary_report)
            
            # Print cost summary
            self.cost_tracker.print_cost_summary()
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}", exc_info=True)
            raise
    
    def run_extraction(self) -> ExtractionResult:
        """Run PDF extraction phase.
        
        Returns:
            ExtractionResult with extracted texts and error info
        """
        result = ExtractionResult()
        
        # Find all PDF files in input directory
        input_path = Path(self.config.input_dir)
        if not input_path.exists():
            error_msg = f"Input directory does not exist: {input_path}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        pdf_files = list(input_path.glob("*.pdf"))
        
        if not pdf_files:
            error_msg = f"No PDF files found in {input_path}"
            logger.warning(error_msg)
            result.errors.append(error_msg)
            return result
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each PDF file
        for idx, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"Processing file {idx}/{len(pdf_files)}: {pdf_path.name}")
            
            try:
                # Extract text from PDF
                text = self.pdf_extractor.extract_text(str(pdf_path))
                result.extracted_texts[str(pdf_path)] = text
                result.successful_files += 1
                logger.info(f"  ✓ Extracted {len(text)} characters")
                
            except PDFExtractionError as e:
                # Log error but continue processing
                error_msg = f"Failed to extract {pdf_path.name}: {e}"
                logger.error(f"  ✗ {error_msg}")
                result.errors.append(error_msg)
                result.failed_files += 1
                
                # Record error in error handler
                self.error_handler.record_error(
                    phase="extraction",
                    file_path=str(pdf_path),
                    error=e,
                    error_type="PDFExtractionError"
                )
                continue
        
        return result
    
    def run_chunking(self) -> ChunkingResult:
        """Run text chunking phase.
        
        Returns:
            ChunkingResult with enriched chunks and error info
        """
        result = ChunkingResult()
        
        if not self.extraction_result or not self.extraction_result.extracted_texts:
            error_msg = "No extracted texts available for chunking"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        # Process each extracted text
        for pdf_path, text in self.extraction_result.extracted_texts.items():
            try:
                # Parse file metadata
                file_metadata = self.metadata_manager.parse_file_path(pdf_path)
                logger.info(f"Chunking {file_metadata.filename}...")
                
                # Chunk the text
                chunks = self.text_chunker.chunk_text(text)
                logger.info(f"  Created {len(chunks)} chunks")
                
                # Enrich chunks with metadata
                for chunk in chunks:
                    enriched_chunk = self.metadata_manager.enrich_chunk(chunk, file_metadata)
                    result.enriched_chunks.append(enriched_chunk)
                
                result.total_chunks += len(chunks)
                
            except Exception as e:
                error_msg = f"Failed to chunk {pdf_path}: {e}"
                logger.error(f"  ✗ {error_msg}")
                result.errors.append(error_msg)
                
                # Record error in error handler
                self.error_handler.record_error(
                    phase="chunking",
                    file_path=pdf_path,
                    error=e
                )
                continue
        
        logger.info(f"Total chunks created: {result.total_chunks}")
        return result
    
    def run_embedding(self) -> EmbeddingResult:
        """Run embedding generation phase.
        
        Returns:
            EmbeddingResult with embeddings and cost info
        """
        result = EmbeddingResult()
        
        if not self.chunking_result or not self.chunking_result.enriched_chunks:
            error_msg = "No chunks available for embedding generation"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        # Extract texts from enriched chunks
        texts = [chunk.text for chunk in self.chunking_result.enriched_chunks]
        
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        
        try:
            # Generate embeddings in batches
            embeddings = self.bedrock_client.generate_batch(
                texts=texts,
                batch_size=self.config.batch_size
            )
            
            result.embeddings = embeddings
            result.total_embeddings = len(embeddings)
            result.tokens_processed = self.bedrock_client.get_token_usage()
            result.estimated_cost = self.bedrock_client.calculate_cost()
            
            logger.info(f"Generated {result.total_embeddings} embeddings")
            logger.info(f"Tokens processed: {result.tokens_processed}")
            logger.info(f"Estimated cost: ${result.estimated_cost:.4f}")
            
        except BedrockAPIError as e:
            error_msg = f"Failed to generate embeddings: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            
            # Record error in error handler
            self.error_handler.record_error(
                phase="embedding",
                file_path="batch_processing",
                error=e,
                error_type="BedrockAPIError"
            )
        
        return result
    
    def run_storage(self) -> StorageResult:
        """Run ChromaDB storage phase.
        
        Returns:
            StorageResult with storage info
        """
        result = StorageResult()
        
        if not self.chunking_result or not self.embedding_result:
            error_msg = "No chunks or embeddings available for storage"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        if not self.chunking_result.enriched_chunks or not self.embedding_result.embeddings:
            error_msg = "Empty chunks or embeddings list"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        try:
            # Create collection
            logger.info("Creating ChromaDB collection...")
            self.chroma_manager.create_collection("educational_content")
            
            # Add documents with embeddings
            logger.info(f"Storing {len(self.chunking_result.enriched_chunks)} documents...")
            self.chroma_manager.add_documents(
                chunks=self.chunking_result.enriched_chunks,
                embeddings=self.embedding_result.embeddings
            )
            
            result.documents_stored = len(self.chunking_result.enriched_chunks)
            
            # Verify storage
            doc_count = self.chroma_manager.count_documents()
            logger.info(f"Verified {doc_count} documents in ChromaDB")
            
        except Exception as e:
            error_msg = f"Failed to store documents in ChromaDB: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            
            # Record error in error handler
            self.error_handler.record_error(
                phase="storage",
                file_path="chromadb",
                error=e
            )
        
        return result
