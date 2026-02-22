# Design Document: Architecture Alignment Refactoring

## Overview

This design document provides the technical blueprint for refactoring the OpenClass Nexus AI codebase to align with the definitive architecture documented in README_DEPLOYMENT_SCENARIOS.md. The refactoring addresses critical gaps identified in ARCHITECTURE_ANALYSIS.md, moving from 40% alignment to 100% alignment with the Hybrid Orchestrated Edge AI architecture.

### Design Goals

1. Align folder structure with definitive architecture naming conventions
2. Implement persistent storage layer (PostgreSQL) replacing in-memory storage
3. Build pedagogical intelligence engine for learning support infrastructure
4. Implement concurrency management with async queue (max 5 threads)
5. Create VKP (Versioned Knowledge Package) format and distribution mechanism
6. Establish AWS Lambda curriculum processing pipeline
7. Implement aggregated telemetry system (anonymized metrics only)
8. Build resilience module (backup, recovery, health monitoring)
9. Maintain 100% offline operation after initial setup
10. Preserve privacy by architecture (no PII to AWS)

### Design Principles

- Incremental implementation (phase by phase)
- Backward compatibility maintained throughout
- No over-engineering - implement only what's specified
- Test-driven approach with validation at each phase
- Privacy by architecture, not policy
- Production-ready with persistence, recovery, and monitoring


## Architecture

### High-Level System Architecture

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


### Data Flow Diagrams

#### Student Query Flow (100% Offline)

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
│ RAG Pipeline    │
│ (Edge Runtime)  │
└────┬────────────┘
     │ 4. Generate Embedding
     ▼
┌─────────────────┐
│ ChromaDB        │
│ (Vector Store)  │
└────┬────────────┘
     │ 5. Semantic Search (top-k)
     ▼
┌─────────────────┐
│ Context         │
│ Assembly        │
└────┬────────────┘
     │ 6. Build Prompt
     ▼
┌─────────────────┐
│ LLM Inference   │
│ (Llama 3.2 3B)  │
└────┬────────────┘
     │ 7. Generate Response (Token Streaming)
     ▼
┌─────────────────┐
│ Pedagogical     │
│ Engine          │
└────┬────────────┘
     │ 8. Update Mastery Tracking
     ▼
┌─────────────────┐
│ PostgreSQL      │
│ (Chat History)  │
└────┬────────────┘
     │ 9. Persist Chat
     ▼
┌─────────┐
│ Student │
│ Browser │◄─── 10. Stream Response
└─────────┘
```

#### Curriculum Update Flow (Periodic Sync)

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


## Components and Interfaces

### 1. Folder Restructuring Module

#### Purpose
Safely rename folders to match definitive architecture naming conventions while preserving Git history and updating all import paths.

#### Components

**FolderRenamer**
- Responsibility: Execute Git-aware folder renames
- Interface:
  ```python
  class FolderRenamer:
      def rename_with_history(self, old_path: str, new_path: str) -> bool
      def verify_rename(self, new_path: str) -> bool
  ```

**ImportPathUpdater**
- Responsibility: Update all import statements across codebase
- Interface:
  ```python
  class ImportPathUpdater:
      def find_imports(self, old_module: str) -> List[str]
      def update_imports(self, old_module: str, new_module: str) -> int
      def verify_imports(self) -> bool
  ```

#### Folder Mapping
```
src/local_inference/     → src/edge_runtime/
src/cloud_sync/          → src/aws_control_plane/
models/cache/            → models/
```

#### Implementation Strategy
1. Use `git mv` for history preservation
2. Automated find/replace for import paths using regex
3. Verify all tests pass after each rename
4. Commit after each successful rename


### 2. Database Persistence Layer

#### Purpose
Replace in-memory storage with PostgreSQL for production-ready persistence of user data, sessions, chat history, and metadata.

#### Components

**DatabaseManager**
- Responsibility: Core database operations and connection management
- Interface:
  ```python
  class DatabaseManager:
      def __init__(self, connection_string: str)
      def get_connection(self) -> Connection
      def execute_query(self, query: str, params: dict) -> Result
      def execute_transaction(self, queries: List[Query]) -> bool
      def health_check(self) -> bool
  ```

**UserRepository**
- Responsibility: User CRUD operations
- Interface:
  ```python
  class UserRepository:
      def create_user(self, username: str, password_hash: str, role: str, full_name: str) -> User
      def get_user_by_username(self, username: str) -> Optional[User]
      def get_user_by_id(self, user_id: int) -> Optional[User]
      def update_user(self, user_id: int, updates: dict) -> bool
      def delete_user(self, user_id: int) -> bool
  ```

**SessionRepository**
- Responsibility: Session management
- Interface:
  ```python
  class SessionRepository:
      def create_session(self, user_id: int, token: str, expires_hours: int) -> Session
      def get_session_by_token(self, token: str) -> Optional[Session]
      def delete_session(self, token: str) -> bool
      def cleanup_expired_sessions(self) -> int
  ```

**ChatHistoryRepository**
- Responsibility: Chat history persistence
- Interface:
  ```python
  class ChatHistoryRepository:
      def save_chat(self, user_id: int, subject_id: int, question: str, 
                    response: str, confidence: float) -> ChatHistory
      def get_user_history(self, user_id: int, limit: int) -> List[ChatHistory]
      def get_subject_history(self, subject_id: int, limit: int) -> List[ChatHistory]
      def delete_old_history(self, days: int) -> int
  ```

**SubjectRepository**
- Responsibility: Dynamic subject management
- Interface:
  ```python
  class SubjectRepository:
      def create_subject(self, grade: int, name: str, code: str) -> Subject
      def get_all_subjects(self) -> List[Subject]
      def get_subjects_by_grade(self, grade: int) -> List[Subject]
      def update_subject(self, subject_id: int, updates: dict) -> bool
      def delete_subject(self, subject_id: int) -> bool
  ```

**BookRepository**
- Responsibility: Curriculum book metadata
- Interface:
  ```python
  class BookRepository:
      def create_book(self, subject_id: int, title: str, filename: str, 
                      vkp_version: str) -> Book
      def get_books_by_subject(self, subject_id: int) -> List[Book]
      def update_book_version(self, book_id: int, vkp_version: str) -> bool
      def get_book_by_version(self, vkp_version: str) -> Optional[Book]
  ```

**CacheManager**
- Responsibility: Optional Redis caching with LRU fallback
- Interface:
  ```python
  class CacheManager:
      def __init__(self, redis_url: Optional[str] = None)
      def get(self, key: str) -> Optional[str]
      def set(self, key: str, value: str, ttl_seconds: int) -> bool
      def delete(self, key: str) -> bool
      def invalidate_pattern(self, pattern: str) -> int
      def get_stats(self) -> CacheStats
  ```

#### Connection Pooling Configuration
```python
# PostgreSQL connection pool settings
POOL_SIZE = 10
MAX_OVERFLOW = 20
POOL_TIMEOUT = 30
POOL_RECYCLE = 3600
```

#### Graceful Degradation Strategy
```python
# If PostgreSQL unavailable:
1. Log error with stack trace
2. Return HTTP 503 Service Unavailable
3. Display user-friendly message: "Database temporarily unavailable"
4. Do NOT fallback to in-memory (data loss risk)
5. Health monitor attempts auto-restart
```


### 3. Pedagogical Intelligence Engine

#### Purpose
Transform the system from a chatbot to learning support infrastructure by tracking mastery, detecting weak areas, and generating adaptive practice questions.

#### Components

**MasteryTracker**
- Responsibility: Track topic mastery per student
- Interface:
  ```python
  class MasteryTracker:
      def classify_topic(self, question: str) -> str
      def update_mastery(self, user_id: int, subject_id: int, topic: str, 
                         question_complexity: float) -> float
      def get_mastery_level(self, user_id: int, subject_id: int, topic: str) -> float
      def get_all_mastery(self, user_id: int, subject_id: int) -> Dict[str, float]
  ```

**Mastery Scoring Algorithm**
```python
# Mastery level: 0.0 (novice) to 1.0 (expert)
# Factors:
# - Question frequency (more questions = lower mastery)
# - Question complexity (harder questions = higher mastery)
# - Time between questions (longer gaps = better retention)
# - Correct responses (if validation available)

def calculate_mastery(question_count: int, avg_complexity: float, 
                      retention_days: int) -> float:
    frequency_factor = 1.0 / (1.0 + question_count * 0.1)  # Diminishes with more questions
    complexity_factor = min(avg_complexity, 1.0)            # Capped at 1.0
    retention_factor = min(retention_days / 30.0, 1.0)      # Capped at 30 days
    
    mastery = (frequency_factor * 0.3 + 
               complexity_factor * 0.5 + 
               retention_factor * 0.2)
    
    return max(0.0, min(mastery, 1.0))
```

**WeakAreaDetector**
- Responsibility: Identify topics needing reinforcement
- Interface:
  ```python
  class WeakAreaDetector:
      def detect_weak_areas(self, user_id: int, subject_id: int, 
                            threshold: float = 0.4) -> List[WeakArea]
      def get_weakness_score(self, user_id: int, subject_id: int, topic: str) -> float
      def recommend_practice(self, weak_area: WeakArea) -> str
  ```

**Weak Area Detection Logic**
```python
# Weak area criteria:
# 1. Mastery level < 0.4 (threshold)
# 2. High question frequency (> 5 questions in 7 days)
# 3. Low complexity questions (avg < 0.5)
# 4. Short retention (< 3 days between questions)

def is_weak_area(mastery_level: float, question_count: int, 
                 avg_complexity: float, retention_days: int) -> bool:
    return (mastery_level < 0.4 or 
            (question_count > 5 and retention_days < 3) or
            (avg_complexity < 0.5 and question_count > 3))
```

**AdaptiveQuestionGenerator**
- Responsibility: Generate practice questions targeting weak areas
- Interface:
  ```python
  class AdaptiveQuestionGenerator:
      def generate_question(self, subject_id: int, topic: str, 
                            difficulty: str, mastery_level: float) -> Question
      def adjust_difficulty(self, mastery_level: float) -> str
      def get_practice_set(self, user_id: int, subject_id: int, count: int) -> List[Question]
  ```

**Difficulty Adjustment Strategy**
```python
# Difficulty levels: easy, medium, hard
# Based on mastery level:
# 0.0 - 0.3: easy (foundational concepts)
# 0.3 - 0.6: medium (application problems)
# 0.6 - 1.0: hard (complex scenarios)

def adjust_difficulty(mastery_level: float) -> str:
    if mastery_level < 0.3:
        return "easy"
    elif mastery_level < 0.6:
        return "medium"
    else:
        return "hard"
