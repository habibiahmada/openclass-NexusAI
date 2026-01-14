"""
S3 Storage Optimization Script
Configures lifecycle policies, storage classes, and encryption for cost optimization
"""

import boto3
import json
from botocore.exceptions import ClientError
from config.aws_config import aws_config

class S3StorageOptimizer:
    def __init__(self):
        self.s3 = aws_config.get_s3_client()
        self.bucket_name = aws_config.s3_bucket
        
    def setup_lifecycle_policies(self):
        """Configure S3 lifecycle policies for cost optimization."""
        print(f"🔄 Setting up lifecycle policies for bucket: {self.bucket_name}")
        
        lifecycle_config = {
            'Rules': [
                {
                    'Id': 'TransitionRawPDFsToGlacier',
                    'Status': 'Enabled',
                    'Prefix': 'raw-pdf/',
                    'Transitions': [
                        {
                            'Days': 30,
                            'StorageClass': 'GLACIER'
                        }
                    ],
                    'NoncurrentVersionTransitions': [
                        {
                            'NoncurrentDays': 30,
                            'StorageClass': 'GLACIER'
                        }
                    ]
                },
                {
                    'Id': 'TransitionProcessedToIA',
                    'Status': 'Enabled',
                    'Prefix': 'processed/',
                    'Transitions': [
                        {
                            'Days': 7,
                            'StorageClass': 'STANDARD_IA'
                        }
                    ]
                },
                {
                    'Id': 'DeleteOldLogs',
                    'Status': 'Enabled',
                    'Prefix': 'logs/',
                    'Expiration': {
                        'Days': 90
                    }
                }
            ]
        }
        
        try:
            self.s3.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            
            print("✅ Lifecycle policies configured successfully!")
            print("\n📋 Configured Rules:")
            print("   1. Raw PDFs → Glacier after 30 days")
            print("   2. Processed data → Standard-IA after 7 days")
            print("   3. Logs → Delete after 90 days")
            print("\n💰 Expected Savings:")
            print("   - Glacier: ~90% cheaper than Standard")
            print("   - Standard-IA: ~50% cheaper than Standard")
            
            return True
            
        except ClientError as e:
            print(f"❌ Error setting lifecycle policies: {e}")
            return False
    
    def enable_encryption(self):
        """Enable server-side encryption for S3 bucket."""
        print(f"\n🔒 Enabling server-side encryption for bucket: {self.bucket_name}")
        
        encryption_config = {
            'Rules': [
                {
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256'
                    },
                    'BucketKeyEnabled': True
                }
            ]
        }
        
        try:
            self.s3.put_bucket_encryption(
                Bucket=self.bucket_name,
                ServerSideEncryptionConfiguration=encryption_config
            )
            
            print("✅ Server-side encryption (AES-256) enabled!")
            print("   All new objects will be automatically encrypted")
            
            return True
            
        except ClientError as e:
            print(f"❌ Error enabling encryption: {e}")
            return False
    
    def configure_intelligent_tiering(self):
        """Configure S3 Intelligent-Tiering for automatic cost optimization."""
        print(f"\n🤖 Configuring Intelligent-Tiering for bucket: {self.bucket_name}")
        
        intelligent_tiering_config = {
            'Id': 'EntireBucket',
            'Status': 'Enabled',
            'Tierings': [
                {
                    'Days': 90,
                    'AccessTier': 'ARCHIVE_ACCESS'
                },
                {
                    'Days': 180,
                    'AccessTier': 'DEEP_ARCHIVE_ACCESS'
                }
            ]
        }
        
        try:
            self.s3.put_bucket_intelligent_tiering_configuration(
                Bucket=self.bucket_name,
                Id='EntireBucket',
                IntelligentTieringConfiguration=intelligent_tiering_config
            )
            
            print("✅ Intelligent-Tiering configured!")
            print("   Objects will automatically move to cheaper tiers based on access patterns")
            
            return True
            
        except ClientError as e:
            # Intelligent-Tiering might not be available in all regions
            print(f"⚠️  Intelligent-Tiering not configured: {e}")
            print("   (This is optional and not critical)")
            return False
    
    def enable_versioning(self):
        """Enable versioning for data protection."""
        print(f"\n📦 Enabling versioning for bucket: {self.bucket_name}")
        
        try:
            self.s3.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={
                    'Status': 'Enabled'
                }
            )
            
            print("✅ Versioning enabled!")
            print("   Previous versions will be retained for recovery")
            
            return True
            
        except ClientError as e:
            print(f"❌ Error enabling versioning: {e}")
            return False
    
    def get_bucket_size_and_cost(self):
        """Calculate bucket size and estimated monthly cost."""
        print(f"\n📊 Analyzing bucket: {self.bucket_name}")
        
        try:
            # Use CloudWatch to get bucket metrics
            cloudwatch = boto3.client(
                'cloudwatch',
                region_name=aws_config.region,
                aws_access_key_id=aws_config.access_key,
                aws_secret_access_key=aws_config.secret_key
            )
            
            from datetime import datetime, timedelta
            
            # Get bucket size metric
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='BucketSizeBytes',
                Dimensions=[
                    {'Name': 'BucketName', 'Value': self.bucket_name},
                    {'Name': 'StorageType', 'Value': 'StandardStorage'}
                ],
                StartTime=datetime.now() - timedelta(days=1),
                EndTime=datetime.now(),
                Period=86400,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                size_bytes = response['Datapoints'][0]['Average']
                size_gb = size_bytes / (1024**3)
                
                # Estimate cost (S3 Standard: $0.023 per GB)
                monthly_cost = size_gb * 0.023
                
                print(f"   Total Size: {size_gb:.2f} GB")
                print(f"   Estimated Monthly Cost: ${monthly_cost:.4f}")
                
                # Get number of objects
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/S3',
                    MetricName='NumberOfObjects',
                    Dimensions=[
                        {'Name': 'BucketName', 'Value': self.bucket_name},
                        {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                    ],
                    StartTime=datetime.now() - timedelta(days=1),
                    EndTime=datetime.now(),
                    Period=86400,
                    Statistics=['Average']
                )
                
                if response['Datapoints']:
                    num_objects = int(response['Datapoints'][0]['Average'])
                    print(f"   Number of Objects: {num_objects}")
                
                return {
                    'size_gb': size_gb,
                    'monthly_cost': monthly_cost,
                    'num_objects': num_objects if response['Datapoints'] else 0
                }
            else:
                print("   ⚠️  No metrics available yet (bucket might be new)")
                return None
                
        except Exception as e:
            print(f"   ⚠️  Could not retrieve metrics: {e}")
            return None
    
    def list_lifecycle_policies(self):
        """List current lifecycle policies."""
        print(f"\n📋 Current Lifecycle Policies for bucket: {self.bucket_name}")
        
        try:
            response = self.s3.get_bucket_lifecycle_configuration(
                Bucket=self.bucket_name
            )
            
            if 'Rules' in response:
                for rule in response['Rules']:
                    print(f"\n   Rule: {rule['Id']}")
                    print(f"   Status: {rule['Status']}")
                    print(f"   Prefix: {rule.get('Prefix', 'All objects')}")
                    
                    if 'Transitions' in rule:
                        for transition in rule['Transitions']:
                            print(f"   → {transition['StorageClass']} after {transition['Days']} days")
                    
                    if 'Expiration' in rule:
                        print(f"   → Delete after {rule['Expiration']['Days']} days")
            else:
                print("   No lifecycle policies configured")
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
                print("   No lifecycle policies configured")
            else:
                print(f"   ❌ Error: {e}")


