# AWS Console Monitoring Guide

Panduan lengkap untuk monitoring proses embedding di AWS Console.

## 🎯 Quick Links

### Region: ap-southeast-2 (Sydney)

| Service | URL |
|---------|-----|
| **Bedrock Dashboard** | https://ap-southeast-2.console.aws.amazon.com/bedrock/home |
| **CloudWatch Metrics** | https://ap-southeast-2.console.aws.amazon.com/cloudwatch/home#metricsV2 |
| **CloudWatch Logs** | https://ap-southeast-2.console.aws.amazon.com/cloudwatch/home#logsV2:log-groups |
| **Cost Explorer** | https://us-east-1.console.aws.amazon.com/cost-management/home#/cost-explorer |

## 📊 1. AWS Bedrock Dashboard

### Cara Akses
1. Login ke AWS Console
2. Pilih region: **ap-southeast-2** (Sydney)
3. Search "Bedrock" di search bar
4. Klik "Amazon Bedrock"

### Yang Bisa Dilihat
- **Model invocations**: Total API calls
- **Success rate**: Persentase request berhasil
- **Latency**: Response time rata-rata
- **Error rate**: Persentase error

### Screenshot Lokasi
```
AWS Console → Services → Bedrock → Model invocations (sidebar kiri)
```

### Metrics Penting
- **Invocations**: Harus naik saat script berjalan
- **Latency**: Normal ~200-500ms
- **Errors**: Harus 0% atau sangat rendah

## 📈 2. CloudWatch Metrics

### Cara Akses
1. AWS Console → CloudWatch
2. Sidebar kiri → Metrics → All metrics
3. Pilih namespace: **AWS/Bedrock**
4. Pilih dimension: **ModelId**
5. Pilih model: **amazon.titan-embed-text-v2:0**

### Metrics Available

#### Invocations
- **Deskripsi**: Total API calls ke model
- **Satuan**: Count
- **Normal**: Naik bertahap saat script berjalan
- **Alert**: Jika stuck/tidak naik

#### InvocationLatency
- **Deskripsi**: Response time per request
- **Satuan**: Milliseconds
- **Normal**: 200-500ms
- **Alert**: >2000ms (2 detik)

#### InvocationClientErrors
- **Deskripsi**: Client errors (4xx)
- **Satuan**: Count
- **Normal**: 0
- **Alert**: >0 (ada masalah di request)

#### InvocationServerErrors
- **Deskripsi**: Server errors (5xx)
- **Satuan**: Count
- **Normal**: 0
- **Alert**: >0 (masalah di AWS)

#### InputTokens
- **Deskripsi**: Total tokens diproses
- **Satuan**: Count
- **Normal**: Naik sesuai jumlah text
- **Alert**: Tidak naik saat script berjalan

### Cara Membuat Graph
1. Pilih metric yang ingin dilihat
2. Klik "Graphed metrics" tab
3. Atur period: 1 minute atau 5 minutes
4. Atur statistic: Sum, Average, atau Maximum
5. Klik "Add to dashboard" untuk save

### Custom Dashboard
Buat dashboard dengan metrics:
- Invocations (Sum, 1 min)
- InvocationLatency (Average, 1 min)
- InvocationClientErrors (Sum, 1 min)
- InputTokens (Sum, 5 min)

## 📝 3. CloudWatch Logs

### Cara Akses
1. AWS Console → CloudWatch
2. Sidebar kiri → Logs → Log groups
3. Cari: **/aws/bedrock/modelinvocations**
4. Klik log group
5. Pilih log stream terbaru

### Log Structure
```json
{
  "timestamp": "2026-02-19T12:34:56Z",
  "requestId": "abc-123-def",
  "modelId": "amazon.titan-embed-text-v2:0",
  "operation": "InvokeModel",
  "inputTokens": 200,
  "outputTokens": 0,
  "latency": 345,
  "status": "success"
}
```

### Filter Patterns

#### Semua Errors
```
[timestamp, requestId, modelId, operation, status=error]
```

#### High Latency (>1000ms)
```
[timestamp, requestId, modelId, operation, inputTokens, outputTokens, latency>1000]
```

#### Specific Model
```
[timestamp, requestId, modelId=amazon.titan-embed-text-v2:0, ...]
```

### Cara Filter
1. Klik "Search log group"
2. Masukkan filter pattern
3. Pilih time range
4. Klik "Search"

### Export Logs
1. Pilih log stream
2. Actions → Export data to S3
3. Pilih S3 bucket
4. Klik "Export"

## 💰 4. Cost Explorer

