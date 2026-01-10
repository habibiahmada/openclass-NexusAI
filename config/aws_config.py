"""
AWS Configuration Management
Handles AWS service configurations and credentials
"""

import os
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AWSConfig:
    """AWS Configuration Manager"""
    
    def __init__(self):
        self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        # S3 Configuration
        self.s3_bucket = os.getenv('S3_BUCKET_NAME')
        self.cloudfront_url = os.getenv('CLOUDFRONT_DISTRIBUTION_URL')
        
        # Bedrock Configuration
        self.bedrock_region = os.getenv('BEDROCK_REGION', 'us-east-1')
        self.bedrock_model_id = os.getenv('BEDROCK_MODEL_ID', 'amazon.titan-embed-text-v2:0')
        
        # DynamoDB Configuration
        self.dynamodb_table = os.getenv('DYNAMODB_TABLE_NAME', 'StudentUsageLogs')
    
    def get_s3_client(self):
        """Get configured S3 client"""
        return boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )
    
    def get_bedrock_client(self):
        """Get configured Bedrock Runtime client"""
        return boto3.client(
            'bedrock-runtime',
            region_name=self.bedrock_region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )
    
    def get_dynamodb_client(self):
        """Get configured DynamoDB client"""
        return boto3.client(
            'dynamodb',
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )
    
    def validate_credentials(self):
        """Validate AWS credentials"""
        try:
            sts = boto3.client(
                'sts',
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
            response = sts.get_caller_identity()
            return True, response
        except Exception as e:
            return False, str(e)

# Global configuration instance
aws_config = AWSConfig()