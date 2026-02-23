# 📁 Struktur Project OpenClass Nexus AI

**Last Updated:** 2026-02-22  
**Version:** 2.0 (Post-Reorganization)

---

## 🌳 Struktur Folder Utama

```
openclass-nexus-ai/
├── api_server.py              # FastAPI server utama
├── app.py                     # CLI interface (legacy)
├── README.md                  # Dokumentasi utama
├── CHANGELOG.md               # Log perubahan
├── CONTRIBUTING.md            # Panduan kontribusi
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Pytest configuration
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── start_web_ui.bat           # Windows launcher
├── start_web_ui.sh            # Linux/Mac launcher
│
├── frontend/                  # Web UI (HTML/CSS/JS)
│   ├── index.html
│   ├── pages/
│   ├── css/
│   └── js/
│
├── src/                       # Source code
│   ├── local_inference/       # RAG pipeline & inference
│   ├── embeddings/            # Embedding strategies
│   ├── data_processing/       # ETL pipeline
│   ├── cloud_sync/            # AWS integration
│   ├── telemetry/             # Telemetry & monitoring
│   └── ui/                    # UI utilities
│
├── scripts/                   # Utility scripts (REORGANIZED)
│   ├── system/                # System checks
│   ├── aws/                   # AWS operations
│   ├── data/                  # Data processing
│   ├── database/              # Database operations
│   ├── deployment/            # Deployment tools
│   ├── maintenance/           # Maintenance & cron
│   └── demo/                  # Demo & config tools
│
├── tests/                     # Test files
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   ├── property/              # Property-based tests
│   └── fixtures/              # Test fixtures
│
├── data/                      # Data storage
│   ├── raw_dataset/           # Raw PDF files
│   ├── processed/             # Processed data
│   ├── vector_db/             # ChromaDB storage
│   └── metadata/              # Metadata files
│
├── models/                    # LLM models
│   └── *.gguf                 # GGUF model files
│
├── config/                    # Configuration files
│   ├── app_config.py          # App configuration
│   ├── logging_config.py      # Logging configuration
│   └── version.json           # Version info
│
├── docs/                      # Documentation (REORGANIZED)
│   ├── README.md              # Documentation index
│   ├── architecture/          # Architecture docs
│   ├── development/           # Development guides
│   ├── deployment/            # Deployment guides
│   ├── guides/                # User guides
│   ├── technical/             # Technical docs
│   ├── user_guide/            # User documentation
│   ├── optimization/          # Optimization docs
│   ├── api/                   # API documentation
│   └── archive/               # Archived docs
│
├── database/                  # Database files
│   ├── nexusai.db             # SQLite database
│   └── schema.sql             # Database schema
│
├── backups/                   # Backup storage
│   └── README.md              # Backup strategy
│
└── systemd/                   # Systemd service files
    └── nexusai.service
```

---

## 📂 Penjelasan Folder Utama

### `frontend/`
Web UI untuk siswa, guru, dan admin.

```
frontend/
├── index.html                 # Landing page
├── pages/
│   ├── siswa.html            # Student interface
│   ├── guru.html             # Teacher interface
│   └── admin.html            # Admin interface
├── css/
│   └── styles.css            # Stylesheets
└── js/
    ├── main.js               # Main JavaScript
    ├── chat.js               # Chat functionality
    └── api.js                # API client
```

### `src/`
Source code utama aplikasi.

```
src/
├── local_inference/           # RAG & LLM inference
│   ├── rag_pipeline.py       # RAG orchestrator
│   ├── inference_engine.py   # LLM inference
│   ├── complete_pipeline.py  # Complete pipeline
│   ├── model_manager.py      # Model loading
│   └── educational_validator.py  # Content validation
│
├── embeddings/                # Embedding strategies
│   ├── chroma_manager.py     # ChromaDB operations
│   ├── bedrock_client.py     # AWS Bedrock client
│   └── local_embeddings_client.py  # Local embeddings
│
├── data_processing/           # ETL pipeline
│   ├── etl_pipeline.py       # Main ETL logic
│   ├── pdf_extractor.py      # PDF processing
│   ├── text_chunker.py       # Text chunking
│   └── metadata_extractor.py # Metadata extraction
│
├── cloud_sync/                # AWS integration
│   ├── s3_storage_manager.py # S3 operations
│   └── bedrock_integration.py # Bedrock integration
│
├── telemetry/                 # Telemetry & monitoring
│   └── telemetry_manager.py  # Telemetry collection
│
└── ui/                        # UI utilities
    └── ui_manager.py         # UI management
```

### `scripts/` (REORGANIZED)
Utility scripts terorganisir berdasarkan fungsi.

```
scripts/
├── README.md                  # Scripts documentation
│
├── system/                    # System verification
│   ├── check_system_ready.py
│   ├── check_embeddings.py
│   └── verify_system.py
│
├── aws/                       # AWS operations
│   ├── setup_aws.py
│   ├── test_aws_connection.py
│   ├── monitor_bedrock.py
│   ├── upload_to_s3.py
│   ├── download_from_s3.py
│   ├── upload_embeddings_to_s3.py
│   └── download_embeddings_from_s3.py
│
├── data/                      # Data processing
│   ├── run_etl_pipeline.py
│   ├── run_cloud_embeddings.py
│   └── reset_vector_db.py
│
├── database/                  # Database operations
│   ├── setup_database.py
│   ├── migrate_database_schema.py
│   ├── migrate_practice_questions_table.py
│   └── migrate_weak_areas_table.py
│
├── deployment/                # Deployment tools
│   ├── start_web_ui.py
│   ├── download_model.py
│   └── install_systemd_services.sh
│
├── maintenance/               # Maintenance & cron
│   ├── run_backup.py
│   ├── setup_backup_cron.sh
│   ├── telemetry_upload_cron.py
│   ├── setup_telemetry_cron.sh
│   ├── setup_telemetry_task_windows.ps1
│   ├── vkp_pull_cron.py
│   ├── setup_vkp_cron.sh
│   └── setup_vkp_task_windows.ps1
│
└── demo/                      # Demo & config
    ├── demo_pedagogical_features.py
    └── config_cli.py
```

