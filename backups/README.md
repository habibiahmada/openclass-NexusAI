# 💾 Backups Directory

Folder ini untuk menyimpan backup data sistem.

## 📁 Struktur

```
backups/
├── README.md                    # File ini
├── backup_YYYYMMDD_HHMMSS.json # Backup konfigurasi
├── vector_db_YYYYMMDD/         # Backup vector database
├── .env.backup                 # Backup environment variables
└── config_backup/              # Backup config files
```

## 🔄 Cara Backup

Lihat [Backup & Restore Guide](../docs/guides/BACKUP_RESTORE.md) untuk panduan lengkap.

### Quick Backup

```bash
# Backup vector database
python scripts/backup_vectordb.py

# Backup ke S3
python scripts/upload_embeddings_to_s3.py
```

## ⚠️ Catatan

- File backup tidak di-commit ke Git (lihat .gitignore)
- Simpan backup penting di external storage atau cloud
- Backup sebelum update atau perubahan besar
- Hapus backup lama secara berkala untuk menghemat space

## 📅 Backup Schedule

- **Daily**: Jika ada perubahan data
- **Weekly**: Full backup
- **Before Update**: Wajib backup
- **After Embedding**: Backup vector DB baru
