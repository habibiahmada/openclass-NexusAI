# Requirements Document: Architecture Alignment Refactoring

## Introduction

OpenClass Nexus AI is a Hybrid Orchestrated Edge AI System for education with 100% offline inference at schools, AWS control plane for orchestration, and privacy by architecture design. The current implementation has significant misalignment with the definitive architecture documented in README_DEPLOYMENT_SCENARIOS.md, with only 40% alignment, 35% needing adjustment, and 25% not aligned.

This refactoring project aims to incrementally align the existing codebase with the definitive architecture without breaking functionality, focusing on critical gaps that block further development. The refactoring must be done in phases with testing at each step, maintaining backward compatibility, and avoiding over-engineering.

## Glossary

- **Edge_Runtime**: The local school server runtime environment that handles 100% offline inference (formerly local_inference)
- **AWS_Control_Plane**: The centralized AWS infrastructure for orchestration, training, and distribution (formerly cloud_sync)
- **VKP**: Versioned Knowledge Package - a packaged format containing embeddings, metadata, integrity checksum, and version manifest
- **School_Server**: The dedicated physical server deployed at each school (16GB RAM, 8-core CPU, 512GB SSD)
- **Pedagogical_Engine**: The learning support infrastructure that tracks mastery, detects weak areas, and generates adaptive practice
- **Persistence_Layer**: The PostgreSQL database layer for storing user data, sessions, chat history, and metadata
- **Resilience_Module**: The backup, recovery, and health monitoring system
- **Telemetry_System**: The aggregated metrics collection system that sends anonymized usage data to DynamoDB
- **Concurrency_Manager**: The async queue management system that limits inference to 5 concurrent threads
- **Embedding_Strategy**: The configurable approach for generating embeddings (default: AWS Bedrock, optional: local MiniLM)

## Requirements

### Requirement 1: Hardware Specification Alignment

**User Story:** As a system architect, I want all documentation to reflect the correct 16GB RAM minimum requirement, so that deployment expectations are accurate and consistent.

#### Acceptance Criteria

1. THE Documentation_System SHALL update all references from "4GB RAM minimum" to "16GB RAM minimum"
2. THE Configuration_Files SHALL remove memory_limit_mb = 3072 constraint
3. THE README_Files SHALL specify minimum hardware as 16GB RAM, 8-core CPU, 512GB SSD
4. WHEN hardware specifications are queried, THE System SHALL return consistent 16GB minimum across all documentation
5. THE System SHALL maintain GPU as optional (not required)

### Requirement 2: Folder Structure Alignment

**User Story:** As a developer, I want the folder structure to match the definitive architecture naming, so that code organization is intuitive and consistent with documentation.

#### Acceptance Criteria

1. THE Refactoring_System SHALL rename src/local_inference/ to src/edge_runtime/
2. THE Refactoring_System SHALL rename src/cloud_sync/ to src/aws_control_plane/
3. THE Refactoring_System SHALL move models from models/cache/ to models/
4. WHEN folder renaming occurs, THE System SHALL update all import statements automatically
5. WHEN folder renaming completes, THE System SHALL verify all existing tests pass
6. THE Refactoring_System SHALL preserve Git history during folder renames

### Requirement 3: Database Persistence Implementation

**User Story:** As a system administrator, I want persistent storage for user data and chat history, so that data survives server restarts and the system is production-ready.

#### Acceptance Criteria

1. THE Persistence_Layer SHALL implement PostgreSQL database with schema for users, sessions, chat_history, subjects, and books
2. THE Persistence_Layer SHALL replace in-memory storage (active_tokens dict, state.chat_logs list) with database operations
3. WHEN the server restarts, THE System SHALL retain all user sessions, chat history, and metadata
4. THE Persistence_Layer SHALL provide transaction support for data integrity
5. THE Persistence_Layer SHALL implement connection pooling for performance
6. IF PostgreSQL is unavailable, THEN THE System SHALL log error and provide graceful degradation message

### Requirement 4: Pedagogical Intelligence Engine

**User Story:** As an educator, I want the system to track student mastery and generate adaptive practice questions, so that it functions as learning support infrastructure rather than just a chatbot.

#### Acceptance Criteria

