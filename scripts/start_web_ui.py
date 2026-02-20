#!/usr/bin/env python3
"""
Script untuk menjalankan Web UI OpenClass Nexus AI
Dengan pre-flight checks dan helpful messages
"""

import sys
import subprocess
import socket
from pathlib import Path

def check_port_available(port=8000):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0

def check_dependencies():
    """Check if required packages are installed"""
    required = ['fastapi', 'uvicorn', 'psutil']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

def check_frontend_files():
    """Check if frontend files exist"""
    frontend_dir = Path('frontend')
    required_files = {
        'index.html': 'index.html',
        'css/base.css': 'css/base.css',
        'js/landing.js': 'js/landing.js'
    }
    
    if not frontend_dir.exists():
        return False, "Folder 'frontend/' tidak ditemukan"
    
    for file, display_name in required_files.items():
        if not (frontend_dir / file).exists():
            return False, f"File 'frontend/{display_name}' tidak ditemukan"
    
    return True, "OK"

def get_local_ip():
    """Get local IP address for LAN access"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "N/A"

def print_banner():
    """Print startup banner"""
    print("=" * 70)
    print("  OpenClass Nexus AI - Web UI Server")
    print("  AI Tutor Kurikulum Nasional - Mode Offline")
    print("=" * 70)
    print()

def print_access_info(local_ip):
    """Print access information"""
    print("✅ Server berhasil dijalankan!")
    print()
    print("📍 Akses Lokal (komputer ini):")
    print("   http://localhost:8000")
    print("   http://127.0.0.1:8000")
    print()
    
    if local_ip != "N/A":
        print("🌐 Akses dari Komputer Lain (LAN):")
        print(f"   http://{local_ip}:8000")
        print()
        print("   💡 Siswa di lab komputer bisa akses menggunakan URL di atas")
        print()
    
    print("🎯 Mode yang Tersedia:")
    print("   • Mode Siswa  - Chat dengan AI Tutor")
    print("   • Mode Guru   - Dashboard & Analytics")
    print("   • Mode Admin  - System Management")
    print()
    print("⚠️  Tekan Ctrl+C untuk menghentikan server")
    print("=" * 70)
    print()

def main():
    """Main function"""
    print_banner()
    
    # Check 1: Dependencies
    print("🔍 Checking dependencies...")
    missing = check_dependencies()
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print()
        print("Install dengan command:")
        print(f"   pip install {' '.join(missing)}")
        sys.exit(1)
    print("✅ All dependencies installed")
    print()
    
    # Check 2: Frontend files
    print("🔍 Checking frontend files...")
    ok, message = check_frontend_files()
    if not ok:
        print(f"❌ {message}")
        print()
        print("Pastikan folder 'frontend/' berisi:")
        print("   - index.html")
        print("   - css/ (folder dengan file CSS)")
        print("   - js/ (folder dengan file JavaScript)")
        sys.exit(1)
    print("✅ Frontend files found")
    print()
    
    # Check 3: Port availability
    print("🔍 Checking port 8000...")
    if not check_port_available(8000):
        print("⚠️  Port 8000 sudah digunakan")
        print()
        print("Solusi:")
        print("   1. Stop aplikasi yang menggunakan port 8000")
        print("   2. Atau edit api_server.py untuk ganti port")
        print()
        response = input("Lanjutkan? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    else:
        print("✅ Port 8000 available")
    print()
    
    # Get local IP
    local_ip = get_local_ip()
    
    # Print access info
    print_access_info(local_ip)
    
    # Start server
    try:
        print("🚀 Starting server...")
        print()
        subprocess.run([sys.executable, "api_server.py"])
    except KeyboardInterrupt:
        print()
        print()
        print("=" * 70)
        print("👋 Server dihentikan. Terima kasih!")
        print("=" * 70)
        sys.exit(0)
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
