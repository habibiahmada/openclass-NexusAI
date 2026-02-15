"""
CloudFront Distribution Setup Script
Creates CloudFront distribution for S3 bucket to enable fast content delivery
"""

import boto3
import json
import time
import sys
import os
from pathlib import Path
from botocore.exceptions import ClientError

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.aws_config import aws_config

class CloudFrontSetup:
    def __init__(self):
        self.cloudfront = boto3.client(
            'cloudfront',
            region_name=aws_config.region,
            aws_access_key_id=aws_config.access_key,
            aws_secret_access_key=aws_config.secret_key
        )
        self.s3 = aws_config.get_s3_client()
        self.bucket_name = aws_config.s3_bucket
        
    def create_distribution(self):
        """Create CloudFront distribution for S3 bucket."""
        print(f"🚀 Creating CloudFront distribution for bucket: {self.bucket_name}")
        
        # Get S3 bucket region
        bucket_location = self.s3.get_bucket_location(Bucket=self.bucket_name)
        region = bucket_location['LocationConstraint'] or 'ap-southeast-2'
        
        # S3 origin domain name
        if region == 'ap-southeast-2':
            origin_domain = f"{self.bucket_name}.s3.amazonaws.com"
        else:
            origin_domain = f"{self.bucket_name}.s3.{region}.amazonaws.com"
        
        # CloudFront distribution configuration
        distribution_config = {
            'CallerReference': f'openclass-nexus-{int(time.time())}',
            'Comment': 'OpenClass Nexus AI - Knowledge Base Distribution',
            'Enabled': True,
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': f'{self.bucket_name}-origin',
                        'DomainName': origin_domain,
                        'S3OriginConfig': {
                            'OriginAccessIdentity': ''
                        }
                    }
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': f'{self.bucket_name}-origin',
                'ViewerProtocolPolicy': 'redirect-to-https',  # Force HTTPS
                'AllowedMethods': {
                    'Quantity': 2,
                    'Items': ['GET', 'HEAD'],
                    'CachedMethods': {
                        'Quantity': 2,
                        'Items': ['GET', 'HEAD']
                    }
                },
                'Compress': True,  # Enable gzip compression
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'},
                    'Headers': {
                        'Quantity': 0
                    }
                },
                'MinTTL': 0,
                'DefaultTTL': 86400,  # 24 hours cache
                'MaxTTL': 31536000,
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                }
            },
            'PriceClass': 'PriceClass_100',  # Use only North America and Europe (cheapest)
            'ViewerCertificate': {
                'CloudFrontDefaultCertificate': True,
                'MinimumProtocolVersion': 'TLSv1.2_2021'
            }
        }
        
        try:
            # Create distribution
            response = self.cloudfront.create_distribution(
                DistributionConfig=distribution_config
            )
            
            distribution = response['Distribution']
            distribution_id = distribution['Id']
            domain_name = distribution['DomainName']
            
            print(f"✅ CloudFront distribution created successfully!")
            print(f"   Distribution ID: {distribution_id}")
            print(f"   Domain Name: {domain_name}")
            print(f"   Status: {distribution['Status']}")
            print(f"\n⏳ Distribution is being deployed (this may take 15-20 minutes)...")
            print(f"   You can check status with: aws cloudfront get-distribution --id {distribution_id}")
            
            # Save distribution info
            self._save_distribution_info(distribution_id, domain_name)
            
            return {
                'distribution_id': distribution_id,
                'domain_name': domain_name,
                'status': distribution['Status']
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'DistributionAlreadyExists':
                print("⚠️  CloudFront distribution already exists")
                return self._get_existing_distribution()
            else:
                print(f"❌ Error creating CloudFront distribution: {e}")
                raise
    
    def _get_existing_distribution(self):
        """Get existing CloudFront distribution for the bucket."""
        try:
            # List all distributions
            response = self.cloudfront.list_distributions()
            
            if 'DistributionList' in response and 'Items' in response['DistributionList']:
                for dist in response['DistributionList']['Items']:
                    # Check if this distribution is for our bucket
                    for origin in dist['Origins']['Items']:
                        if self.bucket_name in origin['DomainName']:
                            distribution_id = dist['Id']
                            domain_name = dist['DomainName']
                            
                            print(f"✅ Found existing CloudFront distribution:")
                            print(f"   Distribution ID: {distribution_id}")
                            print(f"   Domain Name: {domain_name}")
                            print(f"   Status: {dist['Status']}")
                            
                            self._save_distribution_info(distribution_id, domain_name)
                            
                            return {
                                'distribution_id': distribution_id,
                                'domain_name': domain_name,
                                'status': dist['Status']
                            }
            
            print("❌ No existing distribution found for this bucket")
            return None
            
        except ClientError as e:
            print(f"❌ Error listing distributions: {e}")
            return None
    
    def _save_distribution_info(self, distribution_id, domain_name):
        """Save distribution info to config file."""
        config_file = '.env'
        
        # Read existing .env
        try:
            with open(config_file, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []
        
        # Update or add CloudFront config
        updated = False
        new_lines = []
        
        for line in lines:
            if line.startswith('CLOUDFRONT_DISTRIBUTION_ID='):
                new_lines.append(f'CLOUDFRONT_DISTRIBUTION_ID={distribution_id}\n')
                updated = True
            elif line.startswith('CLOUDFRONT_DISTRIBUTION_URL='):
                new_lines.append(f'CLOUDFRONT_DISTRIBUTION_URL=https://{domain_name}\n')
            else:
                new_lines.append(line)
        
        # Add if not found
        if not updated:
            new_lines.append(f'\n# CloudFront Configuration\n')
            new_lines.append(f'CLOUDFRONT_DISTRIBUTION_ID={distribution_id}\n')
            new_lines.append(f'CLOUDFRONT_DISTRIBUTION_URL=https://{domain_name}\n')
        
        # Write back
        with open(config_file, 'w') as f:
            f.writelines(new_lines)
        
        print(f"\n💾 CloudFront configuration saved to {config_file}")
    
    def invalidate_cache(self, paths=['/*']):
        """Invalidate CloudFront cache for specified paths."""
        # Get distribution ID from config
        distribution_id = aws_config.cloudfront_distribution_id
        
        if not distribution_id:
            print("❌ No CloudFront distribution ID found in config")
            return False
        
        print(f"🔄 Invalidating CloudFront cache for paths: {paths}")
        
        try:
            response = self.cloudfront.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': f'invalidation-{int(time.time())}'
                }
            )
            
            invalidation_id = response['Invalidation']['Id']
            print(f"✅ Cache invalidation created: {invalidation_id}")
            print(f"   Status: {response['Invalidation']['Status']}")
            
            return True
            
        except ClientError as e:
            print(f"❌ Error invalidating cache: {e}")
            return False
    
    def get_distribution_status(self):
        """Check CloudFront distribution deployment status."""
        distribution_id = aws_config.cloudfront_distribution_id
        
        if not distribution_id:
            print("❌ No CloudFront distribution ID found in config")
            return None
        
        try:
            response = self.cloudfront.get_distribution(Id=distribution_id)
            distribution = response['Distribution']
            
            status = distribution['Status']
            domain_name = distribution['DomainName']
            
            print(f"📊 CloudFront Distribution Status:")
            print(f"   Distribution ID: {distribution_id}")
            print(f"   Domain Name: {domain_name}")
            print(f"   Status: {status}")
            print(f"   Enabled: {distribution['DistributionConfig']['Enabled']}")
            
            if status == 'Deployed':
                print(f"\n✅ Distribution is fully deployed and ready to use!")
                print(f"   Access URL: https://{domain_name}")
            else:
                print(f"\n⏳ Distribution is still deploying... (typically takes 15-20 minutes)")
            
            return {
                'status': status,
                'domain_name': domain_name,
                'enabled': distribution['DistributionConfig']['Enabled']
            }
            
        except ClientError as e:
            print(f"❌ Error getting distribution status: {e}")
            return None


