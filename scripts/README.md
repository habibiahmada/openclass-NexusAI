# 📁 Scripts Directory

Utility scripts untuk maintenance dan operasi sistem.

## 🔍 System Check & Verification

### `check_system_ready.py`
Verifikasi sistem siap digunakan (dependencies, model, vector DB).

```bash
python scripts/check_system_ready.py
```

### `check_embeddings.py`
Cek status vector database dan embeddings.

```bash
python scripts/check_embeddings.py
```

## 🚀 Deployment & Setup

### `start_web_ui.py`
Launcher untuk web UI dengan pre-flight checks.

```bash
python scripts/start_web_ui.py
```

### `download_model.py`
Download model LLM dari Hugging Face.

```bash
python scripts/download_model.py
```

## ☁️ AWS Operations

### `setup_aws.py`
Setup AWS credentials dan konfigurasi.

```bash
python scripts/setup_aws.py
```

### `test_aws_connection.py`
Test koneksi ke AWS Bedrock.

```bash
python scripts/test_aws_connection.py
```

### `run_cloud_embeddings.py`
Generate embeddings menggunakan AWS Bedrock.

```bash
python scripts/run_cloud_embeddings.py
```

### `upload_to_s3.py` / `download_from_s3.py`
Upload/download data ke/dari S3.

```bash
python scripts/upload_to_s3.py
python scripts/download_from_s3.py
```

### `upload_embeddings_to_s3.py` / `download_embeddings_from_s3.py`
Upload/download vector database ke/dari S3.

```bash
python scripts/upload_embeddings_to_s3.py
python scripts/download_embeddings_from_s3.py
```

### `monitor_bedrock.py`
Monitor penggunaan AWS Bedrock.

```bash
python scripts/monitor_bedrock.py
```

## 🔧 Data Processing

### `run_etl_pipeline.py`
Jalankan ETL pipeline (extract PDF ke text).

```bash
python scripts/run_etl_pipeline.py
```

### `reset_vector_db.py`
Reset vector database (hapus semua data).

```bash
python scripts/reset_vector_db.py
```

## ⚙️ Configuration

### `config_cli.py`
CLI untuk konfigurasi sistem.

```bash
python scripts/config_cli.py
```

## 📂 Deployment Scripts

Folder `deployment/` berisi scripts untuk deployment production.

Lihat `deployment/README.md` untuk detail.
