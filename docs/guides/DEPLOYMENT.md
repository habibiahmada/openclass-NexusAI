# 📋 Deployment Guide

Panduan deployment untuk sekolah.

## System Requirements

- Python 3.8+
- 4GB+ RAM
- 10GB+ disk space
- Windows/Linux/Mac OS
- Network adapter (untuk LAN access)

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python scripts/check_system_ready.py
```

### 3. Prepare Data

Pastikan vector database sudah ada:
```bash
python scripts/check_embeddings.py
```

### 4. Start Server

```bash
python api_server.py
```

## Network Setup (Optional)

Untuk akses dari komputer lain di LAN:

1. Cari IP address server:
   ```bash
   ipconfig  # Windows
   ifconfig  # Linux/Mac
   ```

2. Edit `api_server.py`, ubah:
   ```python
   uvicorn.run(app, host="0.0.0.0", port=8000)
   ```

3. Akses dari komputer lain: `http://[IP-SERVER]:8000`

## Troubleshooting

Lihat [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) untuk troubleshooting lengkap.
