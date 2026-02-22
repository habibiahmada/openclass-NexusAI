# Architecture Alignment Audit Checklist

**Project:** OpenClass Nexus AI - Architecture Alignment Refactoring  
**Date Created:** 2026-02-20  
**Current Alignment:** 40% (as per ARCHITECTURE_ANALYSIS.md)  
**Target Alignment:** 100%  
**Purpose:** Track gaps between current implementation and definitive architecture

---

## Executive Summary

This checklist documents all gaps between the current implementation (40% aligned) and the target architecture (100% aligned) as defined in README_DEPLOYMENT_SCENARIOS.md. It serves as a roadmap for the 13-phase refactoring process.

### Alignment Status Overview
- ✅ **Aligned (40%):** Core concepts, privacy architecture, basic RAG pipeline
- ⚠️ **Needs Adjustment (35%):** Folder structure, embedding strategy, partial implementations
- ❌ **Not Aligned (25%):** Database persistence, pedagogical engine, concurrency management, resilience

---

## Section 1: Hardware Specifications

### Current State (❌ NOT ALIGNED)
- Documentation claims "4GB RAM minimum"
- `config/app_config.py` has `memory_limit_mb = 3072` (3GB constraint)
- README.md states "Low-spec friendly 4GB"
- Inconsistent hardware specifications across documentation

### Target State
- 16GB RAM minimum (definitive requirement)
- 8-core CPU minimum
- 512GB SSD storage
- GPU optional (not required)
- No memory constraints in configuration

### Gap Analysis
| Component | Current | Target | Status |
|-----------|---------|--------|--------|
| RAM Specification | 4GB | 16GB | ❌ |
| Memory Limit Config | 3072 MB | Remove constraint | ❌ |
| README.md | 4GB claim | 16GB minimum | ❌ |
| CPU Specification | Not specified | 8-core minimum | ❌ |
| Storage Specification | Not specified | 512GB SSD | ❌ |
| GPU Requirement | Optional (correct) | Optional | ✅ |

### Components Requiring Modification
1. `README.md` - Update hardware requirements section
2. `config/app_config.py` - Remove `memory_limit_mb = 3072`
3. `docs/SYSTEM_ARCHITECTURE.md` - Update constraints section
4. All documentation files mentioning hardware specs

### Components to Preserve
- GPU optional configuration (already correct)

---

## Section 2: Folder Structure Alignment

### Current State (⚠️ NEEDS ADJUSTMENT)

```
src/
├── local_inference/     # Should be: edge_runtime/
├── cloud_sync/          # Should be: aws_control_plane/
├── embeddings/          # ✅ Correct
├── data_processing/     # ✅ Correct
├── optimization/        # ❌ Not in definitive architecture
├── ui/                  # ⚠️ Duplicates frontend/?
└── telemetry/           # ⚠️ Empty, needs implementation

models/
└── cache/               # Should be: models/ (no cache subfolder)
```

### Target State
```
src/
├── edge_runtime/        # Renamed from local_inference/
├── aws_control_plane/   # Renamed from cloud_sync/
├── embeddings/          # ✅ Keep as-is
├── data_processing/     # ✅ Keep as-is
├── pedagogy/            # ❌ NEW - Pedagogical Intelligence Engine
├── persistence/         # ❌ NEW - Database layer
├── resilience/          # ❌ NEW - Backup & recovery
└── telemetry/           # ⚠️ Expand with aggregated metrics

models/                  # Flatten structure (no cache subfolder)
└── *.gguf
```

### Gap Analysis
| Folder | Current | Target | Action | Status |
|--------|---------|--------|--------|--------|
| src/local_inference/ | Exists | src/edge_runtime/ | Rename | ⚠️ |
| src/cloud_sync/ | Exists | src/aws_control_plane/ | Rename | ⚠️ |
| src/pedagogy/ | Missing | Required | Create | ❌ |
| src/persistence/ | Missing | Required | Create | ❌ |
| src/resilience/ | Missing | Required | Create | ❌ |
| src/telemetry/ | Empty | Needs implementation | Expand | ⚠️ |
| src/optimization/ | Exists | Not in architecture | Evaluate/Remove | ⚠️ |
| src/ui/ | Exists | Duplicates frontend/ | Evaluate | ⚠️ |
| models/cache/ | Exists | models/ | Flatten | ⚠️ |