1. THE Pedagogical_Engine SHALL track topic mastery per student with mastery_level score (0.0 to 1.0)
2. THE Pedagogical_Engine SHALL detect weak areas based on question frequency and complexity patterns
3. THE Pedagogical_Engine SHALL generate adaptive practice questions targeting weak areas
4. THE Pedagogical_Engine SHALL produce weekly summary reports for teachers showing student progress
5. WHEN a student asks questions, THE Pedagogical_Engine SHALL classify topics and update mastery tracking
6. THE Pedagogical_Engine SHALL adjust question difficulty based on current mastery level

### Requirement 5: Concurrency Management

**User Story:** As a system operator, I want controlled concurrent inference with queue management, so that the system remains stable under load from 100-300 active students.

#### Acceptance Criteria

1. THE Concurrency_Manager SHALL limit maximum concurrent inference threads to 5
2. THE Concurrency_Manager SHALL implement async queue for incoming requests
3. WHEN concurrent requests exceed 5, THE System SHALL queue additional requests
4. THE Concurrency_Manager SHALL provide token streaming for responses
5. THE System SHALL maintain target latency of 3-8 seconds per response
6. WHEN load exceeds capacity, THE System SHALL return queue position to users

### Requirement 6: VKP Packaging Format

**User Story:** As a curriculum manager, I want a standardized versioned package format for knowledge distribution, so that updates can be tracked and distributed reliably.

#### Acceptance Criteria

1. THE VKP_Packager SHALL create packages containing embeddings, metadata, integrity checksum (SHA256), and version manifest
2. THE VKP_Format SHALL include fields: version, subject, grade, semester, chunks, embedding_model, created_at, checksum
3. THE VKP_Packager SHALL support delta updates (only changed content)
4. WHEN a VKP is created, THE System SHALL generate integrity checksum for verification
5. THE VKP_Format SHALL be JSON-serializable for S3 storage
6. THE VKP_Packager SHALL tag packages with subject and grade metadata

### Requirement 7: VKP Pull Mechanism

**User Story:** As a school administrator, I want automatic periodic updates from AWS, so that curriculum changes are synchronized without manual intervention.

#### Acceptance Criteria

1. THE VKP_Puller SHALL check for updates from S3 every 1 hour via cron job
2. THE VKP_Puller SHALL compare local version with cloud version
3. WHEN a new version is available, THE VKP_Puller SHALL download delta updates only
4. THE VKP_Puller SHALL verify integrity checksum before applying updates
5. THE VKP_Puller SHALL extract embeddings to ChromaDB after verification
6. THE VKP_Puller SHALL update PostgreSQL metadata with new version information
7. IF internet is unavailable, THEN THE System SHALL continue operating with existing data

### Requirement 8: AWS Lambda Curriculum Processing

**User Story:** As a curriculum coordinator, I want automated PDF processing in AWS, so that new materials are converted to embeddings without manual intervention.

#### Acceptance Criteria

1. WHEN a PDF is uploaded to S3, THE Lambda_Function SHALL trigger automatically
2. THE Lambda_Function SHALL extract text from PDF using pypdf
3. THE Lambda_Function SHALL chunk text with 800 token chunks and 100 token overlap
4. THE Lambda_Function SHALL call Bedrock Titan to generate embeddings
5. THE Lambda_Function SHALL package results into VKP format
6. THE Lambda_Function SHALL upload VKP to S3 versioned bucket
7. IF processing fails, THEN THE Lambda_Function SHALL log error to CloudWatch and send notification

### Requirement 9: Aggregated Telemetry

**User Story:** As a national coordinator, I want anonymized usage metrics, so that I can monitor system health without compromising student privacy.

#### Acceptance Criteria

1. THE Telemetry_System SHALL collect only anonymized metrics: total query count, average latency, model version, error rate, storage usage
2. THE Telemetry_System SHALL NOT collect chat content, user data, or personal information
3. THE Telemetry_System SHALL batch metrics and upload to DynamoDB periodically
4. THE Telemetry_System SHALL include school_id (anonymized) and timestamp in metrics
5. WHEN telemetry is sent, THE System SHALL verify no PII is included
6. IF AWS is unavailable, THEN THE System SHALL queue metrics locally and retry later

### Requirement 10: Resilience and Recovery

**User Story:** As a system administrator, I want automated backup and recovery mechanisms, so that the system can survive failures and restore quickly.

#### Acceptance Criteria

