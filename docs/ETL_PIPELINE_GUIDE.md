# 🔄 ETL Pipeline Quick Guide

**Last Updated:** 2025-02-23  
**Status:** ACTIVE

---

## 🚀 Quick Start

### Windows
```bash
# Activate environment
openclass-env\Scripts\activate.bat

# Run ETL pipeline (easiest way)
run_etl.bat

# Or with options
run_etl.bat --no-upload --log-level DEBUG
```

### Linux/Mac
```bash
# Activate environment
source openclass-env/bin/activate

# Run ETL pipeline (easiest way)
./run_etl.sh

# Or with options
./run_etl.sh --no-upload --log-level DEBUG
```

---

## ⏱️ Embedding Time Estimates

### AWS Bedrock (Cloud) - Default
```
1,000 chunks = ~2-3 minutes
5,000 chunks = ~8-12 minutes
10,000 chunks = ~15-20 minutes

Example: Informatika Kelas 10 (10 PDFs)
→ ~2,000 chunks = ~4-6 minutes
```

### Local MiniLM (CPU)
```
1,000 chunks = ~3-5 minutes
5,000 chunks = ~15-25 minutes
10,000 chunks = ~30-50 minutes

Example: Informatika Kelas 10 (10 PDFs)
→ ~2,000 chunks = ~6-10 minutes
```

### Local MiniLM (GPU)
```
1,000 chunks = ~40-80 seconds
5,000 chunks = ~3-7 minutes
10,000 chunks = ~7-14 minutes

Example: Informatika Kelas 10 (10 PDFs)
→ ~2,000 chunks = ~2-3 minutes
```

---

## 🎯 Where Does It Run?

### ETL Pipeline Location
**Answer:** Runs **locally** on your machine/server

### Embedding Generation Location
**Answer:** Depends on configuration:

#### Option 1: Cloud (Default)
```bash
# .env
EMBEDDING_STRATEGY=bedrock
```
- Embeddings generated in **AWS Bedrock** (cloud)
- Text processing happens **locally**
- Results stored **locally** in ChromaDB
- Optionally uploaded to S3

#### Option 2: Local
```bash
# .env
EMBEDDING_STRATEGY=local
```
- Everything runs **locally**
- No AWS required
- Fully offline

#### Option 3: Hybrid (Recommended)
```bash
# .env
EMBEDDING_STRATEGY=bedrock
FALLBACK_ENABLED=true
```
- Try AWS first
- Fallback to local if AWS unavailable

---

## 📊 Common Commands

### Basic Run
```bash
# Default settings
run_etl.bat
```

### Skip S3 Upload
```bash
# Process locally only
run_etl.bat --no-upload
```

### Custom Input Directory
```bash
# Process specific subject
run_etl.bat --input-dir data/raw_dataset/kelas_11/matematika
```

### Debug Mode
```bash
# Verbose logging
run_etl.bat --log-level DEBUG
```

### Custom Budget
```bash
# Set cost limit
run_etl.bat --budget 0.50
```

### With CloudFront Invalidation
```bash
# Invalidate CDN cache after upload
run_etl.bat --invalidate-cache
```

---

## 🔧 Troubleshooting

### Error: "Module not found"
**Solution:** Use wrapper scripts
```bash
# Windows
run_etl.bat

# Linux/Mac
./run_etl.sh
```

### Error: "AWS credentials not configured"
**Solution:** Either:
1. Configure AWS credentials in `.env`
2. Or use local embeddings: `EMBEDDING_STRATEGY=local`

### Error: "Out of memory"
**Solution:** Reduce batch size
```bash
run_etl.bat --batch-size 10
```

---

## 📁 Output Files

### Processed Text
```
data/processed/text/
├── file1.txt
├── file2.txt
└── ...
```

### Metadata
```
data/processed/metadata/
├── summary.json
├── quality_report.json
└── cost_report.json
```

### Vector Database
```
data/vector_db/
├── chroma.sqlite3
└── embeddings/
```

### S3 (if uploaded)
```
s3://bucket/processed/informatika/kelas_10/
├── chromadb/
├── text/
└── metadata/
```

---

## 💰 Cost Tracking

### View Job History
```bash
python scripts/aws/view_job_history.py
```

### View Cost Summary
```bash
python scripts/aws/view_job_history.py --cost-summary
```

### Example Output
```
Cost Summary (Last 7 Days)
==========================
Total jobs: 5
Total cost: $0.75
Average cost per job: $0.15
Cost per file: $0.015
Cost per embedding: $0.0000375
```

---

## 🎓 Full Documentation

For complete details, see:
- [AWS Services Integration](AWS_SERVICES_INTEGRATION.md)
- [Phase 13 Progress](PHASE_13_PROGRESS.md)
- [Architecture Analysis](ARCHITECTURE_ANALYSIS.md)

