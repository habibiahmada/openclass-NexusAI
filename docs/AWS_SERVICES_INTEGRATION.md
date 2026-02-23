# 🔧 AWS Services Integration Guide

**Date:** 2025-01-XX  
**Status:** ACTIVE  
**Purpose:** Comprehensive guide to AWS services usage in OpenClass Nexus AI

---

## 📊 EXECUTIVE SUMMARY

OpenClass Nexus AI uses AWS services for:
1. **Embedding Generation** (AWS Bedrock) - Cloud-based embeddings
2. **Storage & Distribution** (S3 + CloudFront) - VKP distribution
3. **Job Tracking** (DynamoDB) - ETL pipeline monitoring
4. **Curriculum Processing** (Lambda) - Automated PDF processing
5. **Telemetry** (DynamoDB) - Anonymized usage metrics

---

## 🎯 PART I: FOLDER STRUCTURE CLARIFICATION

### `scripts/` vs `src/` - What's the Difference?

#### `scripts/` - Executable Scripts
**Purpose:** Command-line tools and automation scripts  
**Usage:** Run directly from terminal  
**Examples:**
```bash
# AWS setup and testing
python scripts/aws/setup_aws.py
python scripts/aws/test_aws_connection.py
python scripts/aws/view_job_history.py

# Data processing
python scripts/data/run_etl_pipeline.py
python scripts/data/run_cloud_embeddings.py

# System maintenance
python scripts/maintenance/vkp_pull_cron.py
python scripts/maintenance/telemetry_upload_cron.py
```

#### `src/` - Library Code
**Purpose:** Reusable modules and classes  
**Usage:** Imported by other Python code  
**Examples:**
```python
# AWS Control Plane (used by scripts and API)
from src.aws_control_plane.s3_storage_manager import S3StorageManager
from src.aws_control_plane.cloudfront_manager import CloudFrontManager
from src.aws_control_plane.job_tracker import JobTracker
from src.aws_control_plane.lambda_processor import LambdaProcessorPackager

# Embedding strategies (used by ETL pipeline)
from src.embeddings.bedrock_strategy import BedrockEmbeddingStrategy
from src.embeddings.local_minilm_strategy import LocalMiniLMStrategy
from src.embeddings.strategy_manager import EmbeddingStrategyManager
```

### Why Both Exist?

**Design Pattern:** Separation of Concerns
- `scripts/` = **Executable entry points** (CLI tools)
- `src/` = **Business logic** (reusable libraries)

**Analogy:**
- `scripts/` = Restaurant menu (what you can order)
- `src/` = Kitchen (how food is prepared)

---

## 🔌 PART II: AWS SERVICES USAGE

### 1. AWS Bedrock (Embedding Generation)

#### Purpose
Generate high-quality embeddings for curriculum content using AWS Titan model.

#### Location
- **Library:** `src/embeddings/bedrock_strategy.py`
- **Script:** `scripts/data/run_cloud_embeddings.py`
- **Integration:** `src/data_processing/etl_pipeline.py`

#### Usage in ETL Pipeline
```python
# src/data_processing/etl_pipeline.py (line 107)
from src.embeddings.strategy_manager import EmbeddingStrategyManager

# Initialize strategy manager
strategy_manager = EmbeddingStrategyManager()

# Get active strategy (AWS Bedrock or Local MiniLM)
embedding_strategy = strategy_manager.get_strategy()

# Generate embeddings
embeddings = embedding_strategy.batch_generate(texts)
```

#### Configuration
```bash
# .env
BEDROCK_REGION=ap-southeast-2
BEDROCK_MODEL_ID=amazon.titan-embed-text-v2:0
EMBEDDING_STRATEGY=bedrock  # or 'local'
```

#### When It's Used
- **Default:** ETL pipeline uses Bedrock for embedding generation
- **Fallback:** Automatically switches to local MiniLM if AWS unavailable
- **Manual:** Can be forced to local with `EMBEDDING_STRATEGY=local`

