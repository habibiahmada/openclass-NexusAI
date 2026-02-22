# OpenClass Nexus AI - System Architecture

## Overview

OpenClass Nexus AI is a **Hybrid Orchestrated Edge AI System** designed for Indonesian education with 100% offline inference at schools, AWS control plane for orchestration, and privacy by architecture design. The system implements a "One School - One Sovereign AI Node" model where each school operates an independent, fully functional AI server that can run indefinitely without internet connectivity.

## Architecture Principles

- **Privacy by Architecture**: No student data, chat content, or PII ever leaves the school premises
- **100% Offline Inference**: All AI inference happens locally on school servers
- **Periodic Sync Only**: AWS control plane used only for curriculum updates and anonymized telemetry
- **Production Ready**: Persistent storage, backup/recovery, health monitoring, and auto-restart capabilities
- **Learning Support Infrastructure**: Not just a chatbot - tracks mastery, detects weak areas, generates adaptive practice

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER (Browser)                     │
│              Students/Teachers via School WiFi                  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP (LAN Only)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SCHOOL EDGE SERVER NODE                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Layer (FastAPI)                                     │  │
│  │  - Authentication & Session Management                   │  │
│  │  - Request Routing & Validation                          │  │
│  │  - Concurrency Manager (Max 5 threads)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Edge Runtime (src/edge_runtime/)                        │  │
│  │  - RAG Orchestrator                                      │  │
│  │  - LLM Inference Engine (Llama 3.2 3B Q4_K_M)           │  │
│  │  - Token Streaming                                       │  │
│  │  - Educational Validator                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Pedagogical Engine (src/pedagogy/)                      │  │
│  │  - Mastery Tracker                                       │  │
│  │  - Weak Area Detector                                    │  │
│  │  - Adaptive Question Generator                           │  │
│  │  - Weekly Report Generator                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Persistence Layer (src/persistence/)                    │  │
│  │  - PostgreSQL Database Manager                           │  │
│  │  - Session Store                                         │  │
│  │  - Chat History Store                                    │  │
│  │  - Cache Manager (Redis optional, LRU fallback)          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Data Layer                                              │  │
│  │  - ChromaDB (Vector Store)                               │  │
│  │  - PostgreSQL (Metadata, Users, Chat History)            │  │
│  │  - Local Model Storage (GGUF files)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Resilience Module (src/resilience/)                     │  │
│  │  - Backup Scheduler (Weekly full, Daily incremental)     │  │
│  │  - Health Monitor Daemon                                 │  │
│  │  - Version Manager (Rollback capability)                 │  │
│  │  - Auto-restart Service                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ Periodic Sync Only (Hourly)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              AWS NATIONAL CONTROL PLANE                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Curriculum Processing Pipeline                          │  │
│  │  - S3 (Raw PDF Storage)                                  │  │
│  │  - Lambda (ETL + Embedding Generation)                   │  │
│  │  - Bedrock Titan (Embedding Model)                       │  │
│  │  - VKP Packager (Versioning + Checksum)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Distribution Domain                                     │  │
│  │  - S3 (VKP Storage with Versioning)                      │  │
│  │  - CloudFront (CDN Distribution)                         │  │
│  │  - Signed URL Access                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Model Development Domain                                │  │
│  │  - SageMaker (Fine-tuning, Distillation)                 │  │
│  │  - Bedrock (Quality Benchmarking)                        │  │
│  │  - Model Distribution (S3 + CloudFront)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Telemetry Domain                                        │  │
│  │  - DynamoDB (Aggregated Metrics - Anonymized Only)       │  │
│  │  - CloudWatch (Lambda Logs)                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Edge Runtime (src/edge_runtime/)

The edge runtime handles 100% offline AI inference at the school level.