```

**WeeklyReportGenerator**
- Responsibility: Generate teacher reports on student progress
- Interface:
  ```python
  class WeeklyReportGenerator:
      def generate_report(self, user_id: int, subject_id: int, 
                          start_date: date, end_date: date) -> Report
      def get_class_summary(self, subject_id: int, grade: int) -> ClassSummary
      def export_report(self, report: Report, format: str) -> bytes
  ```

**Report Structure**
```python
# Weekly report includes:
# - Student name and grade
# - Subject and date range
# - Total questions asked
# - Topics covered with mastery levels
# - Weak areas identified
# - Recommended practice topics
# - Progress trend (improving/stable/declining)
# - Comparison to class average (optional)
```

#### Integration with Chat Pipeline
```python
# After each student query:
1. Extract topic from question using LLM or keyword matching
2. Calculate question complexity (length, keywords, context)
3. Update mastery tracker
4. Check for weak areas
5. Optionally suggest practice questions
6. Log interaction for weekly report
```


### 4. Concurrency Management System

#### Purpose
Control concurrent inference threads to maintain system stability under load from 100-300 active students.

#### Components

**ConcurrencyManager**
- Responsibility: Manage async queue and thread limiting
- Interface:
  ```python
  class ConcurrencyManager:
      def __init__(self, max_concurrent: int = 5)
      async def enqueue_request(self, request: InferenceRequest) -> str  # Returns queue_id
      async def process_queue(self) -> None
      def get_queue_position(self, queue_id: str) -> int
      def get_queue_stats(self) -> QueueStats
  ```

**InferenceRequest**
- Data structure for queued requests
- Structure:
  ```python
  @dataclass
  class InferenceRequest:
      queue_id: str
      user_id: int
      question: str
      subject_id: int
      context: List[str]
      timestamp: datetime
      priority: int = 0  # Future: priority queue support
  ```

**TokenStreamer**
- Responsibility: Stream LLM tokens to client
- Interface:
  ```python
  class TokenStreamer:
      async def stream_response(self, llm_output: Iterator[str]) -> AsyncIterator[str]
      def format_sse(self, token: str) -> str  # Server-Sent Events format
  ```

#### Queue Management Strategy

**Queue Data Structure**
```python
# Use asyncio.Queue for thread-safe operations
# FIFO (First In First Out) by default
# Future enhancement: Priority queue for teacher requests

from asyncio import Queue, Semaphore

class AsyncInferenceQueue:
    def __init__(self, max_concurrent: int = 5):
        self.queue = Queue()
        self.semaphore = Semaphore(max_concurrent)
        self.active_requests = {}
        self.completed_requests = {}
```

**Request Processing Flow**
```python
async def process_request(self, request: InferenceRequest):
    # 1. Acquire semaphore (blocks if 5 threads active)
    async with self.semaphore:
        # 2. Mark as active
        self.active_requests[request.queue_id] = request
        
        # 3. Execute inference
        try:
            response = await self.run_inference(request)
            
            # 4. Stream tokens
            async for token in response:
                yield token
                
        finally:
            # 5. Release and cleanup
            del self.active_requests[request.queue_id]
            self.completed_requests[request.queue_id] = datetime.now()
```

**Queue Position Tracking**
```python
def get_queue_position(self, queue_id: str) -> int:
    # Check if active
    if queue_id in self.active_requests:
        return 0  # Currently processing
    
    # Check if completed
    if queue_id in self.completed_requests:
        return -1  # Already completed
    
    # Calculate position in queue
    position = 0
    for item in list(self.queue._queue):
        if item.queue_id == queue_id:
            return position + len(self.active_requests)
        position += 1
    
    return -2  # Not found
```

#### Load Balancing Strategy

**Target Latency: 3-8 seconds per response**
```python
# Factors affecting latency:
# - Model inference time: ~2-5 seconds (Llama 3.2 3B Q4)
# - RAG retrieval time: ~0.5-1 second (ChromaDB)
# - Context assembly: ~0.2-0.5 seconds
# - Network overhead: ~0.3-0.5 seconds
# Total: 3-7 seconds (within target)

# If latency exceeds 8 seconds:
# 1. Check queue depth (> 20 = overload)
# 2. Check system resources (CPU > 90%, RAM > 14GB)
# 3. Return queue position to user
# 4. Suggest retry in X minutes
```

**Concurrent User Capacity**
```python
# With 5 concurrent threads and 5-second avg response time:
# Throughput = 5 threads / 5 seconds = 1 request/second = 60 requests/minute

# For 100 active students:
# If each student asks 1 question every 10 minutes:
# Load = 100 / 10 = 10 requests/minute
# Utilization = 10 / 60 = 16.7% (comfortable)

# For 300 active students:
# Load = 300 / 10 = 30 requests/minute
# Utilization = 30 / 60 = 50% (acceptable)

# Peak load (all students ask simultaneously):
# Queue depth = 300 - 5 = 295 requests
# Wait time for last request = 295 * 5 seconds = 24.6 minutes
# Mitigation: Stagger requests, priority queue, increase threads (if resources allow)
```

#### API Integration

**FastAPI Endpoint**
```python
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    # 1. Enqueue request
    queue_id = await concurrency_manager.enqueue_request(request)
    
    # 2. Return queue position
    position = concurrency_manager.get_queue_position(queue_id)
    
    # 3. Stream response when ready
    return StreamingResponse(
        concurrency_manager.stream_response(queue_id),
        media_type="text/event-stream"
    )
```


### 5. VKP (Versioned Knowledge Package) System

#### Purpose
Standardized format for packaging, versioning, and distributing curriculum embeddings with integrity verification.

#### Components

**VKPPackager**
- Responsibility: Create VKP packages from processed curriculum
- Interface:
  ```python
  class VKPPackager:
      def create_package(self, embeddings: List[Embedding], metadata: VKPMetadata) -> VKP
      def calculate_checksum(self, vkp: VKP) -> str
      def serialize(self, vkp: VKP) -> bytes
      def deserialize(self, data: bytes) -> VKP
  ```

**VKPPuller**
- Responsibility: Periodic check and download of VKP updates
- Interface:
  ```python
  class VKPPuller:
      def check_updates(self) -> List[VKPUpdate]
      def compare_versions(self, local_version: str, cloud_version: str) -> bool
      def download_vkp(self, vkp_key: str) -> VKP
      def verify_integrity(self, vkp: VKP) -> bool
      def extract_to_chromadb(self, vkp: VKP) -> bool
      def update_metadata(self, vkp: VKP) -> bool
  ```

**VKPVersionManager**
- Responsibility: Track installed versions and manage rollback
- Interface:
  ```python
  class VKPVersionManager:
      def get_installed_version(self, subject_code: str) -> Optional[str]
      def register_version(self, subject_code: str, version: str) -> bool
      def rollback_version(self, subject_code: str, target_version: str) -> bool
      def list_versions(self, subject_code: str) -> List[str]
  ```

#### VKP Format Specification

**JSON Schema**
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
  "chunks": [
    {
      "chunk_id": "mat_11_s1_001",
      "text": "Teorema Pythagoras menyatakan bahwa...",
      "embedding": [0.123, -0.456, 0.789, ...],  // 1536 dimensions for Titan
      "metadata": {
        "page": 15,
        "section": "Geometri",
        "topic": "Pythagoras"
      }
    },
    // ... more chunks
  ],
  "checksum": "sha256:abc123def456...",
  "total_chunks": 450,
  "source_files": ["Matematika_Kelas_11_Semester_1.pdf"]
}
```

**Checksum Calculation**
```python
import hashlib
import json

def calculate_checksum(vkp: dict) -> str:
    # Exclude checksum field itself
    vkp_copy = vkp.copy()
    vkp_copy.pop('checksum', None)
    
    # Serialize deterministically (sorted keys)
    vkp_json = json.dumps(vkp_copy, sort_keys=True)
    
    # Calculate SHA256
    checksum = hashlib.sha256(vkp_json.encode()).hexdigest()
    
    return f"sha256:{checksum}"
```

#### Delta Update Mechanism

**Version Comparison**
```python
def compare_versions(local: str, cloud: str) -> str:
    # Semantic versioning: MAJOR.MINOR.PATCH
    local_parts = [int(x) for x in local.split('.')]
    cloud_parts = [int(x) for x in cloud.split('.')]
    
    if cloud_parts > local_parts:
        return "update_available"
    elif cloud_parts == local_parts:
        return "up_to_date"
    else:
        return "local_newer"  # Shouldn't happen
```

**Delta Calculation**
```python
def calculate_delta(old_vkp: VKP, new_vkp: VKP) -> VKPDelta:
    # Compare chunk_ids
    old_ids = {chunk['chunk_id'] for chunk in old_vkp['chunks']}
    new_ids = {chunk['chunk_id'] for chunk in new_vkp['chunks']}
    
    # Identify changes
    added = new_ids - old_ids
    removed = old_ids - new_ids
    
    # Create delta package (only new/modified chunks)
    delta = {
        'version': new_vkp['version'],
        'base_version': old_vkp['version'],
        'added_chunks': [c for c in new_vkp['chunks'] if c['chunk_id'] in added],
        'removed_chunk_ids': list(removed),
        'metadata': new_vkp['metadata']
    }
    
    return delta
```

#### Periodic Pull Mechanism

**Cron Configuration**
```bash
# Linux crontab (runs every hour)
0 * * * * /usr/bin/python3 /opt/nexusai/src/aws_control_plane/vkp_puller.py

# Windows Task Scheduler
# Task: VKP Update Check
# Trigger: Daily, repeat every 1 hour
# Action: python.exe C:\NexusAI\src\aws_control_plane\vkp_puller.py
```

**Pull Workflow**
```python
async def pull_updates():
    # 1. Check internet connectivity
    if not check_internet():
        logger.info("Offline mode - skipping VKP check")
        return
    
    # 2. List VKP files in S3
    s3_vkps = list_s3_vkps()
    
    # 3. Compare with local versions
    for vkp_key in s3_vkps:
        subject_code = extract_subject_code(vkp_key)
        cloud_version = extract_version(vkp_key)
        local_version = version_manager.get_installed_version(subject_code)
        
        # 4. Download if newer
        if compare_versions(local_version, cloud_version) == "update_available":
            logger.info(f"Downloading {subject_code} v{cloud_version}")
            vkp = download_vkp(vkp_key)
            
            # 5. Verify integrity
            if verify_integrity(vkp):
                # 6. Extract to ChromaDB
                extract_to_chromadb(vkp)
                
                # 7. Update metadata
                update_metadata(vkp)
                
                logger.info(f"Updated {subject_code} to v{cloud_version}")
            else:
                logger.error(f"Integrity check failed for {vkp_key}")
```

