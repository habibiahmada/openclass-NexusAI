# Implementation Plan: Architecture Alignment Refactoring

## Overview

This implementation plan breaks down the architecture alignment refactoring into 13 sequential phases, each building on the previous one. The refactoring transforms the OpenClass Nexus AI codebase from 40% alignment to 100% alignment with the definitive Hybrid Orchestrated Edge AI architecture.

Each phase is designed to be independently testable and committable, with validation checkpoints to ensure system stability. The approach prioritizes incremental implementation, backward compatibility, and production readiness.

## Implementation Language

Python 3.9+ (as specified in the design document)

## Tasks

- [ ] 0. Phase 0: Preparation and Audit
  - [x] 0.1 Create full system backup
    - Create backup of entire codebase, database, and configuration
    - Store backup in `/backups/pre-refactoring/`
    - Verify backup integrity
    - _Requirements: 13.1_

  - [x] 0.2 Run comprehensive test suite baseline
    - Execute all existing tests and record results
    - Document current test coverage percentage
    - Create baseline performance metrics
    - _Requirements: 13.2_

  - [x] 0.3 Create architecture alignment audit checklist
    - Document current vs. target architecture gaps
    - List all components requiring modification
    - Identify preserved components (no changes)
    - _Requirements: 13.1, 14.1-14.7_

  - [x] 0.4 Setup Git branching strategy
    - Create `refactoring/phase-0-preparation` branch
    - Configure branch protection rules
    - Setup commit message templates
    - _Requirements: 13.3_


- [ ] 1. Phase 1: Folder Structure Alignment
  - [x] 1.1 Rename src/local_inference to src/edge_runtime
    - Use `git mv` to preserve history
    - Verify folder rename completed successfully
    - _Requirements: 2.1_

  - [x] 1.2 Rename src/cloud_sync to src/aws_control_plane
    - Use `git mv` to preserve history
    - Verify folder rename completed successfully
    - _Requirements: 2.2_

  - [x] 1.3 Move models/cache to models
    - Use `git mv` to preserve history
    - Verify folder structure matches target architecture
    - _Requirements: 2.3_

  - [x] 1.4 Update all import statements automatically
    - Create script to find and replace import paths
    - Update imports from `src.local_inference` to `src.edge_runtime`
    - Update imports from `src.cloud_sync` to `src.aws_control_plane`
    - Verify no old import paths remain in codebase
    - _Requirements: 2.4_

  - [x] 1.5 Write property test for import path consistency
    - **Property 2: Import Path Consistency After Refactoring**
    - **Validates: Requirements 2.4**

  - [x] 1.6 Run all existing tests after folder restructuring
    - Execute full test suite
    - Verify 100% of tests pass
    - _Requirements: 2.5, 13.2_

  - [x] 1.7 Checkpoint - Commit Phase 1
    - Commit changes with message "Phase 1: Folder structure alignment"
    - Tag commit as `refactoring-phase-1`
    - Ensure all tests pass, ask the user if questions arise.


- [x] 2. Phase 2: Database Persistence Layer
  - [x] 2.1 Create PostgreSQL database schema
    - Write SQL schema for all tables (users, sessions, chat_history, subjects, books, topic_mastery, weak_areas, practice_questions)
    - Create indexes for performance optimization
    - Add foreign key constraints and check constraints
    - _Requirements: 3.1_

  - [x] 2.2 Implement DatabaseManager class
    - Create connection pooling (pool_size=10, max_overflow=20)
    - Implement get_connection(), execute_query(), execute_transaction()
    - Add health_check() method
    - _Requirements: 3.1, 3.4, 3.5_

  - [x] 2.3 Implement UserRepository
    - Create CRUD operations for users
    - Implement password hashing with SHA256
    - Add user validation logic
    - _Requirements: 3.1_

  - [x] 2.4 Implement SessionRepository
    - Create session management operations
    - Implement session expiration (24 hours)
    - Add cleanup_expired_sessions() method
    - _Requirements: 3.1_

  - [x] 2.5 Implement ChatHistoryRepository
    - Create chat persistence operations
    - Implement get_user_history() and get_subject_history()
    - Add pagination support
    - _Requirements: 3.1, 3.2_

  - [x] 2.6 Implement SubjectRepository and BookRepository
    - Create dynamic subject management
    - Implement VKP version tracking in books table
    - Add subject-book relationship management
    - _Requirements: 3.1_

  - [x] 2.7 Replace in-memory storage with database operations
    - Replace active_tokens dict with SessionRepository
    - Replace state.chat_logs list with ChatHistoryRepository
    - Update API endpoints to use repositories
    - _Requirements: 3.2_

  - [x] 2.8 Write property test for data persistence across restarts
    - **Property 3: Data Persistence Across Restarts**
    - **Validates: Requirements 3.3**

  - [x] 2.9 Write property test for database transaction atomicity
    - **Property 4: Database Transaction Atomicity**
    - **Validates: Requirements 3.4**

  - [x] 2.10 Write unit tests for repository operations
    - Test CRUD operations for each repository
    - Test error handling (connection failures, constraint violations)
    - Test edge cases (empty results, duplicate keys)
    - _Requirements: 3.1-3.6_

  - [x] 2.11 Implement graceful degradation for database unavailability
    - Add error handling for PostgreSQL connection failures
    - Return HTTP 503 with user-friendly message
    - Log errors with stack traces
    - _Requirements: 3.6_

  - [x] 2.12 Checkpoint - Verify data persists across server restarts
    - Start server, create test data
    - Restart server
    - Verify data is still present
    - Ensure all tests pass, ask the user if questions arise.