1. THE Resilience_Module SHALL perform weekly full backups of PostgreSQL and ChromaDB
2. THE Resilience_Module SHALL perform daily incremental backups of chat history
3. THE Resilience_Module SHALL compress and optionally encrypt backups
4. THE Resilience_Module SHALL implement version rollback capability
5. THE Health_Monitor SHALL check LLM model status, ChromaDB connection, PostgreSQL connection, disk space, and RAM usage
6. WHEN critical failure is detected, THE Health_Monitor SHALL attempt automatic service restart
7. THE Resilience_Module SHALL retain backups for last 4 weeks and cleanup older backups

### Requirement 11: Embedding Strategy Management

**User Story:** As a deployment engineer, I want configurable embedding strategy, so that schools can choose between AWS Bedrock (default) or local MiniLM (sovereign mode).

#### Acceptance Criteria

1. THE Embedding_Strategy_Manager SHALL support two modes: AWS Bedrock (default) and Local MiniLM (optional)
2. THE Embedding_Strategy_Manager SHALL default to AWS Bedrock for curriculum processing
3. WHERE sovereign mode is enabled, THE System SHALL use local MiniLM quantized embedding engine
4. THE Embedding_Strategy_Manager SHALL provide fallback from AWS to local if AWS is unavailable
5. THE Configuration SHALL allow switching embedding strategy without code changes
6. WHEN embedding strategy changes, THE System SHALL log the active strategy

### Requirement 12: Caching Layer

**User Story:** As a performance engineer, I want optional Redis caching for repeated questions, so that CPU load is reduced and response time improves.

#### Acceptance Criteria

1. WHERE Redis is available, THE Caching_Layer SHALL cache repeated question responses
2. THE Caching_Layer SHALL use question text hash as cache key
3. WHEN a cached response exists, THE System SHALL return cached result within 500ms
4. THE Caching_Layer SHALL set TTL of 24 hours for cached responses
5. IF Redis is unavailable, THEN THE System SHALL fallback to in-memory cache with LRU eviction
6. THE Caching_Layer SHALL invalidate cache when curriculum version updates

### Requirement 13: Incremental Refactoring Process

**User Story:** As a development team lead, I want a phased refactoring approach with testing at each step, so that we minimize risk and maintain system stability.

#### Acceptance Criteria

1. THE Refactoring_Process SHALL execute in sequential phases: Preparation, Folder Restructuring, Database Persistence, AWS Infrastructure, VKP Pull, Pedagogy, Resilience
2. WHEN each phase completes, THE System SHALL run full test suite and verify all tests pass
3. THE Refactoring_Process SHALL use Git branching with one branch per phase
4. THE Refactoring_Process SHALL commit after each phase completion
5. IF tests fail after a phase, THEN THE System SHALL rollback to previous commit
6. THE Refactoring_Process SHALL maintain backward compatibility throughout all phases

### Requirement 14: Components to Preserve

**User Story:** As a developer, I want to identify and preserve working components, so that refactoring doesn't break existing functionality.

#### Acceptance Criteria

1. THE Refactoring_Process SHALL preserve src/edge_runtime/rag_pipeline.py (formerly local_inference) without modification
2. THE Refactoring_Process SHALL preserve src/edge_runtime/inference_engine.py without modification
3. THE Refactoring_Process SHALL preserve src/embeddings/chroma_manager.py without modification
4. THE Refactoring_Process SHALL preserve src/embeddings/bedrock_client.py without modification
5. THE Refactoring_Process SHALL preserve src/data_processing/etl_pipeline.py without modification
6. THE Refactoring_Process SHALL preserve frontend/ directory structure without modification
7. WHEN preserved components are referenced, THE System SHALL update only import paths, not implementation

### Requirement 15: AWS Infrastructure Setup

**User Story:** As a DevOps engineer, I want automated AWS infrastructure setup scripts, so that deployment is repeatable and consistent.

#### Acceptance Criteria

1. THE Infrastructure_Setup SHALL create S3 buckets: nexusai-curriculum-raw, nexusai-vkp-packages, nexusai-model-distribution
2. THE Infrastructure_Setup SHALL enable versioning on nexusai-vkp-packages bucket
3. THE Infrastructure_Setup SHALL create DynamoDB tables: nexusai-schools, nexusai-metrics
4. THE Infrastructure_Setup SHALL configure CloudFront distribution for VKP delivery
5. THE Infrastructure_Setup SHALL deploy Lambda function for curriculum processing
6. THE Infrastructure_Setup SHALL configure S3 event trigger for Lambda
7. THE Infrastructure_Setup SHALL provide setup script that can be run idempotently