### Components Requiring Modification
1. **Rename Operations:**
   - `src/local_inference/` → `src/edge_runtime/`
   - `src/cloud_sync/` → `src/aws_control_plane/`
   - `models/cache/` → `models/`

2. **Import Path Updates:**
   - All files importing from `src.local_inference` → `src.edge_runtime`
   - All files importing from `src.cloud_sync` → `src.aws_control_plane`
   - Update model loading paths

3. **New Modules to Create:**
   - `src/pedagogy/` - Pedagogical Intelligence Engine
   - `src/persistence/` - Database persistence layer
   - `src/resilience/` - Backup, recovery, health monitoring

### Components to Preserve (No Changes)
- `src/embeddings/` - Keep structure and implementation
- `src/data_processing/` - Keep structure and implementation
- `frontend/` - Keep structure and implementation

---

## Section 3: Database Persistence Layer

### Current State (❌ NOT ALIGNED)
- In-memory storage using Python dictionaries
- `api_server.py` uses `active_tokens = {}` for sessions
- `state.chat_logs = []` for chat history
- Data lost on server restart
- Not production-ready

### Target State
- PostgreSQL database for persistent storage
- Tables: users, sessions, chat_history, subjects, books, topic_mastery, weak_areas, practice_questions
- Connection pooling (pool_size=10, max_overflow=20)
- Transaction support for data integrity
- Graceful degradation if database unavailable

### Gap Analysis
| Component | Current | Target | Status |
|-----------|---------|--------|--------|
| Session Storage | In-memory dict | PostgreSQL sessions table | ❌ |
| Chat History | In-memory list | PostgreSQL chat_history table | ❌ |
| User Management | Basic dict | PostgreSQL users table | ❌ |
| Subject Metadata | Hardcoded | PostgreSQL subjects table | ❌ |
| Book Tracking | None | PostgreSQL books table | ❌ |
| Connection Pooling | N/A | Required | ❌ |
| Data Persistence | Lost on restart | Survives restart | ❌ |

### Components Requiring Modification
1. **New Components to Create:**
   - `src/persistence/database_manager.py` - Core DB operations
   - `src/persistence/user_repository.py` - User CRUD
   - `src/persistence/session_repository.py` - Session management
   - `src/persistence/chat_history_repository.py` - Chat persistence
   - `src/persistence/subject_repository.py` - Subject management
   - `src/persistence/book_repository.py` - Book/VKP tracking
   - `src/persistence/cache_manager.py` - Redis/LRU caching

2. **Files to Modify:**
   - `api_server.py` - Replace in-memory storage with repositories
   - Authentication endpoints - Use SessionRepository
   - Chat endpoints - Use ChatHistoryRepository

3. **Database Schema:**
   - Create SQL schema file with all tables
   - Add indexes for performance
   - Add foreign key constraints

### Components to Preserve
- None (this is entirely new functionality)

---

## Section 4: Pedagogical Intelligence Engine

### Current State (❌ NOT ALIGNED)
- `src/local_inference/educational_validator.py` only validates content
- No topic mastery tracking
- No weak area detection
- No adaptive question generation
- No weekly reports for teachers
- System functions as chatbot, not learning support infrastructure

### Target State
- Comprehensive Pedagogical Intelligence Engine
- Topic mastery tracker (0.0 to 1.0 scale)
- Weak area detector (threshold < 0.4)
- Adaptive practice question generator
- Weekly summary reports for teachers
- Learning support infrastructure

### Gap Analysis
| Component | Current | Target | Status |
|-----------|---------|--------|--------|
| Topic Classification | None | Required | ❌ |
| Mastery Tracking | None | Per student, per topic | ❌ |
| Weak Area Detection | None | Automatic detection | ❌ |
| Question Generation | None | Adaptive difficulty | ❌ |
| Weekly Reports | None | Teacher summaries | ❌ |
| Mastery Database | None | PostgreSQL tables | ❌ |

### Components Requiring Modification
1. **New Components to Create:**
   - `src/pedagogy/mastery_tracker.py` - Track topic mastery
   - `src/pedagogy/weak_area_detector.py` - Identify weak areas
   - `src/pedagogy/adaptive_question_generator.py` - Generate practice questions
   - `src/pedagogy/weekly_report_generator.py` - Teacher reports

2. **Integration Points:**
   - Chat pipeline - Extract topic from questions
   - RAG pipeline - Update mastery after each query
   - API endpoints - Expose pedagogy features