- [x] 3. Phase 3: AWS Infrastructure Setup
  - [x] 3.1 Create AWS infrastructure setup script
    - Write Python script using boto3
    - Make script idempotent (can run multiple times safely)
    - Add error handling and logging
    - _Requirements: 15.1-15.7_

  - [x] 3.2 Create S3 buckets
    - Create nexusai-curriculum-raw bucket
    - Create nexusai-vkp-packages bucket with versioning enabled
    - Create nexusai-model-distribution bucket
    - Configure bucket policies and CORS
    - _Requirements: 15.1, 15.2_

  - [x] 3.3 Create DynamoDB tables
    - Create nexusai-schools table (school_id as hash key)
    - Create nexusai-metrics table (school_id as hash, timestamp as range)
    - Configure TTL for metrics table (90 days)
    - _Requirements: 15.3_

  - [x] 3.4 Deploy Lambda curriculum processor function
    - Package Lambda function with dependencies (pypdf, boto3)
    - Configure runtime (Python 3.11, 1GB RAM, 5 min timeout)
    - Set environment variables (BEDROCK_MODEL_ID, CHUNK_SIZE, etc.)
    - _Requirements: 15.5_

  - [x] 3.5 Configure S3 event trigger for Lambda
    - Add S3 event notification for .pdf uploads
    - Configure filter (prefix: raw/, suffix: .pdf)
    - Test trigger with sample PDF
    - _Requirements: 15.6_

  - [x] 3.6 Setup IAM roles and permissions
    - Create Lambda execution role with S3 and Bedrock permissions
    - Create school server role for S3 read access
    - Configure least-privilege access policies
    - _Requirements: 15.5_

  - [x] 3.7 Configure CloudFront distribution (optional)
    - Create CloudFront distribution for VKP delivery
    - Configure origin as S3 VKP bucket
    - Setup signed URLs for access control
    - _Requirements: 15.4_

  - [x] 3.8 Write property test for AWS infrastructure idempotence
    - **Property 31: AWS Infrastructure Setup Idempotence**
    - **Validates: Requirements 15.7**

  - [x] 3.9 Write unit tests for infrastructure setup
    - Test S3 bucket creation
    - Test DynamoDB table creation
    - Test Lambda deployment
    - _Requirements: 15.1-15.7_

  - [x] 3.10 Checkpoint - Verify AWS infrastructure is operational
    - Upload test PDF to S3
    - Verify Lambda triggers and processes PDF
    - Check VKP package created in output bucket
    - Ensure all tests pass, ask the user if questions arise.


