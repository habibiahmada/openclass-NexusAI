# Phase 2 AWS Infrastructure Setup Guide

## Overview

Scripts untuk setup infrastruktur AWS yang diperlukan untuk Phase 2: Backend Infrastructure & Knowledge Engineering.

## Scripts Available

### 1. `setup_phase2_aws.py` - Master Setup Script ⭐
**Recommended**: Jalankan script ini untuk setup semua komponen sekaligus.

```bash
python scripts/setup_phase2_aws.py
```

**What it does:**
- ✅ Configures S3 lifecycle policies (auto-move to cheaper storage)
- ✅ Enables S3 encryption (AES-256)
- ✅ Enables S3 versioning (data protection)
- ✅ Creates CloudFront distribution (fast content delivery)
- ✅ Configures Intelligent-Tiering (optional)

**Time:** 5-10 minutes + 15-20 minutes for CloudFront deployment
**Cost:** ~$0.01-0.05/month (well within $1.00 budget)

---

### 2. `setup_cloudfront.py` - CloudFront Distribution

Setup CloudFront CDN untuk distribusi knowledge base.

```bash
# Create CloudFront distribution
python scripts/setup_cloudfront.py

# Check deployment status
python scripts/setup_cloudfront.py --status

# Invalidate cache (force refresh)
python scripts/setup_cloudfront.py --invalidate

# Invalidate specific paths
python scripts/setup_cloudfront.py --invalidate /processed/* /vector_db/*
```

**Features:**
- 🌐 Global CDN for fast content delivery
- 🔒 HTTPS-only (automatic redirect)
- 📦 Gzip compression enabled
- ⏱️ 24-hour cache TTL
- 💰 Uses cheapest price class (North America + Europe)

**Configuration saved to:** `.env` file
- `CLOUDFRONT_DISTRIBUTION_ID`
- `CLOUDFRONT_DISTRIBUTION_URL`

---

### 3. `optimize_s3_storage.py` - S3 Storage Optimization

Optimize S3 bucket untuk cost efficiency.

```bash
# Apply all optimizations
python scripts/optimize_s3_storage.py

# Check current status
python scripts/optimize_s3_storage.py --status
```

**Optimizations Applied:**

1. **Lifecycle Policies:**
   - Raw PDFs → Glacier after 30 days (90% cheaper)
   - Processed data → Standard-IA after 7 days (50% cheaper)
   - Logs → Delete after 90 days

2. **Encryption:**
   - AES-256 server-side encryption
   - Automatic for all new objects

3. **Versioning:**
   - Enabled for data protection
   - Previous versions retained

4. **Intelligent-Tiering (optional):**
   - Auto-move to Archive after 90 days
   - Auto-move to Deep Archive after 180 days

**Expected Savings:** 60-80% on storage costs

---

## Step-by-Step Setup Guide

### Prerequisites

1. AWS credentials configured in `.env`:
   ```
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_DEFAULT_REGION=ap-southeast-2
   S3_BUCKET_NAME=openclass-nexus-data
   ```

2. S3 bucket already created (from Phase 1)

3. Python packages installed:
   ```bash
   pip install boto3 python-dotenv
   ```

### Quick Setup (Recommended)

```bash
# Run master setup script
python scripts/setup_phase2_aws.py
```

Follow the prompts and confirm when asked.

### Manual Setup (Individual Components)

If you prefer to setup components individually:

```bash
# 1. Optimize S3 storage
python scripts/optimize_s3_storage.py

# 2. Setup CloudFront
python scripts/setup_cloudfront.py

# 3. Check status
python scripts/setup_cloudfront.py --status
python scripts/optimize_s3_storage.py --status
```

---

## Verification

### 1. Check S3 Lifecycle Policies

```bash
aws s3api get-bucket-lifecycle-configuration --bucket openclass-nexus-data
```

Expected output: Rules for Glacier transition, IA transition, and log deletion.

### 2. Check S3 Encryption

```bash
aws s3api get-bucket-encryption --bucket openclass-nexus-data
```

Expected output: AES256 encryption enabled.

### 3. Check CloudFront Status

```bash
python scripts/setup_cloudfront.py --status
```

Expected output: Distribution status (InProgress or Deployed).

### 4. Test CloudFront Access

Once deployed (15-20 minutes), test access:

```bash
# Get CloudFront URL from .env
curl -I https://YOUR_CLOUDFRONT_DOMAIN.cloudfront.net/
```

