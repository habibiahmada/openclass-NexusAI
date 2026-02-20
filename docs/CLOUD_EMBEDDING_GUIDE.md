# Panduan Cloud Embedding dengan AWS Bedrock

Panduan lengkap untuk menjalankan proses embedding di cloud menggunakan AWS Bedrock.

## Prasyarat

1. AWS Account dengan akses ke Bedrock
2. Kredensial AWS sudah dikonfigurasi di `.env`
3. File text sudah diproses di `data/processed/text/`

## Konfigurasi AWS

Pastikan file `.env` berisi:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-southeast-2
BEDROCK_REGION=ap-southeast-2
BEDROCK_MODEL_ID=amazon.titan-embed-text-v2:0
```

## Menjalankan Embedding

### 1. Verifikasi Koneksi AWS

```bash
python scripts/test_aws_connection.py
```

### 2. Jalankan Embedding Generation

```bash
python scripts/run_cloud_embeddings.py
```

Script ini akan:
- Membaca semua file text dari `data/processed/text/`
- Membuat chunks dengan ukuran 800 karakter (overlap 100)
- Generate embeddings menggunakan AWS Bedrock Titan
- Menyimpan ke ChromaDB di `data/vector_db/`
- Tracking progress di `data/processed/metadata/embedding_progress.json`

### 3. Resume dari Kegagalan

Jika proses terhenti, jalankan kembali script yang sama. Script akan:
- Membaca progress dari file JSON
- Melanjutkan dari file yang belum diproses
- Tidak mengulang file yang sudah berhasil

## Fitur Script

### Progress Tracking
- Menyimpan progress setiap file berhasil diproses
- File progress: `data/processed/metadata/embedding_progress.json`
- Log detail: `data/processed/metadata/embedding_log.txt`

### Error Handling
- Retry otomatis untuk rate limiting
- Skip file yang error tanpa menghentikan proses
- Logging detail untuk debugging

### Batch Processing
- Batch size kecil (3 chunks) untuk menghindari rate limit
- Delay antar request untuk stabilitas
- Progress report real-time

## Monitoring

### Cek Progress Lokal
```bash
# Lihat file progress
cat data/processed/metadata/embedding_progress.json

# Lihat log
tail -f data/processed/metadata/embedding_log.txt
```

### Monitoring AWS Console

#### 1. AWS Bedrock Dashboard
```
https://ap-southeast-2.console.aws.amazon.com/bedrock/home
```
Lihat: Model invocations, latency, error rate

#### 2. CloudWatch Metrics
```
https://ap-southeast-2.console.aws.amazon.com/cloudwatch/home
```
Metrics → Bedrock → Pilih:
- Invocations (total API calls)
- InvocationLatency (response time)
- InvocationClientErrors (4xx errors)
- InvocationServerErrors (5xx errors)

#### 3. CloudWatch Logs
```
Log Groups → /aws/bedrock/modelinvocations
```
Lihat detail setiap request/response

#### 4. AWS Cost Explorer
```
https://us-east-1.console.aws.amazon.com/cost-management/home
```
Filter: Service = Bedrock, Region = ap-southeast-2

### Monitoring dari Terminal
```bash
# Run monitoring script
python scripts/monitor_bedrock.py
```

Script akan menampilkan:
- Metrics 1 jam terakhir
- Recent logs
- Estimasi biaya

### Cek Vector Database
```python
from src.embeddings.chroma_manager import ChromaDBManager

chroma = ChromaDBManager()
chroma.get_collection("educational_content")
print(f"Total documents: {chroma.count_documents()}")
```

## Estimasi Biaya

Model: Amazon Titan Text Embeddings v2
- Harga: $0.0001 per 1K tokens
- Estimasi: ~1 token per 4 karakter
- 15 file × 50KB = 750KB ≈ 187K tokens
- Biaya estimasi: ~$0.02

## Troubleshooting

### Rate Limiting
Jika terkena rate limit:
- Script akan retry otomatis dengan exponential backoff
- Tunggu beberapa menit lalu jalankan kembali
- Pertimbangkan mengurangi batch size

### Connection Timeout
- Periksa koneksi internet
- Verifikasi kredensial AWS
- Cek region availability

### Memory Issues
- Proses file satu per satu (sudah diimplementasi)
- Monitor penggunaan memory
- Restart script jika perlu (progress tersimpan)

## Best Practices

1. Jalankan di environment yang stabil
2. Monitor log secara berkala
3. Backup vector database setelah selesai
4. Verifikasi hasil dengan query test

## Verifikasi Hasil

```python
from src.embeddings.bedrock_client import BedrockEmbeddingsClient
from src.embeddings.chroma_manager import ChromaDBManager

# Initialize
bedrock = BedrockEmbeddingsClient()
chroma = ChromaDBManager()
chroma.get_collection("educational_content")

# Test query
query_text = "Apa itu algoritma?"
query_embedding = bedrock.generate_embedding(query_text)
results = chroma.query(query_embedding, n_results=3)

for i, result in enumerate(results, 1):
    print(f"\n{i}. Score: {result.similarity_score:.4f}")
    print(f"   Text: {result.text[:100]}...")
    print(f"   Source: {result.metadata['source_file']}")
```
