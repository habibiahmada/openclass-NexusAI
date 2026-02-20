# 🚀 Quick Start Guide - OpenClass Nexus AI

Panduan cepat untuk memulai menggunakan sistem.

## Verifikasi Sistem

Sebelum menjalankan, pastikan sistem sudah siap:

```bash
python scripts/check_system_ready.py
```

Sistem harus menunjukkan:
- ✓ Dependencies terinstall
- ✓ Model LLM tersedia (~1.9 GB)
- ✓ Vector database siap (6937+ dokumen)

## Menjalankan Aplikasi

### Windows
```bash
start_web_ui.bat
```

### Linux/Mac
```bash
./start_web_ui.sh
```

### Manual
```bash
python api_server.py
```

Server akan berjalan di: http://localhost:8000

## Verifikasi Embedding

```bash
python scripts/check_embeddings.py
```

Output yang diharapkan:
```
✅ Vector database found
✅ Collections: 1
✅ Total documents: [jumlah]
✅ Embeddings ready
```

## Mode Penggunaan

- **Siswa**: Chat interface untuk bertanya
- **Guru**: Dashboard dan analytics
- **Admin**: System monitoring dan maintenance

Lihat [USER_GUIDE.md](../USER_GUIDE.md) untuk detail lengkap.
