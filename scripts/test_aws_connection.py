#!/usr/bin/env python3
"""
AWS Connection Test Script
Tests connectivity to all AWS services used by OpenClass Nexus AI
"""

import sys
import json
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.aws_config import aws_config

def test_s3_connection():
    """Test S3 connectivity"""
    print("🔍 Testing S3 connection...")
    
    try:
        s3 = aws_config.get_s3_client()
        
        # List buckets to test basic connectivity
        response = s3.list_buckets()
        print(f"✅ S3 connection successful. Found {len(response['Buckets'])} buckets")
        
        # Test specific bucket if configured
        if aws_config.s3_bucket:
            try:
                s3.head_bucket(Bucket=aws_config.s3_bucket)
                print(f"✅ Target bucket '{aws_config.s3_bucket}' accessible")
            except Exception as e:
                print(f"❌ Target bucket '{aws_config.s3_bucket}' not accessible: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        return False

def test_bedrock_connection():
    """Test Bedrock connectivity"""
    print("\n🔍 Testing Bedrock connection...")
    
    try:
        bedrock = aws_config.get_bedrock_client()
        
        # Test with a simple embedding request
        test_text = "Test embedding generation"
        
        response = bedrock.invoke_model(
            modelId=aws_config.bedrock_model_id,
            body=json.dumps({
                "inputText": test_text
            }),
            contentType='application/json'
        )
        
        result = json.loads(response['body'].read())
        
        if 'embedding' in result:
            embedding_dim = len(result['embedding'])
            print(f"✅ Bedrock connection successful. Embedding dimension: {embedding_dim}")
            return True
        else:
            print(f"❌ Unexpected Bedrock response format: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Bedrock connection failed: {e}")
        print("   Note: Bedrock may not be available in all regions")
        print("   Make sure you have access to Amazon Bedrock in your region")
        return False

def test_dynamodb_connection():
    """Test DynamoDB connectivity"""
    print("\n🔍 Testing DynamoDB connection...")
    
    try:
        dynamodb = aws_config.get_dynamodb_client()
        
        # List tables to test basic connectivity
        response = dynamodb.list_tables()
        print(f"✅ DynamoDB connection successful. Found {len(response['TableNames'])} tables")
        
        # Test specific table if configured
        if aws_config.dynamodb_table:
            try:
                response = dynamodb.describe_table(TableName=aws_config.dynamodb_table)
                table_status = response['Table']['TableStatus']
                print(f"✅ Target table '{aws_config.dynamodb_table}' status: {table_status}")
            except Exception as e:
                print(f"❌ Target table '{aws_config.dynamodb_table}' not accessible: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ DynamoDB connection failed: {e}")
        return False

def test_cost_monitoring():
    """Test cost monitoring setup"""
    print("\n🔍 Testing cost monitoring...")
    
    try:
        # Test CloudWatch for cost monitoring
        import boto3
        cloudwatch = boto3.client('cloudwatch', region_name=aws_config.region)
        
        # List metrics to test connectivity
        response = cloudwatch.list_metrics(Namespace='AWS/Billing')
        
        if response['Metrics']:
            print("✅ Cost monitoring accessible via CloudWatch")
            return True
        else:
            print("⚠️  No billing metrics found - may need to enable detailed billing")
            return True  # Non-critical for development
            
    except Exception as e:
        print(f"⚠️  Cost monitoring test failed: {e}")
        print("   This is non-critical for development")
        return True

def estimate_costs():
    """Provide cost estimates"""
    print("\n💰 Cost Estimates (Monthly):")
    print("=" * 40)
    print("S3 Storage (10GB):           ~$0.23")
    print("CloudFront (1GB transfer):   ~$0.09")
    print("Bedrock (100K tokens):       ~$0.01")
    print("DynamoDB (1GB, low usage):   ~$0.25")
    print("Lambda (1M requests):        ~$0.20")
    print("-" * 40)
    print("Estimated Total:             ~$0.78/month")
    print("\nNote: Actual costs may vary based on usage")

def main():
    """Main test function"""
    print("🧪 Testing AWS connectivity for OpenClass Nexus AI")
    print("=" * 60)
    
    # Validate credentials first
    is_valid, result = aws_config.validate_credentials()
    if not is_valid:
        print(f"❌ AWS credentials not configured: {result}")
        print("Please run 'aws configure' first")
        sys.exit(1)
    
    print(f"✅ AWS credentials valid for account: {result.get('Account')}")
    print(f"   Region: {aws_config.region}")
    print(f"   User/Role: {result.get('Arn', 'Unknown')}")
    
    # Run tests
    tests = [
        ("S3", test_s3_connection),
        ("Bedrock", test_bedrock_connection),
        ("DynamoDB", test_dynamodb_connection),
        ("Cost Monitoring", test_cost_monitoring)
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 30)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! AWS setup is ready for development.")
        estimate_costs()
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
        print("   Common issues:")
        print("   - Incorrect AWS credentials")
        print("   - Missing IAM permissions")
        print("   - Services not available in selected region")
        print("   - Resources not yet created")
        
        sys.exit(1)

if __name__ == "__main__":
    main()