# 🎓 OpenClass Nexus AI

Sistem AI pembelajaran offline untuk sekolah Indonesia dengan RAG (Retrieval-Augmented Generation).

## 🚀 Quick Start

```bash
# 1. Verifikasi sistem
python scripts/system/check_system_ready.py

# 2. Jalankan aplikasi
python api_server.py
# atau
start_web_ui.bat  # Windows
./start_web_ui.sh # Linux/Mac
```

Akses di: http://localhost:8000

## 📋 System Requirements

- Python 3.8+
- RAM 16GB minimum
- CPU 8-core minimum
- Disk space 512GB SSD
- Windows/Linux/Mac OS

## 📚 Dokumentasi

Lihat [docs/README.md](docs/README.md) untuk indeks lengkap dokumentasi.

### Panduan Cepat
- [Quick Start](docs/guides/QUICK_START.md) - Mulai dalam 5 menit
- [User Guide](docs/user_guide/USER_GUIDE.md) - Panduan lengkap
- [Deployment](docs/deployment/DEPLOYMENT.md) - Deploy ke sekolah

### Arsitektur & Development
- [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md) - Arsitektur sistem
- [Deployment Scenarios](docs/architecture/deployment-scenarios.md) - Skenario deployment
- [Developer Guide](docs/development/DEVELOPER_GUIDE.md) - Panduan development
- [Development Strategy](docs/development/development-strategy.md) - Strategi pengembangan

### Teknis
- [Database Schema](docs/technical/DATABASE_SCHEMA.md) - Skema database
- [API Structure](docs/technical/API_MODULAR_STRUCTURE.md) - Struktur API
- [Contributing](CONTRIBUTING.md) - Cara berkontribusi

## 🎯 Fitur Utama

- ✅ **Offline-first**: Berjalan tanpa internet
- ✅ **Multi-role**: Siswa, Guru, Admin
- ✅ **RAG-powered**: Jawaban berdasarkan materi kurikulum
- ✅ **Production-ready**: Optimized for 16GB RAM school servers
- ✅ **LAN support**: Akses dari multiple komputer

## 🏗️ Struktur Project

```
openclass-nexus-ai/
├── api_server.py          # API server utama
├── app.py                 # CLI interface (legacy)
├── frontend/              # Web UI (HTML/CSS/JS)
├── src/                   # Source code
│   ├── local_inference/   # RAG pipeline & inference
│   └── etl/              # Data processing
├── scripts/              # Utility scripts (17 files)
├── data/                 # Data & vector database
├── models/               # LLM models
├── docs/                 # Dokumentasi lengkap (24 files)
└── config/               # Configuration files
```

Lihat [Project Structure](docs/PROJECT_STRUCTURE.md) untuk detail lengkap.

## 🛠️ Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Check embeddings
python scripts/system/check_embeddings.py

# Verify system
python scripts/system/verify_system.py
```

## 📄 License

Lihat [LEGAL_COMPLIANCE.md](docs/LEGAL_COMPLIANCE.md) untuk informasi lisensi.

## 🤝 Contributing

Lihat [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) untuk panduan kontribusi.