Expected: HTTP 200 or 403 (403 is OK if no public files yet).

---

## Cost Breakdown

### Monthly Costs (Estimated)

| Service | Usage | Cost |
|---------|-------|------|
| **S3 Standard** | 0.1 GB | $0.002 |
| **S3 Standard-IA** | 0.05 GB | $0.001 |
| **S3 Glacier** | 0.1 GB | $0.0004 |
| **CloudFront** | 1 GB transfer | $0.085 |
| **CloudFront Requests** | 10K requests | $0.01 |
| **Total** | | **~$0.10/month** |

**Budget:** $1.00/month
**Remaining:** $0.90/month for Phase 2 operations

### Cost Optimization Tips

1. **Use CloudFront for downloads** - Cheaper than S3 direct access
2. **Let lifecycle policies work** - Automatic cost reduction over time
3. **Monitor with CloudWatch** - Track actual usage
4. **Use batch operations** - Reduce API call costs

---

## Troubleshooting

### CloudFront Distribution Creation Fails

**Error:** `DistributionAlreadyExists`
**Solution:** Distribution already exists. Check status:
```bash
python scripts/setup_cloudfront.py --status
```

### S3 Lifecycle Policy Fails

**Error:** `AccessDenied`
**Solution:** Check IAM permissions. User needs:
- `s3:PutLifecycleConfiguration`
- `s3:GetLifecycleConfiguration`

### CloudFront Takes Too Long

**Normal:** CloudFront deployment takes 15-20 minutes.
**Check status:**
```bash
python scripts/setup_cloudfront.py --status
```

### Encryption Already Enabled

**Message:** Encryption already configured
**Action:** No action needed. This is good!

---

## Next Steps After Setup

1. **Wait for CloudFront deployment** (15-20 minutes)
   ```bash
   python scripts/setup_cloudfront.py --status
   ```

2. **Verify all configurations**
   ```bash
   python scripts/optimize_s3_storage.py --status
   ```

3. **Update application config**
   - CloudFront URL is saved in `.env`
   - Use CloudFront URL for knowledge base downloads

4. **Start Phase 2 implementation**
   - PDF extraction
   - Text chunking
   - Vector embeddings
   - ChromaDB creation

---

## Maintenance

### Invalidate CloudFront Cache

When you update knowledge base files:

```bash
# Invalidate all
python scripts/setup_cloudfront.py --invalidate

# Invalidate specific paths
python scripts/setup_cloudfront.py --invalidate /processed/* /vector_db/*
```

**Note:** First 1,000 invalidations/month are free.

### Monitor Costs

```bash
# Check bucket size and cost
python scripts/optimize_s3_storage.py --status

# Check AWS billing
aws ce get-cost-and-usage \
  --time-period Start=2026-01-01,End=2026-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

### Update Lifecycle Policies

Edit `scripts/optimize_s3_storage.py` and re-run:

```python
# Example: Change Glacier transition to 60 days
'Transitions': [
    {
        'Days': 60,  # Changed from 30
        'StorageClass': 'GLACIER'
    }
]
```

---

## FAQ

**Q: Do I need to run these scripts every time?**
A: No, only once. Configurations persist in AWS.

**Q: Can I delete CloudFront distribution later?**
A: Yes, but you'll lose CDN benefits. Not recommended.

**Q: What if I exceed $1.00 budget?**
A: Budget alerts will notify you. You can disable CloudFront temporarily.

**Q: How do I rollback changes?**
A: Use AWS Console or CLI to remove lifecycle policies and disable CloudFront.

**Q: Is CloudFront necessary?**
A: Not required, but highly recommended for:
- Faster downloads for schools
- Lower S3 data transfer costs
- Better user experience

---

## Support

If you encounter issues:

1. Check AWS credentials: `aws sts get-caller-identity`
2. Check IAM permissions
3. Review error messages in script output
4. Check AWS Console for service status

For Phase 2 implementation questions, refer to:
- `.kiro/specs/phase2-backend-knowledge-engineering/requirements.md`
- `.kiro/specs/phase2-backend-knowledge-engineering/design.md`
- `.kiro/specs/phase2-backend-knowledge-engineering/tasks.md`

---

**Last Updated:** 2026-01-14
**Phase:** 2 - Backend Infrastructure & Knowledge Engineering
**Status:** Ready for Setup