#### Cost Tracking
```python
# Bedrock costs are tracked in ETL pipeline
cost_tracker.track_bedrock_embeddings(
    num_embeddings=len(embeddings),
    model_id='amazon.titan-embed-text-v2:0'
)
```

---

### 2. AWS S3 (Storage)

#### Purpose
Store processed curriculum files, ChromaDB backups, and VKP packages.

#### Location
- **Library:** `src/aws_control_plane/s3_storage_manager.py`
- **Script:** `scripts/aws/upload_to_s3.py`
- **Integration:** `scripts/data/run_etl_pipeline.py` (line 320+)

#### Usage in ETL Pipeline
```python
# scripts/data/run_etl_pipeline.py
from src.aws_control_plane.s3_storage_manager import S3StorageManager

s3_manager = S3StorageManager()

# Upload ChromaDB files
s3_manager.upload_chromadb_files(
    chromadb_dir='data/vector_db',
    subject='informatika',
    grade='kelas_10'
)

# Upload processed text
s3_manager.upload_processed_text(
    text_dir='data/processed/text',
    subject='informatika',
    grade='kelas_10'
)

# Upload metadata
s3_manager.upload_metadata(
    metadata_dir='data/processed/metadata',
    subject='informatika',
    grade='kelas_10'
)
```

#### S3 Bucket Structure
```
s3://openclass-nexus-ai/
├── processed/
│   ├── informatika/
│   │   ├── kelas_10/
│   │   │   ├── chromadb/
│   │   │   │   ├── chroma.sqlite3
│   │   │   │   └── embeddings/
│   │   │   ├── text/
│   │   │   │   ├── file1.txt
│   │   │   │   └── file2.txt
│   │   │   └── metadata/
│   │   │       ├── summary.json
│   │   │       └── quality_report.json
│   │   └── kelas_11/
│   └── matematika/
└── vkp/
    ├── informatika_kelas_10_v1.0.0.vkp
    └── matematika_kelas_10_v1.0.0.vkp
```

#### When It's Used
- **ETL Pipeline:** Automatically uploads after processing (use `--no-upload` to skip)
- **Backup:** Manual backup via `scripts/maintenance/run_backup.py`
- **VKP Distribution:** VKP packages uploaded for school servers to download

---

### 3. AWS CloudFront (CDN)

#### Purpose
Distribute VKP packages to school servers with low latency and caching.

#### Location
- **Library:** `src/aws_control_plane/cloudfront_manager.py`
- **Script:** `scripts/aws/setup_cloudfront.py` (not yet created)
- **Integration:** `scripts/data/run_etl_pipeline.py` (line 420+)

#### Usage in ETL Pipeline
```python
# scripts/data/run_etl_pipeline.py
from src.aws_control_plane.cloudfront_manager import CloudFrontManager

cloudfront_manager = CloudFrontManager()

# Invalidate cache after upload
cloudfront_manager.invalidate_cache(
    paths=['/processed/*', '/vkp/*']
)
```

#### Configuration
```bash
# .env
CLOUDFRONT_DISTRIBUTION_ID=E1234567890ABC
CLOUDFRONT_DISTRIBUTION_URL=https://d1234567890abc.cloudfront.net
```

#### When It's Used
- **VKP Updates:** School servers download VKP from CloudFront (not S3 directly)
- **Cache Invalidation:** After ETL pipeline uploads new files
- **Signed URLs:** For secure VKP distribution (prevents unauthorized access)

---

### 4. AWS DynamoDB (Job Tracking)

#### Purpose
Track ETL pipeline jobs, costs, and execution history.

#### Location
- **Library:** `src/aws_control_plane/job_tracker.py`
- **Script:** `scripts/aws/view_job_history.py`
- **Integration:** `scripts/data/run_etl_pipeline.py` (line 500+)