3. **Database Tables:**
   - `topic_mastery` - Store mastery levels
   - `weak_areas` - Track identified weaknesses
   - `practice_questions` - Store generated questions

### Components to Preserve
- `src/local_inference/educational_validator.py` - Keep for content validation

---

## Section 5: Concurrency Management System

### Current State (❌ NOT ALIGNED)
- No queue management
- No thread limiting
- No concurrent request control
- No queue position tracking
- No load testing for 100-300 users
- Potential system overload under high load

### Target State
- Maximum 5 concurrent inference threads
- Async queue management using asyncio.Queue
- Token streaming for responses
- Queue position tracking
- Target latency: 3-8 seconds per response
- Stable performance for 100-300 concurrent students

### Gap Analysis
| Component | Current | Target | Status |
|-----------|---------|--------|--------|
| Thread Limiting | None | Max 5 concurrent | ❌ |
| Queue Management | None | Async queue | ❌ |
| Position Tracking | None | Return queue position | ❌ |
| Token Streaming | Unclear | SSE streaming | ⚠️ |
| Load Testing | None | 100-300 users validated | ❌ |
| Overflow Handling | None | HTTP 503 when full | ❌ |

### Components Requiring Modification
1. **New Components to Create:**
   - `src/edge_runtime/concurrency_manager.py` - Queue and semaphore
   - `src/edge_runtime/inference_request.py` - Request data structure
   - `src/edge_runtime/token_streamer.py` - SSE streaming

2. **Files to Modify:**
   - `api_server.py` - Integrate concurrency manager
   - `/api/chat` endpoint - Use queue system
   - Inference pipeline - Add streaming support

3. **Configuration:**
   - `MAX_CONCURRENT_THREADS = 5`
   - `MAX_QUEUE_SIZE = 1000`
   - `QUEUE_TIMEOUT = 300` seconds

### Components to Preserve
- Core inference logic in `src/edge_runtime/inference_engine.py`
- RAG pipeline in `src/edge_runtime/rag_pipeline.py`

---

## Section 6: VKP (Versioned Knowledge Package) System

### Current State (⚠️ PARTIAL IMPLEMENTATION)
- ETL pipeline exists in `src/data_processing/etl_pipeline.py`
- No VKP packaging format
- No version manifest
- No integrity checksum
- No delta update support
- No periodic pull mechanism

### Target State
- Standardized VKP format with JSON schema
- Version manifest (semantic versioning)
- SHA256 integrity checksum
- Delta update support (only changed chunks)
- Hourly periodic pull from S3
- Automatic ChromaDB update

### Gap Analysis
| Component | Current | Target | Status |
|-----------|---------|--------|--------|
| VKP Format | None | JSON with metadata | ❌ |
| Version Manifest | None | Semantic versioning | ❌ |
| Integrity Checksum | None | SHA256 | ❌ |
| Delta Updates | None | Only changed chunks | ❌ |
| Periodic Pull | None | Hourly cron job | ❌ |
| Version Comparison | None | Semantic version check | ❌ |

### Components Requiring Modification
1. **New Components to Create:**
   - `src/aws_control_plane/vkp_packager.py` - Create VKP packages
   - `src/aws_control_plane/vkp_puller.py` - Pull updates from S3
   - `src/aws_control_plane/vkp_version_manager.py` - Version tracking

2. **Files to Modify:**
   - `src/data_processing/etl_pipeline.py` - Output VKP format
   - Lambda function - Generate VKP packages

3. **Cron Jobs:**
   - Hourly VKP update check
   - Internet connectivity check
   - Offline mode handling

### Components to Preserve
- `src/data_processing/etl_pipeline.py` - Core ETL logic
- `src/data_processing/pdf_extractor.py` - PDF processing
- `src/data_processing/text_chunker.py` - Chunking logic

---

## Section 7: AWS Infrastructure

### Current State (⚠️ PARTIAL IMPLEMENTATION)
- S3 storage exists (`src/cloud_sync/s3_storage_manager.py`)
- CloudFront manager exists (`src/cloud_sync/cloudfront_manager.py`)
- No Lambda curriculum processor
- No DynamoDB tables
- No automated infrastructure setup
- No S3 event triggers

### Target State
- S3 buckets: nexusai-curriculum-raw, nexusai-vkp-packages, nexusai-model-distribution
- DynamoDB tables: nexusai-schools, nexusai-metrics
- Lambda function for curriculum processing
- S3 event trigger for Lambda
- CloudFront distribution for VKP delivery
- Automated setup script (idempotent)

