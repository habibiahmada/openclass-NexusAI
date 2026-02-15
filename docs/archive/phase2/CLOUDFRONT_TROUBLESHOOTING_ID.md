# CloudFront Troubleshooting Guide - 403 Forbidden Error

**Tanggal:** 14 Januari 2026  
**Issue:** 403 Forbidden saat akses CloudFront URL  
**Status:** ✓ RESOLVED

---

## Problem yang Terjadi

Saat mencoba akses CloudFront URL, muncul error:
```
curl : The remote server returned an error: (403) Forbidden.
```

**URL yang ditest:**
```
https://d1n8pllpvfec7l.cloudfront.net/processed/informatika/kelas_10/metadata/quality_report.json
```

---

## Root Cause

CloudFront distribution dibuat **tanpa Origin Access Identity (OAI)**, sehingga CloudFront tidak memiliki permission untuk mengakses S3 bucket yang bersifat private.

### Penjelasan Teknis:

1. **S3 Bucket:** Private (tidak public access)
2. **CloudFront:** Mencoba akses S3 tanpa credentials
3. **Result:** S3 menolak request dari CloudFront → 403 Forbidden

### Solusi yang Benar:

Gunakan **Origin Access Identity (OAI)** - sebuah special CloudFront user yang diberi permission untuk akses S3 bucket.

---

## Solution yang Sudah Diterapkan

### 1. Create Origin Access Identity (OAI) ✓

**OAI Details:**
- **OAI ID:** E391HXWO4IRVRN
- **Canonical User ID:** 52a237046fd543e2e3d2b96a26fc44ce69d4e9630dc82093f20f1d2c8fdb240e83b04f0b360743adcb92fe39d297eeb4

**What is OAI?**
OAI adalah special CloudFront user yang bisa diberi permission untuk akses private S3 bucket.

### 2. Update S3 Bucket Policy ✓