#### Usage in ETL Pipeline
```python
# scripts/data/run_etl_pipeline.py
from src.aws_control_plane.job_tracker import JobTracker

job_tracker = JobTracker()

# Start job
job_id = job_tracker.start_job(
    job_type='etl_pipeline',
    input_dir='data/raw_dataset/kelas_10/informatika',
    config={'chunk_size': 800, 'batch_size': 25}
)

# Update progress
job_tracker.update_job_progress(
    job_id=job_id,
    progress=50,
    status='processing'
)

# Complete job
job_tracker.complete_job(
    job_id=job_id,
    status='completed',
    total_files=10,
    successful_files=10,
    failed_files=0,
    total_chunks=2000,
    total_embeddings=2000,
    processing_time=120.5,
    estimated_cost=0.15
)

# Get cost summary
cost_summary = job_tracker.get_cost_summary(days=7)
print(f"Total cost (7 days): ${cost_summary['total_cost']:.4f}")
```

#### DynamoDB Table Schema
```
Table: ETLPipelineJobs
Primary Key: job_id (String)
Sort Key: timestamp (String)

Attributes:
- job_type (String)
- status (String) - 'running', 'completed', 'failed', 'partial'
- input_dir (String)
- config (Map)
- total_files (Number)
- successful_files (Number)
- failed_files (Number)
- total_chunks (Number)
- total_embeddings (Number)
- processing_time (Number)
- estimated_cost (Number)
- errors (List)
- created_at (String)
- completed_at (String)
```

#### When It's Used
- **ETL Pipeline:** Automatically tracks every run
- **Cost Monitoring:** View costs via `scripts/aws/view_job_history.py`
- **Job History:** View recent jobs and their status
- **Cost Analytics:** 7-day, 30-day cost summaries

---

### 5. AWS Lambda (Curriculum Processing)

#### Purpose
Automatically process PDF files uploaded to S3 and generate VKP packages.

#### Location
- **Library:** `src/aws_control_plane/lambda_processor.py`
- **Script:** `scripts/aws/deploy_lambda.py` (not yet created)
- **Trigger:** S3 event notification

#### Lambda Function Flow
```
1. PDF uploaded to S3 bucket
   ↓
2. S3 event triggers Lambda
   ↓
3. Lambda downloads PDF
   ↓
4. Extract text from PDF
   ↓
5. Chunk text
   ↓
6. Generate embeddings (Bedrock)
   ↓
7. Package into VKP
   ↓
8. Upload VKP to S3
   ↓
9. Invalidate CloudFront cache
   ↓
10. Send notification (SNS/SQS)
```

#### Configuration
```bash
# .env
LAMBDA_FUNCTION_NAME=openclass-curriculum-processor
LAMBDA_ROLE_ARN=arn:aws:iam::123456789012:role/lambda-execution-role
LAMBDA_TIMEOUT=900  # 15 minutes
LAMBDA_MEMORY=3008  # 3GB
```

#### When It's Used
- **Automatic:** When PDF uploaded to S3 `raw-curriculum/` prefix
- **Manual:** Can be invoked via AWS Console or CLI
- **Scheduled:** Can be triggered by EventBridge for batch processing

---

### 6. AWS DynamoDB (Telemetry)

#### Purpose
Store anonymized usage metrics for system monitoring and optimization.

#### Location
- **Library:** `src/telemetry/uploader.py`
- **Script:** `scripts/maintenance/telemetry_upload_cron.py`
- **Integration:** Runs hourly via cron

#### Telemetry Data Collected
```python
# src/telemetry/collector.py
{
    'school_id_hash': 'sha256_hash',  # Anonymized
    'timestamp': '2025-01-XX 10:00:00',
    'metrics': {
        'query_count': 150,
        'avg_latency_ms': 450,
        'error_count': 2,
        'storage_usage_mb': 1024,
        'model_version': 'llama-3.2-3b-instruct',
        'embedding_strategy': 'bedrock'
    }
}
```

