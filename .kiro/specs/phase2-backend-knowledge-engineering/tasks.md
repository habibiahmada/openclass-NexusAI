# Implementation Plan: Phase 2 - Backend Infrastructure & Knowledge Engineering

## Overview

This implementation plan breaks down the ETL pipeline development into discrete, testable tasks. Each task builds on previous work, with checkpoints to ensure quality. The plan follows a bottom-up approach: implement core components first, then integrate them into the pipeline.

## Tasks

- [x] 1. Setup project dependencies and testing framework
  - Install required packages: pypdf, unstructured, langchain, chromadb, boto3, hypothesis, pytest
  - Configure pytest with test directories
  - Setup Hypothesis profile for property-based testing (100 iterations)
  - Create test fixtures directory structure
  - _Requirements: All_

- [x] 2. Implement PDF text extraction
  - [x] 2.1 Create PDFExtractor class with extract_text method
    - Use pypdf for basic extraction
    - Use unstructured library for header/footer removal
    - Implement error handling for corrupted PDFs
    - Save extracted text to data/processed/text/ with UTF-8 encoding
    - _Requirements: 1.1, 1.2, 1.4, 1.5_

  - [x] 2.2 Write property test for complete page extraction
    - **Property 1: Complete Page Extraction**
    - **Validates: Requirements 1.1**

  - [x] 2.3 Write property test for header/footer removal
    - **Property 2: Header/Footer Removal**
    - **Validates: Requirements 1.2**

  - [x] 2.4 Write unit tests for PDF extraction edge cases
    - Test with empty PDF
    - Test with image-only PDF
    - Test with corrupted PDF
    - _Requirements: 1.3, 1.4_

- [x] 3. Implement text chunking
  - [x] 3.1 Create TextChunker class with chunk_text method
    - Use LangChain RecursiveCharacterTextSplitter
    - Configure chunk_size=800, overlap=100
    - Set separators for sentence and word boundaries
    - Return TextChunk objects with position metadata
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.2 Write property test for chunk size bounds
    - **Property 3: Chunk Size Bounds**
    - **Validates: Requirements 2.1**

  - [x] 3.3 Write property test for chunk overlap consistency
    - **Property 4: Chunk Overlap Consistency**
    - **Validates: Requirements 2.2**

  - [x] 3.4 Write property test for no mid-word splits
    - **Property 5: No Mid-Word Splits**
    - **Validates: Requirements 2.4**

  - [x] 3.5 Write property test for chunk position metadata
    - **Property 6: Chunk Position Metadata**
    - **Validates: Requirements 2.5**

- [x] 4. Checkpoint - Ensure extraction and chunking tests pass
  - Run all tests for PDFExtractor and TextChunker
  - Verify property tests pass with 100 iterations
  - Test with sample PDFs from fixtures
  - Ask user if questions arise

- [x] 5. Implement metadata management
  - [x] 5.1 Create MetadataManager class
    - Implement parse_file_path method to extract subject and grade
    - Implement enrich_chunk method to add metadata
    - Generate unique UUIDs for chunk_id
    - Create EnrichedChunk dataclass with all required fields
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 5.2 Write property test for metadata field completeness
    - **Property 7: Metadata Field Completeness**
    - **Validates: Requirements 3.5**

  - [x] 5.3 Write property test for chunk ID uniqueness
    - **Property 8: Chunk ID Uniqueness**
    - **Validates: Requirements 3.4**

  - [x] 5.4 Write unit tests for path parsing
    - Test with valid paths (data/raw_dataset/kelas_10/informatika/file.pdf)
    - Test with invalid paths
    - Test subject and grade extraction
    - _Requirements: 3.1, 3.2_