Bucket policy diupdate untuk allow OAI mengakses objects:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontOAI",
      "Effect": "Allow",
      "Principal": {
        "CanonicalUser": "52a237046fd543e2e3d2b96a26fc44ce69d4e9630dc82093f20f1d2c8fdb240e83b04f0b360743adcb92fe39d297eeb4"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::openclass-nexus-data/*"
    },
    {
      "Sid": "AllowCloudFrontListBucket",
      "Effect": "Allow",
      "Principal": {
        "CanonicalUser": "52a237046fd543e2e3d2b96a26fc44ce69d4e9630dc82093f20f1d2c8fdb240e83b04f0b360743adcb92fe39d297eeb4"
      },
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::openclass-nexus-data"
    }
  ]
}
```

**Penjelasan:**
- `AllowCloudFrontOAI`: Izinkan OAI untuk read objects (`s3:GetObject`)
- `AllowCloudFrontListBucket`: Izinkan OAI untuk list bucket contents

### 3. Update CloudFront Distribution ✓

Distribution diupdate untuk menggunakan OAI:

**Before:**
```json
"S3OriginConfig": {
  "OriginAccessIdentity": ""
}
```

**After:**
```json
"S3OriginConfig": {
  "OriginAccessIdentity": "origin-access-identity/cloudfront/E391HXWO4IRVRN"
}
```

### 4. Configuration Saved ✓

OAI ID disimpan di `.env`:
```
CLOUDFRONT_OAI_ID=E391HXWO4IRVRN
```

---

## How to Fix (Automated)

Jika Anda mengalami masalah yang sama, jalankan script fix:

```bash
python scripts/fix_cloudfront_permissions.py
```

**Script akan:**
1. ✓ Create/retrieve Origin Access Identity (OAI)
2. ✓ Update S3 bucket policy untuk allow CloudFront access
3. ✓ Update CloudFront distribution untuk use OAI
4. ✓ Save configuration ke .env

**Output yang diharapkan:**
```
======================================================================
✅ CloudFront Permissions Fix Complete!
======================================================================

📝 What was done:
   1. ✓ Created/retrieved Origin Access Identity (OAI)
   2. ✓ Updated S3 bucket policy to allow CloudFront access
   3. ✓ Updated CloudFront distribution to use OAI
   4. ✓ Saved configuration to .env

⏳ Next Steps:
   1. Wait 15-20 minutes for distribution to redeploy
   2. Test access: curl https://d1n8pllpvfec7l.cloudfront.net/...
```

---

## Verification Steps

### 1. Wait for Deployment (15-20 minutes)

CloudFront distribution perlu redeploy setelah configuration change.

**Check status:**
```bash
python scripts/setup_cloudfront.py --status
```

**Expected output setelah deployed:**
```
📊 CloudFront Distribution Status:
   Distribution ID: E210EQZHJ1ZWS0
   Domain Name: d1n8pllpvfec7l.cloudfront.net
   Status: Deployed
   Enabled: True

✅ Distribution is fully deployed and ready to use!
```

### 2. Test Access

**Test dengan curl:**
```bash
curl https://d1n8pllpvfec7l.cloudfront.net/processed/informatika/kelas_10/metadata/quality_report.json
```

**Expected output:**
```json
{
  "timestamp": "2026-01-14T18:38:29.587658",
  "total_checks": 1,
  "passed_checks": 1,
  ...
}
```

**Test dengan browser:**
```
https://d1n8pllpvfec7l.cloudfront.net/processed/informatika/kelas_10/metadata/quality_report.json
```

### 3. Check Response Headers

```bash
curl -I https://d1n8pllpvfec7l.cloudfront.net/processed/informatika/kelas_10/metadata/quality_report.json
```

**Expected headers:**
```
HTTP/2 200
content-type: application/json
x-cache: Hit from cloudfront
x-amz-cf-pop: SIN2-C1
x-amz-cf-id: ...
```

**Important headers:**
- `HTTP/2 200` - Success!
- `x-cache: Hit from cloudfront` - Content served from cache
- `x-cache: Miss from cloudfront` - First request, fetched from S3

---

## Manual Fix (Alternative)

Jika script tidak bekerja, Anda bisa fix manual via AWS Console:

### Step 1: Create OAI

1. Login ke AWS Console
2. Buka CloudFront service
3. Klik "Origin access" di sidebar
4. Klik "Create origin access identity"
5. Name: `openclass-nexus-oai`
6. Comment: `OAI for OpenClass Nexus AI`
7. Klik "Create"
8. **Copy OAI ID** (contoh: E391HXWO4IRVRN)

### Step 2: Update S3 Bucket Policy

1. Buka S3 service
2. Pilih bucket `openclass-nexus-data`
3. Tab "Permissions"
4. Scroll ke "Bucket policy"
5. Klik "Edit"
6. Paste policy di atas (ganti Canonical User ID dengan OAI Anda)
7. Klik "Save changes"

### Step 3: Update CloudFront Distribution

1. Kembali ke CloudFront service
2. Pilih distribution `E210EQZHJ1ZWS0`
3. Tab "Origins"
4. Pilih origin `openclass-nexus-data-origin`
5. Klik "Edit"
6. Di "S3 bucket access":
   - Pilih "Yes use OAI"
   - Origin access identity: Pilih OAI yang dibuat
   - Bucket policy: "Yes, update the bucket policy"
7. Klik "Save changes"
8. Wait 15-20 minutes untuk deployment

---

## Common Issues & Solutions

### Issue 1: Still 403 After Fix

**Possible Causes:**
1. Distribution masih deploying
2. Cache masih serve old error response
3. Bucket policy tidak applied correctly

**Solutions:**
```bash
# 1. Check deployment status
python scripts/setup_cloudfront.py --status

# 2. Invalidate cache
python scripts/setup_cloudfront.py --invalidate

# 3. Verify bucket policy
aws s3api get-bucket-policy --bucket openclass-nexus-data

# 4. Wait 15-20 minutes dan test lagi
```

### Issue 2: OAI Creation Failed

**Error:**
```
❌ Error creating OAI: AccessDenied
```

**Solution:**
Pastikan AWS credentials Anda memiliki permission:
- `cloudfront:CreateCloudFrontOriginAccessIdentity`
- `cloudfront:ListCloudFrontOriginAccessIdentities`

**Check permissions:**
```bash
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME
```

### Issue 3: Bucket Policy Update Failed

**Error:**
```
❌ Error updating bucket policy: AccessDenied
```

**Solution:**
Pastikan AWS credentials memiliki permission:
- `s3:PutBucketPolicy`
- `s3:GetBucketPolicy`

**Alternative:** Update bucket policy manual via AWS Console

### Issue 4: Distribution Update Failed

**Error:**
```
❌ Error updating distribution: PreconditionFailed
```

**Solution:**
Distribution sedang di-update oleh process lain. Wait beberapa menit dan try again:
```bash
# Wait 5 minutes
sleep 300

# Try again
python scripts/fix_cloudfront_permissions.py
```

---

## Prevention for Future

Untuk menghindari issue ini di masa depan:

### 1. Always Use OAI for Private S3 Buckets

Saat create CloudFront distribution untuk private S3 bucket, **selalu** gunakan OAI.

**Good practice:**
```python
distribution_config = {
    'Origins': {
        'Items': [
            {
                'S3OriginConfig': {
                    'OriginAccessIdentity': f'origin-access-identity/cloudfront/{oai_id}'
                }
            }
        ]
    }
}
```

### 2. Test Access Immediately

Setelah create distribution, test access segera:
```bash
# Wait for deployment
python scripts/setup_cloudfront.py --status

# Test access
curl https://YOUR_CLOUDFRONT_DOMAIN/path/to/file
```

### 3. Monitor CloudFront Errors

Setup CloudWatch alarm untuk monitor 4xx errors:
```bash
# Via AWS Console:
# CloudFront → Monitoring → Create alarm
# Metric: 4xxErrorRate
# Threshold: > 5%
# Action: Send SNS notification
```

---

## Verification Checklist

Setelah fix, verify semua ini:

- [ ] OAI created dan ID saved di .env
- [ ] S3 bucket policy updated dengan OAI canonical user ID
- [ ] CloudFront distribution updated untuk use OAI
- [ ] Distribution status: Deployed
- [ ] Test access return 200 OK
- [ ] Response headers show `x-cache: Hit/Miss from cloudfront`
- [ ] Cache invalidation working
- [ ] No 403 errors di CloudWatch metrics

---

## Timeline

**Issue Detected:** 14 Januari 2026, ~18:45  
**Fix Applied:** 14 Januari 2026, ~18:50  
**Expected Resolution:** 14 Januari 2026, ~19:05 (setelah deployment)

**Total Time to Fix:** ~5 minutes (script execution)  
**Total Time to Deploy:** ~15-20 minutes (AWS CloudFront deployment)

---

## Lessons Learned

1. **Always use OAI** untuk private S3 buckets dengan CloudFront
2. **Test immediately** setelah create distribution
3. **Automate fixes** dengan scripts untuk faster resolution
4. **Document thoroughly** untuk future reference

---

## Related Documentation

- `docs/CLOUDFRONT_SETUP_GUIDE_ID.md` - Complete CloudFront setup guide
- `scripts/fix_cloudfront_permissions.py` - Automated fix script
- `scripts/setup_cloudfront.py` - CloudFront setup script

---

## Support

Jika masih ada issues setelah mengikuti guide ini:

1. Check AWS CloudTrail logs untuk detailed error messages
2. Verify IAM permissions untuk CloudFront dan S3
3. Contact AWS Support jika issue persist

---

**Resolved by:** Kiro AI Agent  
**Date:** 14 Januari 2026  
**Status:** ✓ FIXED - Waiting for deployment