### Cara Akses
1. AWS Console → Billing
2. Sidebar kiri → Cost Explorer
3. Klik "Launch Cost Explorer"

### Filter untuk Bedrock
1. **Service**: Pilih "Bedrock"
2. **Region**: Pilih "Asia Pacific (Sydney)"
3. **Time range**: Today atau Last 7 days
4. **Granularity**: Daily atau Hourly

### Metrics yang Ditampilkan
- **Total cost**: Biaya total
- **Cost by service**: Breakdown per service
- **Cost by usage type**: Breakdown per tipe usage
- **Forecast**: Prediksi biaya

### Cost Breakdown
```
Bedrock
├── Titan Text Embeddings v2
│   ├── Input tokens: $X.XXXX
│   └── API calls: $X.XXXX
└── Total: $X.XXXX
```

### Set Budget Alert
1. Billing → Budgets
2. Create budget
3. Set amount: $1.00 (untuk testing)
4. Set alert: 80% threshold
5. Add email notification

## 🔔 5. CloudWatch Alarms

### Membuat Alarm untuk Errors

1. CloudWatch → Alarms → Create alarm
2. Select metric: AWS/Bedrock → InvocationClientErrors
3. Conditions:
   - Threshold type: Static
   - Whenever metric is: Greater than
   - Than: 5
4. Configure actions:
   - Send notification to: Your email
5. Name: "Bedrock-Client-Errors"
6. Create alarm

### Alarm untuk High Latency

1. Select metric: InvocationLatency
2. Conditions:
   - Statistic: Average
   - Greater than: 2000 (ms)
   - For: 2 consecutive periods
3. Configure notification
4. Name: "Bedrock-High-Latency"

### Alarm untuk Cost

1. Billing → Budgets → Create budget
2. Budget type: Cost budget
3. Set amount: $1.00
4. Alert threshold: 80%
5. Email notification

## 📱 6. Monitoring dari Terminal

### Script Monitoring
```bash
python scripts/monitor_bedrock.py
```

Output:
```
🔍 AWS Bedrock Monitoring Dashboard
Region: ap-southeast-2
Model: amazon.titan-embed-text-v2:0

======================================================================
AWS Bedrock Metrics (Last 1 Hour)
======================================================================

Invocations:
  Total: 150

InvocationLatency:
  Average: 345.67 ms
  Maximum: 890.00 ms

InvocationClientErrors:
  Total: 0

InvocationServerErrors:
  Total: 0

======================================================================
Recent Bedrock Logs (Last 10 entries)
======================================================================

[2026-02-19 12:34:56]
{"requestId": "abc-123", "status": "success", "latency": 345}

======================================================================
Cost Estimate (Last 24 Hours)
======================================================================

Total Invocations: 500
Estimated Tokens: 100,000
Estimated Cost: $0.0100

======================================================================
✓ Monitoring complete
======================================================================
```

## 🎯 Monitoring Checklist

Saat menjalankan embedding, monitor:

- [ ] **Invocations** naik bertahap
- [ ] **Latency** stabil <1000ms
- [ ] **Errors** = 0
- [ ] **Cost** sesuai estimasi
- [ ] **Logs** tidak ada error messages
- [ ] **Progress file** update setiap file selesai

## 🚨 Troubleshooting

### Invocations Tidak Naik
- Cek script masih berjalan
- Cek koneksi internet
- Cek kredensial AWS

### High Latency
- Normal jika >500ms sesekali
- Alert jika konsisten >2000ms
- Cek region (harus ap-southeast-2)

### Client Errors (4xx)
- 400: Bad request (cek input)
- 403: Permission denied (cek IAM)
- 429: Rate limit (script akan retry)

### Server Errors (5xx)
- 500: Internal server error
- 503: Service unavailable
- Tunggu dan retry

### Cost Lebih Tinggi
- Cek jumlah invocations
- Cek input token size
- Verifikasi model ID

## 📚 Resources

### AWS Documentation
- [Bedrock Metrics](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-cloudwatch.html)
- [CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html)
- [Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html)

### Internal Documentation
- [Cloud Embedding Guide](CLOUD_EMBEDDING_GUIDE.md)
- [Quick Reference](../QUICK_REFERENCE.md)
- [Embedding Checklist](../EMBEDDING_CHECKLIST.md)

## 💡 Tips

1. **Bookmark URLs** untuk akses cepat
2. **Set up alarms** sebelum run embedding
3. **Monitor cost** secara real-time
4. **Export logs** untuk analisis
5. **Create dashboard** untuk overview

---

**Happy Monitoring!** 📊