- [x] 4. Phase 4: VKP Packaging System
  - [x] 4.1 Implement VKP data models
    - Create VKPMetadata, VKPChunk, ChunkMetadata dataclasses
    - Add JSON serialization support
    - Implement validation methods
    - _Requirements: 6.1, 6.2_

  - [x] 4.2 Implement VKPPackager class
    - Create create_package() method
    - Implement calculate_checksum() using SHA256
    - Add serialize() and deserialize() methods
    - _Requirements: 6.1, 6.4_

  - [x] 4.3 Implement delta update calculation
    - Create calculate_delta() method
    - Compare chunk_ids between versions
    - Generate delta package with only changed chunks
    - _Requirements: 6.3_

  - [x] 4.4 Implement VKPVersionManager
    - Create version tracking in PostgreSQL
    - Implement semantic version comparison
    - Add rollback capability
    - _Requirements: 6.1, 6.2_

  - [x] 4.5 Update Lambda function to generate VKP packages
    - Integrate VKPPackager into Lambda processor
    - Extract metadata from PDF filename
    - Generate VKP with proper versioning
    - Upload to S3 with metadata tags
    - _Requirements: 8.5, 8.6_

  - [x] 4.6 Write property test for VKP structure validation
    - **Property 14: VKP Structure Validation**
    - **Validates: Requirements 6.1, 6.2, 6.6**

  - [x] 4.7 Write property test for VKP checksum integrity
    - **Property 16: VKP Checksum Integrity**
    - **Validates: Requirements 6.4**

  - [x] 4.8 Write property test for VKP serialization round-trip
    - **Property 17: VKP Serialization Round-Trip**
    - **Validates: Requirements 6.5**

  - [x] 4.9 Write property test for delta update efficiency
    - **Property 15: VKP Delta Update Efficiency**
    - **Validates: Requirements 6.3**

  - [x] 4.10 Write unit tests for VKP packaging
    - Test VKP creation with various inputs
    - Test checksum calculation
    - Test serialization/deserialization
    - Test delta calculation
    - _Requirements: 6.1-6.6_

  - [x] 4.11 Checkpoint - Verify VKP packaging works end-to-end
    - Upload PDF to S3
    - Verify Lambda creates valid VKP
    - Verify checksum is correct
    - Verify VKP can be deserialized
    - Ensure all tests pass, ask the user if questions arise.


- [x] 5. Phase 5: VKP Pull Mechanism
  - [x] 5.1 Implement VKPPuller class
    - Create check_updates() method to list S3 VKPs
    - Implement compare_versions() for semantic versioning
    - Add download_vkp() method with retry logic
    - _Requirements: 7.1, 7.2_

  - [x] 5.2 Implement VKP integrity verification
    - Create verify_integrity() method
    - Compare calculated checksum with stored checksum
    - Reject VKP if checksum mismatch
    - _Requirements: 7.4_

  - [x] 5.3 Implement ChromaDB extraction
    - Create extract_to_chromadb() method
    - Add embeddings to appropriate collection
    - Handle collection creation if not exists
    - _Requirements: 7.5_

  - [x] 5.4 Implement metadata update in PostgreSQL
    - Update books table with new VKP version
    - Record update timestamp
    - Track chunk count
    - _Requirements: 7.6_

  - [x] 5.5 Create periodic pull cron job
    - Write cron script to run VKP puller hourly
    - Add internet connectivity check
    - Implement offline mode (skip if no internet)
    - _Requirements: 7.1, 7.7_

  - [x] 5.6 Implement delta download optimization
    - Download only changed chunks when possible
    - Apply delta updates to existing ChromaDB
    - Fallback to full download if delta fails
    - _Requirements: 7.3_

  - [x] 5.7 Write property test for version comparison correctness
    - **Property 18: Version Comparison Correctness**
    - **Validates: Requirements 7.2**

  - [x] 5.8 Write property test for VKP delta download
    - **Property 19: VKP Delta Download Only**
    - **Validates: Requirements 7.3**

  - [x] 5.9 Write property test for checksum verification
    - **Property 20: VKP Checksum Verification Before Installation**
    - **Validates: Requirements 7.4**

  - [x] 5.10 Write unit tests for VKP puller
    - Test S3 listing and version comparison
    - Test download and verification
    - Test ChromaDB extraction
    - Test offline mode behavior
    - _Requirements: 7.1-7.7_

  - [x] 5.11 Checkpoint - Verify VKP pull mechanism works
    - Upload new VKP version to S3
    - Run VKP puller manually
    - Verify new version downloaded and installed
    - Verify ChromaDB updated with new embeddings
    - Ensure all tests pass, ask the user if questions arise.