- [x] 6. Implement Bedrock embeddings client
  - [x] 6.1 Create BedrockEmbeddingsClient class
    - Initialize boto3 Bedrock Runtime client
    - Implement generate_embedding method for single text
    - Implement generate_batch method with batching (25 per batch)
    - Implement exponential backoff retry logic for rate limits
    - Track token usage for cost calculation
    - _Requirements: 4.1, 4.2, 4.3, 4.5_

  - [x] 6.2 Write property test for embedding dimensionality
    - **Property 9: Embedding Dimensionality**
    - **Validates: Requirements 4.4**

  - [x] 6.3 Write property test for batch processing efficiency
    - **Property 10: Batch Processing Efficiency**
    - **Validates: Requirements 4.2**

  - [x] 6.4 Write unit tests for API error handling
    - Mock Bedrock API with moto library
    - Test rate limiting with exponential backoff
    - Test service errors
    - Test network timeouts
    - _Requirements: 4.3_

- [x] 7. Checkpoint - Ensure metadata and embeddings tests pass
  - Run all tests for MetadataManager and BedrockEmbeddingsClient
  - Verify property tests pass with 100 iterations
  - Test with mocked Bedrock API
  - Ask user if questions arise

- [x] 8. Implement ChromaDB vector store
  - [x] 8.1 Create ChromaDBManager class
    - Initialize ChromaDB with persistence to data/vector_db/
    - Implement create_collection method for "educational_content"
    - Implement add_documents method to store vectors + text + metadata
    - Implement query method for similarity search
    - Use chunk_id as document identifier
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 8.2 Write property test for vector-text-metadata integrity
    - **Property 11: Vector-Text-Metadata Integrity**
    - **Validates: Requirements 5.2**

  - [x] 8.3 Write property test for persistence round-trip
    - **Property 12: Persistence Round-Trip**
    - **Validates: Requirements 5.4**

  - [x] 8.4 Write unit tests for ChromaDB operations
    - Test collection creation
    - Test document addition
    - Test similarity search
    - Test persistence across restarts
    - _Requirements: 5.1, 5.3, 5.5_

- [x] 9. Implement ETL pipeline orchestrator
  - [x] 9.1 Create ETLPipeline class with configuration
    - Define PipelineConfig dataclass
    - Define PipelineResult dataclass
    - Implement run method to orchestrate all phases
    - Implement run_extraction, run_chunking, run_embedding, run_storage methods
    - Add progress logging after each file
    - _Requirements: 8.1, 8.2, 8.4_

  - [x] 9.2 Implement error handling and reporting
    - Create ErrorHandler class
    - Log errors but continue processing remaining files
    - Generate summary report with success/failure counts
    - Track processing time and estimated costs
    - _Requirements: 8.3, 8.4_

  - [x] 9.3 Write property test for pipeline completeness
    - **Property 15: Pipeline Completeness**
    - **Validates: Requirements 8.1**
    - **Note**: Test passes but has occasional Windows file locking issues with ChromaDB SQLite files in temp directories. Mocked ChromaDB manager resolves 99% of cases.

  - [x] 9.4 Write property test for error isolation
    - **Property 16: Error Isolation**
    - **Validates: Requirements 8.3**
    - **Note**: Test passes but has occasional Windows file locking issues with ChromaDB SQLite files in temp directories. Mocked ChromaDB manager resolves 99% of cases.

  - [x] 9.5 Write integration test for end-to-end pipeline
    - Test with sample PDFs from fixtures
    - Verify all phases execute in sequence
    - Verify ChromaDB contains expected documents
    - Verify summary report is generated
    - _Requirements: 8.1, 8.2, 8.4_

- [x] 10. Checkpoint - Ensure pipeline tests pass
  - Run all tests for ETLPipeline
  - Run end-to-end integration test
  - Verify error handling works correctly
  - Ask user if questions arise

