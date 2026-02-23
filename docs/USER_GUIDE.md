# OpenClass Nexus AI - User Guide

## Panduan Lengkap Sistem AI Tutor Offline

### Daftar Isi
1. [Pengenalan](#pengenalan)
2. [Instalasi](#instalasi)
3. [Penggunaan Dasar](#penggunaan-dasar)
4. [Fitur Lanjutan](#fitur-lanjutan)
5. [Troubleshooting](#troubleshooting)
6. [FAQ](#faq)

## Pengenalan

OpenClass Nexus AI adalah sistem tutor AI offline yang dirancang khusus untuk pendidikan Indonesia. Sistem ini dapat:

- ✅ Menjawab pertanyaan tentang materi pelajaran SMA
- ✅ Bekerja sepenuhnya offline setelah instalasi
- ✅ Menggunakan kurikulum BSE Kemdikbud
- ✅ Berjalan pada server sekolah dengan 16GB RAM
- ✅ Memberikan jawaban dalam Bahasa Indonesia

## Instalasi

### Persyaratan Sistem

**Minimum**:
- Windows 10/11, macOS 10.15+, atau Linux Ubuntu 18.04+
- RAM: 16GB
- CPU: 8-core
- Storage: 512GB SSD
- Internet: Diperlukan untuk instalasi awal

**Direkomendasikan**:
- RAM: 8GB atau lebih
- Storage: 20GB ruang kosong
- CPU: 4 core atau lebih

### Langkah Instalasi

#### 1. Download dan Setup

```bash
# Clone repository
git clone https://github.com/your-org/openclass-nexus.git
cd openclass-nexus

# Buat virtual environment
python -m venv openclass-env

# Aktivasi environment
# Windows:
openclass-env\Scripts\activate
# macOS/Linux:
source openclass-env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Konfigurasi Environment

```bash
# Copy template konfigurasi
cp .env.example .env

# Edit file .env dengan text editor
# Sesuaikan pengaturan sesuai kebutuhan
```

#### 3. Download Model AI

```bash
# Jalankan script setup
python scripts/setup_model.py

# Model akan didownload otomatis (sekitar 2GB)
# Proses ini memerlukan koneksi internet
```

#### 4. Setup Database Pengetahuan

```bash
# Inisialisasi database vektor
python scripts/setup_knowledge_base.py

# Proses ETL untuk materi pendidikan
python scripts/run_etl_pipeline.py
```

## Penggunaan Dasar

### 1. Memulai Sistem

```python
from src.local_inference.complete_pipeline import CompletePipeline

# Inisialisasi sistem
pipeline = CompletePipeline()
print("✅ Sistem AI Tutor siap digunakan!")
```

### 2. Mengajukan Pertanyaan

```python
# Contoh pertanyaan informatika
response = pipeline.query(
    "Jelaskan apa itu algoritma dan berikan contohnya",
    subject="informatika",
    grade_level=10
)

print(f"Jawaban: {response.answer}")
print(f"Sumber: {response.sources}")
print(f"Tingkat keyakinan: {response.confidence}%")
```

### 3. Contoh Pertanyaan yang Didukung

#### Informatika Kelas 10
```python
# Konsep dasar
pipeline.query("Apa perbedaan antara data dan informasi?")

# Algoritma
pipeline.query("Bagaimana cara kerja algoritma pencarian linear?")

# Pemrograman
pipeline.query("Jelaskan konsep variabel dalam pemrograman")

# Struktur data
pipeline.query("Apa itu array dan bagaimana cara menggunakannya?")
```

#### Matematika
```python
# Aljabar
pipeline.query("Bagaimana cara menyelesaikan persamaan kuadrat?")

# Geometri
pipeline.query("Jelaskan teorema Pythagoras dengan contoh")
```

### 4. Interface Command Line

```bash
# Jalankan CLI interaktif
python scripts/interactive_tutor.py

# Contoh sesi:
> Pertanyaan: Jelaskan konsep rekursi dalam pemrograman
> AI Tutor: Rekursi adalah teknik pemrograman di mana sebuah fungsi 
  memanggil dirinya sendiri untuk menyelesaikan masalah yang lebih kecil...
```

## Fitur Lanjutan

### 1. Batch Processing

Untuk memproses banyak pertanyaan sekaligus:

```python
# Daftar pertanyaan
questions = [
    "Apa itu HTML?",
    "Bagaimana cara membuat tabel di HTML?",
    "Jelaskan konsep CSS",
    "Apa perbedaan HTML dan CSS?"
]

# Proses batch
results = pipeline.batch_process(
    questions,
    max_concurrent=3,  # Maksimal 3 pertanyaan bersamaan
    timeout=30         # Timeout 30 detik per pertanyaan
)

# Tampilkan hasil
for i, result in enumerate(results):
    print(f"\nPertanyaan {i+1}: {questions[i]}")
    print(f"Jawaban: {result.answer}")
    print(f"Waktu proses: {result.processing_time}ms")
```

### 2. Monitoring Performa

```python
# Mulai monitoring
monitor = pipeline.get_monitor()
session = monitor.start_session()

# Proses beberapa pertanyaan
for question in my_questions:
    response = pipeline.query(question)
    
# Dapatkan statistik
metrics = session.get_metrics()
print(f"Total pertanyaan: {metrics.total_queries}")
print(f"Rata-rata waktu respons: {metrics.avg_response_time}ms")
print(f"Penggunaan memori puncak: {metrics.peak_memory_mb}MB")
print(f"Throughput: {metrics.queries_per_minute} pertanyaan/menit")
```

### 3. Kustomisasi Respons

```python
# Atur parameter respons
response = pipeline.query(
    "Jelaskan konsep OOP",
    max_tokens=300,        # Maksimal 300 kata
    temperature=0.7,       # Kreativitas respons (0.0-1.0)
    context_limit=2048,    # Batas konteks
    include_sources=True   # Sertakan sumber referensi
)
```

### 4. Validasi Pendidikan

```python
from src.local_inference.educational_validator import EducationalValidator

validator = EducationalValidator()

# Validasi jawaban
validation = validator.validate_response(
    question="Apa itu variabel?",
    answer=response.answer,
    grade_level=10,
    subject="informatika"
)

print(f"Sesuai kurikulum: {validation.is_curriculum_aligned}")
print(f"Sesuai usia: {validation.is_age_appropriate}")
print(f"Kualitas bahasa: {validation.language_score}/100")
```

## Troubleshooting

### Masalah Umum

#### 1. Model Tidak Dapat Dimuat

**Gejala**: Error "Model not found" atau "Out of memory"

**Solusi**:
```bash
# Periksa ruang disk
df -h

# Periksa RAM yang tersedia
free -h

# Download ulang model
python scripts/setup_model.py --force-download
```

#### 2. Respons Lambat

**Gejala**: Waktu respons > 10 detik

**Solusi**:
```python
# Kurangi context limit
response = pipeline.query(
    question,
    context_limit=1024  # Dari 4096 ke 1024
)

# Atau gunakan mode performa tinggi
pipeline.set_performance_mode("fast")
```

#### 3. Database Vektor Error

**Gejala**: Error "ChromaDB connection failed"

**Solusi**:
```bash
# Reset database
rm -rf data/vector_db/*

# Rebuild database
python scripts/setup_knowledge_base.py --rebuild
```

#### 4. Memori Habis

**Gejala**: "Out of memory" error

**Solusi**:
```python
# Aktifkan mode hemat memori
pipeline.enable_memory_optimization()

# Atau kurangi batch size
results = pipeline.batch_process(
    questions,
    max_concurrent=1  # Dari 3 ke 1
)
```

### Log dan Debugging

```python
# Aktifkan logging detail
import logging
logging.basicConfig(level=logging.DEBUG)

# Periksa status sistem
status = pipeline.get_system_status()
print(f"Model loaded: {status.model_loaded}")
print(f"Database ready: {status.database_ready}")
print(f"Memory usage: {status.memory_usage_mb}MB")
```

## FAQ

### Q: Apakah sistem ini benar-benar offline?
**A**: Ya, setelah instalasi awal dan download model, sistem dapat berjalan sepenuhnya offline. Tidak memerlukan koneksi internet untuk menjawab pertanyaan.

### Q: Mata pelajaran apa saja yang didukung?
**A**: Saat ini fokus pada Informatika kelas 10, dengan rencana ekspansi ke mata pelajaran lain seperti Matematika, Fisika, dan Kimia.

### Q: Bisakah menambah materi sendiri?
**A**: Ya, Anda dapat menambahkan PDF materi pendidikan ke folder `data/raw_dataset/` dan menjalankan ETL pipeline untuk memproses materi tersebut.

### Q: Bagaimana cara update model?
**A**: Jalankan `python scripts/update_model.py` untuk mendapatkan versi model terbaru.

### Q: Apakah bisa digunakan untuk ujian?
**A**: Sistem ini dirancang sebagai alat bantu belajar, bukan untuk ujian. Gunakan secara etis sesuai kebijakan sekolah.

### Q: Bagaimana cara melaporkan bug?
**A**: Buat issue di GitHub repository atau hubungi tim pengembang melalui email support.

### Q: Bisakah dijalankan di server?
**A**: Ya, sistem mendukung deployment server dengan REST API. Lihat dokumentasi deployment untuk detail.

## Dukungan

### Komunitas
- **GitHub**: [Repository Issues](https://github.com/your-org/openclass-nexus/issues)
- **Discord**: [OpenClass Community](https://discord.gg/openclass)
- **Forum**: [Diskusi Pengguna](https://forum.openclass.id)

### Kontak
- **Email**: support@openclass.id
- **Website**: https://openclass.id
- **Dokumentasi**: https://docs.openclass.id

---

**Versi Panduan**: 3.0.0  
**Terakhir Diperbarui**: 26 Januari 2026  
**Bahasa**: Indonesia