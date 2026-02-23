# 🎯 STRATEGI PENGEMBANGAN OPENCLASS NEXUS AI

**Tanggal:** 2026-02-20  
**Status:** STRATEGIC GUIDANCE - NO CODE CHANGES

---

## ❓ PERTANYAAN KRITIS YANG DIJAWAB

### 1. Pengembangan di Local atau Cloud?
### 2. Apakah Benar-Benar Memanfaatkan AWS?
### 3. Apakah Perubahan Materi Harus Hard-Code?
### 4. Langkah Apa yang Harus Dilakukan?

---

## 📍 JAWABAN 1: PENGEMBANGAN DI LOCAL ATAU CLOUD?

### **JAWABAN: HYBRID - Keduanya Digunakan Sesuai Fungsi**

```
┌─────────────────────────────────────────────────────────────┐
│                  DEVELOPMENT WORKFLOW                       │
└─────────────────────────────────────────────────────────────┘

FASE 1: DEVELOPMENT (LOCAL)
├── Kode aplikasi → Local machine (VSCode, PyCharm)
├── Testing RAG → Local (dengan sample data kecil)
├── UI Development → Local (frontend testing)
└── Unit Testing → Local (pytest)

FASE 2: DATA PROCESSING (AWS)
├── Upload PDF kurikulum → AWS S3
├── ETL Pipeline → AWS Lambda (triggered by S3)
├── Embedding Generation → AWS Bedrock Titan
├── Package VKP → AWS Lambda
└── Store VKP → AWS S3 + CloudFront

FASE 3: DEPLOYMENT (LOCAL SCHOOL SERVER)
├── Pull VKP dari CloudFront → School Server
├── Extract embeddings → ChromaDB lokal
├── Load LLM model → Local inference
└── Run web server → LAN only (192.168.x.x)

FASE 4: PRODUCTION (100% OFFLINE)
├── Siswa akses → WiFi sekolah
├── Query processing → Local server
├── RAG + LLM → Local inference
└── Response → Browser siswa
```

### **Kesimpulan:**
- **Development:** Local (kode, testing, debugging)
- **Data Processing:** AWS (embedding, packaging)
- **Production Runtime:** Local School Server (100% offline)

---

## 📍 JAWABAN 2: APAKAH BENAR-BENAR MEMANFAATKAN AWS?

### **JAWABAN: YA, Tapi Bukan untuk Runtime Produksi**

### AWS Digunakan Untuk (Sesuai Arsitektur):

#### A. **Model Development Domain**
```
Amazon SageMaker:
├── Fine-tuning Llama 3.2 dengan data Indonesia
├── Knowledge distillation (Teacher → Student model)
├── Performance testing & benchmarking
└── Bias evaluation

Amazon Bedrock:
├── Quality benchmarking (compare responses)
├── Evaluation only (NOT production inference)
└── Embedding generation (Titan Embeddings)
```

**Contoh Workflow:**
```bash
# Di AWS SageMaker
1. Upload dataset interaksi siswa
2. Fine-tune Llama 3.2 70B (teacher model)
3. Distill ke Llama 3.2 3B (student model)
4. Export GGUF quantized model
5. Upload ke S3 untuk distribution
```

#### B. **Curriculum Processing Pipeline**
```
AWS Lambda + S3 + Bedrock:
├── Trigger: Guru upload PDF baru
├── Lambda: Extract text, chunking, cleaning
├── Bedrock: Generate embeddings (Titan)
├── Lambda: Package VKP (versioned)
└── S3: Store VKP untuk distribution
```

**Contoh Workflow:**
```bash
# Guru upload buku baru "Matematika Kelas 11"
1. Upload PDF → S3 bucket (s3://nexusai-curriculum/raw/)
2. S3 Event → Trigger Lambda function
3. Lambda: pypdf extract → text chunks
4. Lambda: Call Bedrock Titan → embeddings
5. Lambda: Package VKP dengan metadata
6. Lambda: Upload VKP → S3 (s3://nexusai-vkp/v1.2.0/)
7. CloudFront: Distribute VKP ke sekolah
```

#### C. **Distribution Domain**
```
S3 + CloudFront:
├── Versioned VKP storage
├── CDN distribution (cepat, global)
├── Signed URL access (security)
└── Delta update support
```

