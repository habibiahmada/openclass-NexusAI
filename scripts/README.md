# 📁 Scripts Directory

Utility scripts untuk maintenance dan operasi sistem, terorganisir berdasarkan fungsi.

## 📂 Struktur Folder

```
scripts/
├── system/         # System verification & checks
├── aws/            # AWS operations
├── data/           # Data processing & ETL
├── database/       # Database operations
├── deployment/     # Deployment & setup
├── maintenance/    # Maintenance & cron jobs
└── demo/           # Demo & configuration tools
```

---

## 🔍 System Check & Verification

### `system/check_system_ready.py`
Verifikasi sistem siap digunakan (dependencies, model, vector DB).

```bash
python scripts/system/check_system_ready.py
```

### `system/check_embeddings.py`
Cek status vector database dan embeddings.

```bash
python scripts/system/check_embeddings.py
```

### `system/verify_system.py`
Verifikasi komponen sistem secara menyeluruh.

```bash
python scripts/system/verify_system.py
```

---

## ☁️ AWS Operations

### `aws/setup_aws.py`
Setup AWS credentials dan konfigurasi.

```bash
python scripts/aws/setup_aws.py
```

### `aws/test_aws_connection.py`
Test koneksi ke AWS Bedrock.

```bash
python scripts/aws/test_aws_connection.py
```

### `aws/monitor_bedrock.py`
Monitor penggunaan AWS Bedrock.

```bash
python scripts/aws/monitor_bedrock.py
```

### `aws/upload_to_s3.py`
Upload data ke S3.

```bash
python scripts/aws/upload_to_s3.py
```

### `aws/download_from_s3.py`
Download data dari S3.

```bash
python scripts/aws/download_from_s3.py
```

### `aws/upload_embeddings_to_s3.py`
Upload vector database ke S3.

```bash
python scripts/aws/upload_embeddings_to_s3.py
```

### `aws/download_embeddings_from_s3.py`
Download vector database dari S3.

```bash
python scripts/aws/download_embeddings_from_s3.py
```

---

## 🔧 Data Processing

### `data/run_etl_pipeline.py`
Jalankan ETL pipeline (extract PDF ke text).

```bash
python scripts/data/run_etl_pipeline.py
```

### `data/run_cloud_embeddings.py`
Generate embeddings menggunakan AWS Bedrock.

```bash
python scripts/data/run_cloud_embeddings.py
```

### `data/reset_vector_db.py`
Reset vector database (hapus semua data).

```bash
python scripts/data/reset_vector_db.py
```

---

## 🗄️ Database Operations

### `database/setup_database.py`
Setup database schema dan initial data.

```bash
python scripts/database/setup_database.py
```

### `database/migrate_database_schema.py`
Migrate database schema ke versi terbaru.

```bash
python scripts/database/migrate_database_schema.py
```

### `database/migrate_practice_questions_table.py`
Migrate practice questions table.

```bash
python scripts/database/migrate_practice_questions_table.py
```

### `database/migrate_weak_areas_table.py`
Migrate weak areas table.

```bash
python scripts/database/migrate_weak_areas_table.py
```

---

## 🚀 Deployment & Setup

### `deployment/start_web_ui.py`
Launcher untuk web UI dengan pre-flight checks.

```bash
python scripts/deployment/start_web_ui.py
```

### `deployment/download_model.py`
Download model LLM dari Hugging Face.

```bash
python scripts/deployment/download_model.py
```

### `deployment/install_systemd_services.sh`
Install systemd services untuk auto-start (Linux).

```bash
sudo bash scripts/deployment/install_systemd_services.sh
```

---

## 🔄 Maintenance & Cron Jobs

### `maintenance/run_backup.py`
Jalankan backup database dan vector DB.

```bash
python scripts/maintenance/run_backup.py
```

### `maintenance/setup_backup_cron.sh`
Setup cron job untuk backup otomatis (Linux).

```bash
bash scripts/maintenance/setup_backup_cron.sh
```

### `maintenance/telemetry_upload_cron.py`
Upload telemetry data ke AWS (cron job).

```bash
python scripts/maintenance/telemetry_upload_cron.py
```

### `maintenance/setup_telemetry_cron.sh`
Setup cron job untuk telemetry upload (Linux).

```bash
bash scripts/maintenance/setup_telemetry_cron.sh
```

### `maintenance/setup_telemetry_task_windows.ps1`
Setup scheduled task untuk telemetry upload (Windows).

```powershell
.\scripts\maintenance\setup_telemetry_task_windows.ps1
```

### `maintenance/vkp_pull_cron.py`
Pull VKP (Versioned Knowledge Package) updates dari AWS.

```bash
python scripts/maintenance/vkp_pull_cron.py
```

### `maintenance/setup_vkp_cron.sh`
Setup cron job untuk VKP pull (Linux).

```bash
bash scripts/maintenance/setup_vkp_cron.sh
```

### `maintenance/setup_vkp_task_windows.ps1`
Setup scheduled task untuk VKP pull (Windows).

```powershell
.\scripts\maintenance\setup_vkp_task_windows.ps1
```

---

## 🎮 Demo & Configuration

### `demo/demo_pedagogical_features.py`
Demo fitur pedagogical (mastery tracking, weak areas, dll).

```bash
python scripts/demo/demo_pedagogical_features.py
```

### `demo/config_cli.py`
CLI untuk konfigurasi sistem interaktif.

```bash
python scripts/demo/config_cli.py
```

---

## 📝 Notes

- Semua scripts dapat dijalankan dari root directory project
- Scripts yang memerlukan AWS credentials akan membaca dari `.env` atau AWS CLI config
- Untuk production deployment, gunakan scripts di folder `deployment/` dan `maintenance/`
- Cron jobs dan scheduled tasks harus di-setup setelah deployment

---

## 🔗 Related Documentation

- [Deployment Guide](../docs/deployment/DEPLOYMENT.md)
- [AWS Setup Guide](../docs/deployment/AWS_SETUP.md)
- [Developer Guide](../docs/development/DEVELOPER_GUIDE.md)
