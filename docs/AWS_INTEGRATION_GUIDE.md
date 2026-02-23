# AWS Integration Guide

## Overview

Project ini sekarang **fully integrated** dengan AWS services untuk production-ready deployment.

## What Changed?

### ✅ Phase 1 Implemented (Completed)

1. **S3 Upload Enabled by Default**
   - Processed files automatically uploaded to S3
   - ChromaDB backups stored in cloud
   - Gzip compression for bandwidth savings
   - Server-side encryption (AES256)

2. **DynamoDB Job Tracking**
   - Every pipeline run tracked in DynamoDB
   - Cost monitoring per job
   - Error logging
   - Performance metrics

3. **Cost Analytics**
   - 7-day cost summary
   - Cost per file/embedding
   - Job history queries

## Quick Start

### 1. Setup AWS Credentials

Create `.env` file:
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-southeast-2

# S3 Configuration
S3_BUCKET_NAME=your-bucket-name

# Bedrock Configuration
BEDROCK_REGION=ap-southeast-2
BEDROCK_MODEL_ID=amazon.titan-embed-text-v2:0

# DynamoDB (optional, will auto-create)
DYNAMODB_TABLE_NAME=ETLPipelineJobs
```

### 2. Run ETL Pipeline (with S3 upload)

```bash
# Default: uploads to S3
python scripts/data/run_etl_pipeline.py

# Skip S3 upload (local only)
python scripts/data/run_etl_pipeline.py --no-upload

# Custom settings
python scripts/data/run_etl_pipeline.py \
  --input-dir data/raw_dataset/kelas_10/informatika \
  --budget 2.0 \
  --log-level DEBUG
```

### 3. View Job History

```bash
# View recent jobs
python scripts/aws/view_job_history.py

# View last 20 jobs
python scripts/aws/view_job_history.py --limit 20

# Filter by status
python scripts/aws/view_job_history.py --status completed

# Get specific job
python scripts/aws/view_job_history.py --job-id etl_pipeline_2024-02-23T10-30-00

# Cost summary
python scripts/aws/view_job_history.py --cost-summary

# JSON output
python scripts/aws/view_job_history.py --json
```

## Architecture

### Before (Local Only):
```
Local Machine
├── Extract PDFs
├── Chunk text
├── Generate embeddings (AWS Bedrock)
└── Store ChromaDB (local only)
```

### After (AWS Integrated):
```
Local Machine
├── Extract PDFs
├── Chunk text
├── Generate embeddings (AWS Bedrock)
├── Store ChromaDB (local)
└── Upload to S3 ✨ NEW
    ├── ChromaDB files (compressed)
    ├── Processed text files
    └── Metadata files

DynamoDB ✨ NEW
└── Track jobs, costs, errors
```

## AWS Services Used

### 1. S3 (Simple Storage Service)
**Purpose:** Store processed data and ChromaDB backups

**Features:**
- Automatic gzip compression
- Server-side encryption (AES256)
- STANDARD_IA storage class (cost-optimized)
- Versioning support

**S3 Path Structure:**
```
s3://your-bucket/
└── processed/
    └── {subject}/
        └── {grade}/
            ├── chromadb/
            │   ├── chroma.sqlite3.gz
            │   └── ...
            ├── text/
            │   ├── file1.txt.gz
            │   └── file2.txt.gz
            └── metadata/
                ├── pipeline_report.json
                └── quality_report.json
```

**Cost:** ~$0.0125/GB/month (STANDARD_IA)

### 2. Bedrock (AI/ML Service)
**Purpose:** Generate embeddings using Titan model

**Model:** `amazon.titan-embed-text-v2:0`
**Dimensions:** 1024
**Cost:** $0.0001 per 1K tokens

**Usage:**
- Batch processing (25 chunks per batch)
- Automatic retry with exponential backoff
- Rate limiting (2s delay between requests)

### 3. DynamoDB (NoSQL Database)
**Purpose:** Track pipeline jobs and costs

**Table:** `ETLPipelineJobs`
**Billing:** Pay-per-request (on-demand)

**Schema:**
```
Primary Key:
- job_id (String) - Partition key
- timestamp (String) - Sort key

