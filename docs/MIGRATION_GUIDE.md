# 🔄 Migration Guide: Struktur Project Baru

**Tanggal:** 2026-02-22  
**Untuk:** Developer yang sudah familiar dengan struktur lama

---

## 📋 Overview

Project OpenClass Nexus AI telah direorganisasi untuk meningkatkan maintainability dan clarity. Panduan ini membantu Anda beradaptasi dengan struktur baru.

---

## 🗺️ Path Mapping: Old → New

### Scripts

| Old Path | New Path | Category |
|----------|----------|----------|
| `scripts/check_system_ready.py` | `scripts/system/check_system_ready.py` | System |
| `scripts/check_embeddings.py` | `scripts/system/check_embeddings.py` | System |
| `scripts/verify_system.py` | `scripts/system/verify_system.py` | System |
| `scripts/setup_aws.py` | `scripts/aws/setup_aws.py` | AWS |
| `scripts/test_aws_connection.py` | `scripts/aws/test_aws_connection.py` | AWS |
| `scripts/monitor_bedrock.py` | `scripts/aws/monitor_bedrock.py` | AWS |
| `scripts/upload_to_s3.py` | `scripts/aws/upload_to_s3.py` | AWS |
| `scripts/download_from_s3.py` | `scripts/aws/download_from_s3.py` | AWS |
| `scripts/upload_embeddings_to_s3.py` | `scripts/aws/upload_embeddings_to_s3.py` | AWS |
| `scripts/download_embeddings_from_s3.py` | `scripts/aws/download_embeddings_from_s3.py` | AWS |
| `scripts/run_etl_pipeline.py` | `scripts/data/run_etl_pipeline.py` | Data |
| `scripts/run_cloud_embeddings.py` | `scripts/data/run_cloud_embeddings.py` | Data |
| `scripts/reset_vector_db.py` | `scripts/data/reset_vector_db.py` | Data |
| `scripts/setup_database.py` | `scripts/database/setup_database.py` | Database |
| `scripts/migrate_database_schema.py` | `scripts/database/migrate_database_schema.py` | Database |
| `scripts/start_web_ui.py` | `scripts/deployment/start_web_ui.py` | Deployment |
| `scripts/download_model.py` | `scripts/deployment/download_model.py` | Deployment |
| `scripts/run_backup.py` | `scripts/maintenance/run_backup.py` | Maintenance |
| `scripts/telemetry_upload_cron.py` | `scripts/maintenance/telemetry_upload_cron.py` | Maintenance |
| `scripts/vkp_pull_cron.py` | `scripts/maintenance/vkp_pull_cron.py` | Maintenance |
| `scripts/demo_pedagogical_features.py` | `scripts/demo/demo_pedagogical_features.py` | Demo |
| `scripts/config_cli.py` | `scripts/demo/config_cli.py` | Demo |

### Documentation

| Old Path | New Path | Category |
|----------|----------|----------|
| `ARCHITECTURE_ANALYSIS.md` | `docs/architecture/architecture-analysis.md` | Architecture |
| `README_DEPLOYMENT_SCENARIOS.md` | `docs/architecture/deployment-scenarios.md` | Architecture |
| `docs/SYSTEM_ARCHITECTURE.md` | `docs/architecture/SYSTEM_ARCHITECTURE.md` | Architecture |
| `docs/WEB_UI_ARCHITECTURE.md` | `docs/architecture/WEB_UI_ARCHITECTURE.md` | Architecture |
| `DEVELOPMENT_STRATEGY.md` | `docs/development/development-strategy.md` | Development |
| `REFACTORING_ROADMAP.md` | `docs/development/refactoring-roadmap.md` | Development |
| `docs/DEVELOPER_GUIDE.md` | `docs/development/DEVELOPER_GUIDE.md` | Development |
| `docs/DEPLOYMENT.md` | `docs/deployment/DEPLOYMENT.md` | Deployment |
| `docs/AWS_SETUP.md` | `docs/deployment/AWS_SETUP.md` | Deployment |
| `docs/USER_GUIDE.md` | `docs/user_guide/USER_GUIDE.md` | User Guide |
| `docs/PHASE3_SYSTEM_CAPABILITIES.md` | `docs/archive/phase3-system-capabilities.md` | Archive |
| `docs/PHASE10_IMPLEMENTATION_SUMMARY.md` | `docs/archive/phase10-implementation-summary.md` | Archive |

### Config Files

| Old Path | New Path |
|----------|----------|
| `dataset_inventory.json` | `data/metadata/dataset_inventory.json` |
| `version.json` | `config/version.json` |

---

## 🔧 Update Your Commands

### System Checks

```bash
# OLD
python scripts/check_system_ready.py
python scripts/check_embeddings.py

# NEW
python scripts/system/check_system_ready.py
python scripts/system/check_embeddings.py
```

### AWS Operations

```bash
# OLD
python scripts/setup_aws.py
python scripts/upload_to_s3.py

# NEW
python scripts/aws/setup_aws.py
python scripts/aws/upload_to_s3.py
```

### Data Processing

```bash
# OLD
python scripts/run_etl_pipeline.py
python scripts/reset_vector_db.py

# NEW
python scripts/data/run_etl_pipeline.py
python scripts/data/reset_vector_db.py
```

### Database Operations

```bash
# OLD
python scripts/setup_database.py
python scripts/migrate_database_schema.py

# NEW
python scripts/database/setup_database.py
python scripts/database/migrate_database_schema.py
```

