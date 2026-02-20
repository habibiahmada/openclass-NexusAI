# 💾 Backup & Restore Guide

Panduan backup dan restore data sistem.

## Backup Vector Database

### Manual Backup

```bash
# Windows
xcopy /E /I data\vector_db backups\vector_db_%date:~-4,4%%date:~-10,2%%date:~-7,2%

# Linux/Mac
cp -r data/vector_db backups/vector_db_$(date +%Y%m%d)
```

### Automated Backup Script

Buat script `scripts/backup_vectordb.py`:

```python
import shutil
from datetime import datetime
from pathlib import Path

def backup_vectordb():
    source = Path("data/vector_db")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = Path(f"backups/vector_db_{timestamp}")
    
    if source.exists():
        shutil.copytree(source, dest)
        print(f"✅ Backup created: {dest}")
    else:
        print("❌ Vector DB not found")

if __name__ == "__main__":
    backup_vectordb()
```

## Restore Vector Database

```bash
# Windows
xcopy /E /I backups\vector_db_YYYYMMDD data\vector_db

# Linux/Mac
cp -r backups/vector_db_YYYYMMDD data/vector_db
```

## Backup to Cloud (S3)

```bash
# Upload to S3
python scripts/upload_embeddings_to_s3.py

# Download from S3
python scripts/download_embeddings_from_s3.py
```

## Backup Configuration

Backup file konfigurasi penting:

```bash
# Backup .env
cp .env backups/.env.backup

# Backup config files
cp -r config backups/config_backup
```

## Restore Checklist

1. Stop server jika sedang berjalan
2. Backup data existing (jika ada)
3. Restore vector database
4. Restore configuration files
5. Verify dengan `python scripts/check_embeddings.py`
6. Start server

## Backup Schedule Recommendation

- **Daily**: Vector database (jika ada perubahan)
- **Weekly**: Full backup (vector DB + config)
- **Before Update**: Full backup sebelum update sistem
- **After Embedding**: Backup setelah generate embeddings baru

## Storage Location

- **Local**: `backups/` folder
- **Cloud**: AWS S3 (optional)
- **External**: USB drive atau network storage (recommended)