### Gap Analysis
| Component | Current | Target | Status |
|-----------|---------|--------|--------|
| S3 Buckets | Partial | 3 buckets with versioning | ⚠️ |
| DynamoDB Tables | None | 2 tables | ❌ |
| Lambda Function | None | Curriculum processor | ❌ |
| S3 Event Trigger | None | Auto-trigger Lambda | ❌ |
| CloudFront | Exists | VKP distribution | ⚠️ |
| Setup Script | None | Idempotent boto3 script | ❌ |

### Components Requiring Modification
1. **New Components to Create:**
   - `scripts/setup_aws_infrastructure.py` - Automated setup
   - Lambda function code - Curriculum processing
   - DynamoDB schema definitions

2. **Files to Modify:**
   - `src/cloud_sync/s3_storage_manager.py` - Add bucket management
   - `src/cloud_sync/cloudfront_manager.py` - VKP distribution

3. **IAM Roles:**
   - Lambda execution role
   - School server S3 read role
   - Least-privilege policies

### Components to Preserve
- `src/cloud_sync/s3_storage_manager.py` - Core S3 operations
- `src/cloud_sync/cloudfront_manager.py` - CloudFront operations

---

## Section 8: Aggregated Telemetry System

### Current State (❌ NOT ALIGNED)
- `src/telemetry/` folder is empty
- No DynamoDB integration
- No aggregated metrics collection
- No anonymization mechanism
- No PII verification
- No periodic upload

### Target State
- Collect only anonymized metrics
- DynamoDB storage (nexusai-metrics table)
- Metrics: query count, latency, model version, error rate, storage usage
- NO chat content, NO user data, NO PII
- Hourly batch upload
- Offline queuing with retry

### Gap Analysis
| Component | Current | Target | Status |
|-----------|---------|--------|--------|
| Metrics Collection | None | Anonymized only | ❌ |
| DynamoDB Client | None | Required | ❌ |
| PII Verification | None | Pattern matching | ❌ |
| School ID Anonymization | None | SHA256 hash | ❌ |
| Batch Upload | None | Hourly | ❌ |
| Offline Queue | None | Local queue + retry | ❌ |

### Components Requiring Modification
1. **New Components to Create:**
   - `src/telemetry/telemetry_collector.py` - Collect metrics
   - `src/telemetry/metrics_aggregator.py` - Aggregate hourly
   - `src/telemetry/pii_verifier.py` - Verify no PII
   - `src/telemetry/telemetry_uploader.py` - Upload to DynamoDB

2. **Integration Points:**
   - API endpoints - Record query metrics
   - Error handlers - Record error metrics
   - System monitor - Record resource usage

3. **Cron Jobs:**
   - Hourly metrics aggregation
   - Hourly upload to DynamoDB
   - Retry failed uploads

### Components to Preserve
- None (entirely new functionality)

---

## Section 9: Resilience and Recovery Module

### Current State (❌ MINIMAL IMPLEMENTATION)
- Basic backup endpoint exists in `api_server.py`
- No weekly automation
- No rollback mechanism
- No health monitoring daemon
- No auto-restart service
- No backup retention policy

### Target State
- Weekly full backups (PostgreSQL + ChromaDB + config)
- Daily incremental backups
- Version rollback capability
- Health monitoring daemon (5-minute checks)
- Automatic restart on critical failures
- 28-day backup retention
- Systemd service integration

### Gap Analysis
| Component | Current | Target | Status |
|-----------|---------|--------|--------|
| Full Backup | Manual endpoint | Weekly automated | ⚠️ |
| Incremental Backup | None | Daily automated | ❌ |
| Rollback | None | Version rollback | ❌ |
| Health Monitor | None | Daemon (5-min checks) | ❌ |
| Auto-restart | None | Systemd integration | ❌ |
| Backup Retention | None | 28-day cleanup | ❌ |

### Components Requiring Modification
1. **New Components to Create:**
   - `src/resilience/backup_manager.py` - Backup operations
   - `src/resilience/backup_scheduler.py` - Cron automation
   - `src/resilience/health_monitor.py` - Health checks
   - `src/resilience/auto_restart_service.py` - Auto-restart
   - `src/resilience/version_manager.py` - Rollback support

2. **Systemd Services:**
   - `nexusai-api.service` - Main API service
   - `nexusai-health-monitor.service` - Health daemon