**Components:**
- **RAG Pipeline** (`rag_pipeline.py`): Orchestrates retrieval-augmented generation
- **Inference Engine** (`inference_engine.py`): Manages Llama 3.2 3B model inference
- **Token Streamer**: Streams LLM responses to clients in real-time
- **Educational Validator**: Ensures responses are curriculum-aligned

**Key Characteristics:**
- Fully offline operation after initial setup
- CPU-optimized (no GPU required)
- 3-8 second response latency target
- Supports 100-300 concurrent students

### 2. AWS Control Plane (src/aws_control_plane/)

The AWS infrastructure provides orchestration, curriculum processing, and distribution.

**Components:**
- **VKP Puller**: Periodically checks for curriculum updates (hourly)
- **Lambda Processor**: Converts PDFs to VKP packages with embeddings
- **Telemetry Uploader**: Sends anonymized metrics to DynamoDB
- **Infrastructure Setup**: Automated AWS resource provisioning

**Key Characteristics:**
- Used only for orchestration, not production inference
- Periodic sync model (not real-time)
- Privacy-preserving (no PII transmitted)
- Graceful offline degradation

### 3. Pedagogical Engine (src/pedagogy/)

Transforms the system from a chatbot to learning support infrastructure.

**Components:**
- **Mastery Tracker**: Tracks topic mastery per student (0.0-1.0 scale)
- **Weak Area Detector**: Identifies topics needing reinforcement
- **Adaptive Question Generator**: Creates practice questions targeting weak areas
- **Weekly Report Generator**: Produces teacher reports on student progress

**Key Characteristics:**
- Tracks mastery based on question frequency, complexity, and retention
- Detects weak areas (mastery < 0.4 or high question frequency)
- Adjusts difficulty: easy (< 0.3), medium (0.3-0.6), hard (≥ 0.6)
- Generates weekly summaries for teachers

### 4. Persistence Layer (src/persistence/)

Production-ready persistent storage replacing in-memory data structures.

**Components:**
- **Database Manager**: PostgreSQL connection pooling and transaction management
- **User Repository**: User CRUD operations with password hashing
- **Session Repository**: Session management with 24-hour expiration
- **Chat History Repository**: Persistent chat storage with pagination
- **Subject/Book Repository**: Dynamic curriculum metadata management
- **Cache Manager**: Redis caching with LRU fallback

**Key Characteristics:**
- Data survives server restarts
- Connection pooling (10 connections, 20 max overflow)
- Transaction support for data integrity
- Graceful degradation on database unavailability

### 5. Concurrency Manager (src/concurrency/)

Controls concurrent inference threads to maintain system stability under load.

**Components:**
- **Async Queue**: FIFO queue for inference requests
- **Semaphore**: Limits concurrent threads to 5
- **Queue Position Tracker**: Returns queue position to users
- **Token Streamer**: Server-Sent Events for response streaming

**Key Characteristics:**
- Maximum 5 concurrent inference threads
- Queue overflow handling (max 1000 requests)
- Queue position tracking for user feedback
- Target latency: 3-8 seconds per response

### 6. VKP System (Versioned Knowledge Package)

Standardized format for packaging, versioning, and distributing curriculum embeddings.

**Components:**
- **VKP Packager**: Creates VKP packages with embeddings and metadata
- **VKP Puller**: Downloads and installs curriculum updates
- **Version Manager**: Tracks versions and supports rollback
- **Integrity Verifier**: SHA256 checksum validation

**VKP Format:**
```json
{
  "version": "1.2.0",
  "subject": "matematika",
  "grade": 11,
  "semester": 1,
  "created_at": "2026-02-15T10:30:00Z",
  "embedding_model": "amazon.titan-embed-text-v1",
  "chunk_config": {
    "chunk_size": 800,
    "chunk_overlap": 100
  },
  "chunks": [...],
  "checksum": "sha256:abc123...",
  "total_chunks": 450
}
```

**Key Characteristics:**
- Semantic versioning (MAJOR.MINOR.PATCH)
- Delta updates (only changed content)
- Integrity verification (SHA256 checksum)
- Hourly update checks with offline fallback