def main():
    """Main setup function."""
    print("=" * 70)
    print("🌐 OpenClass Nexus AI - CloudFront Distribution Setup")
    print("=" * 70)
    print()
    
    setup = CloudFrontSetup()
    
    # Check if distribution already exists
    print("🔍 Checking for existing CloudFront distribution...")
    existing = setup._get_existing_distribution()
    
    if existing:
        print("\n✅ CloudFront is already configured!")
        print(f"   You can access your content via: https://{existing['domain_name']}")
        
        # Check status
        print("\n📊 Checking current status...")
        setup.get_distribution_status()
    else:
        # Create new distribution
        print("\n🚀 Creating new CloudFront distribution...")
        result = setup.create_distribution()
        
        if result:
            print("\n" + "=" * 70)
            print("✅ CloudFront Setup Complete!")
            print("=" * 70)
            print(f"\n📝 Next Steps:")
            print(f"   1. Wait 15-20 minutes for distribution to deploy")
            print(f"   2. Check status: python scripts/setup_cloudfront.py --status")
            print(f"   3. Test access: https://{result['domain_name']}/processed/")
            print(f"   4. Update your application to use CloudFront URL")
            print()
            print(f"💡 Tip: CloudFront will cache content for 24 hours")
            print(f"   To force refresh: python scripts/setup_cloudfront.py --invalidate")
            print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        setup = CloudFrontSetup()
        
        if sys.argv[1] == '--status':
            setup.get_distribution_status()
        elif sys.argv[1] == '--invalidate':
            paths = sys.argv[2:] if len(sys.argv) > 2 else ['/*']
            setup.invalidate_cache(paths)
        else:
            print("Usage:")
            print("  python scripts/setup_cloudfront.py           # Create distribution")
            print("  python scripts/setup_cloudfront.py --status  # Check status")
            print("  python scripts/setup_cloudfront.py --invalidate [paths]  # Invalidate cache")
    else:
        main()
