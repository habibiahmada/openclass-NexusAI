#!/bin/bash
# OpenClass Nexus AI - Web UI Launcher for Linux/Mac
# Run: chmod +x start_web_ui.sh && ./start_web_ui.sh

echo "============================================================"
echo "  OpenClass Nexus AI - Web UI Launcher"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 tidak ditemukan!"
    echo ""
    echo "Silakan install Python3 terlebih dahulu:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  macOS: brew install python3"
    echo ""
    exit 1
fi

echo "[OK] Python3 ditemukan"
echo ""

# Check if virtual environment exists
if [ -d "openclass-env" ]; then
    echo "[INFO] Mengaktifkan virtual environment..."
    source openclass-env/bin/activate
    echo "[OK] Virtual environment aktif"
    echo ""
else
    echo "[WARNING] Virtual environment tidak ditemukan"
    echo "[INFO] Menggunakan Python global"
    echo ""
fi

# Run the startup script
echo "[INFO] Menjalankan pre-flight checks..."
echo ""
python3 scripts/start_web_ui.py

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Terjadi kesalahan saat menjalankan server"
    echo ""
    read -p "Press Enter to exit..."
fi
