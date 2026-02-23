# AWS Services Optimization Analysis

## Current State: Underutilized AWS Infrastructure

### ❌ Problem: Services Initialized but Not Used

Banyak AWS services sudah di-setup tapi hanya digunakan untuk **Bedrock Embeddings** saja. Padahal ada infrastructure lengkap yang bisa dimanfaatkan:

## AWS Services Available (from aws_config.py)

| Service | Status | Current Usage | Potential Usage |
|---------|--------|---------------|-----------------|
| **S3** | ✅ Configured | ❌ Not used in ETL | Upload processed data, ChromaDB backups |
| **CloudFront** | ✅ Configured | ❌ Not used | CDN for serving embeddings/data |
| **Bedrock** | ✅ Configured | ✅ Used (embeddings only) | Could use for LLM inference too |
| **DynamoDB** | ✅ Configured | ❌ Not used | Track processing jobs, metadata |
| **Lambda** | ✅ Code ready | ❌ Not deployed | Serverless PDF processing |

## Detailed Analysis

### 1. S3 Storage Manager (src/aws_control_plane/s3_storage_manager.py)
**Status:** Fully implemented, NOT used in ETL pipeline

**Capabilities:**
- Upload ChromaDB files with compression
- Upload processed text files
- Upload metadata files
- Gzip compression (save bandwidth)
- Server-side encryption (AES256)
- Storage class optimization (STANDARD_IA)

**Current ETL Pipeline:** 
```python
# scripts/data/run_etl_pipeline.py line 32-33
from src.aws_control_plane.s3_storage_manager import S3StorageManager
from src.aws_control_plane.cloudfront_manager import CloudFrontManager
```
✅ Imported but only used with `--no-upload` flag (disabled by default!)

**Problem:** User harus manually enable dengan flag, seharusnya default ON

---

### 2. CloudFront Manager (src/aws_control_plane/cloudfront_manager.py)
**Status:** Fully implemented, NOT used

**Capabilities:**
- Create CDN distribution
- 24-hour cache TTL
- HTTPS-only access
- Cache invalidation for updates
- Gzip compression

**Current Usage:** NONE - hanya di-import, tidak pernah di-call

**Potential:** Serve embeddings via CDN untuk faster access dari edge locations

---

### 3. Lambda Processor (src/aws_control_plane/lambda_processor.py)
**Status:** Complete implementation ready, NOT deployed

**Capabilities:**
- Serverless PDF processing
- S3 event triggers (auto-process on upload)
- VKP packaging
- CloudWatch logging
- Error handling

**Current Usage:** NONE - code exists but never deployed

**Potential:** 
- Upload PDF → Lambda auto-processes → Output to S3
- No need to run local ETL pipeline
- Scalable, pay-per-use

---

### 4. DynamoDB (aws_config.py)
**Status:** Client configured, NOT used anywhere

**Table:** `StudentUsageLogs` (configured but empty)

**Potential Usage:**
- Track ETL pipeline runs
- Store processing metadata
- Job queue management
- Cost tracking per job
- Error logs

---

## Recommended Architecture

### Current (Inefficient):
```
Local Machine
├── Extract PDFs (local)
├── Chunk text (local)
├── Generate embeddings (AWS Bedrock) ← Only AWS usage
├── Store ChromaDB (local)
└── Manual upload to S3 (optional, disabled)
```

### Optimized (Full AWS Integration):
```
Upload PDF to S3
    ↓
Lambda triggered (S3 event)
    ├── Extract text
    ├── Chunk text
    ├── Generate embeddings (Bedrock)
    ├── Create VKP package
    └── Store to S3
    ↓
CloudFront CDN
    └── Serve to users globally
    ↓
DynamoDB
    └── Track jobs, costs, metadata
```

---

## Implementation Priority

### Phase 1: Enable Existing S3 Upload (Quick Win)
**File:** `scripts/data/run_etl_pipeline.py`

**Change:**
```python
# Line 95: Change default from True to False
parser.add_argument(
    '--no-upload',
    action='store_true',
    help='Skip S3 upload phase'
)
# Should be: upload by default, add --no-upload to skip
```

**Impact:** Automatically backup processed data to S3

---

### Phase 2: Add DynamoDB Job Tracking
**New file:** `src/aws_control_plane/job_tracker.py`

**Features:**
- Record pipeline start/end
- Track costs per run
- Store error logs
- Query job history

---

### Phase 3: Deploy Lambda Processor
**Use existing:** `src/aws_control_plane/lambda_processor.py`

**Steps:**
1. Package Lambda function
2. Deploy to AWS
3. Configure S3 event trigger
4. Test with sample PDF

**Benefit:** Serverless, auto-scaling PDF processing

---

### Phase 4: Setup CloudFront CDN
**Use existing:** `src/aws_control_plane/cloudfront_manager.py`

**Steps:**
1. Create distribution pointing to S3
2. Configure cache rules
3. Enable HTTPS
4. Update app to use CloudFront URLs

**Benefit:** Faster global access, reduced S3 costs

---

## Cost Optimization

### Current Costs:
- Bedrock embeddings: ~$0.0001 per 1K tokens
- Local storage: Free but not backed up
- No CDN: Direct S3 access (slower, more expensive)

### With Full AWS Integration:
- S3 storage: ~$0.023/GB/month (STANDARD_IA)
- Lambda: $0.20 per 1M requests + compute time
- CloudFront: $0.085/GB (first 10TB)
- DynamoDB: $0.25/GB/month (on-demand)

**Estimated savings:** 40-60% on data transfer costs with CloudFront

---

## Action Items

### Immediate (This Week):
1. ✅ Fix ETL pipeline to upload to S3 by default
2. ✅ Add DynamoDB job tracking
3. ✅ Test S3 upload with sample data

### Short-term (Next 2 Weeks):
4. Deploy Lambda processor
5. Configure S3 event triggers
6. Test end-to-end serverless flow

### Long-term (Next Month):
7. Setup CloudFront distribution
8. Migrate existing data to S3
9. Update app to use CloudFront URLs
10. Monitor costs and optimize

---

## Files to Modify

### 1. Enable S3 Upload by Default
- `scripts/data/run_etl_pipeline.py` (line 95-99)

### 2. Add DynamoDB Tracking
- Create `src/aws_control_plane/job_tracker.py`
- Modify `src/data_processing/etl_pipeline.py` to use tracker

### 3. Deploy Lambda
- Use `src/aws_control_plane/lambda_processor.py`
- Create deployment script `scripts/aws/deploy_lambda.py`

### 4. Setup CloudFront
- Use `src/aws_control_plane/cloudfront_manager.py`
- Create setup script `scripts/aws/setup_cloudfront.py`

---

## Conclusion

**Current state:** 80% of AWS infrastructure code is unused
**Potential:** Full serverless, scalable, cost-optimized pipeline
**Effort:** Medium (most code already exists)
**ROI:** High (better performance, lower costs, auto-scaling)

**Next step:** Implement Phase 1 (enable S3 upload) immediately