### Requirement 16: Privacy by Architecture

**User Story:** As a privacy officer, I want architectural guarantees that sensitive data never leaves the school, so that privacy is enforced by design rather than policy.

#### Acceptance Criteria

1. THE System SHALL store chat history exclusively in local PostgreSQL database
2. THE System SHALL store student identity exclusively in local PostgreSQL database
3. THE System SHALL store teacher identity exclusively in local PostgreSQL database
4. THE System SHALL NOT send chat content to AWS under any circumstances
5. THE System SHALL NOT send user data to AWS under any circumstances
6. WHEN data is sent to AWS, THE System SHALL verify it contains only anonymized metrics
7. THE Privacy_Audit_Tool SHALL scan all AWS API calls and verify no PII is transmitted

### Requirement 17: Offline Operation Guarantee

**User Story:** As a school administrator, I want the system to function fully offline after initial setup, so that internet outages don't disrupt learning.

#### Acceptance Criteria

1. WHEN internet is unavailable, THE System SHALL continue serving student queries using local LLM
2. WHEN internet is unavailable, THE System SHALL continue RAG operations using local ChromaDB
3. WHEN internet is unavailable, THE System SHALL continue authentication using local PostgreSQL
4. THE System SHALL queue telemetry and VKP updates for later transmission when offline
5. IF AWS is completely unavailable, THEN THE System SHALL operate indefinitely with existing data
6. THE System SHALL log offline status but continue normal operation

### Requirement 18: Load Testing and Performance Validation

**User Story:** As a quality assurance engineer, I want load testing to verify the system handles 100-300 concurrent students, so that performance claims are validated.

#### Acceptance Criteria

1. THE Load_Testing_Suite SHALL simulate 100 concurrent users with stable performance
2. THE Load_Testing_Suite SHALL simulate 300 concurrent users with acceptable degradation
3. WHEN load testing runs, THE System SHALL maintain 3-8 second response time for 90th percentile
4. THE Load_Testing_Suite SHALL measure error rate and verify < 1% errors
5. THE Load_Testing_Suite SHALL measure queue depth and verify requests are processed
6. THE Load_Testing_Suite SHALL generate performance report with latency distribution

### Requirement 19: Documentation Updates

**User Story:** As a new developer, I want updated documentation that reflects the refactored architecture, so that I can understand and contribute to the system.

#### Acceptance Criteria

1. THE Documentation_System SHALL update README.md with 16GB hardware requirements
2. THE Documentation_System SHALL update docs/DEPLOYMENT.md with step-by-step deployment instructions
3. THE Documentation_System SHALL create docs/AWS_SETUP.md with AWS configuration guide
4. THE Documentation_System SHALL create docs/DATABASE_SCHEMA.md with PostgreSQL schema documentation
5. THE Documentation_System SHALL update docs/SYSTEM_ARCHITECTURE.md to match definitive architecture
6. THE Documentation_System SHALL create docs/TROUBLESHOOTING.md with common issues and solutions

### Requirement 20: Deployment Package Creation

**User Story:** As a deployment engineer, I want an automated installer script, so that school servers can be set up quickly and consistently.

#### Acceptance Criteria

1. THE Deployment_Package SHALL include install.sh script that checks system requirements
2. THE Deployment_Package SHALL install PostgreSQL and configure database
3. THE Deployment_Package SHALL install Python dependencies from requirements.txt
4. THE Deployment_Package SHALL download LLM model if not present
5. THE Deployment_Package SHALL setup database schema and create admin user
6. THE Deployment_Package SHALL configure systemd services for auto-start
7. THE Deployment_Package SHALL verify installation and start services
8. WHEN installation completes, THE System SHALL display access URL and admin credentials

## Non-Functional Requirements

### Performance

1. THE System SHALL maintain response latency of 3-8 seconds for 90th percentile queries
2. THE System SHALL support 100-300 concurrent active students with stable performance
3. THE Database_Queries SHALL complete within 100ms for 95th percentile
4. THE VKP_Pull_Operation SHALL complete within 5 minutes for typical curriculum updates

### Reliability

1. THE System SHALL achieve 99.5% uptime during school hours (excluding planned maintenance)
2. THE System SHALL recover automatically from transient failures within 30 seconds
3. THE Backup_System SHALL maintain recovery point objective (RPO) of 24 hours
4. THE Backup_System SHALL maintain recovery time objective (RTO) of 1 hour

