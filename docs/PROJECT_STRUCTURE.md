# 📁 Project Structure

Struktur folder dan file OpenClass Nexus AI.

## 🌳 Directory Tree

```
openclass-nexus-ai/
│
├── 📄 Root Files
│   ├── README.md                  # Project overview
│   ├── CHANGELOG.md               # Version history
│   ├── CONTRIBUTING.md            # Contribution guide
│   ├── requirements.txt           # Python dependencies
│   ├── pytest.ini                 # Test configuration
│   ├── .env.example               # Environment template
│   ├── .gitignore                 # Git ignore rules
│   │
│   ├── api_server.py              # Main API server (FastAPI)
│   ├── app.py                     # CLI interface (legacy)
│   ├── start_web_ui.bat           # Windows launcher
│   └── start_web_ui.sh            # Linux/Mac launcher
│
├── 📁 src/                        # Source code
│   ├── etl/                       # ETL pipeline
│   │   ├── pdf_extractor.py      # PDF to text extraction
│   │   ├── text_processor.py     # Text processing
│   │   └── pipeline.py            # ETL orchestration
│   │
│   └── local_inference/           # RAG & Inference
│       ├── rag_pipeline.py        # RAG implementation
│       ├── inference_engine.py    # LLM inference
│       ├── complete_pipeline.py   # Complete pipeline
│       └── vector_store.py        # Vector DB operations
│
├── 📁 frontend/                   # Web UI
│   ├── index.html                 # Landing page
│   ├── css/                       # Stylesheets
│   │   ├── variables.css
│   │   ├── base.css
│   │   ├── components.css
│   │   ├── landing.css
│   │   ├── chat.css
│   │   └── dashboard.css
│   │
│   ├── js/                        # JavaScript
│   │   ├── common.js              # Shared utilities
│   │   ├── landing.js             # Landing page logic
│   │   ├── siswa.js               # Student interface
│   │   ├── guru.js                # Teacher interface
│   │   └── admin.js               # Admin interface
│   │
│   └── pages/                     # HTML pages
│       ├── siswa.html
│       ├── guru.html
│       └── admin.html
│
├── 📁 scripts/                    # Utility scripts (17 files)
│   ├── README.md                  # Scripts documentation
│   ├── check_system_ready.py     # System verification
│   ├── check_embeddings.py       # Embedding verification
│   ├── start_web_ui.py            # Web UI launcher
│   ├── run_etl_pipeline.py       # ETL runner
│   ├── run_cloud_embeddings.py   # Cloud embedding
│   ├── download_model.py         # Model downloader
│   ├── setup_aws.py               # AWS setup
│   ├── test_aws_connection.py    # AWS test
│   └── ...                        # Other utilities
│
├── 📁 config/                     # Configuration
│   ├── app_config.py              # App configuration
│   ├── aws_config.py              # AWS configuration
│   ├── openclass_config.yaml     # Main config file
│   └── templates/                 # Config templates
│
├── 📁 data/                       # Data storage
│   ├── raw_dataset/               # Original PDFs
│   │   └── kelas_10/informatika/
│   ├── processed/                 # Processed data
│   │   ├── text/                  # Extracted text
│   │   └── metadata/              # Processing logs
│   └── vector_db/                 # ChromaDB storage
│
├── 📁 models/                     # LLM models
│   └── *.gguf                     # GGUF model files
│
├── 📁 tests/                      # Test files
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── e2e/                       # End-to-end tests
│
├── 📁 examples/                   # Example scripts
│   ├── rag_pipeline_example.py
│   ├── validation_example.py
│   └── ...
│
├── 📁 backups/                    # Backup storage
│   └── README.md                  # Backup guide
│
└── 📁 docs/                       # Documentation (24 files)
    ├── README.md                  # Documentation index
    │
    ├── guides/                    # User guides
    │   ├── QUICK_START.md
    │   ├── DEPLOYMENT.md
    │   ├── AUTHENTICATION.md
    │   └── BACKUP_RESTORE.md
    │
    ├── technical/                 # Technical docs
    │   ├── ARCHITECTURE_NOTES.md
    │   └── BUGFIXES.md
    │
    ├── deployment/                # Deployment docs
    │   └── PRODUCTION_DEPLOYMENT.md
    │
    ├── archive/                   # Historical docs
    │   ├── phase1/
    │   ├── phase2/
    │   └── phase3/
    │
    └── [Other documentation files]
```

## 📊 Statistics

- **Root files**: 13 files (cleaned from 27+)
- **Documentation**: 24 markdown files (organized in docs/)
- **Scripts**: 17 utility scripts (cleaned from 30+)
- **Source code**: Modular structure in src/
- **Frontend**: Separated HTML/CSS/JS

## 🎯 Key Improvements

### Before Cleanup
- 14+ .md files scattered in root
- 30+ scripts (many one-time use)
- Unorganized documentation
- optimization_output/ folder
- Test files in root

### After Cleanup
- Clean root with only essential files
- 17 useful scripts with documentation
- Organized docs/ structure
- Removed temporary folders
- Tests in tests/ folder

## 📝 File Naming Conventions

- **UPPERCASE.md**: Important documentation (README, CHANGELOG, CONTRIBUTING)
- **lowercase.py**: Python source files
- **lowercase.html/css/js**: Frontend files
- **snake_case**: Python modules and scripts
- **kebab-case**: Frontend files (optional)

## 🔍 Finding Files

- **Documentation**: Check `docs/README.md` first
- **Scripts**: Check `scripts/README.md`
- **Source code**: Look in `src/`
- **Frontend**: Look in `frontend/`
- **Configuration**: Look in `config/`

## 🚀 Quick Navigation

- Start here: [README.md](../README.md)
- Documentation: [docs/README.md](README.md)
- Quick start: [docs/guides/QUICK_START.md](guides/QUICK_START.md)
- Development: [docs/DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