#### S3 Storage Structure
```
s3://nexusai-vkp-packages/
├── matematika/
│   ├── kelas_10/
│   │   ├── v1.0.0.vkp
│   │   ├── v1.1.0.vkp
│   │   └── v1.2.0.vkp
│   ├── kelas_11/
│   │   └── v1.0.0.vkp
│   └── kelas_12/
│       └── v1.0.0.vkp
├── informatika/
│   ├── kelas_10/
│   │   └── v1.0.0.vkp
│   └── ...
└── manifest.json  # Global version manifest
```


### 6. AWS Lambda Curriculum Processing Pipeline

#### Purpose
Automated serverless pipeline for processing PDF curriculum into VKP packages with embeddings.

#### Components

**LambdaCurriculumProcessor**
- Responsibility: Main Lambda handler for PDF processing
- Interface:
  ```python
  def lambda_handler(event, context):
      # S3 event trigger
      bucket = event['Records'][0]['s3']['bucket']['name']
      key = event['Records'][0]['s3']['object']['key']
      
      # Process pipeline
      pdf_content = download_from_s3(bucket, key)
      text = extract_text(pdf_content)
      chunks = chunk_text(text)
      embeddings = generate_embeddings(chunks)
      vkp = package_vkp(embeddings, metadata)
      upload_vkp(vkp)
      
      return {'statusCode': 200, 'body': 'Success'}
  ```

**PDFTextExtractor**
- Responsibility: Extract text from PDF using pypdf
- Interface:
  ```python
  class PDFTextExtractor:
      def extract_text(self, pdf_bytes: bytes) -> str
      def extract_with_metadata(self, pdf_bytes: bytes) -> List[PageContent]
      def clean_text(self, text: str) -> str
  ```

**TextChunker**
- Responsibility: Chunk text with overlap
- Interface:
  ```python
  class TextChunker:
      def __init__(self, chunk_size: int = 800, overlap: int = 100)
      def chunk_text(self, text: str) -> List[Chunk]
      def chunk_with_metadata(self, pages: List[PageContent]) -> List[Chunk]
  ```

**BedrockEmbeddingGenerator**
- Responsibility: Generate embeddings using Bedrock Titan
- Interface:
  ```python
  class BedrockEmbeddingGenerator:
      def __init__(self, model_id: str = 'amazon.titan-embed-text-v1')
      def generate_embedding(self, text: str) -> List[float]
      def batch_generate(self, texts: List[str]) -> List[List[float]]
  ```

#### Lambda Function Configuration

**Runtime Environment**
```yaml
FunctionName: nexusai-curriculum-processor
Runtime: python3.11
Handler: lambda_function.lambda_handler
Timeout: 300  # 5 minutes
MemorySize: 1024  # 1GB RAM
Environment:
  Variables:
    BEDROCK_MODEL_ID: amazon.titan-embed-text-v1
    CHUNK_SIZE: 800
    CHUNK_OVERLAP: 100
    VKP_BUCKET: nexusai-vkp-packages
```