#### D. **Aggregated Telemetry (Non-Sensitive)**
```
DynamoDB:
├── Total queries per sekolah (anonymized)
├── Average latency metrics
├── Error rate tracking
└── Model version adoption

TIDAK ADA:
├── Chat content
├── Student identity
└── Personal data
```

### **Kesimpulan:**
AWS digunakan untuk:
- ✅ **Training & Fine-tuning** (SageMaker)
- ✅ **Embedding Generation** (Bedrock Titan)
- ✅ **Curriculum Processing** (Lambda)
- ✅ **Distribution** (S3 + CloudFront)
- ✅ **Aggregated Metrics** (DynamoDB)

AWS TIDAK digunakan untuk:
- ❌ Production inference (100% lokal)
- ❌ Chat storage (100% lokal)
- ❌ Real-time query processing (100% lokal)

---

## 📍 JAWABAN 3: APAKAH PERUBAHAN MATERI HARUS HARD-CODE?

### **JAWABAN: TIDAK! Sistem Dirancang untuk Dynamic Update**

### Skenario 1: Guru Menambah Buku Baru

```
┌─────────────────────────────────────────────────────────────┐
│          WORKFLOW: TAMBAH BUKU TANPA HARD-CODE              │
└─────────────────────────────────────────────────────────────┘

STEP 1: Guru Login ke Dashboard
├── URL: http://nexusai.sekolah.local/guru
├── Pilih: Kelas 11 → Matematika
└── Klik: "Tambah Buku Baru"

STEP 2: Upload PDF (Butuh Internet)
├── Guru upload: "Matematika_Kelas_11_Semester_1.pdf"
├── Local server: Simpan temporary
└── Local server: Kirim ke AWS S3

STEP 3: AWS Processing (Otomatis)
├── S3 Event → Lambda trigger
├── Lambda: Extract text dari PDF
├── Lambda: Chunking (800 tokens, overlap 100)
├── Lambda: Call Bedrock Titan → embeddings
├── Lambda: Package VKP dengan metadata:
│   {
│     "version": "1.2.0",
│     "subject": "matematika",
│     "grade": "11",
│     "semester": "1",
│     "chunks": 450,
│     "embedding_model": "amazon.titan-embed-text-v1",
│     "created_at": "2026-02-15T10:30:00Z",
│     "checksum": "sha256:abc123..."
│   }
└── Lambda: Upload VKP ke S3

STEP 4: School Server Pull Update (Otomatis)
├── Cron job: Check update setiap 1 jam
├── Compare version: local (1.1.0) vs cloud (1.2.0)
├── Download: VKP delta (hanya yang baru)
├── Extract: Embeddings → ChromaDB
├── Update: Metadata database
└── Notify: Guru via dashboard

STEP 5: Siswa Langsung Bisa Akses (Offline)
├── Siswa: "Jelaskan teorema Pythagoras"
├── RAG: Query ChromaDB (sudah ada buku baru)
├── LLM: Generate jawaban dengan konteks baru
└── Response: Jawaban dari buku yang baru di-upload
```

### **TIDAK ADA HARD-CODE:**
- ❌ Tidak perlu edit kode
- ❌ Tidak perlu restart server
- ❌ Tidak perlu re-deploy aplikasi
- ✅ Semua dinamis via database & VKP

---

### Skenario 2: Menambah Mata Pelajaran Baru

```
┌─────────────────────────────────────────────────────────────┐
│       WORKFLOW: TAMBAH PELAJARAN TANPA HARD-CODE            │
└─────────────────────────────────────────────────────────────┘

STEP 1: Admin Login
├── URL: http://nexusai.sekolah.local/admin
└── Klik: "Tambah Mata Pelajaran"

STEP 2: Form Input (UI)
├── Kelas: [Dropdown] Kelas 12
├── Nama Pelajaran: [Input] "Fisika"
├── Kode: [Auto-generate] "fisika_12"
└── [Simpan]

STEP 3: Database Update (Otomatis)
├── PostgreSQL: INSERT INTO subjects (grade, name, code)
├── ChromaDB: Create collection "fisika_12"
└── Filesystem: mkdir data/vector_db/fisika_12/

STEP 4: Guru Upload Buku (Sama seperti Skenario 1)
├── Guru Fisika login
├── Pilih: Kelas 12 → Fisika
├── Upload PDF buku fisika
└── AWS processing → VKP → School server

STEP 5: Siswa Akses (Dropdown Otomatis Update)
├── Siswa login
├── Dropdown kelas: [Kelas 10, 11, 12] ← Otomatis
├── Dropdown pelajaran: [Informatika, Matematika, Fisika] ← Otomatis
└── Pilih Fisika → Chat dengan AI
```

