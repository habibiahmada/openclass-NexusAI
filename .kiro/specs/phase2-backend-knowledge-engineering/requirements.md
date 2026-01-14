# Requirements Document - Phase 2: Backend Infrastructure & Knowledge Engineering

## Introduction

Phase 2 focuses on transforming raw PDF educational materials into a searchable knowledge base using vector embeddings. This phase implements the data processing pipeline, AWS infrastructure optimization, and vector database creation that will enable semantic search capabilities for the offline AI tutor.

## Glossary

- **ETL_Pipeline**: Extract, Transform, Load pipeline for processing PDF content
- **Text_Chunker**: Component that splits text into overlapping segments
- **PDF_Extractor**: Component that extracts clean text from PDF files
- **Metadata_Manager**: Component that tracks and enriches content metadata
- **Vector_Store**: ChromaDB database storing embeddings and associated text
- **Bedrock_Client**: AWS Bedrock API client for generating embeddings
- **CloudFront_Distribution**: CDN for distributing knowledge base updates
- **Batch_Processor**: Component for processing multiple documents efficiently

## Requirements

### Requirement 1: PDF Text Extraction

**User Story:** As a data engineer, I want to extract clean text from educational PDFs, so that the content can be processed into embeddings without formatting artifacts.

#### Acceptance Criteria

1. WHEN processing a PDF file, THE PDF_Extractor SHALL extract text content from all pages
2. WHEN extracting text, THE PDF_Extractor SHALL remove headers, footers, and page numbers
3. WHEN encountering images or diagrams, THE PDF_Extractor SHALL skip non-text content gracefully
4. WHEN text extraction fails, THE PDF_Extractor SHALL log the error with filename and continue processing other files
5. WHEN extraction completes, THE PDF_Extractor SHALL save raw text to the processed data directory with UTF-8 encoding

### Requirement 2: Text Chunking Strategy

**User Story:** As a data engineer, I want to split extracted text into optimal chunks, so that embeddings capture meaningful semantic units.

#### Acceptance Criteria

1. WHEN chunking text, THE Text_Chunker SHALL create segments between 500-1000 characters in length
2. WHEN creating chunks, THE Text_Chunker SHALL maintain 100 character overlap between consecutive chunks
3. WHEN splitting text, THE Text_Chunker SHALL attempt to break at sentence boundaries when possible
4. WHEN a sentence exceeds maximum chunk size, THE Text_Chunker SHALL split at word boundaries
5. WHEN chunking completes, THE Text_Chunker SHALL return a list of text segments with position metadata

### Requirement 3: Metadata Enhancement

**User Story:** As a data engineer, I want to enrich text chunks with metadata, so that users can trace answers back to source materials.

#### Acceptance Criteria

1. WHEN processing a chunk, THE Metadata_Manager SHALL extract subject information from the file path
2. WHEN processing a chunk, THE Metadata_Manager SHALL extract grade level from the file path
3. WHEN processing a chunk, THE Metadata_Manager SHALL store the original filename as source reference
4. WHEN processing a chunk, THE Metadata_Manager SHALL assign a unique chunk ID
5. WHEN metadata is complete, THE Metadata_Manager SHALL create a JSON object with all fields: chunk_id, source_file, subject, grade, chunk_text, chunk_position

### Requirement 4: Vector Embeddings Generation

**User Story:** As a data engineer, I want to generate vector embeddings using AWS Bedrock, so that semantic search can be performed on educational content.

#### Acceptance Criteria

1. WHEN generating embeddings, THE Bedrock_Client SHALL use the Titan Text Embeddings v2 model
2. WHEN processing chunks, THE Batch_Processor SHALL send requests in batches of 25 to optimize API usage
3. WHEN API rate limits are encountered, THE Bedrock_Client SHALL implement exponential backoff retry logic
4. WHEN embeddings are generated, THE System SHALL store vectors with 1024 dimensions
5. WHEN batch processing completes, THE System SHALL log the total number of chunks processed and API costs incurred

### Requirement 5: ChromaDB Knowledge Base Creation

