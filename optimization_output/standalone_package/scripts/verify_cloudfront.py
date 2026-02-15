#!/usr/bin/env python3
"""Verify CloudFront distribution for final checkpoint."""

import boto3
from botocore.exceptions import ClientError

def verify_cloudfront():
    """Verify CloudFront distribution exists and is configured correctly."""
    try:
        cloudfront = boto3.client('cloudfront')
        s3 = boto3.client('s3')
        
        print("=" * 60)
        print("CloudFront Distribution Verification")
        print("=" * 60)
        
        # Get bucket location
        bucket = 'openclass-nexus-data'
        try:
            location = s3.get_bucket_location(Bucket=bucket)
            region = location['LocationConstraint'] or 'us-east-1'
            print(f"S3 Bucket: {bucket}")
            print(f"Region: {region}")
        except ClientError as e:
            print(f"✗ Could not get bucket location: {e}")
            return False
        
        # List distributions
        try:
            response = cloudfront.list_distributions()
            
            if 'DistributionList' not in response or 'Items' not in response['DistributionList']:
                print("\n✗ No CloudFront distributions found")
                print("Note: CloudFront distribution may need to be created manually")
                return False
            
            distributions = response['DistributionList']['Items']
            print(f"\nTotal distributions: {len(distributions)}")
            
            # Find distribution for our bucket
            matching_dist = None
            for dist in distributions:
                origins = dist.get('Origins', {}).get('Items', [])
                for origin in origins:
                    domain = origin.get('DomainName', '')
                    if bucket in domain:
                        matching_dist = dist
                        break
                if matching_dist:
                    break
            
            if matching_dist:
                print(f"\n✓ Found distribution for bucket: {bucket}")
                print(f"  Distribution ID: {matching_dist['Id']}")
                print(f"  Domain: {matching_dist['DomainName']}")
                print(f"  Status: {matching_dist['Status']}")
                print(f"  Enabled: {matching_dist['Enabled']}")
                
                # Check cache behavior
                default_cache = matching_dist.get('DefaultCacheBehavior', {})
                viewer_protocol = default_cache.get('ViewerProtocolPolicy', 'N/A')
                print(f"  HTTPS: {viewer_protocol}")
                
                # Check if compression is enabled
                compress = default_cache.get('Compress', False)
                print(f"  Compression: {'Enabled' if compress else 'Disabled'}")
                
                print("\n✓ CloudFront distribution verified successfully!")
                return True
            else:
                print(f"\n⚠ No distribution found for bucket: {bucket}")
                print("Note: CloudFront distribution may need to be created")
                print("Run: python scripts/setup_cloudfront.py")
                return False
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDenied':
                print("\n⚠ Access denied to CloudFront")
                print("Note: CloudFront permissions may not be configured")
                return False
            else:
                print(f"\n✗ CloudFront error: {e}")
                return False
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == '__main__':
    verify_cloudfront()