### **TIDAK ADA HARD-CODE:**
- ❌ Tidak perlu edit `config/app_config.py`
- ❌ Tidak perlu tambah route baru
- ❌ Tidak perlu rebuild frontend
- ✅ Semua dinamis dari database

---

## 📍 JAWABAN 4: LANGKAH YANG HARUS DILAKUKAN

### **ROADMAP IMPLEMENTASI (Tanpa Ubah Kode Sekarang)**

---

### **FASE 0: AUDIT & PLANNING (Minggu 1-2)**

#### Langkah 1: Verifikasi Arsitektur Saat Ini
```bash
# Jalankan audit
python scripts/check_system_ready.py

# Cek komponen yang ada
ls -la src/
ls -la data/
ls -la models/

# Identifikasi gap dari ARCHITECTURE_ANALYSIS.md
```

#### Langkah 2: Setup AWS Account (Jika Belum)
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
# AWS Access Key ID: [your-key]
# AWS Secret Access Key: [your-secret]
# Default region: ap-southeast-1 (Jakarta)
# Default output format: json

# Test connection
aws s3 ls
aws bedrock list-foundation-models --region us-east-1
```

#### Langkah 3: Buat AWS Infrastructure Plan
```
Buat file: infrastructure/aws_setup_plan.md

Isi:
1. S3 Buckets:
   - nexusai-curriculum-raw (PDF uploads)
   - nexusai-vkp-packages (VKP storage)
   - nexusai-model-distribution (Model files)

2. Lambda Functions:
   - curriculum-processor (ETL)
   - vkp-packager (Packaging)
   - delta-generator (Update)

3. DynamoDB Tables:
   - nexusai-schools (School metadata)
   - nexusai-metrics (Aggregated telemetry)

4. CloudFront Distribution:
   - CDN untuk VKP distribution
```

---

### **FASE 1: IMPLEMENTASI DATABASE PERSISTENCE (Minggu 3-4)**

#### Langkah 4: Setup PostgreSQL Lokal
```bash
# Install PostgreSQL
# Ubuntu/Debian:
sudo apt install postgresql postgresql-contrib

# Windows:
# Download dari https://www.postgresql.org/download/windows/

# Create database
sudo -u postgres psql
CREATE DATABASE nexusai_school;
CREATE USER nexusai WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE nexusai_school TO nexusai;
```

#### Langkah 5: Design Database Schema
```sql
-- File: database/schema.sql

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects table (Dynamic)
CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    grade INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Books table (Dynamic)
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects(id),
    title VARCHAR(255) NOT NULL,
    filename VARCHAR(255),
    vkp_version VARCHAR(20),
    chunk_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat history table
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    subject_id INTEGER REFERENCES subjects(id),
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Langkah 6: Buat Database Migration Plan
```
File: database/migration_plan.md

1. Install SQLAlchemy ORM
2. Buat models di src/persistence/models.py
3. Migrate data dari in-memory ke PostgreSQL
4. Update api_server.py untuk use database
5. Testing persistence (restart server, data tetap ada)
```

---

### **FASE 2: IMPLEMENTASI AWS CURRICULUM PIPELINE (Minggu 5-8)**

#### Langkah 7: Setup S3 Buckets
```bash
# Create buckets
aws s3 mb s3://nexusai-curriculum-raw --region ap-southeast-1
aws s3 mb s3://nexusai-vkp-packages --region ap-southeast-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket nexusai-vkp-packages \
    --versioning-configuration Status=Enabled

# Setup lifecycle policy (optional)
```

