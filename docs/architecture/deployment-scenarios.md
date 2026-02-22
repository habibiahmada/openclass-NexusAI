# OPENCLASS NEXUS AI

## Definitive Deployment Topology v1.0

Hybrid Orchestrated Edge AI for Education

---

# I. STRATEGIC POSITIONING (FINAL LOCK)

OpenClass Nexus AI adalah:

Hybrid Orchestrated Edge AI System
dengan:

* 100% offline inference di sekolah
* Control plane terpusat di AWS
* Tanpa cloud runtime dependency saat pembelajaran
* Privacy by architecture (bukan kebijakan administratif)

Model deployment:

One School – One Sovereign AI Node
dengan orkestrasi nasional non-intrusif.

Tidak ada federasi multi-sekolah.
Setiap sekolah adalah node otonom.

---

# II. DEPLOYMENT TOPOLOGY OVERVIEW

```
┌─────────────────────────────────────────────┐
│                CLIENT LAYER                │
│  (Browser Siswa/Guru via WiFi Sekolah)     │
└────────────────────────┬────────────────────┘
                         │ HTTP (LAN Only)
                         ▼
┌─────────────────────────────────────────────┐
│           SCHOOL EDGE SERVER NODE          │
│                                             │
│  - LLM Runtime (Quantized)                 │
│  - Local Embedding Engine                  │
│  - Vector DB (ChromaDB)                    │
│  - RAG Orchestrator                        │
│  - Pedagogical Engine                      │
│  - Local Metadata Store                    │
│  - Chat History (Never Leaves School)      │
└────────────────────────┬────────────────────┘
                         │ Periodic Sync Only
                         ▼
┌─────────────────────────────────────────────┐
│           AWS NATIONAL CONTROL PLANE       │
│                                             │
│  - Model Training (SageMaker)              │
│  - Evaluation & Benchmark (Bedrock)        │
│  - Curriculum Processing Pipeline           │
│  - Version Packaging (VKP)                 │
│  - Distribution (S3 + CloudFront)          │
│  - Aggregated Metadata (DynamoDB)          │
└─────────────────────────────────────────────┘
```

---

# III. SCHOOL EDGE SERVER (LAYER 2 – CORE RUNTIME)

## A. Deployment Model

* Dedicated physical server per school
* Minimum specification:

  * 16GB RAM
  * 8-core CPU
  * 512GB SSD
  * Linux (Ubuntu Server LTS)
* GPU optional (tidak wajib)

Alasan:

* Multi-user concurrency
* Persistent vector store
* Stable inference runtime

Tidak lagi ada klaim 4GB device.

---

## B. Runtime Components (On-Prem Only)

### 1. LLM Runtime

* Model: Llama 3.x 3B (distilled)
* Format: GGUF
* Quantization: 4-bit (Q4_K_M)
* Engine: llama.cpp server mode
* Token streaming enabled
* Max concurrent threads: 5

Inference sepenuhnya lokal.

---

### 2. Local Embedding Engine

Default mode:

* Embedding diproses di AWS saat kurikulum dipaketkan.

Optional sovereign mode:

* Local MiniLM quantized embedding engine
* Digunakan jika sekolah tidak ingin upload PDF

Dengan ini:
AWS bukan dependency mutlak.

---

### 3. Vector Database

* ChromaDB persistent mode
* HNSW index
* Stored per subject & grade
* Version-tagged embedding store

---

### 4. RAG Orchestrator

Pipeline lokal:

1. User query
2. Local embedding
3. Semantic retrieval (top-k)
4. Context assembly
5. Prompt structuring
6. LLM generation
7. Response streaming

Tidak ada external call.

---

### 5. Pedagogical Intelligence Engine

Tambahan struktural untuk menjawab rasio guru–siswa tinggi:

* Topic mastery tracker
* Weak area detection
* Adaptive practice question generation
* Weekly summary report untuk guru

Ini mengubah sistem dari chatbot menjadi learning support infrastructure.

---

### 6. Local Metadata Store

Disimpan di PostgreSQL lokal:

* User login
* Session data
* Chat history
* Usage logs

Chat content tidak pernah keluar.

---

### 7. Caching Layer

* Optional Redis local
* Repeated question optimization
* Reduce CPU load

---