- [x] 6. Phase 6: Pedagogical Intelligence Engine
  - [x] 6.1 Implement MasteryTracker class
    - Create classify_topic() method using keyword matching
    - Implement update_mastery() with scoring algorithm
    - Add get_mastery_level() and get_all_mastery() methods
    - Store mastery data in topic_mastery table
    - _Requirements: 4.1, 4.5_

  - [x] 6.2 Implement mastery scoring algorithm
    - Calculate mastery based on question frequency, complexity, retention
    - Ensure mastery level always between 0.0 and 1.0
    - Update mastery after each student question
    - _Requirements: 4.1_

  - [x] 6.3 Implement WeakAreaDetector class
    - Create detect_weak_areas() method (threshold < 0.4)
    - Implement get_weakness_score() calculation
    - Add recommend_practice() method
    - Store weak areas in weak_areas table
    - _Requirements: 4.2_

  - [x] 6.4 Implement AdaptiveQuestionGenerator class
    - Create generate_question() method
    - Implement adjust_difficulty() based on mastery level
    - Add get_practice_set() for multiple questions
    - Store practice questions in practice_questions table
    - _Requirements: 4.3, 4.6_

  - [x] 6.5 Implement WeeklyReportGenerator class
    - Create generate_report() for individual students
    - Implement get_class_summary() for teachers
    - Add export_report() in PDF/JSON format
    - _Requirements: 4.4_

  - [x] 6.6 Integrate pedagogical engine with chat pipeline
    - Extract topic from each question
    - Calculate question complexity
    - Update mastery tracker after each query
    - Optionally suggest practice questions
    - _Requirements: 4.5_

  - [x] 6.7 Write property test for mastery level bounds
    - **Property 5: Mastery Level Bounds**
    - **Validates: Requirements 4.1**

  - [x] 6.8 Write property test for weak area detection
    - **Property 6: Weak Area Detection**
    - **Validates: Requirements 4.2**

  - [x] 6.9 Write property test for adaptive question difficulty
    - **Property 7: Adaptive Question Difficulty**
    - **Validates: Requirements 4.6**

  - [x] 6.10 Write property test for topic classification
    - **Property 8: Topic Classification and Mastery Update**
    - **Validates: Requirements 4.5**

  - [x] 6.11 Write property test for practice question generation
    - **Property 9: Adaptive Practice Question Generation**
    - **Validates: Requirements 4.3**

  - [x] 6.12 Write unit tests for pedagogical engine
    - Test mastery calculation with various inputs
    - Test weak area detection logic
    - Test question generation
    - Test report generation
    - _Requirements: 4.1-4.6_

  - [x] 6.13 Checkpoint - Verify pedagogical engine tracks mastery
    - Submit test questions as student
    - Verify mastery levels updated in database
    - Verify weak areas detected correctly
    - Verify practice questions generated
    - Ensure all tests pass, ask the user if questions arise.


- [ ] 7. Phase 7: Concurrency Management System
  - [ ] 7.1 Implement ConcurrencyManager class
    - Create async queue using asyncio.Queue
    - Implement semaphore with max_concurrent=5
    - Add enqueue_request() and process_queue() methods
    - Track active and completed requests
    - _Requirements: 5.1, 5.2_

  - [ ] 7.2 Implement InferenceRequest data structure
    - Create dataclass with queue_id, user_id, question, subject_id, context
    - Add timestamp and priority fields
    - Implement unique queue_id generation
    - _Requirements: 5.2_

  - [ ] 7.3 Implement queue position tracking
    - Create get_queue_position() method
    - Return 0 for active requests
    - Return position in queue for waiting requests
    - Return -1 for completed requests
    - _Requirements: 5.6_

  - [ ] 7.4 Implement TokenStreamer for response streaming
    - Create async stream_response() method
    - Format tokens as Server-Sent Events (SSE)
    - Handle streaming errors gracefully
    - _Requirements: 5.4_

  - [ ] 7.5 Integrate concurrency manager with API endpoints
    - Update /api/chat endpoint to use queue
    - Return queue position to users
    - Stream responses when ready
    - _Requirements: 5.2, 5.3_

  - [ ] 7.6 Implement queue overflow handling
    - Set MAX_QUEUE_SIZE = 1000
    - Return HTTP 503 when queue full
    - Provide estimated wait time to users
    - _Requirements: 5.3_

  - [ ] 7.7 Write property test for concurrent thread limit
    - **Property 10: Concurrent Thread Limit**
    - **Validates: Requirements 5.1**

  - [ ] 7.8 Write property test for request queuing
    - **Property 11: Request Queuing When Capacity Exceeded**
    - **Validates: Requirements 5.3**

  - [ ] 7.9 Write property test for queue position tracking
    - **Property 12: Queue Position Tracking**
    - **Validates: Requirements 5.6**

  - [ ] 7.10 Write unit tests for concurrency manager
    - Test queue operations
    - Test semaphore limiting
    - Test position tracking
    - Test streaming
    - _Requirements: 5.1-5.6_

  - [ ] 7.11 Checkpoint - Verify concurrency limits work
    - Submit 10 concurrent requests
    - Verify only 5 process simultaneously
    - Verify remaining 5 are queued
    - Verify queue positions returned correctly
    - Ensure all tests pass, ask the user if questions arise.


