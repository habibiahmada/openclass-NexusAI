# OpenClass Nexus AI - Project Structure

## Current Status: Phase 1 Completed ✅

This document outlines the organized project structure after Phase 1 completion.

## Directory Structure

```
openclass-nexus/
├── .env                          # Environment variables (not tracked)
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules (updated)
├── README.md                     # Main project documentation
├── SETUP_GUIDE.md               # Installation and setup guide
├── requirements.txt              # Python dependencies
├── legal_compliance.md          # Legal documentation
├── dataset_inventory.json       # Educational content metadata
├── PROJECT_STRUCTURE.md         # This file
│
├── .kiro/                       # Kiro specs directory
│   └── specs/
│       └── offline-ai-tutor/
│           └── requirements.md   # Feature requirements
│
├── src/                         # Source code modules
│   ├── data_processing/         # PDF processing and text extraction
│   │   └── __init__.py
│   ├── embeddings/              # Vector embeddings creation
│   │   └── __init__.py
│   ├── local_inference/         # AI inference engine
│   │   └── __init__.py
│   ├── ui/                      # Streamlit user interface
│   │   └── __init__.py
│   ├── cloud_sync/              # AWS synchronization
│   │   └── __init__.py
│   └── telemetry/               # Usage analytics
│       └── __init__.py
│
├── data/                        # Data storage (not tracked)
│   ├── processed/               # Processed text content
│   │   └── .gitignore
│   └── vector_db/               # ChromaDB vector database
│   │   └── .gitignore
│   └──raw_dataset/                 # Educational content structure (PDFs in S3)
│      ├── README.md                # S3 storage explanation
│      └── kelas_10/
│          └── informatika/         # Computer Science materials
│               └── .gitkeep         # Maintains folder structure (PDFs in S3)
│
├── models/                      # AI model storage (not tracked)
│   └── .gitignore
│
├── config/                      # Configuration files
│   ├── .gitignore
│   ├── app_config.py            # Application settings
│   ├── aws_config.py            # AWS service configuration
│   └── __pycache__/             # Python cache (not tracked)
│
├── scripts/                     # Utility scripts
│   ├── .gitignore
│   ├── download_sample_data.py  # Data acquisition script
│   ├── setup_aws.py             # AWS infrastructure setup
│   └── test_aws_connection.py   # Connectivity validation
│
├── tests/                       # Test files
│   └── .gitignore
│
├── docs/                        # Documentation
│   ├── .gitignore
│   └── phase1/                  # Phase 1 documentation
│       ├── fase1_checklist.md
│       ├── fase1_completion_report.md
│       ├── fase1_structure_verification.md
│       └── README.md
│
└── openclass-env/               # Virtual environment (not tracked)
```

## Files Removed/Cleaned Up

- ❌ `AWS_ACCESS.txt` - Removed (security risk, should not be tracked)
- ❌ `raw_dataset/**/*.pdf` - Moved to S3 (large files, better storage)
- ✅ Updated `.gitignore` with comprehensive rules including PDF exclusion
- ✅ Updated `dataset_inventory.json` with S3 keys and AWS configuration
- ✅ Created `raw_dataset/README.md` explaining S3 storage architecture
- ✅ Created `scripts/upload_to_s3.py` for PDF management

## Phase 1 Achievements

### ✅ Data Acquisition (Langkah 1.1)
- **15 PDF files** from BSE Kemdikbud successfully uploaded to S3 (140.6 MB)
- **S3 Storage**: PDFs stored in `s3://openclass-nexus-data/raw-pdf/`
- **Organized structure**: Proper folder hierarchy maintained
- **Legal compliance**: All materials verified as open educational resources
- **Metadata system**: Complete inventory with S3 keys in `dataset_inventory.json`
- **Upload completed**: 2026-01-10, all files verified accessible

### ✅ AWS Infrastructure (Langkah 1.2)
- **Cost control**: $1.00 budget with alerts
- **S3 bucket**: `openclass-nexus-data` configured
- **DynamoDB**: `StudentUsageLogs` table ready
- **Security**: IAM roles with minimal permissions
- **Lifecycle policies**: Auto-cleanup after 30 days

### ✅ Environment Setup (Langkah 1.3)
- **Python 3.13.8**: Virtual environment configured
- **Dependencies**: All required packages installed
- **AWS CLI**: Configured and tested
- **Project structure**: Complete module organization
- **Configuration**: Environment variables and settings

## Next Steps (Phase 2)

Ready to proceed with:
1. **PDF Text Extraction** - Process 15 educational PDFs
2. **Vector Embeddings** - Create knowledge base using Bedrock
3. **ChromaDB Setup** - Local vector database implementation
4. **Model Quantization** - Prepare GGUF models for offline use

## Development Guidelines

### Git Workflow
- Use feature branches for development
- All sensitive files are properly ignored
- Commit messages should reference phase/task numbers

### Code Organization
- Each module has clear separation of concerns
- Configuration is centralized in `config/`
- Tests should mirror the `src/` structure

### Security
- Never commit AWS credentials
- Use environment variables for sensitive data
- Follow principle of least privilege for AWS permissions

---

**Status**: Phase 1 Complete ✅  
**Next Phase**: Backend Infrastructure & Knowledge Engineering  
**Last Updated**: 2026-01-10