### Security

1. THE System SHALL hash all passwords using SHA256 before storage
2. THE System SHALL expire sessions after 24 hours of inactivity
3. THE System SHALL validate all user inputs to prevent SQL injection
4. THE System SHALL use HTTPS for all external communications (AWS API calls)
5. THE System SHALL restrict database access to localhost only

### Maintainability

1. THE Codebase SHALL maintain test coverage above 70% for critical paths
2. THE System SHALL log all errors with stack traces to facilitate debugging
3. THE Configuration SHALL be externalized in config files (no hardcoded values)
4. THE Code SHALL follow PEP 8 style guidelines for Python

### Scalability

1. THE System SHALL support up to 500 students per school server
2. THE ChromaDB SHALL support up to 100,000 document chunks per subject
3. THE PostgreSQL SHALL support up to 1 million chat history records
4. THE System SHALL support up to 20 subjects per grade level

### Compatibility

1. THE System SHALL run on Ubuntu Server 20.04 LTS or later
2. THE System SHALL support Python 3.9 or later
3. THE System SHALL support PostgreSQL 12 or later
4. THE System SHALL be compatible with AWS services in ap-southeast-1 region

## Constraints

### Technical Constraints

1. Refactoring MUST be incremental (one module at a time)
2. All changes MUST be tested before and after each phase
3. System MUST maintain backward compatibility during refactoring
4. Git branching MUST be used for each refactoring phase
5. NO over-engineering - implement only what is specified in definitive architecture
6. Folder renames MUST preserve Git history
7. Import path updates MUST be automated to prevent errors

### Operational Constraints

1. Refactoring MUST NOT break existing functionality at any phase
2. Each phase MUST be committable and deployable independently
3. Rollback MUST be possible at any phase boundary
4. Testing MUST pass 100% before proceeding to next phase
5. Documentation MUST be updated concurrently with code changes

### Resource Constraints

1. School servers have 16GB RAM (not 4GB)
2. Maximum 5 concurrent inference threads
3. LLM model size limited to 4GB (quantized)
4. ChromaDB storage limited to 512GB SSD capacity
5. Network bandwidth for VKP updates assumed to be 10 Mbps minimum

### Business Constraints

1. Privacy by architecture is non-negotiable (no chat data to AWS)
2. 100% offline operation after initial setup is mandatory
3. One School - One Sovereign AI Node model must be preserved
4. AWS is for orchestration only, not production inference
5. System must align with all README documents (README_DEPLOYMENT_SCENARIOS.md, ARCHITECTURE_ANALYSIS.md, DEVELOPMENT_STRATEGY.md, REFACTORING_ROADMAP.md)

## Success Criteria

The architecture alignment refactoring will be considered successful when:

1. All folder names match definitive architecture (edge_runtime, aws_control_plane)
2. PostgreSQL persistence is implemented and tested (data survives restarts)
3. Pedagogical Engine tracks mastery and generates adaptive questions
4. Concurrency management limits to 5 threads with queue
5. VKP format is implemented with versioning and checksums
6. VKP pull mechanism runs hourly and updates ChromaDB
7. AWS Lambda processes PDFs and generates VKPs automatically
8. Telemetry sends only anonymized metrics to DynamoDB
9. Resilience module performs weekly backups and health monitoring
10. All documentation reflects 16GB RAM requirement
11. Load testing validates 100-300 concurrent user support
12. All existing tests pass after refactoring
13. System operates 100% offline after initial setup
14. Privacy audit confirms no PII sent to AWS
15. Deployment package installs system automatically

## Out of Scope

The following are explicitly OUT OF SCOPE for this refactoring:

1. Changing the LLM model (Llama 3.2 3B remains)
2. Changing the vector database (ChromaDB remains)
3. Changing the embedding model (Bedrock Titan remains default)
4. Implementing new features beyond definitive architecture
5. UI/UX redesign (frontend structure preserved)
6. Multi-school federation (remains single sovereign node)
7. Real-time synchronization (remains periodic pull)
8. GPU optimization (remains CPU-focused)
9. Mobile app development
10. Integration with external learning management systems
11. Advanced analytics beyond basic telemetry
12. Multi-language support beyond existing capabilities
13. Custom model training workflows (SageMaker setup only)
14. Production deployment to actual schools (development/testing only)
15. Performance optimization beyond meeting stated requirements