- [x] 11. Implement validation and quality control
  - [x] 11.1 Create validation module
    - Implement validate_extraction to check text files exist
    - Implement validate_chunks to check chunk counts
    - Implement validate_embeddings to check dimensions and counts
    - Implement validate_metadata to check required fields
    - Generate quality report with pass/fail status
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 11.2 Write property test for validation completeness
    - **Property 17: Validation Completeness**
    - **Validates: Requirements 9.1**

  - [x] 11.3 Write property test for embedding-chunk correspondence
    - **Property 18: Embedding-Chunk Correspondence**
    - **Validates: Requirements 9.3**

  - [x] 11.4 Write unit tests for validation checks
    - Test with complete data
    - Test with missing files
    - Test with invalid dimensions
    - Test with missing metadata fields
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 12. Implement cost monitoring
  - [x] 12.1 Create cost tracking module
    - Track Bedrock token usage
    - Track S3 data transfer
    - Calculate estimated costs using AWS pricing
    - Log costs to data/processed/metadata/cost_log.json
    - Implement budget alert at 80% threshold
    - _Requirements: 10.1, 10.2, 10.4, 10.5_

  - [x] 12.2 Write property test for cost tracking accuracy
    - **Property 19: Cost Tracking Accuracy**
    - **Validates: Requirements 10.4**

  - [x] 12.3 Write unit tests for cost calculation
    - Test Bedrock cost calculation
    - Test S3 cost calculation
    - Test budget alert triggering
    - _Requirements: 10.1, 10.2, 10.4, 10.5_

- [x] 13. Implement S3 storage optimization
  - [x] 13.1 Create S3 upload module
    - Implement upload with path structure: s3://bucket/processed/{subject}/{grade}/
    - Compress knowledge base files with gzip
    - Set storage class to Standard-IA
    - Enable server-side encryption (AES-256)
    - Upload ChromaDB files to S3
    - _Requirements: 7.1, 7.2, 7.3, 7.5_

  - [x] 13.2 Write property test for S3 path structure
    - **Property 13: S3 Path Structure**
    - **Validates: Requirements 7.1**

  - [x] 13.3 Write property test for compression applied
    - **Property 14: Compression Applied**
    - **Validates: Requirements 7.2**

  - [x] 13.4 Write unit tests for S3 operations
    - Test upload with correct path structure
    - Test gzip compression
    - Test storage class configuration
    - Test encryption settings
    - _Requirements: 7.1, 7.2, 7.3, 7.5_

- [x] 14. Implement CloudFront distribution
  - [x] 14.1 Create CloudFrontManager class
    - Implement create_distribution method
    - Configure cache TTL to 24 hours
    - Require HTTPS for all requests
    - Output CloudFront domain URL
    - Implement invalidate_cache method
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 14.2 Write unit tests for CloudFront operations
    - Test distribution creation
    - Test cache configuration
    - Test HTTPS requirement
    - Test cache invalidation
    - _Requirements: 6.1, 6.2, 6.3, 6.5_

- [x] 15. Checkpoint - Ensure all components are integrated
  - Run complete test suite (unit + property + integration)
  - Verify all 19 properties pass with 100 iterations
  - Test with real PDFs from data/raw_dataset/
  - Verify S3 upload and CloudFront work
  - Ask user if questions arise

- [x] 16. Create main pipeline script
  - [x] 16.1 Create scripts/run_etl_pipeline.py
    - Parse command-line arguments
    - Load configuration from .env
    - Initialize all components
    - Run complete pipeline
    - Generate and display summary report
    - Save cost log and quality report
    - _Requirements: 8.1, 8.4, 9.5, 10.5_

  - [x] 16.2 Test pipeline with full dataset
    - Run with all 15 PDFs from data/raw_dataset/kelas_10/informatika/
    - Verify processing completes in under 30 minutes
    - Verify estimated cost is under $0.10
    - Verify ChromaDB contains all documents
    - Verify S3 upload succeeds
    - _Requirements: 8.1, 8.4_

- [x] 17. Final checkpoint - Complete system validation
  - Run full pipeline with 15 PDFs
  - Verify all tests pass
  - Verify cost is within budget
  - Verify knowledge base is uploaded to S3
  - Verify CloudFront distribution works
  - Generate final quality and cost reports
  - Ask user if questions arise

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties with 100 iterations
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- Use mocked AWS services (moto) for testing to avoid costs
- Real AWS integration only in final testing phase