#### Langkah 8: Buat Lambda Function untuk ETL
```
File: aws_lambda/curriculum_processor/lambda_function.py

Fungsi:
1. Trigger dari S3 upload event
2. Download PDF dari S3
3. Extract text (pypdf)
4. Chunking (800 tokens, overlap 100)
5. Call Bedrock Titan untuk embeddings
6. Package VKP dengan metadata
7. Upload VKP ke S3
8. Send notification (SNS/SQS)

Deploy:
- Package dependencies (boto3, pypdf, etc)
- Create Lambda layer
- Deploy via AWS CLI atau Console
- Setup S3 trigger
```

#### Langkah 9: Test AWS Pipeline
```bash
# Upload test PDF
aws s3 cp test_book.pdf s3://nexusai-curriculum-raw/kelas_10/informatika/

# Monitor Lambda logs
aws logs tail /aws/lambda/curriculum-processor --follow

# Check VKP output
aws s3 ls s3://nexusai-vkp-packages/

# Download VKP untuk testing
aws s3 cp s3://nexusai-vkp-packages/v1.0.0/informatika_10.vkp ./
```

---

### **FASE 3: IMPLEMENTASI VKP PULL MECHANISM (Minggu 9-10)**

#### Langkah 10: Buat VKP Puller di School Server
```
File: src/aws_control_plane/vkp_puller.py

Fungsi:
1. Periodic check (cron job setiap 1 jam)
2. Compare local version vs cloud version
3. Download delta VKP (hanya yang baru)
4. Extract embeddings
5. Update ChromaDB
6. Update PostgreSQL metadata
7. Log update history

Cron setup:
# Linux crontab
0 * * * * /usr/bin/python3 /path/to/vkp_puller.py

# Windows Task Scheduler
# Buat task yang run setiap 1 jam
```

#### Langkah 11: Test Update Flow End-to-End
```bash
# Simulasi:
1. Upload PDF baru via guru dashboard
2. AWS process → VKP
3. Wait 1 hour (atau trigger manual)
4. School server pull update
5. Verify ChromaDB updated
6. Test siswa query dengan materi baru
```

---

### **FASE 4: IMPLEMENTASI PEDAGOGICAL ENGINE (Minggu 11-14)**

#### Langkah 12: Design Pedagogical Database Schema
```sql
-- Topic mastery tracking
CREATE TABLE topic_mastery (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    subject_id INTEGER REFERENCES subjects(id),
    topic VARCHAR(255) NOT NULL,
    mastery_level FLOAT DEFAULT 0.0, -- 0.0 to 1.0
    question_count INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    last_interaction TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weak areas detection
CREATE TABLE weak_areas (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    subject_id INTEGER REFERENCES subjects(id),
    topic VARCHAR(255) NOT NULL,
    weakness_score FLOAT, -- Higher = weaker
    recommended_practice TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Practice questions
CREATE TABLE practice_questions (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects(id),
    topic VARCHAR(255) NOT NULL,
    difficulty VARCHAR(20), -- easy, medium, hard
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Langkah 13: Implementasi Mastery Tracker
```
File: src/pedagogy/mastery_tracker.py

Fungsi:
1. Track setiap pertanyaan siswa
2. Classify topic dari pertanyaan
3. Update mastery level berdasarkan:
   - Frequency of questions
   - Complexity of questions
   - Time between questions (retention)
4. Generate mastery report
```

#### Langkah 14: Implementasi Adaptive Question Generator
```
File: src/pedagogy/adaptive_question_generator.py

Fungsi:
1. Analyze weak areas dari mastery tracker
2. Generate practice questions (via LLM)
3. Adjust difficulty based on mastery level
4. Store questions untuk reuse
```

---

### **FASE 5: IMPLEMENTASI RESILIENCE (Minggu 15-16)**

#### Langkah 15: Setup Backup Automation
```bash
# Create backup script
File: src/resilience/backup_scheduler.py

Fungsi:
1. Weekly full backup (PostgreSQL + ChromaDB)
2. Daily incremental backup (chat history)
3. Compress & encrypt backup
4. Store di local + optional S3
5. Cleanup old backups (keep last 4 weeks)

Cron:
# Weekly full backup (Sunday 2 AM)
0 2 * * 0 /usr/bin/python3 /path/to/backup_scheduler.py --full