- [ ] 8. Phase 8: Aggregated Telemetry System
  - [ ] 8.1 Implement TelemetryCollector class
    - Create record_query() method for query metrics
    - Implement record_error() for error tracking
    - Add get_metrics_snapshot() for current metrics
    - Store metrics in memory for aggregation
    - _Requirements: 9.1_

  - [ ] 8.2 Implement MetricsAggregator class
    - Create aggregate_hourly() method
    - Calculate percentiles (p50, p90, p99) for latency
    - Aggregate error types and counts
    - Get storage usage metrics
    - _Requirements: 9.1_

  - [ ] 8.3 Implement PIIVerifier class
    - Create verify_no_pii() method with pattern matching
    - Scan for NIK, email, phone, name patterns
    - Check for suspicious keys (username, email, etc.)
    - Reject telemetry if PII detected
    - _Requirements: 9.2, 9.5_

  - [ ] 8.4 Implement school ID anonymization
    - Create anonymize_school_id() using SHA256 hash
    - Use salt from environment variable
    - Ensure one-way hashing (cannot reverse)
    - _Requirements: 9.4_

  - [ ] 8.5 Implement TelemetryUploader class
    - Create upload_metrics() to DynamoDB
    - Implement queue_offline_metrics() for offline mode
    - Add retry_failed_uploads() with exponential backoff
    - _Requirements: 9.3_

  - [ ] 8.6 Create hourly telemetry upload cron job
    - Aggregate metrics every hour
    - Verify no PII before upload
    - Upload to DynamoDB if online
    - Queue locally if offline
    - _Requirements: 9.3_

  - [ ] 8.7 Integrate telemetry collection with API endpoints
    - Record query metrics after each request
    - Record error metrics on failures
    - Track latency and success rate
    - _Requirements: 9.1_

  - [ ] 8.8 Write property test for telemetry anonymization
    - **Property 23: Telemetry Data Anonymization**
    - **Validates: Requirements 9.1, 9.2, 9.4, 9.5**

  - [ ] 8.9 Write property test for AWS data transmission privacy
    - **Property 33: AWS Data Transmission Privacy**
    - **Validates: Requirements 16.4, 16.5, 16.6, 16.7**

  - [ ] 8.10 Write unit tests for telemetry system
    - Test metrics collection and aggregation
    - Test PII verification
    - Test anonymization
    - Test upload and offline queuing
    - _Requirements: 9.1-9.5_

  - [ ] 8.11 Checkpoint - Verify telemetry contains no PII
    - Generate test telemetry data
    - Run PII verification
    - Upload to DynamoDB
    - Verify only anonymized metrics stored
    - Ensure all tests pass, ask the user if questions arise.


- [ ] 9. Phase 9: Resilience and Recovery Module
  - [ ] 9.1 Implement BackupManager class
    - Create create_full_backup() method (PostgreSQL + ChromaDB + config)
    - Implement create_incremental_backup() for daily backups
    - Add restore_backup() with verification
    - Implement compress_backup() using gzip
    - Add optional encrypt_backup() method
    - _Requirements: 10.1, 10.2, 10.3_

  - [ ] 9.2 Implement BackupScheduler class
    - Create schedule_weekly_full_backup() cron job (Sunday 2 AM)
    - Implement schedule_daily_incremental_backup() (Monday-Saturday 2 AM)
    - Add cleanup_old_backups() with 28-day retention
    - _Requirements: 10.1, 10.2, 10.7_

  - [ ] 9.3 Implement HealthMonitor class
    - Create check_llm_status() method
    - Implement check_chromadb_connection()
    - Add check_postgres_connection()
    - Create check_disk_space() with thresholds (80% warning, 90% critical)
    - Implement check_ram_usage() with thresholds
    - Add run_health_checks() to execute all checks
    - _Requirements: 10.5_

  - [ ] 9.4 Implement AutoRestartService class
    - Create detect_failure() method
    - Implement attempt_restart() with max 3 attempts
    - Add restart cooldown (5 minutes)
    - Create escalate_failure() for manual intervention
    - _Requirements: 10.6_

  - [ ] 9.5 Implement VersionManager class
    - Create get_current_version() method
    - Implement rollback_to_version() with verification
    - Add create_version_snapshot()
    - Store version metadata in PostgreSQL
    - _Requirements: 10.4_

  - [ ] 9.6 Create health monitoring daemon
    - Run health checks every 5 minutes
    - Attempt auto-restart on critical failures
    - Log all health check results
    - Send alerts on repeated failures
    - _Requirements: 10.5, 10.6_

  - [ ] 9.7 Setup systemd services for auto-start
    - Create nexusai-api.service
    - Create nexusai-health-monitor.service
    - Configure auto-restart on failure
    - _Requirements: 10.6_

  - [ ] 9.8 Write property test for backup compression
    - **Property 24: Backup Compression**
    - **Validates: Requirements 10.3**

  - [ ] 9.9 Write property test for version rollback
    - **Property 25: Version Rollback Round-Trip**
    - **Validates: Requirements 10.4**

  - [ ] 9.10 Write property test for backup retention
    - **Property 26: Backup Retention Policy**
    - **Validates: Requirements 10.7**

  - [ ] 9.11 Write unit tests for resilience module
    - Test backup creation and restoration
    - Test health checks
    - Test auto-restart logic
    - Test version rollback
    - _Requirements: 10.1-10.7_

  - [ ] 9.12 Checkpoint - Verify backup and recovery works
    - Create full backup
    - Make changes to system
    - Restore from backup
    - Verify system restored to previous state
    - Ensure all tests pass, ask the user if questions arise.