### `tests/`
Test files terorganisir berdasarkan tipe.

```
tests/
├── __init__.py
├── conftest.py                # Pytest configuration
├── setup_test_database.py    # Test database setup
│
├── unit/                      # Unit tests
│   ├── test_rag_pipeline.py
│   ├── test_embeddings.py
│   └── test_etl.py
│
├── integration/               # Integration tests
│   ├── test_api_endpoints.py
│   └── test_full_pipeline.py
│
├── property/                  # Property-based tests
│   └── test_properties.py
│
├── fixtures/                  # Test fixtures
│   └── sample_data.json
│
└── checkpoint/                # Test checkpoints
    └── test_results.json
```

### `docs/` (REORGANIZED)
Dokumentasi terorganisir berdasarkan kategori.

```
docs/
├── README.md                  # Documentation index
│
├── architecture/              # Architecture documentation
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── deployment-scenarios.md
│   ├── architecture-analysis.md
│   └── WEB_UI_ARCHITECTURE.md
│
├── development/               # Development guides
│   ├── DEVELOPER_GUIDE.md
│   ├── development-strategy.md
│   ├── refactoring-roadmap.md
│   └── MODULAR_REFACTORING_GUIDE.md
│
├── deployment/                # Deployment guides
│   ├── DEPLOYMENT.md
│   ├── AWS_SETUP.md
│   ├── S3_SYNC_GUIDE.md
│   └── AWS_CONSOLE_MONITORING.md
│
├── guides/                    # User guides
│   ├── QUICK_START.md
│   ├── EMBEDDING_STRATEGY_GUIDE.md
│   ├── LOCAL_EMBEDDINGS_GUIDE.md
│   └── CLOUD_EMBEDDING_GUIDE.md
│
├── technical/                 # Technical documentation
│   ├── DATABASE_SCHEMA.md
│   ├── API_MODULAR_STRUCTURE.md
│   └── CACHING_LAYER.md
│
├── user_guide/                # User documentation
│   └── USER_GUIDE.md
│
├── optimization/              # Optimization docs
│   └── (optimization files)
│
├── api/                       # API documentation
│   └── (API docs)
│
└── archive/                   # Archived documentation
    ├── phase3-system-capabilities.md
    ├── phase10-implementation-summary.md
    ├── cleanup-summary.md
    ├── ui-comparison.md
    └── ui-mockup.md
```

---

## 🔑 File Penting

### Root Level

- `api_server.py` - FastAPI server utama, entry point aplikasi
- `app.py` - CLI interface (legacy, untuk backward compatibility)
- `README.md` - Dokumentasi utama project
- `requirements.txt` - Python dependencies
- `.env.example` - Template environment variables

### Configuration

- `config/app_config.py` - Konfigurasi aplikasi
- `config/logging_config.py` - Konfigurasi logging
- `config/version.json` - Informasi versi

### Database

- `database/nexusai.db` - SQLite database
- `database/schema.sql` - Database schema

---

## 📝 Naming Conventions

### Files
- Python files: `snake_case.py`
- Markdown files: `kebab-case.md` (lowercase)
- Config files: `snake_case.py` atau `kebab-case.json`

### Folders
- Lowercase dengan underscore: `local_inference/`
- Atau lowercase: `scripts/`, `docs/`

### Documentation
- Markdown files di docs/: `kebab-case.md`
- Contoh: `deployment-scenarios.md`, `architecture-analysis.md`

---

## 🔄 Perubahan dari Versi Sebelumnya

### Reorganisasi Scripts (v2.0)

**Before:**
```
scripts/
├── check_system_ready.py
├── setup_aws.py
├── run_etl_pipeline.py
└── (30+ files in flat structure)
```

**After:**
```
scripts/
├── system/
├── aws/
├── data/
├── database/
├── deployment/
├── maintenance/
└── demo/
```

### Reorganisasi Dokumentasi (v2.0)

**Before:**
```
docs/
├── SYSTEM_ARCHITECTURE.md
├── DEVELOPER_GUIDE.md
├── DEPLOYMENT.md
└── (20+ files in flat structure)
```

**After:**
```
docs/
├── architecture/
├── development/
├── deployment/
├── guides/
├── technical/
└── archive/
```

---

## 🚀 Quick Navigation

### Untuk Development
- Source code: `src/`
- Tests: `tests/`
- Scripts: `scripts/`
- Config: `config/`

### Untuk Deployment
- Deployment scripts: `scripts/deployment/`
- Deployment docs: `docs/deployment/`
- Systemd services: `systemd/`

### Untuk Documentation
- Main docs: `docs/`
- Architecture: `docs/architecture/`
- Development: `docs/development/`
- User guides: `docs/guides/`

---

## 📚 Related Documentation

- [Documentation Index](README.md)
- [Developer Guide](development/DEVELOPER_GUIDE.md)
- [System Architecture](architecture/SYSTEM_ARCHITECTURE.md)
- [Deployment Guide](deployment/DEPLOYMENT.md)

---

**Last Updated:** 2026-02-22  
**Maintained by:** Development Team