Attributes:
- status (String) - "running", "completed", "failed", "partial"
- job_type (String) - "etl_pipeline"
- input_dir (String)
- total_files (Number)
- successful_files (Number)
- failed_files (Number)
- total_chunks (Number)
- total_embeddings (Number)
- processing_time (Number)
- estimated_cost (Number)
- errors (String) - JSON array
- started_at (String) - ISO timestamp
- completed_at (String) - ISO timestamp
```

**Cost:** $0.25/GB/month + $1.25 per million write requests

### 4. CloudFront (CDN) - Coming Soon
**Purpose:** Serve embeddings globally with low latency

**Status:** Code ready, not yet deployed
**Next Phase:** Phase 4

### 5. Lambda (Serverless Compute) - Coming Soon
**Purpose:** Serverless PDF processing

**Status:** Code ready, not yet deployed
**Next Phase:** Phase 3

## Cost Estimation

### Current Usage (15 PDFs, ~3000 chunks):

| Service | Usage | Cost |
|---------|-------|------|
| Bedrock Embeddings | ~750K tokens | $0.075 |
| S3 Storage | ~500 MB | $0.006/month |
| S3 Upload | 500 MB | $0.005 |
| DynamoDB | 1 job record | $0.000125 |
| **Total per run** | | **~$0.08** |

### Monthly Cost (4 runs/month):
- Bedrock: $0.30
- S3 Storage: $0.006
- S3 Uploads: $0.02
- DynamoDB: $0.0005
- **Total: ~$0.33/month**

## Monitoring & Analytics

### Job Tracking
Every pipeline run is tracked with:
- Start/end timestamps
- Files processed (success/failure)
- Chunks and embeddings generated
- Processing time
- Estimated cost
- Error messages

### Cost Analytics
View cost trends:
```bash
python scripts/aws/view_job_history.py --cost-summary
```

Output:
```
Cost Summary (Last 7 Days)
============================================================
Total jobs: 5
Total cost: $0.4250
Average cost per job: $0.0850
Total files processed: 75
Total embeddings: 15000
Cost per file: $0.005667
Cost per embedding: $0.00002833
============================================================
```

## Troubleshooting

### Issue: "No module named 'src'"
**Solution:** Run from project root:
```bash
cd /path/to/NexusAI
python scripts/data/run_etl_pipeline.py
```

### Issue: "S3 bucket not configured"
**Solution:** Set `S3_BUCKET_NAME` in `.env`:
```bash
S3_BUCKET_NAME=your-bucket-name
```

### Issue: "DynamoDB table creation failed"
**Solution:** Check AWS credentials and permissions:
```bash
aws sts get-caller-identity
aws dynamodb list-tables
```

### Issue: "Rate limit exceeded"
**Solution:** Increase delays in `bedrock_client.py`:
```python
time.sleep(3)  # Increase from 2 to 3 seconds
```

## Next Steps

### Phase 2: Enhanced Monitoring (Next Week)
- CloudWatch metrics integration
- Email alerts for failures
- Cost threshold warnings
- Performance dashboards

### Phase 3: Lambda Deployment (2 Weeks)
- Deploy serverless PDF processor
- S3 event triggers
- Auto-scaling
- Reduced local processing

### Phase 4: CloudFront CDN (1 Month)
- Global content delivery
- Cache optimization
- HTTPS-only access
- Reduced S3 costs

## Security Best Practices

1. **Never commit `.env` file**
   - Already in `.gitignore`
   - Use AWS Secrets Manager for production

2. **Use IAM roles with minimal permissions**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "bedrock:InvokeModel",
           "dynamodb:PutItem",
           "dynamodb:GetItem",
           "dynamodb:Query"
         ],
         "Resource": [
           "arn:aws:s3:::your-bucket/*",
           "arn:aws:bedrock:*:*:model/*",
           "arn:aws:dynamodb:*:*:table/ETLPipelineJobs"
         ]
       }
     ]
   }
   ```

3. **Enable S3 bucket versioning**
   ```bash
   aws s3api put-bucket-versioning \
     --bucket your-bucket \
     --versioning-configuration Status=Enabled
   ```

4. **Enable CloudTrail logging**
   - Track all API calls
   - Audit access patterns
   - Detect anomalies

## Support

For issues or questions:
1. Check logs: `data/processed/metadata/pipeline_report.json`
2. View job history: `python scripts/aws/view_job_history.py`
3. Check AWS CloudWatch logs
4. Review DynamoDB job records

## References

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Project Architecture](./AWS_SERVICES_OPTIMIZATION.md)