- [ ] 10. Phase 10: Embedding Strategy Manager
  - [ ] 10.1 Implement EmbeddingStrategy abstract base class
    - Define generate_embedding() abstract method
    - Add batch_generate() abstract method
    - Create get_dimension() abstract method
    - Add health_check() abstract method
    - _Requirements: 11.1_

  - [ ] 10.2 Implement BedrockEmbeddingStrategy class
    - Create AWS Bedrock client integration
    - Implement embedding generation using Titan model
    - Add batch processing support
    - Handle API errors and throttling
    - _Requirements: 11.2_

  - [ ] 10.3 Implement LocalMiniLMEmbeddingStrategy class
    - Integrate sentence-transformers library
    - Load quantized MiniLM model
    - Implement local embedding generation
    - Optimize for CPU inference
    - _Requirements: 11.3_

  - [ ] 10.4 Implement EmbeddingStrategyManager class
    - Create get_strategy() method
    - Implement set_strategy() for configuration
    - Add fallback_to_local() for AWS unavailability
    - Load strategy from configuration file
    - _Requirements: 11.1, 11.4, 11.5_

  - [ ] 10.5 Update RAG pipeline to use strategy manager
    - Replace direct Bedrock calls with strategy manager
    - Add fallback logic for AWS failures
    - Log active embedding strategy
    - _Requirements: 11.4, 11.6_

  - [ ] 10.6 Add configuration for embedding strategy
    - Create config parameter for default strategy
    - Add sovereign mode flag
    - Allow runtime strategy switching
    - _Requirements: 11.5_

  - [ ] 10.7 Write unit tests for embedding strategies
    - Test Bedrock strategy
    - Test local MiniLM strategy
    - Test strategy manager
    - Test fallback behavior
    - _Requirements: 11.1-11.6_

  - [ ] 10.8 Checkpoint - Verify embedding strategy switching works
    - Test with Bedrock strategy
    - Switch to local strategy
    - Verify embeddings generated correctly
    - Test fallback when AWS unavailable
    - Ensure all tests pass, ask the user if questions arise.


- [ ] 11. Phase 11: Caching Layer
  - [ ] 11.1 Implement CacheManager class
    - Create get(), set(), delete() methods
    - Add invalidate_pattern() for bulk invalidation
    - Implement get_stats() for cache metrics
    - Support both Redis and LRU fallback
    - _Requirements: 12.1, 12.2_

  - [ ] 11.2 Implement RedisCache class
    - Create Redis client connection
    - Implement cache operations with TTL
    - Add pattern-based deletion
    - Handle connection errors gracefully
    - _Requirements: 12.1_

  - [ ] 11.3 Implement LRUCache class
    - Create in-memory LRU cache (max 1000 items)
    - Implement eviction policy
    - Add thread-safe operations
    - _Requirements: 12.5_

  - [ ] 11.4 Implement cache key generation
    - Create generate_cache_key() using SHA256 hash
    - Include question, subject_id, vkp_version in key
    - Normalize question text (lowercase, strip)
    - _Requirements: 12.2_

  - [ ] 11.5 Integrate caching with RAG pipeline
    - Check cache before RAG query
    - Store response in cache after generation
    - Set TTL to 24 hours
    - _Requirements: 12.1, 12.3, 12.4_

  - [ ] 11.6 Implement cache invalidation on VKP update
    - Invalidate all cached responses for updated subject
    - Use pattern matching for bulk deletion
    - Log invalidation count
    - _Requirements: 12.6_

  - [ ] 11.7 Write property test for cache key consistency
    - **Property 27: Cache Key Consistency**
    - **Validates: Requirements 12.2**

  - [ ] 11.8 Write property test for cache hit performance
    - **Property 28: Cache Hit Performance**
    - **Validates: Requirements 12.3**

  - [ ] 11.9 Write property test for cache invalidation
    - **Property 29: Cache Invalidation on VKP Update**
    - **Validates: Requirements 12.6**

  - [ ] 11.10 Write property test for repeated question caching
    - **Property 30: Repeated Question Caching**
    - **Validates: Requirements 12.1**

  - [ ] 11.11 Write unit tests for caching layer
    - Test Redis cache operations
    - Test LRU cache operations
    - Test cache manager
    - Test key generation
    - Test invalidation
    - _Requirements: 12.1-12.6_

  - [ ] 11.12 Checkpoint - Verify caching improves performance
    - Ask same question twice
    - Verify first request hits database
    - Verify second request hits cache (< 500ms)
    - Update VKP and verify cache invalidated
    - Ensure all tests pass, ask the user if questions arise.


