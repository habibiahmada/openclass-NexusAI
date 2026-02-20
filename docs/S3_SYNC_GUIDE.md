# S3 Sync Guide - Embeddings Backup & Distribution

Panduan untuk upload dan download embeddings ke/dari S3 untuk backup dan distribusi ke komputer lain.

## 📦 Struktur S3

```
s3://your-bucket/
├── model-weights/              # Model files (Llama, dll)
├── processed/
│   └── informatika/
│       └── kelas_10/
│           ├── text/           # Processed text files
│           ├── chromadb/       # Vector database (embeddings)
│           │   ├── chroma.sqlite3.gz
│           │   └── [UUID folders].gz
│           └── metadata/       # Progress & logs
│               ├── embedding_progress.json
│               └── [other metadata]
└── vector-db/                  # (Legacy, bisa dihapus)
```

## 🚀 Upload Embeddings ke S3

### Kapan Upload?
- Setelah embedding generation selesai
- Untuk backup
- Untuk distribusi ke komputer lain
- Untuk production deployment

### Cara Upload

```bash
python scripts/upload_embeddings_to_s3.py
```

### Yang Di-upload
1. **Vector Database (ChromaDB)**
   - Semua file di `data/vector_db/`
   - Compressed dengan gzip
   - Encrypted dengan AES256
   - Storage class: STANDARD_IA

2. **Metadata**
   - `embedding_progress.json`
   - Log files
   - Other metadata

### Output
```
======================================================================
Upload Embeddings to S3
======================================================================

Initializing S3 storage manager...
✓ Connected to bucket: your-bucket-name

======================================================================
1. Uploading Vector Database (ChromaDB)
======================================================================
Uploading data/vector_db
Found 25 files to upload
✓ Uploaded processed/informatika/kelas_10/chromadb/chroma.sqlite3.gz
✓ Uploaded processed/informatika/kelas_10/chromadb/[UUID]/...
...

ChromaDB Upload Results:
  Successful: 25
  Failed: 0
  Total bytes: 45.67 MB

======================================================================
2. Uploading Metadata Files
======================================================================
...

======================================================================
UPLOAD SUMMARY
======================================================================
Total files uploaded: 27
Total files failed: 0
Total data uploaded: 46.23 MB

✓ Upload selesai! Semua file berhasil di-upload ke S3
```

## 📥 Download Embeddings dari S3

### Kapan Download?
- Setup komputer baru
- Restore setelah data loss
- Sync dari production
- Testing di environment lain

### Cara Download

```bash
python scripts/download_embeddings_from_s3.py
```

### Yang Di-download
1. **Vector Database**
   - Download dari S3
   - Decompress otomatis
   - Simpan ke `data/vector_db/`

2. **Metadata**
   - Download progress files
   - Simpan ke `data/processed/metadata/`

### Output
```
======================================================================
Download Embeddings from S3
======================================================================

Connecting to S3 bucket: your-bucket-name
Listing files with prefix: processed/informatika/kelas_10/
Found 27 files to download

Downloading: processed/informatika/kelas_10/chromadb/chroma.sqlite3.gz
  ✓ Downloaded and decompressed to: data/vector_db/chroma.sqlite3
...

======================================================================
DOWNLOAD SUMMARY
======================================================================
Files downloaded: 27
Files failed: 0
Total data downloaded: 46.23 MB

Local paths:
  Vector DB: data/vector_db
  Metadata: data/processed/metadata

======================================================================
VERIFICATION
======================================================================
✓ ChromaDB collection loaded
✓ Total documents: 1250

✓ Download selesai! Embeddings berhasil di-download dari S3
```

## 🔄 Workflow: Development → Production

### 1. Development (Komputer Lokal)
```bash
# Generate embeddings
python scripts/run_cloud_embeddings.py

# Upload ke S3
python scripts/upload_embeddings_to_s3.py
```

### 2. Production (Server/Komputer Lain)
```bash
# Download dari S3
python scripts/download_embeddings_from_s3.py

# Verify
python scripts/check_embeddings.py

# Run aplikasi
streamlit run app.py
```

## 💰 Cost Optimization

### Storage Class: STANDARD_IA
- **Infrequent Access**: Lebih murah untuk data jarang diakses
- **Cost**: ~$0.0125 per GB/month
- **Retrieval**: $0.01 per GB
- **Ideal untuk**: Backup, distribusi

### Compression
- Files di-compress dengan gzip
- Compression ratio: ~60-70%
- Menghemat storage & transfer cost

### Encryption
- Server-side encryption: AES256
- No additional cost
- Data aman di S3

## 🔍 Verifikasi Upload/Download

### Cek di S3 Console
```
https://s3.console.aws.amazon.com/s3/buckets/your-bucket?prefix=processed/informatika/kelas_10/
```

### Cek Lokal
```bash
# Check embeddings
python scripts/check_embeddings.py

# Test query
python -c "from src.embeddings.chroma_manager import ChromaDBManager; chroma = ChromaDBManager(); chroma.get_collection('educational_content'); print(f'Docs: {chroma.count_documents()}')"
```

### List Files di S3
```bash
aws s3 ls s3://your-bucket/processed/informatika/kelas_10/ --recursive
```

## 🚨 Troubleshooting

### Upload Failed
```bash
# Check AWS credentials
python scripts/test_aws_connection.py

# Check bucket permissions
aws s3 ls s3://your-bucket/

# Retry upload
python scripts/upload_embeddings_to_s3.py
```

### Download Failed
```bash
# Check S3 files exist
aws s3 ls s3://your-bucket/processed/informatika/kelas_10/

# Check local permissions
# Ensure data/ directory is writable

# Retry download
python scripts/download_embeddings_from_s3.py
```

### Decompression Error
```bash
# Check gzip files
gzip -t data/vector_db/*.gz

# Manual decompress
gzip -d data/vector_db/chroma.sqlite3.gz
```

## 📊 Monitoring

### S3 Metrics
- **Storage**: CloudWatch → S3 → BucketSizeBytes
- **Requests**: CloudWatch → S3 → AllRequests
- **Cost**: Cost Explorer → S3

### Upload/Download Progress
- Monitor terminal output
- Check log files
- Verify file counts

## 🔐 Security Best Practices

1. **Encryption at Rest**: AES256 (enabled)
2. **Encryption in Transit**: HTTPS (default)
3. **Access Control**: IAM policies
4. **Bucket Policy**: Restrict public access
5. **Versioning**: Enable for backup

## 💡 Tips

1. **Upload setelah embedding selesai** untuk backup
2. **Download di production** untuk deployment
3. **Compress files** untuk hemat cost
4. **Use STANDARD_IA** untuk storage jarang diakses
5. **Monitor cost** di Cost Explorer
6. **Set lifecycle policy** untuk auto-archive

## 📚 Related Documentation

- [Cloud Embedding Guide](CLOUD_EMBEDDING_GUIDE.md)
- [AWS Console Monitoring](AWS_CONSOLE_MONITORING.md)
- [Quick Reference](../QUICK_REFERENCE.md)

---

**Happy Syncing!** 🔄
