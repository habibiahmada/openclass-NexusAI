# Guide: Menggunakan Local Embeddings (Tanpa AWS)

## Kenapa Pakai Local Embeddings?

Jika Anda mengalami masalah dengan AWS Bedrock (quota limit, billing, dll), Anda bisa menggunakan model embedding lokal yang:

✅ **Gratis** - Tidak ada biaya API
✅ **Offline** - Berjalan di laptop setelah download model
✅ **Support Indonesian** - Model multilingual
✅ **Mudah** - Tidak perlu konfigurasi AWS

## Perbandingan

| Aspek | AWS Bedrock | Local Model |
|-------|-------------|-------------|
| **Model** | Amazon Titan v2 | Sentence-Transformers |
| **Dimensi** | 1024 | 768 |
| **Biaya** | ~$0.50-1.00 | $0 (Gratis) |
| **Kecepatan** | Cepat (cloud) | Sedang (CPU) |
| **Internet** | Perlu | Tidak perlu |
| **Setup** | AWS credentials | pip install |
| **Bahasa Indonesia** | ✓ | ✓ |

## Cara Menggunakan

### 1. Install Dependencies

```bash
pip install sentence-transformers torch
```

Atau jika sudah install requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Jalankan Script Local Embeddings

```bash
python scripts/complete_phase2_local_embeddings.py
```

**First run**: Script akan download model (~278MB) dari HuggingFace. Ini hanya sekali.

**Output**:
```
Fase 2: Generate Embeddings (LOCAL MODEL)
============================================================
Ditemukan 15 file text untuk diproses
Inisialisasi local embedding model...
⚠️  First run akan download model (~278MB)
Loading local embedding model: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
Model loaded successfully! Embedding dimension: 768

[1/15] Processing: 20221-informatika.txt
  Generated 413 chunks
  Generating embeddings for chunks 1-32...
  Generating embeddings for chunks 33-64...
  ...
  ✓ Successfully stored 413 embeddings

...

SUMMARY
============================================================
Files processed: 15
Total chunks: 7000
Total embeddings: 7000
Cost: $0.00 (FREE - Local model)
Documents in vector DB: 7000

✓ Fase 2 selesai! Vector database berhasil dibuat.
```

### 3. Estimasi Waktu

Dengan CPU (tanpa GPU):
- **Per chunk**: ~0.1-0.2 detik
- **7000 chunks**: ~15-30 menit
- **Dengan GPU**: ~5-10 menit

### 4. Lanjut ke Fase 3

Setelah fase 2 selesai, lanjut download model Llama:

```bash
python scripts/download_model.py
```

## Model Options

Jika laptop Anda lemah, bisa pakai model lebih kecil:

### Option 1: Multilingual (Recommended)
```python
# 768-dim, 278MB, support Indonesian
model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
```

### Option 2: Smaller English-focused
```python
# 384-dim, 80MB, lebih cepat tapi English-focused
model_name="sentence-transformers/all-MiniLM-L6-v2"
```

Edit di `scripts/complete_phase2_local_embeddings.py` line 52.

## Troubleshooting

### Error: "No module named 'sentence_transformers'"
```bash
pip install sentence-transformers
```

### Error: "torch not found"
```bash
pip install torch
```

### Download model lambat?
Model di-download dari HuggingFace. Jika lambat:
1. Gunakan VPN jika HuggingFace di-block
2. Download manual dari: https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2
3. Simpan di `~/.cache/torch/sentence_transformers/`

### Out of Memory?
Kurangi batch_size di script:
```python
batch_size = 16  # dari 32 ke 16
```

## Kompatibilitas dengan RAG System

Local embeddings **100% kompatibel** dengan sistem RAG Anda:
- ChromaDB tetap sama
- Query embeddings bisa pakai local atau Bedrock
- Llama model tetap sama
- Hanya embedding generation yang berbeda

## Migrasi ke Bedrock Nanti

Jika nanti quota AWS approved, Anda bisa:
1. Hapus vector DB lama: `rm -rf data/vector_db`
2. Jalankan script Bedrock: `python scripts/complete_phase2_embeddings.py`
3. Bedrock embeddings (1024-dim) lebih optimal tapi local (768-dim) juga bagus

## Kesimpulan

Local embeddings adalah solusi sempurna untuk:
- Development dan testing
- Menunggu AWS quota approval
- Budget terbatas
- Prefer offline solution

Kualitas hasil tetap bagus untuk educational chatbot!