- [ ] 12. Phase 12: Documentation and Configuration Updates
  - [ ] 12.1 Update hardware specifications in all documentation
    - Update README.md to specify 16GB RAM minimum
    - Update all references from 4GB to 16GB
    - Update hardware specs to 16GB RAM, 8-core CPU, 512GB SSD
    - Remove memory_limit_mb = 3072 constraint from config
    - _Requirements: 1.1, 1.2, 1.3, 19.1_

  - [ ] 12.2 Create deployment documentation
    - Write docs/DEPLOYMENT.md with step-by-step instructions
    - Include prerequisites and system requirements
    - Document installation process
    - Add troubleshooting section
    - _Requirements: 19.2_

  - [ ] 12.3 Create AWS setup documentation
    - Write docs/AWS_SETUP.md with AWS configuration guide
    - Document S3 bucket setup
    - Document Lambda deployment
    - Document DynamoDB table creation
    - Include IAM permissions
    - _Requirements: 19.3_

  - [ ] 12.4 Create database schema documentation
    - Write docs/DATABASE_SCHEMA.md
    - Document all tables and relationships
    - Include ER diagram
    - Document indexes and constraints
    - _Requirements: 19.4_

  - [ ] 12.5 Update system architecture documentation
    - Update docs/SYSTEM_ARCHITECTURE.md
    - Reflect new folder structure
    - Document all components and interactions
    - Include data flow diagrams
    - _Requirements: 19.5_

  - [ ] 12.6 Create troubleshooting guide
    - Write docs/TROUBLESHOOTING.md
    - Document common issues and solutions
    - Include error messages and fixes
    - Add debugging tips
    - _Requirements: 19.6_

  - [ ] 12.7 Write property test for documentation consistency
    - **Property 1: Documentation Hardware Specification Consistency**
    - **Validates: Requirements 1.1, 1.3, 1.4**

  - [ ] 12.8 Checkpoint - Verify documentation is complete and accurate
    - Review all documentation files
    - Verify hardware specs are consistent (16GB)
    - Verify deployment instructions are clear
    - Test documentation by following steps
    - Ensure all tests pass, ask the user if questions arise.


