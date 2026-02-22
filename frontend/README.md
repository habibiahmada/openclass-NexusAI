# OpenClass Nexus AI - Web Interface

UI berbasis web untuk OpenClass Nexus AI sesuai dengan rekomendasi arsitektur di `platform_base.md`.

## 🎯 Fitur Utama

### 1. **Mode Siswa** 
- Chat interface untuk bertanya tentang materi pelajaran
- Filter mata pelajaran (Informatika, Matematika, IPA, Bahasa Indonesia)
- Aksi cepat: Ringkas, Contoh Soal, Latihan, Jelaskan Konsep
- Menampilkan sumber jawaban dari buku kurikulum

### 2. **Mode Guru**
- Dashboard statistik pertanyaan siswa
- Analisis topik yang sering ditanyakan
- Export laporan dalam format PDF/CSV
- Monitoring aktivitas pembelajaran

### 3. **Mode Admin**
- Status sistem (Model AI, Database, Versi)
- Update model dan kurikulum
- Backup database
- Monitoring resource (RAM, Storage)

## 🚀 Cara Menjalankan

### Opsi 1: Server Lokal (Recommended)

1. Install dependencies:
```bash
pip install fastapi uvicorn psutil
```

2. Jalankan server:
```bash
python api_server.py
```

3. Buka browser dan akses:
```
http://localhost:8000
```

### Opsi 2: Akses via LAN (Lab Komputer)

1. Jalankan server di komputer guru/server:
```bash
python api_server.py
```

2. Cari IP address komputer server:
```bash
ipconfig  # Windows
ifconfig  # Linux/Mac
```

3. Siswa akses via browser:
```
http://[IP-SERVER]:8000
```

Contoh: `http://192.168.1.100:8000`

## 📁 Struktur File

```
frontend/
├── index.html      # Main HTML structure
├── styles.css      # Styling (minimalis, warna biru pendidikan)
├── app.js          # JavaScript logic & API calls
└── README.md       # Dokumentasi ini

api_server.py       # FastAPI backend server
```

## 🎨 Desain UI

### Prinsip Desain
- **Minimalis**: Tidak menampilkan kompleksitas AI
- **Warna Netral**: Biru pendidikan (#2563eb)
- **Font Besar**: Mudah dibaca untuk semua usia
- **Offline Indicator**: Menunjukkan status koneksi
- **Responsive**: Berfungsi di desktop, tablet, dan mobile

### Komponen Utama
1. **Header**: Logo, subtitle, mode selector
2. **Offline Badge**: Indicator status (hijau = aktif)
3. **Sidebar**: Filter dan quick actions (mode siswa)
4. **Chat Area**: Messages dengan avatar dan source
5. **Dashboard**: Stats dan analytics (mode guru/admin)

## 🔧 Konfigurasi

### API Endpoint
Edit di `app.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000/api';
```

### Port Server
Edit di `api_server.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 📊 API Endpoints

### Student Mode
- `POST /api/chat` - Send question, get answer
- `GET /api/health` - Check server status

### Teacher Mode
- `GET /api/teacher/stats` - Get statistics
- `GET /api/teacher/export?format=csv` - Export report

### Admin Mode
- `GET /api/admin/status` - System status
- `POST /api/admin/update-model` - Update AI model
- `POST /api/admin/update-curriculum` - Update curriculum
- `POST /api/admin/backup` - Create backup

## 🎓 Penggunaan untuk Sekolah

### Skenario 1: Single Computer (Guru)
- Install di 1 komputer guru
- Guru menggunakan langsung via browser

### Skenario 2: Lab Komputer (Multi-User)
- Install di 1 server/komputer utama
- Semua siswa akses via WiFi lokal
- Tidak perlu install di setiap komputer
- Tidak perlu internet

### Skenario 3: Portable (USB)
- Copy seluruh folder ke USB
- Jalankan dari USB di komputer mana saja
- Plug & play

## 🔒 Keamanan

- Server hanya accessible di jaringan lokal
- Tidak ada data yang dikirim ke internet
- Semua proses berjalan offline
- Chat logs tersimpan lokal

## 🛠️ Troubleshooting

### Server tidak bisa diakses
1. Pastikan firewall tidak memblokir port 8000
2. Cek apakah server sudah running: `netstat -an | findstr 8000`
3. Pastikan IP address benar

### Model tidak load
1. Cek file model ada di folder `models/`
2. Cek log error di terminal
3. Pastikan RAM cukup (minimal 4GB)

### UI tidak muncul
1. Clear browser cache
2. Cek console browser (F12) untuk error
3. Pastikan file frontend/ ada semua

## 📝 Customization

### Mengubah Warna
Edit di `styles.css`:
```css
:root {
    --primary-blue: #2563eb;  /* Warna utama */
    --success-green: #10b981; /* Warna sukses */
}
```

### Menambah Mata Pelajaran
Edit di `index.html`:
```html
<option value="fisika">Fisika</option>
```

### Mengubah Welcome Message
Edit di `index.html` bagian welcome message.

## 🚀 Roadmap

- [ ] PWA support (install as app)
- [ ] Dark mode
- [ ] Multi-language support
- [ ] Voice input
- [ ] PDF viewer untuk sumber
- [ ] Collaborative learning features

## 📄 Lisensi

Sesuai dengan lisensi proyek OpenClass Nexus AI.

## 🤝 Kontribusi

Untuk kontribusi UI/UX, silakan buat pull request dengan:
1. Screenshot perubahan
2. Penjelasan improvement
3. Test di berbagai browser

---

**Dibuat sesuai rekomendasi di `platform_base.md`**
- ✅ Offline-first
- ✅ Optimized for school servers (16GB RAM)
- ✅ Mudah dipasang
- ✅ Mudah digunakan (SD-SMA)
- ✅ Mudah dipelihara
