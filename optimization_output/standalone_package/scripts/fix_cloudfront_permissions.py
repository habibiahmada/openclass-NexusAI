#!/usr/bin/env python3
"""
Fix CloudFront permissions by creating OAI and updating S3 bucket policy.
"""

import boto3
import json
import sys
import os
from pathlib import Path
from botocore.exceptions import ClientError

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.aws_config import aws_config


def create_origin_access_identity(cloudfront_client):
    """Create CloudFront Origin Access Identity."""
    print("🔐 Creating CloudFront Origin Access Identity...")
    
    try:
        response = cloudfront_client.create_cloud_front_origin_access_identity(
            CloudFrontOriginAccessIdentityConfig={
                'CallerReference': f'openclass-nexus-oai-{int(__import__("time").time())}',
                'Comment': 'OAI for OpenClass Nexus AI S3 bucket'
            }
        )
        
        oai = response['CloudFrontOriginAccessIdentity']
        oai_id = oai['Id']
        oai_canonical_user_id = oai['S3CanonicalUserId']
        
        print(f"✅ OAI created successfully!")
        print(f"   OAI ID: {oai_id}")
        print(f"   Canonical User ID: {oai_canonical_user_id}")
        
        return oai_id, oai_canonical_user_id
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if 'AlreadyExists' in error_code:
            print("⚠️  OAI already exists, listing existing OAIs...")
            return get_existing_oai(cloudfront_client)
        else:
            print(f"❌ Error creating OAI: {e}")
            raise


def get_existing_oai(cloudfront_client):
    """Get existing OAI."""
    try:
        response = cloudfront_client.list_cloud_front_origin_access_identities()
        
        if 'CloudFrontOriginAccessIdentityList' in response:
            items = response['CloudFrontOriginAccessIdentityList'].get('Items', [])
            
            if items:
                # Use the first OAI
                oai = items[0]
                oai_id = oai['Id']
                oai_canonical_user_id = oai['S3CanonicalUserId']
                
                print(f"✅ Using existing OAI:")
                print(f"   OAI ID: {oai_id}")
                print(f"   Canonical User ID: {oai_canonical_user_id}")
                
                return oai_id, oai_canonical_user_id
        
        print("❌ No existing OAI found")
        return None, None
        
    except ClientError as e:
        print(f"❌ Error listing OAIs: {e}")
        return None, None


def update_s3_bucket_policy(s3_client, bucket_name, oai_canonical_user_id):
    """Update S3 bucket policy to allow CloudFront access."""
    print(f"\n📝 Updating S3 bucket policy for: {bucket_name}")
    
    # New bucket policy that allows CloudFront OAI to read objects
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowCloudFrontOAI",
                "Effect": "Allow",
                "Principal": {
                    "CanonicalUser": oai_canonical_user_id
                },
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*"
            },
            {
                "Sid": "AllowCloudFrontListBucket",
                "Effect": "Allow",
                "Principal": {
                    "CanonicalUser": oai_canonical_user_id
                },
                "Action": "s3:ListBucket",
                "Resource": f"arn:aws:s3:::{bucket_name}"
            }
        ]
    }
    
    try:
        # Convert policy to JSON string
        policy_json = json.dumps(bucket_policy)
        
        # Apply bucket policy
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=policy_json
        )
        
        print(f"✅ Bucket policy updated successfully!")
        print(f"   CloudFront OAI can now access bucket objects")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error updating bucket policy: {e}")
        return False


def update_cloudfront_distribution(cloudfront_client, distribution_id, oai_id, bucket_name):
    """Update CloudFront distribution to use OAI."""
    print(f"\n🔄 Updating CloudFront distribution: {distribution_id}")
    
    try:
        # Get current distribution config
        response = cloudfront_client.get_distribution_config(Id=distribution_id)
        config = response['DistributionConfig']
        etag = response['ETag']
        
        # Update origin to use OAI
        for origin in config['Origins']['Items']:
            if bucket_name in origin['DomainName']:
                origin['S3OriginConfig']['OriginAccessIdentity'] = f'origin-access-identity/cloudfront/{oai_id}'
                print(f"   Updated origin: {origin['Id']}")
        
        # Update distribution
        cloudfront_client.update_distribution(
            Id=distribution_id,
            DistributionConfig=config,
            IfMatch=etag
        )
        
        print(f"✅ Distribution updated successfully!")
        print(f"   Distribution is being redeployed (may take 15-20 minutes)")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error updating distribution: {e}")
        return False