- [ ] 13. Phase 13: Testing, Validation, and Deployment Package
  - [ ] 13.1 Implement Lambda curriculum processor
    - Create PDFTextExtractor class using pypdf
    - Implement TextChunker with 800/100 token configuration
    - Create BedrockEmbeddingGenerator for Titan embeddings
    - Integrate VKPPackager for output
    - Add error handling and CloudWatch logging
    - _Requirements: 8.1-8.7_

  - [ ] 13.2 Write property test for PDF text extraction
    - **Property 21: PDF Text Extraction Completeness**
    - **Validates: Requirements 8.2**

  - [ ] 13.3 Write property test for text chunking
    - **Property 22: Text Chunking Parameters**
    - **Validates: Requirements 8.3**

  - [ ] 13.4 Write unit tests for Lambda processor
    - Test PDF extraction
    - Test text chunking
    - Test embedding generation
    - Test VKP packaging
    - Test S3 upload
    - _Requirements: 8.1-8.7_

  - [ ] 13.5 Implement privacy verification tests
    - Create test suite for local data storage
    - Verify chat history stored only locally
    - Verify user data never sent to AWS
    - Scan all AWS API calls for PII
    - _Requirements: 16.1-16.7_

  - [ ] 13.6 Write property test for local data storage
    - **Property 32: Local Data Storage Privacy**
    - **Validates: Requirements 16.1, 16.2, 16.3**

  - [ ] 13.7 Implement offline operation tests
    - Test system functionality with internet disabled
    - Verify queries work offline
    - Verify RAG operations work offline
    - Verify authentication works offline
    - _Requirements: 17.1-17.5_

  - [ ] 13.8 Write property test for offline operation
    - **Property 34: Offline Operation Completeness**
    - **Validates: Requirements 17.1, 17.2, 17.3, 17.5**

  - [ ] 13.9 Implement load testing suite
    - Create load test with Locust or similar tool
    - Test with 100 concurrent users
    - Test with 300 concurrent users
    - Measure latency distribution (p50, p90, p99)
    - Measure error rate
    - _Requirements: 18.1-18.6_

  - [ ] 13.10 Write property test for response latency
    - **Property 13: Response Latency Target**
    - **Validates: Requirements 5.5**

  - [ ] 13.11 Write property test for file preservation
    - **Property 35: File Preservation During Refactoring**
    - **Validates: Requirements 14.1-14.7**

  - [ ] 13.12 Run comprehensive test suite
    - Execute all unit tests
    - Execute all property tests (100 iterations each)
    - Verify test coverage > 70%
    - Fix any failing tests
    - _Requirements: 13.2_

  - [ ] 13.13 Create deployment package
    - Write install.sh script with system requirement checks
    - Include PostgreSQL installation and configuration
    - Add Python dependency installation
    - Include LLM model download
    - Setup database schema and admin user
    - Configure systemd services
    - Add verification and startup
    - _Requirements: 20.1-20.8_

  - [ ] 13.14 Test deployment package
    - Run install.sh on clean Ubuntu 20.04 system
    - Verify all components installed correctly
    - Verify system starts and responds to queries
    - Test with sample questions
    - _Requirements: 20.1-20.8_

  - [ ] 13.15 Run load testing validation
    - Execute load test with 100 concurrent users
    - Verify stable performance (3-8s latency)
    - Execute load test with 300 concurrent users
    - Verify acceptable degradation
    - Verify error rate < 1%
    - _Requirements: 18.1-18.6_

  - [ ] 13.16 Final checkpoint - Complete system validation
    - Verify all 20 requirements are met
    - Verify all 35 correctness properties pass
    - Verify system operates 100% offline
    - Verify no PII sent to AWS
    - Verify load testing passes
    - Ensure all tests pass, ask the user if questions arise.



## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP delivery
- Each phase should be completed and tested before moving to the next phase
- Git commits should be made after each phase completion with descriptive messages
- All phases maintain backward compatibility - system remains functional throughout refactoring
- Property tests use Hypothesis library with minimum 100 iterations per test
- Unit tests focus on specific examples, edge cases, and integration points
- Checkpoints ensure incremental validation and provide rollback points
- Each task references specific requirements for traceability
- Implementation language is Python 3.9+ as specified in the design document
- The refactoring follows the phased approach from REFACTORING_ROADMAP.md
- Privacy by architecture is enforced - no PII ever sent to AWS
- System must operate 100% offline after initial setup
- Load testing validates 100-300 concurrent user support
- All correctness properties must pass before deployment

## Success Criteria

The refactoring is complete when:

1. All 13 phases are implemented and tested
2. All folder names match definitive architecture (edge_runtime, aws_control_plane)
3. PostgreSQL persistence is operational (data survives restarts)
4. Pedagogical engine tracks mastery and generates adaptive questions
5. Concurrency management limits to 5 threads with queue
6. VKP format is implemented with versioning and checksums
7. VKP pull mechanism runs hourly and updates ChromaDB
8. AWS Lambda processes PDFs and generates VKPs automatically
9. Telemetry sends only anonymized metrics to DynamoDB
10. Resilience module performs weekly backups and health monitoring
11. All documentation reflects 16GB RAM requirement
12. Load testing validates 100-300 concurrent user support
13. All existing tests pass after refactoring
14. System operates 100% offline after initial setup
15. Privacy audit confirms no PII sent to AWS
16. Deployment package installs system automatically
17. All 35 correctness properties pass validation
18. Test coverage exceeds 70% for critical paths

## Execution Instructions

To begin implementation:

1. Open this tasks.md file in your IDE
2. Click "Start task" next to any task item to begin execution
3. Complete tasks sequentially within each phase
4. Run tests after each phase before proceeding
5. Commit changes after each phase completion
6. Use checkpoints to verify system stability

This workflow creates planning artifacts only. Implementation begins when you start executing individual tasks.