# IV. AWS NATIONAL CONTROL PLANE (LAYER 3)

AWS tidak menjalankan inference produksi.

Fungsi AWS dibagi menjadi 4 domain.

---

## A. Model Development Domain

### Amazon SageMaker

Digunakan untuk:

* Fine-tuning lightweight LLM
* Knowledge distillation
* Performance testing
* Bias evaluation
* CPU-optimized training configuration

### Amazon Bedrock

Digunakan untuk:

* Quality benchmarking
* Comparative response validation
* Evaluation only (not production embedding)

Bedrock bukan runtime engine.

---

## B. Curriculum Processing Pipeline

Alur:

1. PDF kurikulum masuk ke S3
2. Lambda trigger preprocessing
3. Cleaning & chunking
4. Metadata enrichment
5. Embedding generation
6. Packaging into Versioned Knowledge Package (VKP)

VKP berisi:

* Embedding vectors
* Metadata
* Integrity checksum
* Version manifest
* Subject & grade tagging

Setelah selesai:
PDF dapat dihapus (tidak disimpan permanen).

---

## C. Distribution Domain

* S3 (versioned bucket)
* CloudFront CDN
* Signed URL access

School server melakukan:

* Periodic version check
* Delta update
* Integrity verification

Update bersifat pull-based, bukan push.

---

## D. Aggregated Impact Monitoring

Disimpan di DynamoDB:

Hanya metadata agregat:

* Total query count
* Average latency
* Model version
* Error rate
* Storage usage

Tidak ada chat content.
Tidak ada personal data.

---

# V. SECURITY & PRIVACY MODEL (LOCKED)

## Data Never Leaves School

* Chat history
* Question text
* Student identity
* Teacher identity
* Detailed logs

## Data Sent to AWS (Limited Cases)

Saat:

* Model update
* Curriculum package retrieval

Yang dikirim:

* No chat content
* No user data
* Only anonymized usage metrics

Privacy dijamin oleh desain arsitektur.

---

# VI. PERFORMANCE & CONCURRENCY STRATEGY

Untuk menghindari bottleneck:

* Max 5 inference threads
* Async queue management
* Token streaming
* Redis cache
* Optional GPU acceleration

Target latency:

* 3–8 detik per response
* Stable hingga 100–300 siswa aktif (bergantung distribusi waktu)

---

# VII. FAILURE & RECOVERY DESIGN

Ditambahkan untuk enterprise-grade resilience:

1. Weekly snapshot backup
2. Version rollback capability
3. Offline restore package
4. Health monitoring daemon
5. Automatic restart service

Jika internet mati total:
Sistem tetap berjalan.

Jika AWS mati:
Sistem tetap berjalan.

Jika satu sekolah gagal:
Tidak mempengaruhi sekolah lain.

---

# VIII. GOVERNANCE MODEL (FINAL DECISION)

Deployment type:

Independent School Sovereign Node

Tidak ada:

* Inter-school data sharing
* Cross-school authentication
* Federated identity system
* Centralized governance enforcement

AWS hanya:

* Orchestration
* Training
* Version distribution
* Impact aggregation (non-sensitive)

---

# IX. END-TO-END FLOW SUMMARY

## Student Interaction Flow

Browser → Local Server → RAG → LLM → Response
100% offline

## Curriculum Update Flow

School → Internet → AWS → VKP → School
Periodic only

## Model Update Flow

AWS → CloudFront → School pull → Replace model → Restart runtime

---

# X. FINAL SYSTEM IDENTITY

OpenClass Nexus AI adalah:

Distributed Edge AI Infrastructure
dengan Centralized Intelligence Orchestration
dan Local Sovereign Runtime

Bukan:

* Cloud chatbot
* Thin client AI
* Subscription AI SaaS
* Federated governance AI

---

# XI. STATUS: ARSITEKTUR DIKUNCI

Dengan blueprint ini:

* Tidak ada lagi ambiguitas hardware
* Tidak ada konflik peran AWS
* Tidak ada konflik embedding strategy
* Tidak ada konflik deployment model
* Tidak ada konflik privacy claim
* Tidak ada konflik operasional

Dokumen ini menjadi:

Single Source of Architectural Truth
untuk proposal, pengembangan, dan evaluasi.