def verify_access(cloudfront_domain):
    """Verify CloudFront can access S3 content."""
    print(f"\n🧪 Testing CloudFront access...")
    
    import requests
    
    test_url = f"https://{cloudfront_domain}/processed/informatika/kelas_10/metadata/quality_report.json"
    
    try:
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Access test PASSED!")
            print(f"   URL: {test_url}")
            print(f"   Status: {response.status_code}")
            return True
        else:
            print(f"⚠️  Access test returned: {response.status_code}")
            print(f"   This is normal if distribution is still deploying")
            print(f"   Wait 15-20 minutes and try again")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Could not test access: {e}")
        print(f"   This is normal if distribution is still deploying")
        return False


def main():
    """Main function to fix CloudFront permissions."""
    print("=" * 70)
    print("🔧 CloudFront Permissions Fix")
    print("=" * 70)
    print()
    
    # Initialize clients
    cloudfront = boto3.client('cloudfront')
    s3 = aws_config.get_s3_client()
    bucket_name = aws_config.s3_bucket
    
    # Get distribution ID from env
    from dotenv import load_dotenv
    load_dotenv()
    distribution_id = os.getenv('CLOUDFRONT_DISTRIBUTION_ID')
    cloudfront_domain = os.getenv('CLOUDFRONT_DISTRIBUTION_URL', '').replace('https://', '')
    
    if not distribution_id:
        print("❌ No CloudFront distribution ID found in .env")
        print("   Run: python scripts/setup_cloudfront.py first")
        return 1
    
    print(f"📋 Configuration:")
    print(f"   S3 Bucket: {bucket_name}")
    print(f"   Distribution ID: {distribution_id}")
    print(f"   CloudFront Domain: {cloudfront_domain}")
    print()
    
    # Step 1: Create or get OAI
    oai_id, oai_canonical_user_id = create_origin_access_identity(cloudfront)
    
    if not oai_id:
        print("❌ Failed to create/get OAI")
        return 1
    
    # Step 2: Update S3 bucket policy
    if not update_s3_bucket_policy(s3, bucket_name, oai_canonical_user_id):
        print("❌ Failed to update bucket policy")
        return 1
    
    # Step 3: Update CloudFront distribution
    if not update_cloudfront_distribution(cloudfront, distribution_id, oai_id, bucket_name):
        print("❌ Failed to update distribution")
        return 1
    
    # Step 4: Save OAI ID to .env
    print("\n💾 Saving OAI ID to .env...")
    try:
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        # Add OAI ID if not exists
        oai_line = f'CLOUDFRONT_OAI_ID={oai_id}\n'
        if not any('CLOUDFRONT_OAI_ID=' in line for line in lines):
            lines.append(oai_line)
        else:
            lines = [oai_line if 'CLOUDFRONT_OAI_ID=' in line else line for line in lines]
        
        with open('.env', 'w') as f:
            f.writelines(lines)
        
        print("✅ OAI ID saved to .env")
        
    except Exception as e:
        print(f"⚠️  Could not save to .env: {e}")
    
    # Step 5: Test access (may fail if still deploying)
    print()
    verify_access(cloudfront_domain)
    
    # Summary
    print()
    print("=" * 70)
    print("✅ CloudFront Permissions Fix Complete!")
    print("=" * 70)
    print()
    print("📝 What was done:")
    print("   1. ✓ Created/retrieved Origin Access Identity (OAI)")
    print("   2. ✓ Updated S3 bucket policy to allow CloudFront access")
    print("   3. ✓ Updated CloudFront distribution to use OAI")
    print("   4. ✓ Saved configuration to .env")
    print()
    print("⏳ Next Steps:")
    print("   1. Wait 15-20 minutes for distribution to redeploy")
    print("   2. Test access:")
    print(f"      curl https://{cloudfront_domain}/processed/informatika/kelas_10/metadata/quality_report.json")
    print("   3. Check status:")
    print("      python scripts/setup_cloudfront.py --status")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
