#!/usr/bin/env python3
"""
AWS Setup Script
Automates the setup of AWS infrastructure for OpenClass Nexus AI
"""

import boto3
import json
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.aws_config import aws_config

def create_s3_bucket():
    """Create S3 bucket with proper configuration"""
    s3 = aws_config.get_s3_client()
    bucket_name = aws_config.s3_bucket
    
    try:
        # Check if bucket already exists
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"ℹ️  S3 bucket '{bucket_name}' already exists")
        except Exception:
            # Create bucket if it doesn't exist
            if aws_config.region == 'us-east-1':
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': aws_config.region}
                )
            print(f"✅ S3 bucket '{bucket_name}' created successfully")
        
        # Configure bucket settings (even if bucket already exists)
        # Block public access
        try:
            s3.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            print(f"✅ Public access blocked for bucket '{bucket_name}'")
        except Exception as e:
            print(f"⚠️  Could not configure public access block: {e}")
        
        # Enable versioning
        try:
            s3.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            print(f"✅ Versioning enabled for bucket '{bucket_name}'")
        except Exception as e:
            print(f"⚠️  Could not enable versioning: {e}")
        
        # Set lifecycle policy
        try:
            lifecycle_policy = {
                'Rules': [
                    {
                        'ID': 'DeleteRawFilesAfter30Days',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'raw-pdf/'},
                        'Expiration': {'Days': 30}
                    },
                    {
                        'ID': 'TransitionToIA',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'processed-text/'},
                        'Transitions': [
                            {
                                'Days': 30,
                                'StorageClass': 'STANDARD_IA'
                            }
                        ]
                    }
                ]
            }
            
            s3.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_policy
            )
            print(f"✅ Lifecycle policies configured for bucket '{bucket_name}'")
        except Exception as e:
            print(f"⚠️  Could not configure lifecycle policies: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring S3 bucket: {e}")
        return False

def create_dynamodb_table():
    """Create DynamoDB table for usage logs"""
    dynamodb = aws_config.get_dynamodb_client()
    table_name = aws_config.dynamodb_table
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'SchoolID',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'Timestamp',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'SchoolID',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'Timestamp',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print(f"✅ DynamoDB table '{table_name}' created successfully")
        return True
        
    except Exception as e:
        if 'ResourceInUseException' in str(e):
            print(f"ℹ️  DynamoDB table '{table_name}' already exists")
            return True
        else:
            print(f"❌ Error creating DynamoDB table: {e}")
            return False

def setup_budget_alert():
    """Set up budget alerts"""
    try:
        budgets = boto3.client('budgets', region_name=aws_config.region)
        
        budget_config = {
            'BudgetName': 'OpenClassNexusAI-Budget',
            'BudgetLimit': {
                'Amount': '1.00',
                'Unit': 'USD'
            },
            'TimeUnit': 'MONTHLY',
            'BudgetType': 'COST',
            'CostFilters': {
                'TagKey': ['Project'],
                'TagValue': ['OpenClassNexusAI']
            }
        }
        
        # Note: Budget creation requires additional permissions
        # This is a template - actual implementation may vary
        print("ℹ️  Budget alert setup requires manual configuration in AWS Console")
        print("   Navigate to AWS Budgets and create a $1.00 monthly budget")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Budget setup note: {e}")
        return True  # Non-critical for development

def validate_setup():
    """Validate AWS setup"""
    print("\n🔍 Validating AWS setup...")
    
    # Validate credentials
    is_valid, result = aws_config.validate_credentials()
    if not is_valid:
        print(f"❌ AWS credentials invalid: {result}")
        return False
    
    print(f"✅ AWS credentials valid for account: {result.get('Account')}")
    
    # Check S3 bucket
    s3 = aws_config.get_s3_client()
    try:
        s3.head_bucket(Bucket=aws_config.s3_bucket)
        print(f"✅ S3 bucket '{aws_config.s3_bucket}' accessible")
    except Exception as e:
        print(f"❌ S3 bucket not accessible: {e}")
        return False
    
    # Check DynamoDB table
    dynamodb = aws_config.get_dynamodb_client()
    try:
        response = dynamodb.describe_table(TableName=aws_config.dynamodb_table)
        print(f"✅ DynamoDB table '{aws_config.dynamodb_table}' accessible")
    except Exception as e:
        print(f"❌ DynamoDB table not accessible: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up AWS infrastructure for OpenClass Nexus AI")
    print("=" * 60)
    
    # Validate credentials first
    is_valid, result = aws_config.validate_credentials()
    if not is_valid:
        print(f"❌ AWS credentials not configured properly: {result}")
        print("Please run 'aws configure' first")
        sys.exit(1)
    
    print(f"✅ Connected to AWS account: {result.get('Account')}")
    
    # Create infrastructure
    success = True
    
    print("\n📦 Creating S3 bucket...")
    success &= create_s3_bucket()
    
    print("\n🗄️  Creating DynamoDB table...")
    success &= create_dynamodb_table()
    
    print("\n💰 Setting up budget alerts...")
    success &= setup_budget_alert()
    
    # Validate setup
    if success:
        success &= validate_setup()
    
    if success:
        print("\n🎉 AWS setup completed successfully!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and update with your values")
        print("2. Run 'python scripts/test_aws_connection.py' to verify setup")
        print("3. Start processing educational content")
    else:
        print("\n❌ Setup completed with errors. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()