### 7. Telemetry System (src/telemetry/)

Collects anonymized usage metrics for national monitoring without compromising privacy.

**Components:**
- **Telemetry Collector**: Records local metrics (query count, latency, errors)
- **Metrics Aggregator**: Aggregates hourly/daily metrics
- **PII Verifier**: Scans for and rejects any PII in telemetry data
- **Telemetry Uploader**: Batch uploads to DynamoDB with offline queuing

**Allowed Metrics (Anonymized Only):**
- Total query count, success/failure rates
- Average latency, p50/p90/p99 percentiles
- Model version, embedding model version
- Error rate and error types
- Storage usage (ChromaDB, PostgreSQL, disk)
- Active user count (no user IDs)
- Subjects queried (no chat content)

**Prohibited Data (Never Sent):**
- Chat content (questions or responses)
- User identifiers (usernames, names, IDs)
- Teacher identifiers
- School name or location
- IP addresses, session tokens
- Any personal information

### 8. Resilience Module (src/resilience/)

Ensures system reliability through automated backup, health monitoring, and recovery.

**Components:**
- **Backup Manager**: Creates full and incremental backups
- **Backup Scheduler**: Weekly full (Sunday 2 AM), daily incremental (Mon-Sat 2 AM)
- **Health Monitor**: Checks LLM, ChromaDB, PostgreSQL, disk, RAM every 5 minutes
- **Auto-Restart Service**: Attempts automatic recovery on critical failures
- **Version Manager**: Supports rollback to previous versions

**Backup Strategy:**
- Weekly full backup: PostgreSQL + ChromaDB + config + models
- Daily incremental: New chat history + VKP updates
- 28-day retention policy with automatic cleanup
- Optional compression and encryption
- Optional S3 upload for off-site backup

**Health Monitoring:**
- LLM status (test inference)
- ChromaDB connection
- PostgreSQL connection
- Disk space (warning at 80%, critical at 90%)
- RAM usage (warning at 80%, critical at 90%)
- Auto-restart on critical failures (max 3 attempts)

### 9. Embedding Strategy Manager (src/embeddings/)

Provides configurable embedding strategy with AWS Bedrock as default and local MiniLM as fallback.

**Strategies:**
- **Bedrock Titan** (default): 1536 dimensions, AWS-hosted
- **Local MiniLM** (optional): 384 dimensions, CPU-optimized

**Key Characteristics:**
- Configurable default strategy
- Automatic fallback to local on AWS unavailability
- Separate ChromaDB collections per strategy
- Migration support between strategies

### 10. Caching Layer (src/cache/)

Optional Redis caching for repeated questions to reduce CPU load and improve response time.

**Components:**
- **Redis Cache**: Primary cache with TTL support
- **LRU Cache**: In-memory fallback (max 1000 items)
- **Cache Key Generator**: SHA256 hash of question + subject + VKP version

**Key Characteristics:**
- 24-hour TTL for cached responses
- < 500ms cache hit latency
- Automatic invalidation on VKP updates
- Graceful fallback to LRU if Redis unavailable

## Data Flow Diagrams

### Student Query Flow (100% Offline)