#### Privacy Guarantees
- ❌ **NO chat content**
- ❌ **NO user data**
- ❌ **NO personal information**
- ✅ **Only aggregated metrics**
- ✅ **Anonymized school ID**
- ✅ **PII verification before upload**

#### When It's Used
- **Automatic:** Hourly upload via cron
- **Manual:** Can be triggered via `scripts/maintenance/telemetry_upload_cron.py`
- **Offline:** Queues metrics locally if AWS unavailable

---

## ⏱️ PART III: EMBEDDING TIME ESTIMATION

### How Long Does Embedding Take?

#### Factors Affecting Time
1. **Number of chunks** - More chunks = more time
2. **Embedding strategy** - AWS Bedrock vs Local MiniLM
3. **Batch size** - Larger batches = faster (but more memory)
4. **Network latency** - AWS Bedrock requires internet

#### Time Estimates

**AWS Bedrock (Cloud)**
```
Batch size: 25 chunks
Time per batch: ~2-3 seconds
Throughput: ~8-12 chunks/second

Example:
- 1,000 chunks = ~2-3 minutes
- 5,000 chunks = ~8-12 minutes
- 10,000 chunks = ~15-20 minutes
```

**Local MiniLM (On-premise)**
```
Batch size: 25 chunks
Time per batch: ~5-8 seconds (CPU) or ~1-2 seconds (GPU)
Throughput: ~3-5 chunks/second (CPU) or ~12-25 chunks/second (GPU)

Example (CPU):
- 1,000 chunks = ~3-5 minutes
- 5,000 chunks = ~15-25 minutes
- 10,000 chunks = ~30-50 minutes

Example (GPU):
- 1,000 chunks = ~40-80 seconds
- 5,000 chunks = ~3-7 minutes
- 10,000 chunks = ~7-14 minutes
```

#### Real-world Example
```bash
# Informatika Kelas 10 (10 PDF files)
Total pages: ~300 pages
Total chunks: ~2,000 chunks

AWS Bedrock: ~4-6 minutes
Local MiniLM (CPU): ~6-10 minutes
Local MiniLM (GPU): ~2-3 minutes
```

---

## 🏃 PART IV: ETL PIPELINE EXECUTION

### Where Does ETL Run?

**Answer:** ETL pipeline runs **locally** on your machine or school server.

### Where Are Embeddings Generated?

**Answer:** Depends on configuration:

#### Option 1: Cloud Embeddings (Default)
```bash
# .env
EMBEDDING_STRATEGY=bedrock

# Run ETL pipeline
python scripts/data/run_etl_pipeline.py
```
- Embeddings generated in **AWS Bedrock** (cloud)
- Text processing happens **locally**
- Embeddings downloaded and stored **locally** in ChromaDB
- Optionally uploaded to S3 for backup

#### Option 2: Local Embeddings
```bash
# .env
EMBEDDING_STRATEGY=local

# Run ETL pipeline
python scripts/data/run_etl_pipeline.py
```
- Everything runs **locally**
- No AWS required
- Slower but fully offline

#### Option 3: Hybrid (Recommended)
```bash
# .env
EMBEDDING_STRATEGY=bedrock
FALLBACK_ENABLED=true

# Run ETL pipeline
python scripts/data/run_etl_pipeline.py
```
- Try AWS Bedrock first
- Fallback to local if AWS unavailable
- Best of both worlds

### ETL Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ETL PIPELINE FLOW                        │
└─────────────────────────────────────────────────────────────┘

1. PDF Extraction (Local)
   ├── Read PDF files from data/raw_dataset/
   ├── Extract text using PyMuPDF
   └── Save to data/processed/text/

2. Text Chunking (Local)
   ├── Split text into chunks (800 chars)
   ├── Add overlap (100 chars)
   └── Save metadata