3. **Cron Jobs:**
   - Weekly full backup (Sunday 2 AM)
   - Daily incremental backup (Monday-Saturday 2 AM)
   - Backup cleanup (28-day retention)

### Components to Preserve
- Existing backup logic in `api_server.py` (enhance, don't replace)

---

## Section 10: Embedding Strategy Management

### Current State (⚠️ NEEDS CLARIFICATION)
- Multiple embedding clients exist:
  - `src/embeddings/bedrock_client.py` (AWS Bedrock)
  - `src/embeddings/local_embeddings_client.py` (Local)
  - `src/embeddings/chroma_manager.py` (Vector DB)
- No clear "default vs optional" mechanism
- No strategy manager
- No fallback logic

### Target State
- Default mode: AWS Bedrock (for curriculum processing)
- Optional sovereign mode: Local MiniLM quantized
- Strategy manager for switching
- Automatic fallback from AWS to local if unavailable
- Configuration-based strategy selection

### Gap Analysis
| Component | Current | Target | Status |
|-----------|---------|--------|--------|
| Strategy Manager | None | Required | ❌ |
| Default Strategy | Unclear | AWS Bedrock | ⚠️ |
| Fallback Logic | None | AWS → Local | ❌ |
| Configuration | None | Strategy selection | ❌ |
| Sovereign Mode | Exists | Needs integration | ⚠️ |

### Components Requiring Modification
1. **New Components to Create:**
   - `src/embeddings/embedding_strategy.py` - Abstract base class
   - `src/embeddings/bedrock_embedding_strategy.py` - AWS implementation
   - `src/embeddings/local_minilm_strategy.py` - Local implementation
   - `src/embeddings/embedding_strategy_manager.py` - Strategy selector

2. **Files to Modify:**
   - RAG pipeline - Use strategy manager
   - Configuration - Add strategy selection
   - ETL pipeline - Use strategy manager

3. **Configuration:**
   - `EMBEDDING_STRATEGY = "bedrock"` (default)
   - `SOVEREIGN_MODE = false`
   - `FALLBACK_TO_LOCAL = true`

### Components to Preserve
- `src/embeddings/bedrock_client.py` - Wrap in strategy
- `src/embeddings/local_embeddings_client.py` - Wrap in strategy
- `src/embeddings/chroma_manager.py` - Keep as-is

---

## Section 11: Caching Layer

### Current State (❌ NOT IMPLEMENTED)
- No Redis integration
- No caching mechanism
- No repeated question optimization
- No cache invalidation on VKP update

### Target State
- Optional Redis caching
- LRU fallback if Redis unavailable
- Cache repeated question responses
- TTL: 24 hours
- Cache hit < 500ms
- Invalidate cache on curriculum update

### Gap Analysis
| Component | Current | Target | Status |
|-----------|---------|--------|--------|
| Redis Client | None | Optional | ❌ |
| LRU Cache | None | Fallback | ❌ |
| Cache Key Generation | None | SHA256 hash | ❌ |
| TTL Management | None | 24 hours | ❌ |
| Cache Invalidation | None | On VKP update | ❌ |

### Components Requiring Modification
1. **New Components to Create:**
   - `src/persistence/cache_manager.py` - Cache operations
   - `src/persistence/redis_cache.py` - Redis implementation
   - `src/persistence/lru_cache.py` - In-memory fallback

2. **Integration Points:**
   - RAG pipeline - Check cache before query
   - VKP puller - Invalidate cache on update

3. **Configuration:**
   - `REDIS_URL` (optional)
   - `CACHE_TTL_SECONDS = 86400` (24 hours)
   - `LRU_MAX_SIZE = 1000`

### Components to Preserve
- None (entirely new functionality)

---

## Section 12: Documentation Updates

### Current State (⚠️ INCONSISTENT)
- Hardware specs inconsistent (4GB vs 16GB)
- No deployment guide
- No AWS setup guide
- No database schema documentation
- System architecture doc outdated
- No troubleshooting guide

### Target State
- All documentation reflects 16GB RAM minimum
- Comprehensive deployment guide
- AWS setup guide with step-by-step instructions
- Database schema documentation with ER diagram
- Updated system architecture documentation
- Troubleshooting guide with common issues

### Gap Analysis
| Document | Current | Target | Status |
|----------|---------|--------|--------|
| README.md | 4GB claim | 16GB minimum | ❌ |
| DEPLOYMENT.md | Missing | Required | ❌ |
| AWS_SETUP.md | Missing | Required | ❌ |
| DATABASE_SCHEMA.md | Missing | Required | ❌ |
| SYSTEM_ARCHITECTURE.md | Outdated | Updated | ⚠️ |
| TROUBLESHOOTING.md | Missing | Required | ❌ |

### Components Requiring Modification
1. **Files to Update:**
   - `README.md` - Hardware specs
   - `config/app_config.py` - Remove memory limit
   - `docs/SYSTEM_ARCHITECTURE.md` - Reflect new structure

2. **Files to Create:**
   - `docs/DEPLOYMENT.md` - Deployment instructions
   - `docs/AWS_SETUP.md` - AWS configuration
   - `docs/DATABASE_SCHEMA.md` - Schema documentation
   - `docs/TROUBLESHOOTING.md` - Common issues

### Components to Preserve
- Existing documentation structure
- Existing guides (enhance, don't replace)

---

## Section 13: Components to Preserve (No Changes)

The following components are aligned with the definitive architecture and should be preserved without modification during refactoring:

### ✅ Fully Aligned Components

1. **Core Inference Engine**
   - `src/local_inference/rag_pipeline.py` (will be renamed to `src/edge_runtime/rag_pipeline.py`)
   - `src/local_inference/inference_engine.py` (will be renamed to `src/edge_runtime/inference_engine.py`)
   - Implementation is correct, only folder rename needed

2. **Embedding Components**
   - `src/embeddings/chroma_manager.py` - ChromaDB operations
   - `src/embeddings/bedrock_client.py` - AWS Bedrock integration
   - Keep as-is, will be wrapped by strategy manager

3. **Data Processing Pipeline**
   - `src/data_processing/etl_pipeline.py` - Core ETL logic
   - `src/data_processing/pdf_extractor.py` - PDF processing
   - `src/data_processing/text_chunker.py` - Text chunking
   - `src/data_processing/metadata_manager.py` - Metadata handling
   - Keep as-is, will output VKP format

4. **Frontend**
   - `frontend/` directory structure
   - `frontend/index.html` - Main interface
   - `frontend/css/` - Styling
   - `frontend/js/` - Client-side logic
   - No changes required

5. **Model Storage**
   - `models/Llama-3.2-3B-Instruct-Q4_K_M.gguf` - LLM model
   - Model files remain unchanged
   - Only folder structure flattened (models/cache/ → models/)

6. **Configuration Templates**
   - `config/templates/` - Configuration templates
   - Keep as-is

7. **Scripts (Selective)**
   - `scripts/download_model.py` - Model download
   - `scripts/check_system_ready.py` - System checks
   - Keep as-is

### ⚠️ Components Requiring Only Import Path Updates

These components are functionally correct but need import path updates after folder renames:

1. **API Server**
   - `api_server.py` - Update imports from `src.local_inference` to `src.edge_runtime`
   - Update imports from `src.cloud_sync` to `src.aws_control_plane`

2. **Test Suite**
   - `tests/unit/` - Update import paths
   - `tests/integration/` - Update import paths
   - Test logic remains unchanged

3. **Examples**
   - `examples/rag_pipeline_example.py` - Update imports
   - `examples/graceful_degradation_example.py` - Update imports

### ❌ Components to Evaluate for Removal

These components are not mentioned in the definitive architecture:

1. **Optimization Module**
   - `src/optimization/` - Not in definitive architecture
   - Evaluate if needed or can be removed

2. **UI Module**
   - `src/ui/` - Duplicates `frontend/`?
   - Evaluate relationship with frontend

---

## Section 14: Phase-by-Phase Gap Summary

### Phase 0: Preparation and Audit ✅
- [x] Full system backup created
- [x] Test suite baseline recorded
- [-] Architecture audit checklist (this document)
- [~] Git branching strategy

### Phase 1: Folder Structure Alignment
**Gaps:**
- Rename `src/local_inference/` → `src/edge_runtime/`
- Rename `src/cloud_sync/` → `src/aws_control_plane/`
- Flatten `models/cache/` → `models/`
- Update all import paths

### Phase 2: Database Persistence Layer
**Gaps:**
- No PostgreSQL implementation
- No session persistence
- No chat history persistence
- No user management database
- No connection pooling

### Phase 3: AWS Infrastructure Setup
**Gaps:**
- No DynamoDB tables
- No Lambda curriculum processor
- No S3 event triggers
- No automated setup script

### Phase 4: VKP Packaging System
**Gaps:**
- No VKP format specification
- No version manifest
- No integrity checksum
- No delta update support

### Phase 5: VKP Pull Mechanism
**Gaps:**
- No periodic pull cron job
- No version comparison logic
- No ChromaDB extraction from VKP
- No offline mode handling

### Phase 6: Pedagogical Intelligence Engine
**Gaps:**
- No topic mastery tracking
- No weak area detection
- No adaptive question generation
- No weekly report generation

### Phase 7: Concurrency Management System
**Gaps:**
- No thread limiting (max 5)
- No async queue management
- No queue position tracking
- No load testing validation

### Phase 8: Aggregated Telemetry System
**Gaps:**
- No metrics collection
- No DynamoDB integration
- No PII verification
- No anonymization mechanism

### Phase 9: Resilience and Recovery Module
**Gaps:**
- No automated backup scheduling
- No version rollback capability
- No health monitoring daemon
- No auto-restart service

### Phase 10: Embedding Strategy Manager
**Gaps:**
- No strategy manager
- No default/optional mechanism
- No fallback logic
- No configuration-based selection

### Phase 11: Caching Layer
**Gaps:**
- No Redis integration
- No LRU fallback
- No cache invalidation
- No repeated question optimization

### Phase 12: Documentation Updates
**Gaps:**
- Hardware specs inconsistent
- Missing deployment guide
- Missing AWS setup guide
- Missing database schema docs
- Missing troubleshooting guide

### Phase 13: Testing, Validation, Deployment
**Gaps:**
- No Lambda processor implementation
- No privacy verification tests
- No offline operation tests
- No load testing suite
- No deployment package

---

## Section 15: Risk Assessment

### High-Risk Changes
1. **Database Migration** - Data loss risk if not handled carefully
2. **Folder Renames** - Import path breakage if not comprehensive
3. **Concurrency Changes** - Performance degradation if not tested

### Medium-Risk Changes
1. **VKP Format** - Backward compatibility with existing data
2. **Telemetry** - Privacy violations if PII not verified
3. **Caching** - Cache invalidation bugs

### Low-Risk Changes
1. **Documentation Updates** - No code impact
2. **Embedding Strategy** - Existing code can be wrapped
3. **Resilience Module** - Additive functionality

---

## Section 16: Success Criteria

The refactoring will be considered successful when:

### Alignment Metrics
- [ ] 100% folder structure alignment with definitive architecture
- [ ] All 20 requirements from requirements.md implemented
- [ ] All 35 correctness properties pass validation
- [ ] Test coverage > 70% for critical paths

### Functional Criteria
- [ ] PostgreSQL persistence operational (data survives restarts)
- [ ] Pedagogical engine tracks mastery and generates questions
- [ ] Concurrency limited to 5 threads with queue management
- [ ] VKP format implemented with versioning and checksums
- [ ] VKP pull mechanism runs hourly and updates ChromaDB
- [ ] AWS Lambda processes PDFs and generates VKPs
- [ ] Telemetry sends only anonymized metrics to DynamoDB
- [ ] Resilience module performs weekly backups and health monitoring

### Performance Criteria
- [ ] Load testing validates 100-300 concurrent user support
- [ ] Response latency 3-8 seconds for 90th percentile
- [ ] System operates 100% offline after initial setup
- [ ] Cache hit < 500ms for repeated questions

### Privacy Criteria
- [ ] Privacy audit confirms no PII sent to AWS
- [ ] Chat history stored only locally
- [ ] User data never transmitted to cloud
- [ ] Telemetry contains only anonymized metrics

### Documentation Criteria
- [ ] All documentation reflects 16GB RAM requirement
- [ ] Deployment guide complete and tested
- [ ] AWS setup guide complete
- [ ] Database schema documented
- [ ] Troubleshooting guide available

---

## Section 17: Next Steps

1. **Review this checklist** with the development team
2. **Prioritize gaps** based on risk and dependencies
3. **Begin Phase 1** (Folder Structure Alignment)
4. **Execute phases sequentially** with testing at each checkpoint
5. **Update this checklist** as gaps are addressed

---

**Document Status:** COMPLETE  
**Last Updated:** 2026-01-XX  
**Next Review:** After Phase 1 completion  
**Owner:** Development Team