**User Story:** As a developer, I want to store embeddings in ChromaDB, so that the local application can perform fast semantic search.

#### Acceptance Criteria

1. WHEN creating the knowledge base, THE Vector_Store SHALL initialize a ChromaDB collection named "educational_content"
2. WHEN adding embeddings, THE Vector_Store SHALL store the vector, original text, and metadata together
3. WHEN storing documents, THE Vector_Store SHALL use chunk_id as the document identifier
4. WHEN the collection is created, THE Vector_Store SHALL enable persistence to disk in the data/vector_db directory
5. WHEN all embeddings are added, THE Vector_Store SHALL create an index for efficient similarity search

### Requirement 6: CloudFront Distribution Setup

**User Story:** As a system administrator, I want to distribute knowledge base updates via CloudFront, so that schools can download updates efficiently.

#### Acceptance Criteria

1. WHEN setting up CloudFront, THE System SHALL create a distribution pointing to the S3 bucket
2. WHEN configuring caching, THE CloudFront_Distribution SHALL set cache TTL to 24 hours for knowledge base files
3. WHEN configuring security, THE CloudFront_Distribution SHALL require HTTPS for all requests
4. WHEN distribution is created, THE System SHALL output the CloudFront domain URL for configuration
5. WHEN knowledge base is updated, THE System SHALL invalidate CloudFront cache for updated files

### Requirement 7: S3 Storage Optimization

**User Story:** As a cost-conscious administrator, I want to optimize S3 storage structure, so that bandwidth and storage costs are minimized.

#### Acceptance Criteria

1. WHEN organizing S3 files, THE System SHALL use the folder structure: s3://bucket/processed/subject/grade/
2. WHEN uploading processed data, THE System SHALL compress knowledge base files using gzip
3. WHEN storing embeddings, THE System SHALL use S3 Standard-IA storage class for infrequent access
4. WHEN lifecycle policies are applied, THE System SHALL transition raw PDFs to Glacier after 30 days
5. WHEN uploading files, THE System SHALL enable server-side encryption with AES-256

### Requirement 8: ETL Pipeline Orchestration

**User Story:** As a data engineer, I want an automated pipeline that processes all PDFs end-to-end, so that knowledge base creation is reproducible.

#### Acceptance Criteria

1. WHEN the pipeline starts, THE ETL_Pipeline SHALL process all PDF files in the raw_dataset directory
2. WHEN processing each file, THE ETL_Pipeline SHALL execute extraction, chunking, metadata enhancement, and embedding generation in sequence
3. WHEN errors occur, THE ETL_Pipeline SHALL log errors but continue processing remaining files
4. WHEN pipeline completes, THE ETL_Pipeline SHALL generate a summary report with success/failure counts
5. WHEN all processing is done, THE ETL_Pipeline SHALL upload the final knowledge base to S3 and invalidate CloudFront cache

### Requirement 9: Quality Control and Validation

**User Story:** As a quality assurance engineer, I want to validate processed data quality, so that the knowledge base contains accurate and complete information.

#### Acceptance Criteria

1. WHEN validation runs, THE System SHALL verify that all PDF files have corresponding processed text files
2. WHEN checking chunks, THE System SHALL verify that chunk count matches expected range based on document length
3. WHEN validating embeddings, THE System SHALL verify that all chunks have corresponding 1024-dimensional vectors
4. WHEN checking metadata, THE System SHALL verify that all required fields are present and non-empty
5. WHEN validation completes, THE System SHALL generate a quality report with pass/fail status for each document

### Requirement 10: Cost Monitoring and Reporting

**User Story:** As a project manager, I want to track AWS costs during processing, so that I can ensure the project stays within budget.

#### Acceptance Criteria

1. WHEN using Bedrock API, THE System SHALL log the number of tokens processed for cost calculation
2. WHEN uploading to S3, THE System SHALL log the total data transferred in MB
3. WHEN CloudFront is accessed, THE System SHALL monitor request counts via CloudWatch
4. WHEN processing completes, THE System SHALL calculate estimated costs based on AWS pricing
5. WHEN costs exceed 80% of budget, THE System SHALL send an alert notification
