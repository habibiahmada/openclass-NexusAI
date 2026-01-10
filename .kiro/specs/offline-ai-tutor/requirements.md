# Requirements Document

## Introduction

OpenClass Nexus AI is an offline-capable AI tutoring system that combines AWS cloud infrastructure with local AI inference to provide educational assistance in Indonesian schools. The system processes educational materials from official sources, creates vector embeddings for knowledge retrieval, and runs AI models locally on school laptops with limited internet connectivity.

## Glossary

- **System**: The complete OpenClass Nexus AI platform including cloud and local components
- **Knowledge_Base**: Vector database containing processed educational content
- **Local_Engine**: Offline AI inference system running on school laptops
- **Cloud_Pipeline**: AWS-based data processing and distribution system
- **Vector_Embeddings**: Numerical representations of text content for semantic search
- **GGUF_Model**: Quantized AI model format optimized for local inference

## Requirements

### Requirement 1: Data Acquisition and Processing

**User Story:** As a system administrator, I want to acquire and process official educational materials, so that the AI tutor has accurate and legal content to work with.

#### Acceptance Criteria

1. WHEN the system processes PDF educational materials, THE System SHALL extract clean text content removing headers, footers, and page numbers
2. WHEN text is extracted from PDFs, THE System SHALL chunk content into 500-1000 character segments with 100 character overlap
3. WHEN processing educational content, THE System SHALL add metadata including source, subject, and chapter information
4. THE System SHALL only process materials from official educational sources like BSE Kemdikbud
5. WHEN content is processed, THE System SHALL store both raw and processed versions in organized folder structures

### Requirement 2: AWS Infrastructure and Cost Control

**User Story:** As a project manager, I want to set up AWS infrastructure with strict cost controls, so that the project stays within budget constraints.

#### Acceptance Criteria

1. WHEN setting up AWS services, THE System SHALL implement budget alerts at $1.00 threshold
2. WHEN using S3 storage, THE System SHALL implement lifecycle rules to expire raw files after 30 days
3. WHEN accessing AWS services, THE System SHALL use appropriate IAM roles with minimal required permissions
4. THE System SHALL utilize AWS Free Tier services wherever possible
5. WHEN costs approach budget limits, THE System SHALL send email notifications to administrators

### Requirement 3: Vector Database and Embeddings

**User Story:** As a developer, I want to create vector embeddings from educational content, so that the AI can perform semantic search and retrieval.

#### Acceptance Criteria

1. WHEN creating embeddings, THE System SHALL use Amazon Bedrock Titan Text Embeddings v2 model
2. WHEN processing text chunks, THE System SHALL generate vector embeddings for each chunk
3. WHEN storing embeddings, THE System SHALL maintain association between vectors and original text content
4. THE System SHALL store vector databases in formats compatible with ChromaDB or FAISS
5. WHEN embeddings are created, THE System SHALL upload the knowledge base to S3 for distribution

### Requirement 4: Model Optimization for Offline Use

**User Story:** As a school IT administrator, I want AI models that run on laptops with 4GB RAM, so that students can use the system without internet connectivity.

#### Acceptance Criteria

1. WHEN selecting AI models, THE System SHALL use models like Llama-3-8B-Instruct or Mistral-7B-Instruct
2. WHEN optimizing models, THE System SHALL quantize models to Q4_K_M format using GGUF
3. WHEN quantized, THE Model SHALL be under 5GB in size for local storage
4. THE Local_Engine SHALL run inference using llama.cpp with configurable context windows
5. WHEN running locally, THE Model SHALL operate without internet connectivity

### Requirement 5: Local Application Interface

**User Story:** As a teacher or student, I want an intuitive chat interface for asking questions about educational content, so that I can get immediate help with learning materials.

#### Acceptance Criteria

1. WHEN the application starts, THE System SHALL provide a chat interface similar to ChatGPT
2. WHEN users ask questions, THE System SHALL search the local knowledge base for relevant content
3. WHEN providing answers, THE System SHALL include source citations with book and page references
4. THE System SHALL allow filtering by subject through a sidebar configuration
5. WHEN no relevant content is found, THE System SHALL respond "Maaf, materi ini belum ada di database saya"

### Requirement 6: Synchronization and Updates

**User Story:** As a content administrator, I want to update educational materials across all school installations, so that students have access to the latest curriculum content.

#### Acceptance Criteria

1. WHEN updates are available, THE System SHALL check version information via CloudFront
2. WHEN local version is outdated, THE System SHALL download delta updates automatically
3. WHEN internet is available, THE System SHALL sync usage telemetry to AWS DynamoDB
4. THE System SHALL maintain offline functionality even during update processes
5. WHEN updates are downloaded, THE System SHALL verify integrity before applying changes

### Requirement 7: Privacy and Data Security

**User Story:** As a school administrator, I want student data to remain private and secure, so that we comply with educational data protection requirements.

#### Acceptance Criteria

1. WHEN collecting usage data, THE System SHALL anonymize all personal information
2. WHEN storing logs locally, THE System SHALL use non-identifiable session tokens
3. WHEN transmitting telemetry, THE System SHALL only send aggregated usage statistics
4. THE System SHALL process all AI inference locally without sending queries to external services
5. WHEN handling student interactions, THE System SHALL not store conversation history permanently

### Requirement 8: System Performance and Reliability

**User Story:** As a user, I want the AI tutor to respond quickly and reliably, so that it doesn't interrupt the learning process.

#### Acceptance Criteria

1. WHEN processing queries, THE Local_Engine SHALL respond within 10 seconds on 4GB RAM systems
2. WHEN running inference, THE System SHALL utilize available CPU cores efficiently
3. WHEN the application starts, THE System SHALL initialize the knowledge base within 30 seconds
4. THE System SHALL handle concurrent users on the same machine without performance degradation
5. WHEN system resources are low, THE System SHALL gracefully reduce context window size