```
┌─────────┐
│ Student │
│ Browser │
└────┬────┘
     │ 1. Submit Question
     ▼
┌─────────────────┐
│  API Server     │
│  (FastAPI)      │
└────┬────────────┘
     │ 2. Authenticate & Validate
     ▼
┌─────────────────┐
│ Concurrency     │
│ Manager         │◄─── Queue if > 5 concurrent
└────┬────────────┘
     │ 3. Enqueue Request
     ▼
┌─────────────────┐
│ Cache Manager   │
│ (Check Cache)   │
└────┬────────────┘
     │ 4. Cache Miss
     ▼
┌─────────────────┐
│ RAG Pipeline    │
│ (Edge Runtime)  │
└────┬────────────┘
     │ 5. Generate Embedding
     ▼
┌─────────────────┐
│ ChromaDB        │
│ (Vector Store)  │
└────┬────────────┘
     │ 6. Semantic Search (top-k)
     ▼
┌─────────────────┐
│ Context         │
│ Assembly        │
└────┬────────────┘
     │ 7. Build Prompt
     ▼
┌─────────────────┐
│ LLM Inference   │
│ (Llama 3.2 3B)  │
└────┬────────────┘
     │ 8. Generate Response (Token Streaming)
     ▼
┌─────────────────┐
│ Pedagogical     │
│ Engine          │
└────┬────────────┘
     │ 9. Update Mastery Tracking
     ▼
┌─────────────────┐
│ PostgreSQL      │
│ (Chat History)  │
└────┬────────────┘
     │ 10. Persist Chat
     ▼
┌─────────────────┐
│ Cache Manager   │
│ (Store Result)  │
└────┬────────────┘
     │ 11. Stream Response
     ▼
┌─────────┐
│ Student │
│ Browser │
└─────────┘
```

### Curriculum Update Flow (Periodic Sync)

```
┌─────────┐
│ Teacher │
│Dashboard│
└────┬────┘
     │ 1. Upload PDF
     ▼
┌─────────────────┐
│ School Server   │
│ (Temp Storage)  │
└────┬────────────┘
     │ 2. Upload to S3
     ▼
┌─────────────────┐
│ S3 Bucket       │
│ (Raw PDFs)      │
└────┬────────────┘
     │ 3. S3 Event Trigger
     ▼
┌─────────────────┐
│ Lambda Function │
│ (Processor)     │
└────┬────────────┘
     │ 4. Extract Text (pypdf)
     ▼
┌─────────────────┐
│ Text Chunker    │
│ (800/100)       │
└────┬────────────┘
     │ 5. Chunk Text
     ▼
┌─────────────────┐
│ Bedrock Titan   │
│ (Embeddings)    │
└────┬────────────┘
     │ 6. Generate Embeddings
     ▼
┌─────────────────┐
│ VKP Packager    │
│ (Lambda)        │
└────┬────────────┘
     │ 7. Package VKP (version, checksum, metadata)
     ▼
┌─────────────────┐
│ S3 Bucket       │
│ (VKP Packages)  │
└────┬────────────┘
     │ 8. Hourly Cron Check
     ▼
┌─────────────────┐
│ VKP Puller      │
│ (School Server) │
└────┬────────────┘
     │ 9. Compare Versions
     ▼
┌─────────────────┐
│ Download Delta  │
│ (Only New)      │
└────┬────────────┘
     │ 10. Verify Checksum
     ▼
┌─────────────────┐
│ ChromaDB        │
│ (Update)        │
└────┬────────────┘
     │ 11. Extract Embeddings
     ▼
┌─────────────────┐
│ PostgreSQL      │
│ (Metadata)      │◄─── 12. Update Version Info
└─────────────────┘
```

## Database Schema

### PostgreSQL Tables

**users**: User accounts (students, teachers, admins)
- id, username, password_hash, role, full_name, created_at, updated_at

**sessions**: Active user sessions with 24-hour expiration
- id, user_id, token, expires_at, created_at

**subjects**: Dynamic subject management
- id, grade, name, code, created_at

**books**: Curriculum book metadata with VKP versioning
- id, subject_id, title, filename, vkp_version, chunk_count, created_at

**chat_history**: Persistent chat storage
- id, user_id, subject_id, question, response, confidence, created_at

**topic_mastery**: Student mastery tracking per topic
- id, user_id, subject_id, topic, mastery_level, question_count, correct_count, last_interaction, created_at

**weak_areas**: Detected weak areas for targeted practice
- id, user_id, subject_id, topic, weakness_score, recommended_practice, detected_at

**practice_questions**: Adaptive practice question bank
- id, subject_id, topic, difficulty, question, answer, created_at