---

## 📝 Update Your Documentation Links

### In Markdown Files

```markdown
# OLD
[System Architecture](docs/SYSTEM_ARCHITECTURE.md)
[Developer Guide](docs/DEVELOPER_GUIDE.md)
[Deployment Guide](docs/DEPLOYMENT.md)

# NEW
[System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)
[Developer Guide](docs/development/DEVELOPER_GUIDE.md)
[Deployment Guide](docs/deployment/DEPLOYMENT.md)
```

### In Code Comments

```python
# OLD
# See docs/DEVELOPER_GUIDE.md for details

# NEW
# See docs/development/DEVELOPER_GUIDE.md for details
```

---

## 🗑️ Removed Files

These files have been removed as they are no longer needed:

### Scripts
- `scripts/migrate_to_modular_api.py` - One-time migration script (completed)
- `scripts/update_imports.py` - One-time update script (completed)
- `scripts/verify_phase10_implementation.py` - Verification script (completed)
- `scripts/verify_telemetry_checkpoint.py` - Verification script (completed)
- `scripts/test_cache_integration.py` - Moved to tests/
- `scripts/test_modular_api.py` - Moved to tests/

### Backups
- `backups/api_migration/` - Old migration backups
- `backups/pre-refactoring/` - Old refactoring backups
- `backups/backup_20260219_*.json` - Old backup files
- `backups/backup_20260220_*.json` - Old backup files

---

## 🔍 Finding Files

### By Category

**System Operations:**
```bash
ls scripts/system/
```

**AWS Operations:**
```bash
ls scripts/aws/
```

**Data Processing:**
```bash
ls scripts/data/
```

**Database Operations:**
```bash
ls scripts/database/
```

**Deployment:**
```bash
ls scripts/deployment/
```

**Maintenance:**
```bash
ls scripts/maintenance/
```

### By Documentation Type

**Architecture:**
```bash
ls docs/architecture/
```

**Development:**
```bash
ls docs/development/
```

**Deployment:**
```bash
ls docs/deployment/
```

**User Guides:**
```bash
ls docs/guides/
```

---

## 🚀 Quick Reference

### Most Common Commands

```bash
# System check
python scripts/system/check_system_ready.py

# Start application
python api_server.py

# Run tests
pytest

# Check embeddings
python scripts/system/check_embeddings.py

# Setup AWS
python scripts/aws/setup_aws.py

# Run ETL
python scripts/data/run_etl_pipeline.py

# Setup database
python scripts/database/setup_database.py

# Backup
python scripts/maintenance/run_backup.py
```

### Most Common Documentation

```bash
# Quick start
docs/guides/QUICK_START.md

# System architecture
docs/architecture/SYSTEM_ARCHITECTURE.md

# Developer guide
docs/development/DEVELOPER_GUIDE.md

# Deployment guide
docs/deployment/DEPLOYMENT.md

# User guide
docs/user_guide/USER_GUIDE.md
```

---

## 🔄 Updating Your Scripts

If you have custom scripts that reference old paths, update them:

### Python Scripts

```python
# OLD
import sys
sys.path.append('scripts')
from check_system_ready import check_system

# NEW
import sys
sys.path.append('scripts/system')
from check_system_ready import check_system
```

### Shell Scripts

```bash
# OLD
python scripts/check_system_ready.py
python scripts/setup_aws.py

# NEW
python scripts/system/check_system_ready.py
python scripts/aws/setup_aws.py
```

### Cron Jobs

```bash
# OLD
0 * * * * /usr/bin/python3 /path/to/scripts/vkp_pull_cron.py

# NEW
0 * * * * /usr/bin/python3 /path/to/scripts/maintenance/vkp_pull_cron.py
```

---

## 📚 New Documentation Structure

The documentation is now organized by category:

```
docs/
├── architecture/      # System architecture & design
├── development/       # Development guides & strategies
├── deployment/        # Deployment & AWS setup
├── guides/           # User guides & tutorials
├── technical/        # Technical reference
├── user_guide/       # End-user documentation
├── optimization/     # Optimization docs
├── api/             # API documentation
└── archive/         # Archived/historical docs
```

**Benefits:**
- Easier to find relevant documentation
- Clear separation of concerns
- Better organization for large projects
- Easier to maintain

---

## ❓ FAQ

### Q: Do I need to update my imports in Python code?

**A:** No, the `src/` folder structure hasn't changed. Only `scripts/` and `docs/` were reorganized.

### Q: Will my existing scripts break?

**A:** If your scripts reference paths in `scripts/` or `docs/`, you'll need to update them. See the path mapping table above.

### Q: Where can I find the old documentation?

**A:** Old phase documentation has been moved to `docs/archive/`.

### Q: How do I run the system check now?

**A:** `python scripts/system/check_system_ready.py`

### Q: Where is the deployment guide?

**A:** `docs/deployment/DEPLOYMENT.md`

### Q: Can I still use the old paths?

**A:** No, the old files have been moved. You must use the new paths.

---

## 🆘 Need Help?

- Check [Documentation Index](README.md)
- Check [Project Structure](PROJECT_STRUCTURE.md)
- Check [Developer Guide](development/DEVELOPER_GUIDE.md)
- Check [Troubleshooting](TROUBLESHOOTING.md)

---

**Last Updated:** 2026-02-22  
**Questions?** Open an issue or check the documentation.