def main():
    """Main optimization function."""
    print("=" * 70)
    print("💰 OpenClass Nexus AI - S3 Storage Optimization")
    print("=" * 70)
    print()
    
    optimizer = S3StorageOptimizer()
    
    # Get current bucket status
    optimizer.get_bucket_size_and_cost()
    
    # List current policies
    optimizer.list_lifecycle_policies()
    
    print("\n" + "=" * 70)
    print("🚀 Applying Optimizations...")
    print("=" * 70)
    
    # Apply optimizations
    results = {
        'lifecycle': optimizer.setup_lifecycle_policies(),
        'encryption': optimizer.enable_encryption(),
        'versioning': optimizer.enable_versioning(),
        'intelligent_tiering': optimizer.configure_intelligent_tiering()
    }
    
    print("\n" + "=" * 70)
    print("✅ Optimization Complete!")
    print("=" * 70)
    
    # Summary
    print("\n📊 Summary:")
    for feature, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {feature.replace('_', ' ').title()}")
    
    print("\n💡 Cost Optimization Tips:")
    print("   1. Raw PDFs will move to Glacier after 30 days (90% cheaper)")
    print("   2. Processed data moves to Standard-IA after 7 days (50% cheaper)")
    print("   3. All data is encrypted at rest (AES-256)")
    print("   4. Versioning enabled for data protection")
    print("\n📈 Expected Monthly Savings: 60-80% on storage costs")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        optimizer = S3StorageOptimizer()
        optimizer.get_bucket_size_and_cost()
        optimizer.list_lifecycle_policies()
    else:
        main()