**IAM Permissions**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::nexusai-curriculum-raw/*",
        "arn:aws:s3:::nexusai-vkp-packages/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

#### Processing Pipeline

**Step 1: PDF Text Extraction**
```python
from pypdf import PdfReader
from io import BytesIO

def extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    text = ""
    
    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()
        # Clean extracted text
        page_text = clean_text(page_text)
        text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"
    
    return text

def clean_text(text: str) -> str:
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters (keep Indonesian)
    text = re.sub(r'[^\w\s\.,;:!?\-áéíóúÁÉÍÓÚ]', '', text)
    return text.strip()
```

**Step 2: Text Chunking**
```python
def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[dict]:
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = ' '.join(chunk_words)
        
        chunks.append({
            'chunk_id': f"chunk_{i // (chunk_size - overlap):04d}",
            'text': chunk_text,
            'start_word': i,
            'end_word': i + len(chunk_words)
        })
    
    return chunks
```

**Step 3: Embedding Generation**
```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def generate_embeddings(chunks: List[dict]) -> List[dict]:
    for chunk in chunks:
        # Call Bedrock Titan
        response = bedrock.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=json.dumps({'inputText': chunk['text']})
        )
        
        result = json.loads(response['body'].read())
        chunk['embedding'] = result['embedding']  # 1536 dimensions
    
    return chunks
```

**Step 4: VKP Packaging**
```python
def package_vkp(chunks: List[dict], metadata: dict) -> dict:
    vkp = {
        'version': metadata['version'],
        'subject': metadata['subject'],
        'grade': metadata['grade'],
        'semester': metadata.get('semester', 1),
        'created_at': datetime.utcnow().isoformat(),
        'embedding_model': 'amazon.titan-embed-text-v1',
        'chunk_config': {
            'chunk_size': 800,
            'chunk_overlap': 100
        },
        'chunks': chunks,
        'total_chunks': len(chunks),
        'source_files': [metadata['source_file']]
    }
    
    # Calculate checksum
    vkp['checksum'] = calculate_checksum(vkp)
    
    return vkp
```

**Step 5: S3 Upload**
```python
def upload_vkp(vkp: dict, bucket: str = 'nexusai-vkp-packages'):
    s3 = boto3.client('s3')
    
    # Generate S3 key
    key = f"{vkp['subject']}/kelas_{vkp['grade']}/v{vkp['version']}.vkp"
    
    # Upload
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(vkp),
        ContentType='application/json',
        Metadata={
            'version': vkp['version'],
            'subject': vkp['subject'],
            'grade': str(vkp['grade'])
        }
    )
    
    logger.info(f"Uploaded VKP: s3://{bucket}/{key}")
```

#### Error Handling

**CloudWatch Logging**
```python
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Processing logic
        logger.info(f"Processing: {event}")
        result = process_curriculum(event)
        logger.info(f"Success: {result}")
        return {'statusCode': 200, 'body': json.dumps(result)}
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        
        # Send SNS notification (optional)
        send_error_notification(e)
        
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
```

**Retry Strategy**
```python
# Lambda automatic retry for failures:
# - Asynchronous invocation: 2 retries
# - Event source mapping (S3): Retry until success or event expires

# Dead Letter Queue (DLQ) for failed events:
DeadLetterConfig:
  TargetArn: arn:aws:sqs:ap-southeast-1:ACCOUNT:nexusai-dlq
```

#### S3 Event Trigger Configuration

```json
{
  "LambdaFunctionConfigurations": [
    {
      "Id": "curriculum-processor-trigger",
      "LambdaFunctionArn": "arn:aws:lambda:ap-southeast-1:ACCOUNT:function:nexusai-curriculum-processor",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "prefix",
              "Value": "raw/"
            },
            {
              "Name": "suffix",
              "Value": ".pdf"
            }
          ]
        }
      }
    }
  ]
}
```


### 7. Aggregated Telemetry System

#### Purpose
Collect anonymized usage metrics for national monitoring without compromising student privacy.

#### Components

**TelemetryCollector**
- Responsibility: Collect local metrics
- Interface:
  ```python
  class TelemetryCollector:
      def record_query(self, latency: float, success: bool) -> None
      def record_error(self, error_type: str, error_message: str) -> None
      def get_metrics_snapshot(self) -> MetricsSnapshot
      def reset_metrics(self) -> None
  ```

**MetricsAggregator**
- Responsibility: Aggregate metrics for batch upload
- Interface:
  ```python
  class MetricsAggregator:
      def aggregate_hourly(self) -> AggregatedMetrics
      def aggregate_daily(self) -> AggregatedMetrics
      def get_storage_usage(self) -> StorageMetrics
  ```

**TelemetryUploader**
- Responsibility: Batch upload to DynamoDB
- Interface:
  ```python
  class TelemetryUploader:
      def upload_metrics(self, metrics: AggregatedMetrics) -> bool
      def queue_offline_metrics(self, metrics: AggregatedMetrics) -> None
      def retry_failed_uploads(self) -> int
  ```

**PIIVerifier**
- Responsibility: Verify no PII in telemetry data
- Interface:
  ```python
  class PIIVerifier:
      def verify_no_pii(self, data: dict) -> bool
      def scan_for_patterns(self, text: str) -> List[PIIMatch]
      def anonymize_school_id(self, school_id: str) -> str
  ```

#### Metrics Schema

**Allowed Metrics (Anonymized Only)**
```python
@dataclass
class AggregatedMetrics:
    school_id: str  # Anonymized hash
    timestamp: int  # Unix timestamp
    
    # Query metrics
    total_queries: int
    successful_queries: int
    failed_queries: int
    average_latency_ms: float
    p50_latency_ms: float
    p90_latency_ms: float
    p99_latency_ms: float
    
    # System metrics
    model_version: str
    embedding_model: str
    chromadb_version: str
    
    # Error metrics
    error_rate: float
    error_types: Dict[str, int]  # {"timeout": 5, "oom": 2}
    
    # Storage metrics
    chromadb_size_mb: float
    postgres_size_mb: float
    disk_usage_percent: float
    
    # Usage patterns (aggregated)
    active_users_count: int  # No user IDs
    subjects_queried: List[str]  # ["matematika", "informatika"]
    peak_concurrent_users: int
```

**Prohibited Data (Never Sent)**
```python
# NEVER include:
# - Chat content (questions or responses)
# - User identifiers (usernames, names, IDs)
# - Teacher identifiers
# - School name or location
# - IP addresses
# - Session tokens
# - Any personal information
```

#### DynamoDB Schema

**Table: nexusai-metrics**
```json
{
  "TableName": "nexusai-metrics",
  "KeySchema": [
    {"AttributeName": "school_id", "KeyType": "HASH"},
    {"AttributeName": "timestamp", "KeyType": "RANGE"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "school_id", "AttributeType": "S"},
    {"AttributeName": "timestamp", "AttributeType": "N"}
  ],
  "BillingMode": "PAY_PER_REQUEST",
  "TimeToLiveSpecification": {
    "Enabled": true,
    "AttributeName": "ttl"
  }
}
```

**Item Structure**
```json
{
  "school_id": "hash_abc123",
  "timestamp": 1705320000,
  "ttl": 1737456000,
  "total_queries": 1250,
  "successful_queries": 1230,
  "failed_queries": 20,
  "average_latency_ms": 4500,
  "p90_latency_ms": 6200,
  "model_version": "llama-3.2-3b-q4",
  "error_rate": 0.016,
  "active_users_count": 85,
  "subjects_queried": ["matematika", "informatika"],
  "disk_usage_percent": 45.2
}
```

#### PII Verification

**Verification Checks**
```python
class PIIVerifier:
    # Patterns to detect (and reject)
    PII_PATTERNS = [
        r'\b\d{16}\b',  # NIK (Indonesian ID)
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{3}-\d{3}-\d{4}\b',  # Phone
        r'\b(?:Nama|Name):\s*[A-Z][a-z]+',  # Name patterns
    ]
    
    def verify_no_pii(self, data: dict) -> bool:
        # Convert to JSON string
        data_str = json.dumps(data)
        
        # Check against patterns
        for pattern in self.PII_PATTERNS:
            if re.search(pattern, data_str):
                logger.error(f"PII detected: {pattern}")
                return False
        
        # Check for suspicious keys
        suspicious_keys = ['username', 'name', 'email', 'phone', 'address', 'nik']
        for key in suspicious_keys:
            if key in data_str.lower():
                logger.error(f"Suspicious key detected: {key}")
                return False
        
        return True
```

**School ID Anonymization**
```python
import hashlib

def anonymize_school_id(school_id: str) -> str:
    # One-way hash with salt
    salt = os.getenv('TELEMETRY_SALT', 'nexusai-2026')
    combined = f"{school_id}:{salt}"
    hashed = hashlib.sha256(combined.encode()).hexdigest()
    return f"school_{hashed[:16]}"
```

#### Batch Upload Strategy

**Upload Schedule**
```python
# Hourly aggregation and upload
# Cron: 0 * * * * (every hour at minute 0)

async def upload_telemetry():
    # 1. Aggregate last hour's metrics
    metrics = aggregator.aggregate_hourly()
    
    # 2. Verify no PII
    if not verifier.verify_no_pii(metrics.__dict__):
        logger.error("PII verification failed - aborting upload")
        return
    
    # 3. Check internet connectivity
    if not check_internet():
        logger.info("Offline - queuing metrics")
        uploader.queue_offline_metrics(metrics)
        return
    
    # 4. Upload to DynamoDB
    try:
        success = uploader.upload_metrics(metrics)
        if success:
            logger.info("Telemetry uploaded successfully")
        else:
            uploader.queue_offline_metrics(metrics)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        uploader.queue_offline_metrics(metrics)
    
    # 5. Retry queued metrics
    uploader.retry_failed_uploads()
```

**Offline Queue**
```python
# Store failed uploads locally
# File: data/telemetry_queue.json

class OfflineQueue:
    def __init__(self, queue_file: str = 'data/telemetry_queue.json'):
        self.queue_file = queue_file
    
    def enqueue(self, metrics: AggregatedMetrics):
        queue = self.load_queue()
        queue.append(metrics.__dict__)
        self.save_queue(queue)
    
    def dequeue_all(self) -> List[AggregatedMetrics]:
        queue = self.load_queue()
        metrics_list = [AggregatedMetrics(**m) for m in queue]
        self.clear_queue()
        return metrics_list
```

#### Monitoring Dashboard (AWS)

**CloudWatch Dashboard**
```python
# Metrics to visualize:
# - Total queries per school (aggregated)
# - Average latency across all schools
# - Error rate trends
# - Model version adoption
# - Storage usage distribution
# - Active schools count

# Alarms:
# - Error rate > 5% for any school
# - Average latency > 10 seconds
# - Disk usage > 80% for any school
```


### 8. Resilience and Recovery Module

#### Purpose
Ensure system reliability through automated backup, health monitoring, and recovery mechanisms.

#### Components

**BackupScheduler**
- Responsibility: Automated backup execution
- Interface:
  ```python
  class BackupScheduler:
      def schedule_weekly_full_backup(self) -> None
      def schedule_daily_incremental_backup(self) -> None
      def execute_backup(self, backup_type: str) -> BackupResult
      def cleanup_old_backups(self, retention_days: int = 28) -> int
  ```

**BackupManager**
- Responsibility: Backup creation and restoration
- Interface:
  ```python
  class BackupManager:
      def create_full_backup(self) -> BackupMetadata
      def create_incremental_backup(self, since: datetime) -> BackupMetadata
      def restore_backup(self, backup_id: str) -> bool
      def verify_backup_integrity(self, backup_id: str) -> bool
      def compress_backup(self, backup_path: str) -> str
      def encrypt_backup(self, backup_path: str, key: str) -> str
  ```

**HealthMonitor**
- Responsibility: System health monitoring daemon
- Interface:
  ```python
  class HealthMonitor:
      def check_llm_status(self) -> HealthStatus
      def check_chromadb_connection(self) -> HealthStatus
      def check_postgres_connection(self) -> HealthStatus
      def check_disk_space(self) -> HealthStatus
      def check_ram_usage(self) -> HealthStatus
      def run_health_checks(self) -> SystemHealth
  ```

**AutoRestartService**
- Responsibility: Automatic service recovery
- Interface:
  ```python
  class AutoRestartService:
      def detect_failure(self, service_name: str) -> bool
      def attempt_restart(self, service_name: str) -> bool
      def escalate_failure(self, service_name: str) -> None
  ```

**VersionManager**
- Responsibility: Version rollback capability
- Interface:
  ```python
  class VersionManager:
      def get_current_version(self) -> str
      def list_available_versions(self) -> List[str]
      def rollback_to_version(self, version: str) -> bool
      def create_version_snapshot(self) -> str
  ```

#### Backup Strategy

**Weekly Full Backup**
```python
# Cron: 0 2 * * 0 (Sunday 2 AM)

def create_full_backup():
    backup_id = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir = f"/backups/{backup_id}"
    
    # 1. Backup PostgreSQL
    pg_dump_cmd = f"pg_dump -U nexusai nexusai_school > {backup_dir}/postgres.sql"
    subprocess.run(pg_dump_cmd, shell=True, check=True)
    
    # 2. Backup ChromaDB
    shutil.copytree('/data/vector_db', f"{backup_dir}/vector_db")
    
    # 3. Backup configuration
    shutil.copytree('/config', f"{backup_dir}/config")
    
    # 4. Backup models (if changed)
    shutil.copytree('/models', f"{backup_dir}/models")
    
    # 5. Create metadata
    metadata = {
        'backup_id': backup_id,
        'type': 'full',
        'timestamp': datetime.now().isoformat(),
        'size_mb': get_directory_size(backup_dir),
        'components': ['postgres', 'chromadb', 'config', 'models']
    }
    
    with open(f"{backup_dir}/metadata.json", 'w') as f:
        json.dump(metadata, f)
    
    # 6. Compress
    compressed = compress_backup(backup_dir)
    
    # 7. Optional: Encrypt
    if os.getenv('BACKUP_ENCRYPTION_ENABLED', 'false') == 'true':
        encrypted = encrypt_backup(compressed)
    
    # 8. Optional: Upload to S3
    if os.getenv('BACKUP_S3_ENABLED', 'false') == 'true':
        upload_to_s3(compressed, 'nexusai-backups')
    
    logger.info(f"Full backup completed: {backup_id}")
    return backup_id
```

**Daily Incremental Backup**
```python
# Cron: 0 2 * * 1-6 (Monday-Saturday 2 AM)

def create_incremental_backup():
    backup_id = f"incr_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir = f"/backups/{backup_id}"
    
    # Get last backup timestamp
    last_backup = get_last_backup_timestamp()
    
    # 1. Backup PostgreSQL (only new chat history)
    pg_dump_cmd = f"""
    pg_dump -U nexusai nexusai_school \
        --table=chat_history \
        --where="created_at > '{last_backup}'" \
        > {backup_dir}/postgres_incremental.sql
    """
    subprocess.run(pg_dump_cmd, shell=True, check=True)
    
    # 2. Backup ChromaDB (only if VKP updated)
    if check_vkp_updated_since(last_backup):
        shutil.copytree('/data/vector_db', f"{backup_dir}/vector_db")
    
    # 3. Create metadata
    metadata = {
        'backup_id': backup_id,
        'type': 'incremental',
        'base_backup': get_last_full_backup_id(),
        'timestamp': datetime.now().isoformat(),
        'since': last_backup.isoformat()
    }
    
    with open(f"{backup_dir}/metadata.json", 'w') as f:
        json.dump(metadata, f)
    
    # 4. Compress
    compressed = compress_backup(backup_dir)
    
    logger.info(f"Incremental backup completed: {backup_id}")
    return backup_id
```

**Backup Retention Policy**
```python
def cleanup_old_backups(retention_days: int = 28):
    backup_dir = '/backups'
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    deleted_count = 0
    for backup_folder in os.listdir(backup_dir):
        backup_path = os.path.join(backup_dir, backup_folder)
        
        # Read metadata
        metadata_path = os.path.join(backup_path, 'metadata.json')
        if not os.path.exists(metadata_path):
            continue
        
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        backup_date = datetime.fromisoformat(metadata['timestamp'])
        
        # Delete if older than retention period
        if backup_date < cutoff_date:
            shutil.rmtree(backup_path)
            deleted_count += 1
            logger.info(f"Deleted old backup: {backup_folder}")
    
    return deleted_count
```

#### Health Monitoring

**Health Check Daemon**
```python
# Systemd service: nexusai-health-monitor.service
# Runs every 5 minutes

class HealthMonitor:
    def __init__(self):
        self.checks = [
            self.check_llm_status,
            self.check_chromadb_connection,
            self.check_postgres_connection,
            self.check_disk_space,
            self.check_ram_usage
        ]
    
    def run_health_checks(self) -> SystemHealth:
        results = {}
        
        for check in self.checks:
            try:
                status = check()
                results[check.__name__] = status
            except Exception as e:
                results[check.__name__] = HealthStatus(
                    healthy=False,
                    message=str(e)
                )
        
        # Determine overall health
        all_healthy = all(r.healthy for r in results.values())
        critical_failures = [k for k, v in results.items() 
                             if not v.healthy and v.critical]
        
        return SystemHealth(
            healthy=all_healthy,
            checks=results,
            critical_failures=critical_failures,
            timestamp=datetime.now()
        )
    
    def check_llm_status(self) -> HealthStatus:
        try:
            # Test inference
            response = llm_engine.generate("test", max_tokens=5)
            return HealthStatus(healthy=True, message="LLM operational")
        except Exception as e:
            return HealthStatus(
                healthy=False,
                critical=True,
                message=f"LLM failure: {e}"
            )
    
    def check_chromadb_connection(self) -> HealthStatus:
        try:
            # Test query
            chroma_manager.health_check()
            return HealthStatus(healthy=True, message="ChromaDB connected")
        except Exception as e:
            return HealthStatus(
                healthy=False,
                critical=True,
                message=f"ChromaDB failure: {e}"
            )
    
    def check_postgres_connection(self) -> HealthStatus:
        try:
            # Test query
            db_manager.health_check()
            return HealthStatus(healthy=True, message="PostgreSQL connected")
        except Exception as e:
            return HealthStatus(
                healthy=False,
                critical=True,
                message=f"PostgreSQL failure: {e}"
            )
    
    def check_disk_space(self) -> HealthStatus:
        usage = psutil.disk_usage('/')
        percent_used = usage.percent
        
        if percent_used > 90:
            return HealthStatus(
                healthy=False,
                critical=True,
                message=f"Disk usage critical: {percent_used}%"
            )
        elif percent_used > 80:
            return HealthStatus(
                healthy=True,
                warning=True,
                message=f"Disk usage high: {percent_used}%"
            )
        else:
            return HealthStatus(
                healthy=True,
                message=f"Disk usage normal: {percent_used}%"
            )
    
    def check_ram_usage(self) -> HealthStatus:
        memory = psutil.virtual_memory()
        percent_used = memory.percent
        
        if percent_used > 90:
            return HealthStatus(
                healthy=False,
                critical=True,
                message=f"RAM usage critical: {percent_used}%"
            )
        elif percent_used > 80:
            return HealthStatus(
                healthy=True,
                warning=True,
                message=f"RAM usage high: {percent_used}%"
            )
        else:
            return HealthStatus(
                healthy=True,
                message=f"RAM usage normal: {percent_used}%"
            )
```

**Auto-Restart Logic**
```python
class AutoRestartService:
    MAX_RESTART_ATTEMPTS = 3
    RESTART_COOLDOWN = 300  # 5 minutes
    
    def __init__(self):
        self.restart_history = {}
    
    def attempt_restart(self, service_name: str) -> bool:
        # Check restart history
        if service_name in self.restart_history:
            last_restart, attempt_count = self.restart_history[service_name]
            
            # Check cooldown
            if (datetime.now() - last_restart).seconds < self.RESTART_COOLDOWN:
                logger.warning(f"Restart cooldown active for {service_name}")
                return False
            
            # Check max attempts
            if attempt_count >= self.MAX_RESTART_ATTEMPTS:
                logger.error(f"Max restart attempts reached for {service_name}")
                self.escalate_failure(service_name)
                return False
        
        # Attempt restart
        try:
            if service_name == 'api_server':
                subprocess.run(['systemctl', 'restart', 'nexusai-api'], check=True)
            elif service_name == 'chromadb':
                subprocess.run(['systemctl', 'restart', 'chromadb'], check=True)
            elif service_name == 'postgres':
                subprocess.run(['systemctl', 'restart', 'postgresql'], check=True)
            
            # Update history
            current_count = self.restart_history.get(service_name, (None, 0))[1]
            self.restart_history[service_name] = (datetime.now(), current_count + 1)
            
            logger.info(f"Successfully restarted {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart {service_name}: {e}")
            return False
    
    def escalate_failure(self, service_name: str):
        # Send alert (email, SMS, etc.)
        logger.critical(f"CRITICAL: {service_name} failed after max restart attempts")
        
        # Optional: Send notification
        # send_admin_notification(f"Service {service_name} requires manual intervention")
```

#### Version Rollback

**Rollback Mechanism**
```python
class VersionManager:
    def rollback_to_version(self, version: str) -> bool:
        # 1. Verify version exists
        if not self.version_exists(version):
            logger.error(f"Version {version} not found")
            return False
        
        # 2. Create snapshot of current state
        current_snapshot = self.create_version_snapshot()
        logger.info(f"Created snapshot: {current_snapshot}")
        
        # 3. Stop services
        self.stop_services()
        
        # 4. Restore backup
        backup_id = self.get_backup_for_version(version)
        backup_manager.restore_backup(backup_id)
        
        # 5. Update version metadata
        self.set_current_version(version)
        
        # 6. Restart services
        self.start_services()
        
        # 7. Verify health
        health = health_monitor.run_health_checks()
        if not health.healthy:
            logger.error("Rollback health check failed - reverting")
            self.rollback_to_version(current_snapshot)
            return False
        
        logger.info(f"Successfully rolled back to version {version}")
        return True
```


### 9. Embedding Strategy Manager

#### Purpose
Provide configurable embedding strategy with AWS Bedrock as default and local MiniLM as optional fallback.

#### Components

**EmbeddingStrategyManager**
- Responsibility: Manage embedding strategy selection and fallback
- Interface:
  ```python
  class EmbeddingStrategyManager:
      def __init__(self, config: EmbeddingConfig)
      def get_strategy(self) -> EmbeddingStrategy
      def set_strategy(self, strategy_name: str) -> bool
      def fallback_to_local(self) -> bool
  ```

**EmbeddingStrategy (Abstract)**
- Responsibility: Define embedding interface
- Interface:
  ```python
  class EmbeddingStrategy(ABC):
      @abstractmethod
      def generate_embedding(self, text: str) -> List[float]
      
      @abstractmethod
      def batch_generate(self, texts: List[str]) -> List[List[float]]
      
      @abstractmethod
      def get_dimension(self) -> int
      
      @abstractmethod
      def health_check(self) -> bool
  ```

**BedrockEmbeddingStrategy**
- Responsibility: AWS Bedrock Titan embeddings
- Interface:
  ```python
  class BedrockEmbeddingStrategy(EmbeddingStrategy):
      def __init__(self, model_id: str = 'amazon.titan-embed-text-v1')
      def generate_embedding(self, text: str) -> List[float]  # 1536 dimensions
      def batch_generate(self, texts: List[str]) -> List[List[float]]
      def get_dimension(self) -> int  # Returns 1536
      def health_check(self) -> bool
  ```

**LocalMiniLMStrategy**
- Responsibility: Local MiniLM quantized embeddings
- Interface:
  ```python
  class LocalMiniLMStrategy(EmbeddingStrategy):
      def __init__(self, model_path: str = './models/minilm-l6-v2-q4.gguf')
      def generate_embedding(self, text: str) -> List[float]  # 384 dimensions
      def batch_generate(self, texts: List[str]) -> List[List[float]]
      def get_dimension(self) -> int  # Returns 384
      def health_check(self) -> bool
  ```

#### Strategy Selection Logic

**Configuration**
```yaml
# config/embedding_config.yaml
embedding:
  default_strategy: bedrock  # or 'local'
  fallback_enabled: true
  
  bedrock:
    model_id: amazon.titan-embed-text-v1
    region: us-east-1
    timeout: 30
  
  local:
    model_path: ./models/minilm-l6-v2-q4.gguf
    n_threads: 4
```

**Strategy Manager Implementation**
```python
class EmbeddingStrategyManager:
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.current_strategy = None
        self.strategies = {
            'bedrock': BedrockEmbeddingStrategy(config.bedrock),
            'local': LocalMiniLMStrategy(config.local)
        }
        
        # Initialize default strategy
        self.set_strategy(config.default_strategy)
    
    def get_strategy(self) -> EmbeddingStrategy:
        # Check if current strategy is healthy
        if not self.current_strategy.health_check():
            logger.warning(f"Current strategy unhealthy, attempting fallback")
            if self.config.fallback_enabled:
                self.fallback_to_local()
        
        return self.current_strategy
    
    def set_strategy(self, strategy_name: str) -> bool:
        if strategy_name not in self.strategies:
            logger.error(f"Unknown strategy: {strategy_name}")
            return False
        
        self.current_strategy = self.strategies[strategy_name]
        logger.info(f"Embedding strategy set to: {strategy_name}")
        return True
    
    def fallback_to_local(self) -> bool:
        if self.current_strategy == self.strategies['local']:
            logger.error("Already using local strategy, cannot fallback")
            return False
        
        logger.info("Falling back to local embedding strategy")
        self.current_strategy = self.strategies['local']
        return True
```

#### Dimension Compatibility

**Challenge: Different Embedding Dimensions**
```python
# Bedrock Titan: 1536 dimensions
# Local MiniLM: 384 dimensions

# Solution: Separate ChromaDB collections per strategy
# - bedrock_embeddings (1536d)
# - local_embeddings (384d)

# When switching strategies:
# 1. Check if embeddings exist for target strategy
# 2. If not, re-embed curriculum using new strategy
# 3. Update ChromaDB collection
```

**Migration Strategy**
```python
def migrate_embeddings(from_strategy: str, to_strategy: str):
    logger.info(f"Migrating embeddings: {from_strategy} -> {to_strategy}")
    
    # 1. Get all documents from old collection
    old_collection = chroma_manager.get_collection(f"{from_strategy}_embeddings")
    documents = old_collection.get()
    
    # 2. Re-embed using new strategy
    new_strategy = strategy_manager.strategies[to_strategy]
    new_embeddings = new_strategy.batch_generate(documents['texts'])
    
    # 3. Create new collection
    new_collection = chroma_manager.create_collection(f"{to_strategy}_embeddings")
    
    # 4. Add to new collection
    new_collection.add(
        embeddings=new_embeddings,
        documents=documents['texts'],
        metadatas=documents['metadatas'],
        ids=documents['ids']
    )
    
    logger.info(f"Migration complete: {len(documents['texts'])} documents")
```

### 10. Caching Layer

#### Purpose
Optional Redis caching for repeated questions to reduce CPU load and improve response time.

#### Components

**CacheManager**
- Responsibility: Manage cache operations with Redis/LRU fallback
- Interface:
  ```python
  class CacheManager:
      def __init__(self, redis_url: Optional[str] = None)
      def get(self, key: str) -> Optional[str]
      def set(self, key: str, value: str, ttl_seconds: int = 86400) -> bool
      def delete(self, key: str) -> bool
      def invalidate_pattern(self, pattern: str) -> int
      def get_stats(self) -> CacheStats
  ```

**RedisCache**
- Responsibility: Redis-based caching
- Interface:
  ```python
  class RedisCache:
      def __init__(self, redis_url: str)
      def get(self, key: str) -> Optional[str]
      def set(self, key: str, value: str, ttl: int) -> bool
      def delete(self, key: str) -> bool
      def flush_pattern(self, pattern: str) -> int
  ```

**LRUCache**
- Responsibility: In-memory LRU fallback
- Interface:
  ```python
  class LRUCache:
      def __init__(self, max_size: int = 1000)
      def get(self, key: str) -> Optional[str]
      def set(self, key: str, value: str) -> bool
      def evict_oldest(self) -> None
  ```

#### Cache Key Generation

**Question Hash**
```python
import hashlib

def generate_cache_key(question: str, subject_id: int, vkp_version: str) -> str:
    # Normalize question (lowercase, strip whitespace)
    normalized = question.lower().strip()
    
    # Include subject and version in key
    key_input = f"{normalized}:{subject_id}:{vkp_version}"
    
    # Generate hash
    hash_value = hashlib.sha256(key_input.encode()).hexdigest()
    
    return f"cache:response:{hash_value}"
```

#### Cache Invalidation

**On VKP Update**
```python
def invalidate_cache_on_vkp_update(subject_id: int, new_version: str):
    # Invalidate all cached responses for this subject
    pattern = f"cache:response:*:{subject_id}:*"
    deleted_count = cache_manager.invalidate_pattern(pattern)
    
    logger.info(f"Invalidated {deleted_count} cached responses for subject {subject_id}")
```

**TTL Strategy**
```python
# Default TTL: 24 hours (86400 seconds)
# Rationale:
# - Curriculum doesn't change frequently
# - 24 hours balances freshness and cache hit rate
# - Automatic expiration prevents stale data

CACHE_TTL = 86400  # 24 hours
```

#### Cache Integration

**RAG Pipeline Integration**
```python
async def query_with_cache(question: str, subject_id: int) -> str:
    # 1. Generate cache key
    vkp_version = get_current_vkp_version(subject_id)
    cache_key = generate_cache_key(question, subject_id, vkp_version)
    
    # 2. Check cache
    cached_response = cache_manager.get(cache_key)
    if cached_response:
        logger.info(f"Cache hit: {cache_key}")
        return cached_response
    
    # 3. Cache miss - run RAG pipeline
    logger.info(f"Cache miss: {cache_key}")
    response = await rag_pipeline.query(question, subject_id)
    
    # 4. Store in cache
    cache_manager.set(cache_key, response, ttl_seconds=CACHE_TTL)
    
    return response
```


## Data Models

### Database Schema (PostgreSQL)

#### Entity Relationship Diagram

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │
│ username        │◄──────┐
│ password_hash   │       │
│ role            │       │
│ full_name       │       │
│ created_at      │       │
│ updated_at      │       │
└─────────────────┘       │
         │                │
         │                │
         ▼                │
┌─────────────────┐       │
│    sessions     │       │
├─────────────────┤       │
│ id (PK)         │       │
│ user_id (FK)    │───────┘
│ token           │
│ expires_at      │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│    subjects     │
├─────────────────┤
│ id (PK)         │◄──────┐
│ grade           │       │
│ name            │       │
│ code            │       │
│ created_at      │       │
└─────────────────┘       │
         │                │
         │                │
         ▼                │
┌─────────────────┐       │
│     books       │       │
├─────────────────┤       │
│ id (PK)         │       │
│ subject_id (FK) │───────┘
│ title           │
│ filename        │
│ vkp_version     │
│ chunk_count     │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│  chat_history   │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │───────┐
│ subject_id (FK) │───────┼───┐
│ question        │       │   │
│ response        │       │   │
│ confidence      │       │   │
│ created_at      │       │   │
└─────────────────┘       │   │
         │                │   │
         └────────────────┘   │
                              │
┌─────────────────┐           │
│ topic_mastery   │           │
├─────────────────┤           │
│ id (PK)         │           │
│ user_id (FK)    │───────────┘
│ subject_id (FK) │───────────┐
│ topic           │           │
│ mastery_level   │           │
│ question_count  │           │
│ correct_count   │           │
│ last_interaction│           │
│ created_at      │           │
└─────────────────┘           │
                              │
┌─────────────────┐           │
│   weak_areas    │           │
├─────────────────┤           │
│ id (PK)         │           │
│ user_id (FK)    │───────────┘
│ subject_id (FK) │───────────┘
│ topic           │
│ weakness_score  │
│ recommended     │
│ detected_at     │
└─────────────────┘

┌─────────────────┐
│practice_questions│
├─────────────────┤
│ id (PK)         │
│ subject_id (FK) │───────┐
│ topic           │       │
│ difficulty      │       │
│ question        │       │
│ answer          │       │
│ created_at      │       │
└─────────────────┘       │
                          │
                          └───────────────┐
                                          │
                                          ▼
                                  ┌─────────────────┐
                                  │    subjects     │
                                  └─────────────────┘
```

#### SQL Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('siswa', 'guru', 'admin')),
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects table (Dynamic subjects)
CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    grade INTEGER NOT NULL CHECK (grade BETWEEN 10 AND 12),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Books table (Dynamic curriculum)
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    filename VARCHAR(255),
    vkp_version VARCHAR(20),
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat history table
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Topic mastery tracking
CREATE TABLE topic_mastery (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    mastery_level FLOAT DEFAULT 0.0 CHECK (mastery_level BETWEEN 0.0 AND 1.0),
    question_count INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    last_interaction TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, subject_id, topic)
);

-- Weak areas detection
CREATE TABLE weak_areas (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    weakness_score FLOAT,
    recommended_practice TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Practice questions
CREATE TABLE practice_questions (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_chat_history_user ON chat_history(user_id);
CREATE INDEX idx_chat_history_created ON chat_history(created_at);
CREATE INDEX idx_chat_history_subject ON chat_history(subject_id);
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_topic_mastery_user_subject ON topic_mastery(user_id, subject_id);
CREATE INDEX idx_weak_areas_user_subject ON weak_areas(user_id, subject_id);
CREATE INDEX idx_practice_questions_subject_topic ON practice_questions(subject_id, topic);
```

### VKP Data Model

```python
@dataclass
class VKPMetadata:
    version: str  # Semantic versioning (e.g., "1.2.0")
    subject: str  # e.g., "matematika"
    grade: int  # 10, 11, or 12
    semester: int  # 1 or 2
    created_at: str  # ISO 8601 timestamp
    embedding_model: str  # e.g., "amazon.titan-embed-text-v1"
    chunk_config: ChunkConfig
    total_chunks: int
    source_files: List[str]
    checksum: str  # SHA256 hash

@dataclass
class ChunkConfig:
    chunk_size: int  # 800
    chunk_overlap: int  # 100

@dataclass
class VKPChunk:
    chunk_id: str  # Unique identifier
    text: str  # Chunk content
    embedding: List[float]  # 1536 dimensions for Titan
    metadata: ChunkMetadata

@dataclass
class ChunkMetadata:
    page: int
    section: str
    topic: str

@dataclass
class VKP:
    metadata: VKPMetadata
    chunks: List[VKPChunk]
```

### Telemetry Data Model

```python
@dataclass
class AggregatedMetrics:
    school_id: str  # Anonymized hash
    timestamp: int  # Unix timestamp
    
    # Query metrics
    total_queries: int
    successful_queries: int
    failed_queries: int
    average_latency_ms: float
    p50_latency_ms: float
    p90_latency_ms: float
    p99_latency_ms: float
    
    # System metrics
    model_version: str
    embedding_model: str
    chromadb_version: str
    
    # Error metrics
    error_rate: float
    error_types: Dict[str, int]
    
    # Storage metrics
    chromadb_size_mb: float
    postgres_size_mb: float
    disk_usage_percent: float
    
    # Usage patterns (aggregated)
    active_users_count: int
    subjects_queried: List[str]
    peak_concurrent_users: int
```

### Configuration Data Model

```python
@dataclass
class SystemConfig:
    # Hardware
    ram_gb: int  # 16
    cpu_cores: int  # 8
    disk_gb: int  # 512
    
    # LLM
    model_path: str
    max_context_length: int  # 2048
    max_response_tokens: int  # 512
    n_threads: int  # 4
    n_gpu_layers: int  # 0 (CPU only)
    
    # RAG
    chunk_size: int  # 800
    chunk_overlap: int  # 100
    similarity_threshold: float  # 0.7
    top_k: int  # 5
    
    # Concurrency
    max_concurrent_threads: int  # 5
    queue_timeout_seconds: int  # 300
    
    # Database
    postgres_url: str
    postgres_pool_size: int  # 10
    postgres_max_overflow: int  # 20
    
    # Cache
    redis_url: Optional[str]
    cache_ttl_seconds: int  # 86400
    lru_cache_size: int  # 1000
    
    # Embedding
    default_embedding_strategy: str  # "bedrock" or "local"
    fallback_enabled: bool  # True
    
    # Backup
    backup_retention_days: int  # 28
    backup_encryption_enabled: bool  # False
    backup_s3_enabled: bool  # False
    
    # Telemetry
    telemetry_enabled: bool  # True
    telemetry_upload_interval_hours: int  # 1
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection

After analyzing all acceptance criteria, I identified the following redundancies and consolidations:

**Redundancy Analysis:**

1. **Documentation Consistency (1.1, 1.4)**: Property 1.1 tests that all documentation references are updated to 16GB, while 1.4 tests consistency across documentation. These can be combined into a single property about documentation consistency.

2. **Folder Preservation (14.1-14.7)**: All these criteria test that specific files are preserved. Rather than separate properties for each file, we can have one property that tests file preservation for a list of files.

3. **Data Location (16.1-16.3)**: All three test that sensitive data is stored locally. These can be combined into one property about local data storage.

4. **Offline Operation (17.1-17.3)**: All three test that the system works offline. These can be combined into one property about offline functionality.

5. **VKP Structure (6.1, 6.2, 6.6)**: All test that VKP packages contain required fields. These can be combined into one comprehensive property about VKP structure validation.

6. **Telemetry Anonymization (9.1, 9.2, 9.4, 9.5)**: All test aspects of telemetry data being anonymized. These can be combined into one comprehensive property about telemetry data validation.

7. **AWS Privacy (16.4, 16.5, 16.6, 16.7)**: All test that no PII is sent to AWS. These can be combined into one property about AWS data transmission validation.

**Consolidated Properties:**

After reflection, I've consolidated 100+ acceptance criteria into 35 unique, non-redundant properties that provide comprehensive validation coverage.


### Property 1: Documentation Hardware Specification Consistency

*For any* documentation file in the project, all references to minimum RAM requirements should specify 16GB, and all hardware specifications should consistently state 16GB RAM, 8-core CPU, and 512GB SSD.

**Validates: Requirements 1.1, 1.3, 1.4**

### Property 2: Import Path Consistency After Refactoring

*For any* Python file in the codebase after folder restructuring, no import statements should reference the old paths (src.local_inference, src.cloud_sync), and all imports should use the new paths (src.edge_runtime, src.aws_control_plane).

**Validates: Requirements 2.4**

### Property 3: Data Persistence Across Restarts

*For any* user session, chat history entry, or metadata stored in the system, restarting the server should preserve that data, and querying the database after restart should return the same data.

**Validates: Requirements 3.3**

### Property 4: Database Transaction Atomicity

*For any* set of database operations that should be atomic, either all operations should succeed and be committed, or all should fail and be rolled back, maintaining data integrity.

**Validates: Requirements 3.4**

### Property 5: Mastery Level Bounds

*For any* student and topic combination, the mastery_level score stored in the database should always be between 0.0 and 1.0 inclusive.

**Validates: Requirements 4.1**

### Property 6: Weak Area Detection

*For any* student with low mastery level (< 0.4) or high question frequency (> 5 in 7 days) on a topic, the weak area detector should identify that topic as a weak area.

**Validates: Requirements 4.2**

### Property 7: Adaptive Question Difficulty

*For any* mastery level, the generated practice question difficulty should be appropriate: easy for mastery < 0.3, medium for 0.3 ≤ mastery < 0.6, and hard for mastery ≥ 0.6.

**Validates: Requirements 4.6**

### Property 8: Topic Classification and Mastery Update

*For any* student question, the pedagogical engine should classify the topic and update the mastery tracking in the database.

**Validates: Requirements 4.5**

### Property 9: Adaptive Practice Question Generation

*For any* detected weak area, the system should generate practice questions targeting that specific topic.

**Validates: Requirements 4.3**

### Property 10: Concurrent Thread Limit

*For any* point in time during system operation, the number of active inference threads should never exceed 5.

**Validates: Requirements 5.1**

### Property 11: Request Queuing When Capacity Exceeded

*For any* number of concurrent requests greater than 5, the additional requests beyond the first 5 should be placed in a queue.

**Validates: Requirements 5.3**

### Property 12: Queue Position Tracking

*For any* queued request, the system should return the request's position in the queue to the user.

**Validates: Requirements 5.6**

### Property 13: Response Latency Target

*For any* student query under normal load (< 100 concurrent users), the response latency should be between 3 and 8 seconds for the 90th percentile.

**Validates: Requirements 5.5**

### Property 14: VKP Structure Validation

*For any* VKP package created, it should contain all required fields: version, subject, grade, semester, chunks, embedding_model, created_at, checksum, and all chunks should have embeddings and metadata.

**Validates: Requirements 6.1, 6.2, 6.6**

### Property 15: VKP Delta Update Efficiency

*For any* two VKP versions of the same subject, the delta update should only contain chunks that were added or modified, not unchanged chunks.

**Validates: Requirements 6.3**

### Property 16: VKP Checksum Integrity

*For any* VKP package, recalculating the checksum from the package contents should match the stored checksum value.

**Validates: Requirements 6.4**

### Property 17: VKP Serialization Round-Trip

*For any* VKP package, serializing to JSON and then deserializing should produce an equivalent VKP object with the same data.

**Validates: Requirements 6.5**

### Property 18: Version Comparison Correctness

*For any* two semantic version strings, the version comparison should correctly identify which is newer, older, or if they are equal.

**Validates: Requirements 7.2**

### Property 19: VKP Delta Download Only

*For any* VKP update where a newer version is available, only the delta (changed content) should be downloaded, not the entire package.

**Validates: Requirements 7.3**

### Property 20: VKP Checksum Verification Before Installation

*For any* downloaded VKP package, the integrity checksum should be verified before extracting embeddings to ChromaDB.

**Validates: Requirements 7.4**

### Property 21: PDF Text Extraction Completeness

*For any* valid PDF file, the text extraction process should extract all readable text content from all pages.

**Validates: Requirements 8.2**

### Property 22: Text Chunking Parameters

*For any* text processed by the chunker, all chunks should have approximately 800 tokens with 100 token overlap between consecutive chunks.

**Validates: Requirements 8.3**

### Property 23: Telemetry Data Anonymization

*For any* telemetry data collected, it should only contain anonymized metrics (query count, latency, model version, error rate, storage usage) and should contain no chat content, user data, or personal information, and all PII pattern scans should return no matches.

**Validates: Requirements 9.1, 9.2, 9.4, 9.5**

### Property 24: Backup Compression

*For any* backup created (full or incremental), the backup should be compressed, and the compressed size should be smaller than the original size.

**Validates: Requirements 10.3**

### Property 25: Version Rollback Round-Trip

*For any* system version, creating a snapshot, making changes, and then rolling back to that snapshot should restore the system to the original state.

**Validates: Requirements 10.4**

### Property 26: Backup Retention Policy

*For any* point in time, the backup directory should only contain backups from the last 28 days, and older backups should be automatically cleaned up.

**Validates: Requirements 10.7**

### Property 27: Cache Key Consistency

*For any* question text, subject ID, and VKP version, generating the cache key multiple times should always produce the same hash value.

**Validates: Requirements 12.2**

### Property 28: Cache Hit Performance

*For any* cached response, retrieving it from the cache should complete in less than 500ms.

**Validates: Requirements 12.3**

### Property 29: Cache Invalidation on VKP Update

*For any* subject where the VKP version is updated, all cached responses for that subject should be invalidated.

**Validates: Requirements 12.6**

### Property 30: Repeated Question Caching

*For any* question asked multiple times with the same subject and VKP version, the second and subsequent requests should return the cached response.

**Validates: Requirements 12.1**

### Property 31: AWS Infrastructure Setup Idempotence

*For any* AWS infrastructure setup script, running it multiple times should produce the same result (all resources exist and are configured correctly) without errors.

**Validates: Requirements 15.7**

### Property 32: Local Data Storage Privacy

*For any* sensitive data (chat history, student identity, teacher identity), it should be stored exclusively in the local PostgreSQL database and never transmitted to AWS.

**Validates: Requirements 16.1, 16.2, 16.3**

### Property 33: AWS Data Transmission Privacy

*For any* data transmitted to AWS, it should contain only anonymized metrics, and scanning for PII patterns (names, emails, IDs, chat content) should find no matches.

**Validates: Requirements 16.4, 16.5, 16.6, 16.7**

### Property 34: Offline Operation Completeness

*For any* core system functionality (student queries, RAG operations, authentication), the system should continue operating normally when internet is unavailable, using only local resources (LLM, ChromaDB, PostgreSQL).

**Validates: Requirements 17.1, 17.2, 17.3, 17.5**

### Property 35: File Preservation During Refactoring

*For any* file in the preservation list (rag_pipeline.py, inference_engine.py, chroma_manager.py, bedrock_client.py, etl_pipeline.py, frontend/), the file content should remain unchanged after refactoring, with only import paths updated.

**Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7**


## Error Handling

### Error Handling Strategy

The system implements a layered error handling approach with graceful degradation and comprehensive logging.

#### 1. Database Connection Errors

**PostgreSQL Unavailable**
```python
try:
    db_connection = db_manager.get_connection()
except DatabaseConnectionError as e:
    logger.error(f"PostgreSQL connection failed: {e}", exc_info=True)
    # Do NOT fallback to in-memory (data loss risk)
    return HTTPException(
        status_code=503,
        detail="Database temporarily unavailable. Please try again later."
    )
```

**Connection Pool Exhausted**
```python
try:
    with db_manager.get_connection(timeout=30) as conn:
        # Execute query
        pass
except PoolTimeoutError:
    logger.warning("Connection pool exhausted")
    return HTTPException(
        status_code=503,
        detail="System is under heavy load. Please try again in a moment."
    )
```

#### 2. LLM Inference Errors

**Model Loading Failure**
```python
try:
    llm_engine.load_model()
except ModelLoadError as e:
    logger.critical(f"Failed to load LLM model: {e}", exc_info=True)
    # Attempt auto-restart
    auto_restart_service.attempt_restart('llm_engine')
    raise SystemError("LLM model unavailable")
```

**Inference Timeout**
```python
try:
    response = await asyncio.wait_for(
        llm_engine.generate(prompt),
        timeout=30.0
    )
except asyncio.TimeoutError:
    logger.error("LLM inference timeout")
    return {
        'error': 'Request timeout',
        'message': 'The system is taking longer than expected. Please try a simpler question.'
    }
```

**Out of Memory**
```python
try:
    response = llm_engine.generate(prompt)
except MemoryError:
    logger.critical("Out of memory during inference")
    # Clear cache
    cache_manager.clear()
    # Attempt restart
    auto_restart_service.attempt_restart('api_server')
    raise
```

#### 3. ChromaDB Errors

**Collection Not Found**
```python
try:
    collection = chroma_manager.get_collection(subject_code)
except CollectionNotFoundError:
    logger.warning(f"Collection not found: {subject_code}")
    return {
        'error': 'Subject not available',
        'message': f'The subject {subject_code} has not been set up yet.'
    }
```

**Query Failure**
```python
try:
    results = collection.query(embedding, n_results=5)
except ChromaDBError as e:
    logger.error(f"ChromaDB query failed: {e}", exc_info=True)
    # Attempt health check
    if not chroma_manager.health_check():
        auto_restart_service.attempt_restart('chromadb')
    raise
```

#### 4. AWS Service Errors

**S3 Upload Failure**
```python
try:
    s3_client.upload_file(file_path, bucket, key)
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'NoSuchBucket':
        logger.error(f"S3 bucket not found: {bucket}")
    elif error_code == 'AccessDenied':
        logger.error(f"S3 access denied: {bucket}/{key}")
    else:
        logger.error(f"S3 upload failed: {e}", exc_info=True)
    # Queue for retry
    upload_queue.enqueue(file_path, bucket, key)
```

**Bedrock API Failure**
```python
try:
    response = bedrock_client.invoke_model(model_id, body)
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'ThrottlingException':
        logger.warning("Bedrock API throttled, retrying with backoff")
        time.sleep(2 ** retry_count)  # Exponential backoff
        return retry_with_backoff()
    elif error_code == 'ModelNotReadyException':
        logger.error("Bedrock model not ready")
        # Fallback to local embeddings
        return embedding_strategy_manager.fallback_to_local()
    else:
        logger.error(f"Bedrock API error: {e}", exc_info=True)
        raise
```

**Lambda Invocation Failure**
```python
try:
    lambda_client.invoke(FunctionName=function_name, Payload=payload)
except ClientError as e:
    logger.error(f"Lambda invocation failed: {e}", exc_info=True)
    # Send to DLQ
    sqs_client.send_message(QueueUrl=dlq_url, MessageBody=payload)
```

#### 5. Network Errors

**Internet Unavailable**
```python
def check_internet() -> bool:
    try:
        requests.get('https://www.google.com', timeout=5)
        return True
    except requests.ConnectionError:
        return False

# In VKP puller
if not check_internet():
    logger.info("Offline mode - skipping VKP check")
    return  # Continue with existing data
```

**AWS Endpoint Unreachable**
```python
try:
    response = s3_client.list_objects_v2(Bucket=bucket)
except EndpointConnectionError:
    logger.warning("AWS endpoint unreachable - operating in offline mode")
    # Queue telemetry for later
    telemetry_uploader.queue_offline_metrics(metrics)
    return
```

#### 6. Validation Errors

**Invalid User Input**
```python
def validate_question(question: str) -> None:
    if not question or not question.strip():
        raise ValidationError("Question cannot be empty")
    
    if len(question) > 5000:
        raise ValidationError("Question too long (max 5000 characters)")
    
    # Check for SQL injection patterns
    if re.search(r'(DROP|DELETE|INSERT|UPDATE)\s+', question, re.IGNORECASE):
        raise ValidationError("Invalid question content")
```

**Invalid VKP Format**
```python
def validate_vkp(vkp: dict) -> None:
    required_fields = ['version', 'subject', 'grade', 'chunks', 'checksum']
    missing = [f for f in required_fields if f not in vkp]
    
    if missing:
        raise ValidationError(f"VKP missing required fields: {missing}")
    
    # Verify checksum
    calculated = calculate_checksum(vkp)
    if calculated != vkp['checksum']:
        raise ValidationError("VKP checksum mismatch - possible corruption")
```

#### 7. Concurrency Errors

**Queue Overflow**
```python
MAX_QUEUE_SIZE = 1000

async def enqueue_request(request: InferenceRequest) -> str:
    if queue.qsize() >= MAX_QUEUE_SIZE:
        logger.error("Queue overflow - rejecting request")
        raise HTTPException(
            status_code=503,
            detail="System is at maximum capacity. Please try again in a few minutes."
        )
    
    await queue.put(request)
    return request.queue_id
```

**Deadlock Detection**
```python
try:
    with db_manager.get_connection() as conn:
        conn.execute(query, timeout=30)
except OperationalError as e:
    if 'deadlock' in str(e).lower():
        logger.warning("Deadlock detected, retrying transaction")
        time.sleep(0.1)
        return retry_transaction()
    raise
```

### Error Logging Strategy

**Log Levels**
```python
# DEBUG: Detailed diagnostic information
logger.debug(f"Processing request: {request_id}")

# INFO: General informational messages
logger.info(f"VKP updated: {subject_code} v{version}")

# WARNING: Warning messages for recoverable issues
logger.warning(f"Cache miss: {cache_key}")

# ERROR: Error messages for failures
logger.error(f"Database query failed: {e}", exc_info=True)

# CRITICAL: Critical errors requiring immediate attention
logger.critical(f"LLM model failed to load: {e}", exc_info=True)
```

**Structured Logging**
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "query_processed",
    user_id=user_id,
    subject_id=subject_id,
    latency_ms=latency,
    cache_hit=cache_hit,
    queue_position=queue_position
)
```

**Log Rotation**
```python
# logging.conf
[handler_file]
class=handlers.RotatingFileHandler
filename=/var/log/nexusai/app.log
maxBytes=10485760  # 10MB
backupCount=10
formatter=detailed
```


## Testing Strategy

### Dual Testing Approach

The system requires both unit testing and property-based testing for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, error conditions, and integration points
- **Property tests**: Verify universal properties across all inputs through randomization
- Both approaches are complementary and necessary

### Unit Testing Strategy

Unit tests focus on:
- Specific examples that demonstrate correct behavior
- Integration points between components
- Edge cases (empty inputs, boundary values, special characters)
- Error conditions (database unavailable, network failures, invalid inputs)

**Unit Test Balance**: Avoid writing too many unit tests for scenarios that property tests can cover. Focus unit tests on concrete examples and integration scenarios.

**Example Unit Tests**:
```python
# Specific example
def test_create_user_with_valid_data():
    user = user_repo.create_user("john_doe", "hashed_pass", "siswa", "John Doe")
    assert user.username == "john_doe"
    assert user.role == "siswa"

# Edge case
def test_empty_question_rejected():
    with pytest.raises(ValidationError):
        validate_question("")

# Error condition
def test_database_unavailable_returns_503():
    with mock.patch('db_manager.get_connection', side_effect=DatabaseConnectionError):
        response = client.post("/api/chat", json={"question": "test"})
        assert response.status_code == 503

# Integration
def test_end_to_end_query_flow():
    # Login
    token = login("student1", "password")
    # Query
    response = query_with_token(token, "What is Pythagoras theorem?")
    # Verify
    assert response.status_code == 200
    assert "Pythagoras" in response.json()["answer"]
```


### Property-Based Testing Strategy

Property-based testing verifies universal properties across many generated inputs (minimum 100 iterations per test).

**Property-Based Testing Library**: Use Hypothesis for Python

**Configuration**:
```python
from hypothesis import given, settings
import hypothesis.strategies as st

# Minimum 100 iterations per property test
@settings(max_examples=100)
@given(...)
def test_property(...):
    pass
```

**Test Tagging**: Each property test must reference its design document property
```python
# Feature: architecture-alignment-refactoring, Property 1: Documentation Hardware Specification Consistency
@settings(max_examples=100)
@given(doc_file=st.sampled_from(documentation_files))
def test_documentation_ram_specification_consistency(doc_file):
    content = read_file(doc_file)
    ram_specs = extract_ram_specifications(content)
    assert all(spec == "16GB" for spec in ram_specs)
```

**Example Property Tests**:

```python
# Property 3: Data Persistence Across Restarts
# Feature: architecture-alignment-refactoring, Property 3: Data Persistence Across Restarts
@settings(max_examples=100)
@given(
    username=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    question=st.text(min_size=10, max_size=500),
    response=st.text(min_size=10, max_size=1000)
)
def test_data_persists_across_restarts(username, question, response):
    # Store data
    user = create_user(username, "password", "siswa")
    chat = save_chat(user.id, 1, question, response)
    
    # Simulate restart
    restart_server()
    
    # Verify data persists
    retrieved_user = get_user_by_username(username)
    retrieved_chat = get_chat_by_id(chat.id)
    
    assert retrieved_user is not None
    assert retrieved_user.username == username
    assert retrieved_chat is not None
    assert retrieved_chat.question == question
    assert retrieved_chat.response == response
```

```python
# Property 5: Mastery Level Bounds
# Feature: architecture-alignment-refactoring, Property 5: Mastery Level Bounds
@settings(max_examples=100)
@given(
    user_id=st.integers(min_value=1, max_value=1000),
    subject_id=st.integers(min_value=1, max_value=20),
    topic=st.text(min_size=3, max_size=100),
    question_count=st.integers(min_value=0, max_value=100),
    avg_complexity=st.floats(min_value=0.0, max_value=1.0)
)
def test_mastery_level_always_in_bounds(user_id, subject_id, topic, question_count, avg_complexity):
    # Update mastery
    mastery_level = mastery_tracker.update_mastery(
        user_id, subject_id, topic, question_count, avg_complexity
    )
    
    # Verify bounds
    assert 0.0 <= mastery_level <= 1.0
```

```python
# Property 10: Concurrent Thread Limit
# Feature: architecture-alignment-refactoring, Property 10: Concurrent Thread Limit
@settings(max_examples=100)
@given(num_requests=st.integers(min_value=1, max_value=50))
async def test_concurrent_threads_never_exceed_limit(num_requests):
    # Submit requests
    tasks = [submit_inference_request(f"question_{i}") for i in range(num_requests)]
    
    # Monitor active threads
    max_concurrent = 0
    while any(not task.done() for task in tasks):
        active = concurrency_manager.get_active_count()
        max_concurrent = max(max_concurrent, active)
        await asyncio.sleep(0.1)
    
    # Verify limit never exceeded
    assert max_concurrent <= 5
```

```python
# Property 17: VKP Serialization Round-Trip
# Feature: architecture-alignment-refactoring, Property 17: VKP Serialization Round-Trip
@settings(max_examples=100)
@given(
    version=st.text(min_size=5, max_size=10, alphabet='0123456789.'),
    subject=st.sampled_from(['matematika', 'informatika', 'fisika']),
    grade=st.integers(min_value=10, max_value=12),
    num_chunks=st.integers(min_value=1, max_value=100)
)
def test_vkp_serialization_round_trip(version, subject, grade, num_chunks):
    # Create VKP
    vkp = create_random_vkp(version, subject, grade, num_chunks)
    
    # Serialize
    serialized = vkp_packager.serialize(vkp)
    
    # Deserialize
    deserialized = vkp_packager.deserialize(serialized)
    
    # Verify equivalence
    assert deserialized.metadata.version == vkp.metadata.version
    assert deserialized.metadata.subject == vkp.metadata.subject
    assert deserialized.metadata.grade == vkp.metadata.grade
    assert len(deserialized.chunks) == len(vkp.chunks)
    assert deserialized.metadata.checksum == vkp.metadata.checksum
```

```python
# Property 23: Telemetry Data Anonymization
# Feature: architecture-alignment-refactoring, Property 23: Telemetry Data Anonymization
@settings(max_examples=100)
@given(
    total_queries=st.integers(min_value=0, max_value=10000),
    avg_latency=st.floats(min_value=0.0, max_value=30000.0),
    error_rate=st.floats(min_value=0.0, max_value=1.0)
)
def test_telemetry_contains_no_pii(total_queries, avg_latency, error_rate):
    # Create telemetry data
    metrics = AggregatedMetrics(
        school_id=anonymize_school_id("school_123"),
        timestamp=int(time.time()),
        total_queries=total_queries,
        average_latency_ms=avg_latency,
        error_rate=error_rate,
        model_version="llama-3.2-3b-q4",
        active_users_count=50
    )
    
    # Verify no PII
    assert pii_verifier.verify_no_pii(metrics.__dict__)
    
    # Verify anonymized school ID
    assert metrics.school_id.startswith("school_")
    assert len(metrics.school_id) > 20  # Hash length
```

```python
# Property 33: AWS Data Transmission Privacy
# Feature: architecture-alignment-refactoring, Property 33: AWS Data Transmission Privacy
@settings(max_examples=100)
@given(data=st.dictionaries(
    keys=st.sampled_from(['total_queries', 'avg_latency', 'error_rate', 'model_version']),
    values=st.one_of(st.integers(), st.floats(), st.text(max_size=50))
))
def test_aws_transmission_contains_no_pii(data):
    # Simulate AWS transmission
    transmission_data = prepare_for_aws_transmission(data)
    
    # Scan for PII patterns
    pii_patterns = [
        r'\b\d{16}\b',  # NIK
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{3}-\d{3}-\d{4}\b',  # Phone
        r'\b(?:Nama|Name):\s*[A-Z][a-z]+',  # Name
    ]
    
    data_str = json.dumps(transmission_data)
    for pattern in pii_patterns:
        assert not re.search(pattern, data_str), f"PII pattern detected: {pattern}"
```

### Test Coverage Requirements

- **Overall Coverage**: Minimum 70% for critical paths
- **Component Coverage**:
  - Database layer: 80%
  - Pedagogical engine: 75%
  - Concurrency manager: 80%
  - VKP system: 75%
  - Telemetry system: 70%

### Test Execution Strategy

**Development**:
```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run property tests only
pytest tests/property/

# Run with coverage
pytest --cov=src --cov-report=html
```

**CI/CD Pipeline**:
```yaml
# .github/workflows/test.yml
- name: Run Unit Tests
  run: pytest tests/unit/ -v

- name: Run Property Tests
  run: pytest tests/property/ -v --hypothesis-seed=random

- name: Check Coverage
  run: pytest --cov=src --cov-fail-under=70
```

**Load Testing**:
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/load_test.py --host=http://localhost:8000

# Target metrics:
# - 100 concurrent users: stable performance
# - 300 concurrent users: acceptable degradation
# - 90th percentile latency: 3-8 seconds
# - Error rate: < 1%
```