### ChromaDB Collections

**bedrock_embeddings**: Embeddings generated by AWS Bedrock Titan (1536 dimensions)
**local_embeddings**: Embeddings generated by local MiniLM (384 dimensions)

## Technology Stack

| Component | Technology | Version | Role |
|-----------|------------|---------|------|
| **Language** | Python | 3.9+ | Core logic |
| **API Framework** | FastAPI | Latest | REST API server |
| **LLM Model** | Llama 3.2 3B | Q4_K_M | Text generation (CPU-optimized) |
| **LLM Runtime** | llama.cpp | Latest | Inference engine |
| **Vector DB** | ChromaDB | Latest | Semantic search |
| **Database** | PostgreSQL | 12+ | Persistent storage |
| **Cache** | Redis | Latest | Optional response caching |
| **Embeddings** | AWS Bedrock Titan | v1 | Default embedding model |
| **Embeddings (Local)** | MiniLM-L6-v2 | Quantized | Optional local embeddings |
| **Cloud Storage** | AWS S3 | - | VKP distribution |
| **Serverless** | AWS Lambda | Python 3.11 | Curriculum processing |
| **Metrics** | DynamoDB | - | Anonymized telemetry |
| **CDN** | CloudFront | - | VKP delivery |

## Hardware Requirements

### School Server Specifications

**Minimum Requirements:**
- **RAM**: 16GB (not 4GB - updated specification)
- **CPU**: 8-core processor
- **Storage**: 512GB SSD
- **GPU**: Optional (not required - CPU-optimized)
- **Network**: 10 Mbps minimum for VKP updates
- **OS**: Ubuntu Server 20.04 LTS or later

**Resource Allocation:**
- LLM Model: ~4GB RAM (quantized)
- ChromaDB: ~2GB RAM
- PostgreSQL: ~2GB RAM
- System + API: ~2GB RAM
- Available: ~6GB RAM for overhead

## Performance Targets

### Response Time
- **Target**: 3-8 seconds for 90th percentile queries
- **Cache Hit**: < 500ms
- **Database Query**: < 100ms for 95th percentile

### Concurrency
- **Comfortable Load**: 100 concurrent students (16.7% utilization)
- **Acceptable Load**: 300 concurrent students (50% utilization)
- **Max Concurrent Threads**: 5 inference threads
- **Queue Capacity**: 1000 requests

### Reliability
- **Uptime**: 99.5% during school hours
- **Auto-Recovery**: 30 seconds for transient failures
- **Backup RPO**: 24 hours (recovery point objective)
- **Backup RTO**: 1 hour (recovery time objective)

### Accuracy
- **Curriculum Alignment**: > 85%
- **Response Quality**: Validated by educational content

## Security

### Authentication & Authorization
- Password hashing: SHA256
- Session expiration: 24 hours of inactivity
- Role-based access: siswa (student), guru (teacher), admin

### Data Protection
- **Local Storage Only**: All sensitive data stored in local PostgreSQL
- **No PII to AWS**: Architectural guarantee - no chat content or user data transmitted
- **Anonymized Telemetry**: One-way hashed school IDs, no user identifiers
- **Input Validation**: SQL injection prevention

### Network Security
- **LAN Only**: API server accessible only on school network
- **HTTPS**: All AWS API calls use HTTPS
- **Signed URLs**: CloudFront access control for VKP downloads

## Offline Operation

### Offline Capabilities
- **100% Functional**: All core features work without internet
- **Student Queries**: Fully offline using local LLM and ChromaDB
- **Authentication**: Local PostgreSQL authentication
- **Chat History**: Local persistence
- **Pedagogical Engine**: Local mastery tracking

### Offline Degradation
- **VKP Updates**: Queued for later when internet returns
- **Telemetry**: Queued locally, uploaded when online
- **AWS Fallback**: Automatic fallback to local embeddings if Bedrock unavailable

