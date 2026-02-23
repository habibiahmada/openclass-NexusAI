# 🏗️ Architecture Notes

## Platform Design Philosophy

Sistem dirancang untuk:

1. **Offline-first**: Berjalan tanpa internet
2. **Production-ready**: Optimized for 16GB RAM school servers
3. **Easy deployment**: Mudah dipasang oleh sekolah
4. **User-friendly**: Mudah digunakan siswa SD–SMA
5. **Maintainable**: Mudah dipelihara dan di-update

## Architecture Choice: Local Web Server

### Why Web-Based?

- **Cross-platform**: Windows, Linux, Mac
- **Easy updates**: Update sekali, semua user dapat
- **Lightweight UI**: Browser-based interface
- **LAN support**: 1 server, multiple clients
- **School-friendly**: Cocok untuk lab komputer

### Stack

- **Backend**: Python + FastAPI + llama.cpp + ChromaDB
- **Frontend**: HTML/CSS/JavaScript (vanilla)
- **Deployment**: Local server (localhost atau LAN)
- **Optional**: PWA atau Electron wrapper

Lihat [SYSTEM_ARCHITECTURE.md](../SYSTEM_ARCHITECTURE.md) untuk detail lengkap.
