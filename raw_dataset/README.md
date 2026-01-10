# Raw Dataset Directory

## ⚠️ Important Notice

**PDF files are NOT stored in this repository.** They are stored in AWS S3 for the following reasons:

### Why S3 Storage?

1. **File Size**: Educational PDFs are large (150-200MB total)
2. **Version Control**: Git is not suitable for large binary files
3. **Distribution**: S3 + CloudFront provides global content delivery
4. **Cost Efficiency**: S3 lifecycle policies manage storage costs
5. **Security**: Proper access controls and encryption

### S3 Bucket Structure

```
s3://openclass-nexus-data/
├── raw-pdf/
│   └── kelas_10/
│       └── informatika/
│           ├── 20221-informatika.pdf
│           ├── 70764605INFORMATIKASMK.pdf
│           ├── Buku Murid Informatika - Informatika Semester 1 Bab 4 - Fase E.pdf
│           ├── Buku-Panduan-Informatika-untuk-SMA-Kelas-X.pdf
│           ├── Buku-Panduan-Informatika-untuk-SMK-MAK-Kelas-X.pdf
│           ├── informatika-31320.pdf
│           ├── Informatika-BG-KLS-X.pdf
│           ├── Informatika-BS-KLS-X.pdf
│           ├── Informatika-KLS-X-Sem-1.pdf
│           ├── INFORMATIKA-SMA-X-ANALISIS-DATA.pdf
│           ├── Informatika-untuk-SMK-MAK-Kelas-X-Semester-1.pdf
│           ├── Informatika-untuk-SMK-MAK-Kelas-X-Semester-2.pdf
│           ├── Modul-Pengenalan-Perangkat-TIK-Dasar.pdf
│           ├── ModulBahanBelajar_Informatika_2021_Pembelajaran 1.pdf
│           └── Smk-Informatika-BS-KLS-X.pdf
├── processed-text/
│   └── kelas_10/
│       └── informatika/
├── vector-db/
│   └── educational_content.db
└── model-weights/
    └── openclass-nexus-q4.gguf
```

### Local Directory Structure

This directory maintains the **folder structure only** for development reference:

```
raw_dataset/
└── kelas_10/
    └── informatika/
        └── .gitkeep  # Keeps folder structure in git
```

### How to Access PDFs

1. **For Development**: Use `scripts/download_sample_data.py`
2. **For Production**: Files are automatically downloaded from S3
3. **For Processing**: Use `src/data_processing/` modules

### Scripts Available

- `scripts/setup_aws.py` - Creates S3 bucket and folder structure ✅
- `scripts/upload_to_s3.py` - Uploads PDFs to S3 (completed) ✅
- `scripts/download_from_s3.py` - Downloads PDFs from S3 for local development ✅
- `scripts/test_aws_connection.py` - Tests AWS connectivity ✅

### Current Status: ✅ COMPLETED

All 15 PDF files (140.6 MB total) have been successfully uploaded to S3:
- Location: `s3://openclass-nexus-data/raw-pdf/kelas_10/informatika/`
- Upload completed: 2024-01-10
- All files verified and accessible

### Cost Management

- **Lifecycle Policy**: Raw PDFs deleted after 30 days (processed versions kept)
- **Intelligent Tiering**: Automatic cost optimization
- **Budget Alerts**: $1.00 monthly limit with notifications

### Legal Compliance

All PDFs are from BSE Kemdikbud (Open Educational Resources):
- Source: https://bse.kemdikbud.go.id/
- License: Open for educational use
- Attribution: "Buku Sekolah Elektronik, Kementerian Pendidikan dan Kebudayaan"

---

**Note**: To work with PDFs locally during development, run:
```bash
python scripts/download_from_s3.py --subject informatika --grade kelas_10
```

Or to list all files in S3:
```bash
python scripts/download_from_s3.py --list-only
```