### Internet Required For
- Initial setup and model download
- Curriculum updates (VKP pull)
- Telemetry upload (optional)
- AWS Bedrock embeddings (optional - local fallback available)

## Deployment

### Installation
1. Check system requirements (16GB RAM, 8-core CPU, 512GB SSD)
2. Install PostgreSQL and configure database
3. Install Python dependencies from requirements.txt
4. Download LLM model (Llama 3.2 3B Q4_K_M)
5. Setup database schema and create admin user
6. Configure systemd services for auto-start
7. Verify installation and start services

### Systemd Services
- **nexusai-api.service**: Main API server
- **nexusai-health-monitor.service**: Health monitoring daemon
- **nexusai-backup.timer**: Backup scheduler
- **nexusai-vkp-puller.timer**: VKP update checker
- **nexusai-telemetry.timer**: Telemetry uploader

### Configuration Files
- **config/system_config.yaml**: System configuration
- **config/embedding_config.yaml**: Embedding strategy configuration
- **config/database_config.yaml**: Database connection settings
- **.env**: Environment variables (secrets, API keys)

## Monitoring & Observability

### Health Checks (Every 5 Minutes)
- LLM model status (test inference)
- ChromaDB connection
- PostgreSQL connection
- Disk space (warning at 80%, critical at 90%)
- RAM usage (warning at 80%, critical at 90%)

### Logging
- Application logs: `/var/log/nexusai/app.log`
- Error logs: `/var/log/nexusai/error.log`
- Health monitor logs: `/var/log/nexusai/health.log`
- Backup logs: `/var/log/nexusai/backup.log`

### Metrics (Local)
- Query count, success/failure rates
- Response latency (p50, p90, p99)
- Queue depth and wait times
- Cache hit rate
- Storage usage

### Metrics (AWS - Anonymized)
- Aggregated query counts per school
- Average latency across schools
- Error rate trends
- Model version adoption
- Storage usage distribution

## Troubleshooting

### Common Issues

**High Memory Usage**
- Check LLM model size (should be ~4GB)
- Clear cache: `cache_manager.clear()`
- Restart services: `systemctl restart nexusai-api`

**Slow Response Times**
- Check concurrent request count
- Verify disk space available
- Check ChromaDB index size
- Review cache hit rate

**Database Connection Errors**
- Verify PostgreSQL is running: `systemctl status postgresql`
- Check connection pool settings
- Review database logs: `/var/log/postgresql/`

**VKP Update Failures**
- Check internet connectivity
- Verify AWS credentials
- Check S3 bucket permissions
- Review VKP puller logs

**LLM Inference Failures**
- Verify model file exists and is not corrupted
- Check available RAM
- Review inference engine logs
- Attempt auto-restart: `systemctl restart nexusai-api`

## Future Enhancements

### Planned Features
- Multi-language support (beyond Indonesian)
- Advanced analytics dashboard for teachers
- Real-time collaboration features
- Mobile app for offline access
- Integration with external learning management systems

### Scalability Improvements
- GPU acceleration support (optional)
- Distributed inference across multiple nodes
- Advanced caching strategies
- Model quantization optimization

### Privacy Enhancements
- End-to-end encryption for backups
- Differential privacy for telemetry
- Zero-knowledge proof for authentication
- Federated learning for model improvements

## References

- **Definitive Architecture**: README_DEPLOYMENT_SCENARIOS.md
- **Architecture Analysis**: ARCHITECTURE_ANALYSIS.md
- **Development Strategy**: DEVELOPMENT_STRATEGY.md
- **Refactoring Roadmap**: REFACTORING_ROADMAP.md
- **Deployment Guide**: docs/DEPLOYMENT.md
- **AWS Setup Guide**: docs/AWS_SETUP.md
- **Database Schema**: docs/DATABASE_SCHEMA.md
- **Troubleshooting Guide**: docs/TROUBLESHOOTING.md