3. Embedding Generation (Cloud or Local)
   ├── If EMBEDDING_STRATEGY=bedrock:
   │   ├── Send chunks to AWS Bedrock
   │   ├── Receive embeddings (1024 dimensions)
   │   └── Track costs
   └── If EMBEDDING_STRATEGY=local:
       ├── Load MiniLM model locally
       ├── Generate embeddings (384 dimensions)
       └── No cost

4. ChromaDB Storage (Local)
   ├── Store embeddings in data/vector_db/
   ├── Create collection per subject
   └── Add metadata

5. S3 Upload (Optional, Cloud)
   ├── Upload ChromaDB files to S3
   ├── Upload processed text to S3
   └── Upload metadata to S3

6. CloudFront Invalidation (Optional, Cloud)
   └── Invalidate cache for updated files

7. Job Tracking (Cloud)
   ├── Record job in DynamoDB
   ├── Track costs
   └── Store execution history
```

---

## 🔧 PART V: FIXING THE IMPORT ERROR

### Problem
```bash
python scripts/data/run_etl_pipeline.py
# Error: ModuleNotFoundError: No module named 'src'
```

### Root Cause
Python can't find the `src` module because project root is not in PYTHONPATH.

### Solution 1: Use Wrapper Scripts (Recommended)
```bash
# Windows
run_etl.bat

# Linux/Mac
./run_etl.sh
```

These scripts automatically set PYTHONPATH.

### Solution 2: Set PYTHONPATH Manually
```bash
# Windows
set PYTHONPATH=%CD%
python scripts\data\run_etl_pipeline.py

# Linux/Mac
export PYTHONPATH=$(pwd)
python scripts/data/run_etl_pipeline.py
```

### Solution 3: Install as Package (Advanced)
```bash
# Create setup.py and install in editable mode
pip install -e .
```

---

## 📊 PART VI: AWS SERVICES UTILIZATION SUMMARY

### Current Status

| Service | Initialized | Used in ETL | Used in API | Exposed in UI |
|---------|-------------|-------------|-------------|---------------|
| S3 Storage | ✅ | ✅ | ❌ | ❌ |
| Bedrock Embeddings | ✅ | ✅ | ❌ | ❌ |
| CloudFront CDN | ✅ | ✅ | ❌ | ❌ |
| DynamoDB Jobs | ✅ | ✅ | ❌ | ❌ |
| Lambda Processor | ✅ | ❌ | ❌ | ❌ |
| DynamoDB Telemetry | ✅ | ❌ | ❌ | ❌ |

### Recommendations

1. **Expose in UI** (Phase 13 - Current)
   - Create admin dashboard showing AWS status
   - Add job history page with cost analytics
   - Add VKP manager with update checker
   - Add telemetry dashboard

2. **Deploy Lambda** (Phase 13 - Week 5)
   - Create deployment script
   - Configure S3 trigger
   - Test with sample PDFs

3. **Integrate Telemetry** (Phase 13 - Week 3)
   - Enable hourly uploads
   - Create telemetry dashboard
   - Show privacy status

---

## 🎯 CONCLUSION

### Key Takeaways

1. **scripts/ vs src/**
   - `scripts/` = Executable tools
   - `src/` = Reusable libraries
   - Both are needed and serve different purposes

2. **AWS Services**
   - All services are initialized and working
   - Used extensively in ETL pipeline
   - Not yet exposed in UI (Phase 13 goal)

3. **Embedding Time**
   - AWS Bedrock: ~2-3 minutes for 1,000 chunks
   - Local MiniLM: ~3-5 minutes (CPU) or ~40-80 seconds (GPU)

4. **ETL Pipeline**
   - Runs locally
   - Embeddings can be cloud or local
   - Hybrid mode recommended

5. **Import Error**
   - Fixed by setting PYTHONPATH
   - Use wrapper scripts for convenience

---

**Next Steps:**
1. Use `run_etl.bat` to run ETL pipeline
2. Review Phase 13 progress
3. Create UI components to expose AWS features

