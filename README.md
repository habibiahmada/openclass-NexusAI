# 🎓 OpenClass Nexus AI

**Hybrid Orchestrated Edge AI System untuk Pendidikan Indonesia**

[![Status](https://img.shields.io/badge/Status-Active%20Development-yellow)](https://github.com/habibiahmada/openclass-nexus-ai)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-See%20LEGAL__COMPLIANCE.md-green)](docs/LEGAL_COMPLIANCE.md)

> Sistem AI pembelajaran offline yang bekerja 100% tanpa internet, berbasis kurikulum nasional, dengan orkestrasi cloud untuk distribusi konten.

---

## 📖 Daftar Isi

- [Tentang Proyek](#-tentang-proyek)
- [Visi & Misi](#-visi--misi)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Fitur Utama](#-fitur-utama)
- [Status Implementasi](#-status-implementasi)
- [Quick Start](#-quick-start)
- [Roadmap Pengembangan](#-roadmap-pengembangan)
- [Kelebihan & Kekurangan](#-kelebihan--kekurangan)
- [Dokumentasi](#-dokumentasi)
- [Kontribusi](#-kontribusi)

---

## 🌟 Tentang Proyek

OpenClass Nexus AI adalah sistem AI tutor offline yang dirancang khusus untuk mengatasi tantangan pendidikan di Indonesia, terutama di daerah dengan keterbatasan infrastruktur internet dan perangkat keras.

### Masalah yang Diselesaikan

1. **Keterbatasan Akses Internet**: Banyak sekolah di Indonesia tidak memiliki koneksi internet yang stabil
2. **Rasio Guru-Siswa Tinggi**: Satu guru harus melayani 30-40 siswa, sulit memberikan perhatian individual
3. **Keterbatasan Perangkat**: Sekolah sering hanya memiliki komputer dengan spesifikasi terbatas
4. **Kebutuhan Konten Kurikulum**: Jawaban harus sesuai dengan kurikulum nasional resmi

### Solusi yang Ditawarkan

- ✅ **100% Offline Inference**: AI berjalan lokal tanpa internet setelah instalasi
- ✅ **Berbasis Kurikulum Nasional**: Menggunakan buku BSE Kemdikbud resmi
- ✅ **Browser-Based Access**: Tidak perlu instalasi di perangkat siswa
- ✅ **Privacy by Architecture**: Data siswa tidak pernah keluar dari sekolah
- ✅ **Hybrid Cloud-Edge**: Update konten via cloud, inference di edge

---

## 🎯 Visi & Misi

### Visi
**"Demokratisasi akses AI untuk pendidikan di seluruh Indonesia, tanpa batasan infrastruktur"**

### Misi
1. Menyediakan AI tutor yang dapat diakses offline di sekolah manapun
2. Membantu guru mengatasi rasio guru-siswa yang tinggi dengan AI assistant
3. Memberikan pembelajaran personal untuk setiap siswa
4. Menjaga privasi dan kedaulatan data pendidikan di tingkat sekolah

### Alignment dengan SDG
- **SDG 4**: Quality Education - Pendidikan berkualitas untuk semua
- **SDG 9**: Industry, Innovation, and Infrastructure - Inovasi teknologi pendidikan
- **SDG 10**: Reduced Inequalities - Mengurangi kesenjangan akses pendidikan

---

## 🏗️ Arsitektur Sistem

### Model Deployment: **One School - One Sovereign AI Node**

```
┌─────────────────────────────────────────────┐
│           CLIENT LAYER (Browser)           │
│  Siswa, Guru, Admin via WiFi Sekolah       │
└────────────────────┬────────────────────────┘
                     │ HTTP (LAN Only)
                     ▼
┌─────────────────────────────────────────────┐
│        SCHOOL EDGE SERVER NODE             │
│  ┌──────────────────────────────────────┐  │
│  │ LLM Runtime (Llama 3.2-3B GGUF)      │  │
│  │ Vector DB (ChromaDB)                 │  │
│  │ RAG Orchestrator                     │  │
│  │ Pedagogical Intelligence Engine      │  │
│  │ Local PostgreSQL Database            │  │
│  │ Redis Cache (Optional)               │  │
│  └──────────────────────────────────────┘  │
│  Chat History NEVER Leaves School          │
└────────────────────┬────────────────────────┘
                     │ Periodic Sync Only
                     ▼
┌─────────────────────────────────────────────┐
│      AWS NATIONAL CONTROL PLANE            │
│  ┌──────────────────────────────────────┐  │
│  │ Model Training (SageMaker)           │  │
│  │ Curriculum Processing (Lambda)       │  │
│  │ VKP Packaging & Distribution (S3)    │  │
│  │ CloudFront CDN                       │  │
│  │ Aggregated Metrics (DynamoDB)        │  │
│  └──────────────────────────────────────┘  │
│  NO Chat Content, NO Personal Data         │
└─────────────────────────────────────────────┘
```

### Prinsip Arsitektur

1. **Privacy by Architecture**: Data sensitif tidak pernah keluar dari sekolah
2. **Offline-First**: Sistem tetap berjalan tanpa internet
3. **Sovereign Node**: Setiap sekolah adalah node independen
4. **Centralized Orchestration**: AWS hanya untuk distribusi konten dan training model
5. **No Federation**: Tidak ada sharing data antar sekolah

---

## ✨ Fitur Utama

### 🎓 Mode Siswa
- **AI Chat Interface**: Tanya jawab dengan AI tutor berbasis kurikulum
- **Subject Filtering**: Filter berdasarkan mata pelajaran
- **Quick Actions**: Ringkas materi, contoh soal, latihan, jelaskan konsep
- **Source Citations**: Setiap jawaban menyertakan referensi buku dan halaman
- **Progress Tracking**: Pelacakan topik yang sudah dipelajari (🔄 In Development)
- **Adaptive Practice**: Soal latihan yang disesuaikan dengan kemampuan (🔄 In Development)

### 👨‍🏫 Mode Guru
- **Dashboard Analytics**: Statistik pertanyaan siswa real-time
- **Topic Analysis**: Topik yang paling sering ditanyakan
- **Student Insights**: Identifikasi siswa yang kesulitan (🔄 In Development)
- **Weekly Reports**: Laporan otomatis mingguan (🔄 In Development)
- **Export Reports**: Download laporan dalam format PDF/CSV
- **Intervention Recommendations**: Saran tindakan untuk siswa tertentu (🔄 In Development)

### ⚙️ Mode Admin
- **System Monitoring**: Status model AI, database, dan resource
- **Content Management**: Update model AI dan kurikulum
- **Backup & Restore**: Backup otomatis dan manual
- **Health Monitoring**: Daemon monitoring kesehatan sistem
- **Version Management**: Rollback ke versi sebelumnya jika diperlukan
- **User Management**: Kelola akun siswa, guru, dan admin

### 🔧 Fitur Teknis
- **Concurrency Management**: Queue system untuk handle multiple users
- **Token Streaming**: Response streaming untuk UX yang lebih baik
- **Caching Layer**: Redis/LRU cache untuk optimasi performa
- **Graceful Degradation**: Sistem tetap berjalan meski resource terbatas
- **Auto-Restart**: Service restart otomatis saat critical failure
- **Delta Updates**: Update inkremental untuk hemat bandwidth

---

## 📊 Status Implementasi

### ✅ Sudah Diimplementasi (70%)

#### Core Infrastructure
- ✅ FastAPI backend server dengan modular architecture
- ✅ PostgreSQL database untuk persistence
- ✅ Redis cache dengan LRU fallback
- ✅ Authentication & authorization system
- ✅ Multi-role access control (Siswa, Guru, Admin)

#### AI & RAG Pipeline
- ✅ Local LLM inference dengan llama.cpp
- ✅ ChromaDB vector database
- ✅ RAG orchestrator dengan context management
- ✅ Educational content validator
- ✅ Embedding strategy manager (AWS Bedrock + Local MiniLM)

#### Data Processing
- ✅ ETL pipeline untuk PDF processing
- ✅ Text chunking dengan metadata enrichment
- ✅ AWS S3 storage integration
- ✅ CloudFront CDN untuk distribusi
- ✅ VKP (Versioned Knowledge Package) system

#### Resilience & Monitoring
- ✅ Backup manager dengan compression & encryption
- ✅ Health monitoring daemon
- ✅ Auto-restart service
- ✅ Version manager dengan rollback capability
- ✅ Backup scheduler (weekly automation)

#### Concurrency & Performance
- ✅ Async inference queue
- ✅ Semaphore-based request limiting
- ✅ Token streaming
- ✅ Resource manager untuk CPU optimization
- ✅ Graceful degradation under load

#### Web Interface
- ✅ Landing page dengan role selection
- ✅ Student chat interface
- ✅ Teacher dashboard (basic)
- ✅ Admin panel (basic)
- ✅ Responsive design

### 🔄 Dalam Pengembangan (20%)

#### Pedagogical Intelligence Engine
- 🔄 Topic mastery tracker
- 🔄 Weak area detection
- 🔄 Adaptive practice question generator
- 🔄 Weekly summary report generator

#### Enhanced Teacher Features
- 🔄 Student mastery heatmap
- 🔄 Weak area alerts
- 🔄 Intervention recommendations
- 🔄 Detailed student drill-down

#### Enhanced Student Features
- 🔄 Progress visualization dashboard
- 🔄 Learning history view
- 🔄 Personalized learning path
- 🔄 Achievement badges

#### Telemetry & Analytics
- 🔄 Aggregated metrics collector
- 🔄 DynamoDB integration
- 🔄 PII verifier
- 🔄 Anonymization engine

### 📅 Belum Diimplementasi (10%)

#### AWS Infrastructure Automation
- ❌ Lambda curriculum processor
- ❌ S3 event triggers
- ❌ DynamoDB tables setup
- ❌ Automated infrastructure deployment script

#### Advanced Features
- ❌ Voice input support
- ❌ Multi-language support (English, regional languages)
- ❌ Collaborative learning features
- ❌ Parent dashboard
- ❌ Mobile app (PWA)

#### Production Deployment
- ❌ Docker containerization
- ❌ Kubernetes orchestration
- ❌ CI/CD pipeline
- ❌ Load testing untuk 100-300 concurrent users

---

## 🚀 Quick Start

### System Requirements

**Minimum (Development):**
- Python 3.8+
- RAM 8GB
- CPU 4-core
- Disk 100GB SSD
- Windows/Linux/Mac OS

**Recommended (Production - School Server):**
- Python 3.8+
- RAM 16GB
- CPU 8-core
- Disk 512GB SSD
- Ubuntu Server LTS
- GPU optional (tidak wajib)

### Installation

#### 1. Clone Repository
```bash
git clone https://github.com/habibiahmada/openclass-nexus-ai.git
cd openclass-nexus-ai
```

#### 2. Setup Virtual Environment
```bash
# Windows
python -m venv openclass-env
openclass-env\Scripts\activate.bat

# Linux/Mac
python3 -m venv openclass-env
source openclass-env/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Setup Environment Variables
```bash
# Copy template
cp .env.example .env

# Edit .env dengan text editor
# Minimal configuration:
# - SECRET_KEY (generate dengan: python -c "import secrets; print(secrets.token_hex(32))")
# - DATABASE_URL (default: sqlite:///./openclass.db)
```

#### 5. Initialize Database
```bash
python database/init_database.py
```

#### 6. Download Model (Optional - untuk testing)
```bash
# Model akan di-download otomatis saat pertama kali dijalankan
# Atau download manual dari Hugging Face
python scripts/model/download_model.py
```

#### 7. Run Server
```bash
# Development mode
python api_server.py

# Production mode
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 8. Access Application
```
http://localhost:8000
```

**Demo Credentials:**
- Siswa: `siswa / siswa123`
- Guru: `guru / guru123`
- Admin: `admin / admin123`

### Quick Start (Windows - One Click)
```bash
# Double-click file ini
start_web_ui.bat
```

---

## 🗺️ Roadmap Pengembangan

### Phase 1: Core System Foundation ✅ (COMPLETED)
**Timeline**: Bulan 1-2 (Selesai)
- ✅ Database persistence (PostgreSQL)
- ✅ Authentication system
- ✅ Basic RAG pipeline
- ✅ Web interface (basic)
- ✅ Multi-role access

### Phase 2: Pedagogical Intelligence 🔄 (IN PROGRESS)
**Timeline**: Bulan 3-4 (Current)
**Target**: Mengubah dari "chatbot" menjadi "learning support infrastructure"

**Week 1-2: Database Schema & Tracking**
- 🔄 Student progress tracking schema
- 🔄 Topic mastery scoring system
- 🔄 Practice history storage
- 🔄 Learning analytics foundation

**Week 3-4: Intelligence Engine**
- 🔄 Topic mastery tracker implementation
- 🔄 Weak area detection algorithm
- 🔄 Adaptive question difficulty adjustment
- 🔄 Learning path recommendation

**Week 5-6: Teacher Insights**
- 🔄 Student mastery heatmap
- 🔄 Weak area alerts
- 🔄 Weekly report generator
- 🔄 Intervention recommendations

**Week 7-8: Student UI Enhancement**
- 🔄 Progress dashboard
- 🔄 Learning history view
- 🔄 Achievement system
- 🔄 Personalized recommendations

### Phase 3: Production Readiness 📅 (PLANNED)
**Timeline**: Bulan 5-6

**Concurrency & Performance**
- Load testing (100-300 concurrent users)
- Performance optimization
- Memory usage optimization
- Response time tuning

**Telemetry & Monitoring**
- Aggregated metrics collection
- DynamoDB integration
- Anonymization verification
- Dashboard monitoring

**Deployment & DevOps**
- Docker containerization
- Deployment documentation
- Backup automation testing
- Disaster recovery procedures

### Phase 4: AWS Infrastructure Automation 📅 (PLANNED)
**Timeline**: Bulan 7

- Lambda curriculum processor
- S3 event triggers
- DynamoDB tables
- Infrastructure as Code (Terraform/CloudFormation)
- Automated deployment scripts

### Phase 5: Advanced Features 📅 (FUTURE)
**Timeline**: Bulan 8+

- Voice input support
- Multi-language support
- Collaborative learning
- Parent dashboard
- Mobile PWA
- Gamification

---

## ⚖️ Kelebihan & Kekurangan

### ✅ Kelebihan

#### 1. Offline-First Architecture
- **Kelebihan**: Sistem tetap berjalan 100% tanpa internet setelah instalasi
- **Impact**: Cocok untuk daerah 3T dan sekolah dengan koneksi tidak stabil
- **Unique**: Berbeda dari chatbot cloud yang memerlukan internet terus-menerus

#### 2. Privacy by Architecture
- **Kelebihan**: Data siswa tidak pernah keluar dari sekolah
- **Impact**: Compliance dengan regulasi privasi data pendidikan
- **Unique**: Bukan kebijakan administratif, tapi desain sistem

#### 3. Browser-Based Access
- **Kelebihan**: Tidak perlu instalasi di perangkat siswa
- **Impact**: Support Windows lama, Chromebook, smartphone
- **Unique**: Thin client architecture, hemat resource

#### 4. Kurikulum Nasional
- **Kelebihan**: Jawaban berdasarkan buku BSE Kemdikbud resmi
- **Impact**: Akurat dan sesuai standar pendidikan nasional
- **Unique**: Bukan general knowledge, tapi curriculum-specific

#### 5. Pedagogical Intelligence
- **Kelebihan**: Bukan sekedar chatbot, tapi learning support system
- **Impact**: Tracking progress, deteksi area lemah, adaptive learning
- **Unique**: Membantu guru dengan insights dan recommendations

#### 6. Hybrid Cloud-Edge
- **Kelebihan**: Update konten via cloud, inference di edge
- **Impact**: Best of both worlds - flexibility + privacy
- **Unique**: Sovereign node dengan centralized orchestration

#### 7. Production-Ready Architecture
- **Kelebihan**: Backup, monitoring, auto-restart, rollback
- **Impact**: Reliable untuk deployment di sekolah
- **Unique**: Enterprise-grade resilience

### ⚠️ Kekurangan & Keterbatasan

#### 1. Hardware Requirements
- **Kekurangan**: Memerlukan server 16GB RAM (bukan 4GB laptop)
- **Impact**: Sekolah perlu investasi hardware minimal
- **Mitigasi**: Masih lebih murah dari solusi cloud subscription jangka panjang
- **Status**: Dokumentasi sudah diperbaiki untuk transparansi

#### 2. Initial Setup Complexity
- **Kekurangan**: Setup awal memerlukan technical knowledge
- **Impact**: Perlu IT support atau training
- **Mitigasi**: Sedang develop installer otomatis dan dokumentasi lengkap
- **Status**: 🔄 Dalam pengembangan

#### 3. Model Accuracy Limitations
- **Kekurangan**: Model 3B parameter lebih kecil dari GPT-4
- **Impact**: Jawaban mungkin kurang detail untuk pertanyaan kompleks
- **Mitigasi**: RAG membantu dengan context dari buku, fallback ke guru
- **Status**: Acceptable trade-off untuk offline capability

#### 4. Content Update Dependency
- **Kekurangan**: Update kurikulum memerlukan internet (periodic)
- **Impact**: Perlu koneksi internet sesekali untuk update
- **Mitigasi**: Delta updates hemat bandwidth, bisa via USB jika perlu
- **Status**: By design - hybrid approach

#### 5. Pedagogical Features Incomplete
- **Kekurangan**: Mastery tracking dan adaptive learning belum selesai
- **Impact**: Belum optimal sebagai "learning support infrastructure"
- **Mitigasi**: Prioritas development Phase 2
- **Status**: 🔄 20% complete, target 2 bulan

#### 6. Scalability per Node
- **Kekurangan**: Satu server untuk satu sekolah (tidak multi-tenant)
- **Impact**: Tidak bisa shared hosting untuk hemat biaya
- **Mitigasi**: By design untuk privacy, cost masih reasonable
- **Status**: Architectural decision - won't change

#### 7. Limited Multi-Language Support
- **Kekurangan**: Saat ini hanya Bahasa Indonesia
- **Impact**: Tidak bisa untuk sekolah internasional atau daerah
- **Mitigasi**: Planned untuk Phase 5
- **Status**: 📅 Future enhancement

#### 8. No Real-Time Collaboration
- **Kekurangan**: Siswa tidak bisa belajar bersama dalam sistem
- **Impact**: Kehilangan aspek social learning
- **Mitigasi**: Planned untuk Phase 5
- **Status**: 📅 Future enhancement

### 🎯 Trade-offs yang Disengaja

1. **Model Size vs Offline Capability**: Pilih model kecil (3B) untuk bisa offline
2. **Privacy vs Analytics**: Pilih privacy, korbankan detailed analytics
3. **Simplicity vs Features**: Prioritas core features yang stable
4. **Cost vs Performance**: Optimize untuk low-cost hardware

---

## 📚 Dokumentasi

### Panduan Pengguna
- [Quick Start Guide](docs/guides/QUICK_START.md) - Mulai dalam 5 menit
- [User Guide](docs/user_guide/USER_GUIDE.md) - Panduan lengkap untuk siswa, guru, admin
- [Deployment Guide](docs/deployment/DEPLOYMENT.md) - Deploy ke sekolah

### Arsitektur & Desain
- [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md) - Arsitektur sistem lengkap
- [Deployment Scenarios](docs/architecture/deployment-scenarios.md) - Skenario deployment
- [Architecture Analysis](ARCHITECTURE_ANALYSIS.md) - Analisis gap implementasi vs desain

### Development
- [Developer Guide](docs/development/DEVELOPER_GUIDE.md) - Panduan development
- [Development Strategy](docs/development/development-strategy.md) - Strategi pengembangan
- [API Structure](docs/technical/API_MODULAR_STRUCTURE.md) - Struktur API modular
- [Database Schema](docs/technical/DATABASE_SCHEMA.md) - Skema database

### Teknis
- [AWS Implementation](docs/AWS_IMPLEMENTATION_AUDIT.md) - Audit implementasi AWS
- [Legal Compliance](docs/LEGAL_COMPLIANCE.md) - Compliance dan lisensi
- [Contributing Guide](CONTRIBUTING.md) - Cara berkontribusi
- [Changelog](CHANGELOG.md) - Riwayat perubahan

### Indeks Lengkap
- [Documentation Index](docs/README.md) - Indeks semua dokumentasi

---

## 🛠️ Troubleshooting

### Error: "Module not found"
```bash
pip install -r requirements.txt
```

### Port sudah digunakan
Edit `config/app_config.py` atau `.env`:
```
API_PORT=8001
```

### Model tidak load
1. Cek file model ada di `models/`
2. Cek RAM cukup (minimal 8GB untuk development)
3. Lihat log error di terminal

### Database error
```bash
# Reset database
python database/init_database.py --reset
```

### UI tidak muncul
1. Clear browser cache (Ctrl+Shift+Delete)
2. Cek console browser (F12) untuk error
3. Pastikan file `frontend/` ada semua

Lihat [Troubleshooting Guide](docs/guides/TROUBLESHOOTING.md) untuk detail lengkap.

---

## 🤝 Kontribusi

Kami sangat terbuka untuk kontribusi! Lihat [CONTRIBUTING.md](CONTRIBUTING.md) untuk panduan lengkap.

### Cara Berkontribusi

1. Fork repository
2. Buat branch baru (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

### Area yang Membutuhkan Kontribusi

- 🔄 Pedagogical Intelligence Engine
- 🔄 UI/UX improvements
- 🔄 Documentation (especially in English)
- 🔄 Testing (unit tests, integration tests)
- 🔄 Performance optimization
- 📅 Multi-language support
- 📅 Mobile PWA

---

## 📄 License

Lihat [LEGAL_COMPLIANCE.md](docs/LEGAL_COMPLIANCE.md) untuk informasi lengkap tentang lisensi.

**Summary:**
- Kode: Open source (lisensi akan ditentukan)
- Konten Kurikulum: Menggunakan buku BSE Kemdikbud (domain publik)
- Model AI: Llama 3.2 (Meta License)

---

## 🙏 Acknowledgments

- **Kemdikbud**: Untuk buku BSE yang menjadi sumber konten
- **Meta AI**: Untuk Llama model
- **AWS**: Untuk AWS Educate program
- **Community**: Untuk feedback dan kontribusi

---

## 📞 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/habibiahmada/openclass-nexus-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/habibiahmada/openclass-nexus-ai/discussions)
- **Email**: [habibiahmadaziz@gmail.com](mailto:habibiahmadaziz@gmail.com)

---

## 🌟 Star History

Jika proyek ini bermanfaat, berikan ⭐ untuk mendukung pengembangan!

---

**Built with ❤️ for Indonesian Education**

*Redistribusi kecerdasan ke setiap sudut Indonesia*