# Daily incremental (2 AM)
0 2 * * 1-6 /usr/bin/python3 /path/to/backup_scheduler.py --incremental
```

#### Langkah 16: Setup Health Monitoring
```
File: src/resilience/health_monitor.py

Fungsi:
1. Check LLM model status
2. Check ChromaDB connection
3. Check PostgreSQL connection
4. Check disk space
5. Check RAM usage
6. Auto-restart if critical failure
7. Send alert (email/SMS) jika down

Systemd service:
# /etc/systemd/system/nexusai-health.service
[Unit]
Description=NexusAI Health Monitor
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/health_monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

### **FASE 6: TESTING & OPTIMIZATION (Minggu 17-20)**

#### Langkah 17: Load Testing
```bash
# Install locust
pip install locust

# Create load test script
File: tests/load_test.py

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000

# Target:
- 100 concurrent users
- 1000 requests/minute
- < 8 second response time
- < 1% error rate
```

#### Langkah 18: Performance Optimization
```
Berdasarkan hasil load test:
1. Tune PostgreSQL (connection pooling)
2. Implement Redis caching
3. Optimize ChromaDB queries
4. Tune LLM inference (batch size, threads)
5. Add CDN untuk static assets
```

---

### **FASE 7: DOCUMENTATION & DEPLOYMENT (Minggu 21-24)**

#### Langkah 19: Update Dokumentasi
```
Update files:
1. README.md (16GB requirement)
2. docs/DEPLOYMENT.md (step-by-step)
3. docs/AWS_SETUP.md (AWS configuration)
4. docs/DATABASE_SCHEMA.md (PostgreSQL schema)
5. docs/TROUBLESHOOTING.md (common issues)
```

#### Langkah 20: Create Deployment Package
```bash
# Create installer script
File: deployment/install.sh

Fungsi:
1. Check system requirements (16GB RAM, etc)
2. Install PostgreSQL
3. Install Python dependencies
4. Download LLM model
5. Setup database schema
6. Configure systemd services
7. Setup firewall rules
8. Create admin user
9. Start services
10. Verify installation

Usage:
sudo bash deployment/install.sh
```

---

## 🎯 KESIMPULAN STRATEGI

### **Development Environment:**
```
Local Machine:
├── Kode development (VSCode/PyCharm)
├── Unit testing (pytest)
├── UI development (frontend)
└── Integration testing (local)

AWS Cloud:
├── Model training (SageMaker)
├── Embedding generation (Bedrock)
├── Curriculum processing (Lambda)
└── Distribution (S3 + CloudFront)

School Server:
├── Production runtime (100% offline)
├── PostgreSQL database
├── ChromaDB vector store
└── LLM inference engine
```

### **Update Mechanism (Tanpa Hard-Code):**
```
Guru Upload PDF → AWS Process → VKP Package → School Pull → ChromaDB Update → Siswa Akses

TIDAK ADA HARD-CODE:
- Mata pelajaran: Dynamic dari database
- Buku: Dynamic dari VKP
- Pertanyaan: Dynamic dari chat
- Topik: Dynamic dari mastery tracker
```

### **AWS Utilization:**
```
✅ SageMaker: Model training & fine-tuning
✅ Bedrock: Embedding generation & evaluation
✅ Lambda: Curriculum processing automation
✅ S3: VKP storage & versioning
✅ CloudFront: Fast distribution
✅ DynamoDB: Aggregated telemetry (non-sensitive)

❌ TIDAK untuk production inference
❌ TIDAK untuk chat storage
❌ TIDAK untuk real-time processing
```

### **Next Immediate Actions:**
1. ✅ Baca ARCHITECTURE_ANALYSIS.md (sudah ada)
2. ✅ Baca DEVELOPMENT_STRATEGY.md (ini)
3. ⏭️ Setup AWS account & credentials
4. ⏭️ Design PostgreSQL schema
5. ⏭️ Buat migration plan dari in-memory ke database
6. ⏭️ Setup S3 buckets untuk testing
7. ⏭️ Buat Lambda function prototype
8. ⏭️ Test end-to-end flow dengan 1 PDF

---

**PENTING:** Jangan ubah kode sekarang. Ikuti fase-fase di atas secara bertahap.

**Status:** STRATEGIC GUIDANCE COMPLETE  
**Next Review:** Setelah Fase 0 selesai
