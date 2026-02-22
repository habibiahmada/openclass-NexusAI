# AWS Infrastructure Setup Guide

Complete guide for setting up AWS infrastructure for OpenClass Nexus AI's Hybrid Orchestrated Edge AI architecture.

## Overview

This guide covers the setup of AWS Control Plane components that support the edge-based school servers. The AWS infrastructure handles:

- **Curriculum Processing**: Automated PDF-to-VKP conversion via Lambda
- **Content Distribution**: S3 and CloudFront for VKP package delivery
- **Telemetry Collection**: Anonymized metrics aggregation in DynamoDB
- **Model Development**: SageMaker for fine-tuning and distillation (optional)

**Important**: AWS is for orchestration only. All student inference happens 100% offline at school edge servers.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              AWS NATIONAL CONTROL PLANE                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Curriculum Processing Pipeline                          │  │
│  │  - S3 (Raw PDF Storage)                                  │  │
│  │  - Lambda (ETL + Embedding Generation)                   │  │
│  │  - Bedrock Titan (Embedding Model)                       │  │
│  │  - VKP Packager (Versioning + Checksum)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Distribution Domain                                     │  │
│  │  - S3 (VKP Storage with Versioning)                      │  │
│  │  - CloudFront (CDN Distribution)                         │  │
│  │  - Signed URL Access                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Telemetry Domain                                        │  │
│  │  - DynamoDB (Aggregated Metrics - Anonymized Only)       │  │
│  │  - CloudWatch (Lambda Logs)                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### 1. AWS Account Requirements

- Active AWS account with billing enabled
- Root account access or IAM user with AdministratorAccess
- Credit card on file for pay-as-you-go services
- MFA enabled (recommended for security)

### 2. AWS CLI Installation

**Linux/macOS:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Windows:**
Download and run the MSI installer from: https://awscli.amazonaws.com/AWSCLIV2.msi

**Verify Installation:**
```bash
aws --version
# Expected: aws-cli/2.x.x Python/3.x.x
```

### 3. Configure AWS Credentials

```bash
aws configure
```

Enter the following when prompted:
- **AWS Access Key ID**: Your IAM access key
- **AWS Secret Access Key**: Your IAM secret key
- **Default region name**: `ap-southeast-1` (Singapore)
- **Default output format**: `json`

**Verify Configuration:**
```bash
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

### 4. Python and Boto3

```bash
# Install boto3
pip install boto3

# Verify
python -c "import boto3; print(boto3.__version__)"
```

### 5. Region Selection

**Primary Region**: `ap-southeast-1` (Singapore)
- Closest to Indonesia
- Full service availability
- Bedrock Titan model available

**Alternative**: `ap-southeast-2` (Sydney) if Singapore unavailable

## Step 1: S3 Bucket Setup

### 1.1 Create S3 Buckets

Three buckets are required for the system:

#### Bucket 1: nexusai-curriculum-raw
**Purpose**: Store raw PDF curriculum files uploaded by teachers

```bash
aws s3api create-bucket \
    --bucket nexusai-curriculum-raw \
    --region ap-southeast-1 \
    --create-bucket-configuration LocationConstraint=ap-southeast-1

# Enable versioning (optional but recommended)
aws s3api put-bucket-versioning \
    --bucket nexusai-curriculum-raw \
    --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
    --bucket nexusai-curriculum-raw \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

#### Bucket 2: nexusai-vkp-packages
**Purpose**: Store processed VKP (Versioned Knowledge Package) files

```bash
aws s3api create-bucket \
    --bucket nexusai-vkp-packages \
    --region ap-southeast-1 \
    --create-bucket-configuration LocationConstraint=ap-southeast-1

# Enable versioning (REQUIRED for VKP tracking)
aws s3api put-bucket-versioning \
    --bucket nexusai-vkp-packages \
    --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
    --bucket nexusai-vkp-packages \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

#### Bucket 3: nexusai-model-distribution
**Purpose**: Store and distribute LLM model files

```bash
aws s3api create-bucket \
    --bucket nexusai-model-distribution \
    --region ap-southeast-1 \
    --create-bucket-configuration LocationConstraint=ap-southeast-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket nexusai-model-distribution \
    --versioning-configuration Status=Enabled
```

### 1.2 Configure S3 Bucket Policies

#### Policy for nexusai-curriculum-raw

Create file `curriculum-raw-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowLambdaRead",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::nexusai-curriculum-raw",
        "arn:aws:s3:::nexusai-curriculum-raw/*"
      ]
    }
  ]
}
```

Apply policy:
```bash
aws s3api put-bucket-policy \
    --bucket nexusai-curriculum-raw \
    --policy file://curriculum-raw-policy.json
```

#### Policy for nexusai-vkp-packages

Create file `vkp-packages-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowLambdaWrite",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::nexusai-vkp-packages/*"
    },
    {
      "Sid": "AllowSchoolServerRead",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:role/NexusAI-SchoolServer-Role"
      },
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::nexusai-vkp-packages",
        "arn:aws:s3:::nexusai-vkp-packages/*"
      ]
    }
  ]
}
```

Apply policy (replace ACCOUNT_ID with your AWS account ID):
```bash
aws s3api put-bucket-policy \
    --bucket nexusai-vkp-packages \
    --policy file://vkp-packages-policy.json
```

### 1.3 Configure S3 Lifecycle Policies

#### Lifecycle for nexusai-curriculum-raw
Transition old PDFs to cheaper storage after 90 days:

Create file `curriculum-lifecycle.json`:
```json
{
  "Rules": [
    {
      "Id": "TransitionToIA",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "STANDARD_IA"
        }
      ]
    }
  ]
}
```

Apply lifecycle:
```bash
aws s3api put-bucket-lifecycle-configuration \
    --bucket nexusai-curriculum-raw \
    --lifecycle-configuration file://curriculum-lifecycle.json
```

### 1.4 Enable S3 Event Notifications

Configure S3 to trigger Lambda when PDFs are uploaded:

```bash
# This will be configured after Lambda function is created (Step 3)
# Placeholder for now - see Step 3.5
```

### 1.5 Verify S3 Setup

```bash
# List all buckets
aws s3 ls

# Expected output:
# nexusai-curriculum-raw
# nexusai-vkp-packages
# nexusai-model-distribution

# Test upload
echo "test" > test.txt
aws s3 cp test.txt s3://nexusai-curriculum-raw/test.txt
aws s3 rm s3://nexusai-curriculum-raw/test.txt
rm test.txt
```

## Step 2: DynamoDB Table Setup

### 2.1 Create nexusai-schools Table

**Purpose**: Store school registration and configuration data

```bash
aws dynamodb create-table \
    --table-name nexusai-schools \
    --attribute-definitions \
        AttributeName=school_id,AttributeType=S \
    --key-schema \
        AttributeName=school_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ap-southeast-1
```

**Table Schema:**
- **Partition Key**: `school_id` (String) - Anonymized school identifier
- **Attributes**:
  - `school_name` (String) - School name (optional)
  - `region` (String) - Geographic region
  - `registered_at` (Number) - Unix timestamp
  - `last_sync` (Number) - Last VKP sync timestamp
  - `model_version` (String) - Current LLM model version
  - `vkp_versions` (Map) - Subject → VKP version mapping

### 2.2 Create nexusai-metrics Table

**Purpose**: Store anonymized telemetry metrics from school servers

```bash
aws dynamodb create-table \
    --table-name nexusai-metrics \
    --attribute-definitions \
        AttributeName=school_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=N \
    --key-schema \
        AttributeName=school_id,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region ap-southeast-1
```

**Table Schema:**
- **Partition Key**: `school_id` (String) - Anonymized school identifier
- **Sort Key**: `timestamp` (Number) - Unix timestamp
- **Attributes**:
  - `total_queries` (Number)
  - `successful_queries` (Number)
  - `failed_queries` (Number)
  - `average_latency_ms` (Number)
  - `p90_latency_ms` (Number)
  - `p99_latency_ms` (Number)
  - `model_version` (String)
  - `error_rate` (Number)
  - `error_types` (Map)
  - `chromadb_size_mb` (Number)
  - `postgres_size_mb` (Number)
  - `disk_usage_percent` (Number)
  - `active_users_count` (Number)
  - `subjects_queried` (List)

### 2.3 Configure TTL for nexusai-metrics

Enable Time-To-Live to automatically delete old metrics after 90 days:

```bash
aws dynamodb update-time-to-live \
    --table-name nexusai-metrics \
    --time-to-live-specification \
        "Enabled=true,AttributeName=ttl" \
    --region ap-southeast-1
```

**Note**: School servers must set `ttl` attribute when writing metrics:
```python
ttl = int(time.time()) + (90 * 24 * 60 * 60)  # 90 days from now
```

### 2.4 Create Global Secondary Indexes (Optional)

For querying metrics by date range across all schools:

```bash
aws dynamodb update-table \
    --table-name nexusai-metrics \
    --attribute-definitions \
        AttributeName=timestamp,AttributeType=N \
    --global-secondary-index-updates \
        "[{\"Create\":{\"IndexName\":\"timestamp-index\",\"KeySchema\":[{\"AttributeName\":\"timestamp\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}}]" \
    --region ap-southeast-1
```

### 2.5 Verify DynamoDB Setup

```bash
# List tables
aws dynamodb list-tables --region ap-southeast-1

# Describe nexusai-schools table
aws dynamodb describe-table \
    --table-name nexusai-schools \
    --region ap-southeast-1

# Describe nexusai-metrics table
aws dynamodb describe-table \
    --table-name nexusai-metrics \
    --region ap-southeast-1

# Test write to nexusai-schools
aws dynamodb put-item \
    --table-name nexusai-schools \
    --item '{
        "school_id": {"S": "test_school_001"},
        "school_name": {"S": "Test School"},
        "region": {"S": "Jakarta"},
        "registered_at": {"N": "1705320000"}
    }' \
    --region ap-southeast-1

# Test read
aws dynamodb get-item \
    --table-name nexusai-schools \
    --key '{"school_id": {"S": "test_school_001"}}' \
    --region ap-southeast-1

# Delete test item
aws dynamodb delete-item \
    --table-name nexusai-schools \
    --key '{"school_id": {"S": "test_school_001"}}' \
    --region ap-southeast-1
```

## Step 3: IAM Roles and Permissions

### 3.1 Create Lambda Execution Role

Create file `lambda-trust-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Create the role:
```bash
aws iam create-role \
    --role-name NexusAI-Lambda-CurriculumProcessor \
    --assume-role-policy-document file://lambda-trust-policy.json
```

### 3.2 Create Lambda Execution Policy

Create file `lambda-execution-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::nexusai-curriculum-raw",
        "arn:aws:s3:::nexusai-curriculum-raw/*",
        "arn:aws:s3:::nexusai-vkp-packages",
        "arn:aws:s3:::nexusai-vkp-packages/*"
      ]
    },
    {
      "Sid": "BedrockAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:ap-southeast-1::foundation-model/amazon.titan-embed-text-v1"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:ap-southeast-1:*:*"
    }
  ]
}
```

Create and attach the policy:
```bash
aws iam create-policy \
    --policy-name NexusAI-Lambda-Execution-Policy \
    --policy-document file://lambda-execution-policy.json

aws iam attach-role-policy \
    --role-name NexusAI-Lambda-CurriculumProcessor \
    --policy-arn arn:aws:iam::ACCOUNT_ID:policy/NexusAI-Lambda-Execution-Policy
```

Replace `ACCOUNT_ID` with your AWS account ID.

### 3.3 Create School Server IAM Role

Create file `school-server-trust-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Create the role:
```bash
aws iam create-role \
    --role-name NexusAI-SchoolServer-Role \
    --assume-role-policy-document file://school-server-trust-policy.json
```

### 3.4 Create School Server Policy

Create file `school-server-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3VKPRead",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::nexusai-vkp-packages",
        "arn:aws:s3:::nexusai-vkp-packages/*",
        "arn:aws:s3:::nexusai-model-distribution",
        "arn:aws:s3:::nexusai-model-distribution/*"
      ]
    },
    {
      "Sid": "DynamoDBTelemetry",
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:ap-southeast-1:ACCOUNT_ID:table/nexusai-schools",
        "arn:aws:dynamodb:ap-southeast-1:ACCOUNT_ID:table/nexusai-metrics"
      ]
    }
  ]
}
```

Create and attach the policy:
```bash
aws iam create-policy \
    --policy-name NexusAI-SchoolServer-Policy \
    --policy-document file://school-server-policy.json

aws iam attach-role-policy \
    --role-name NexusAI-SchoolServer-Role \
    --policy-arn arn:aws:iam::ACCOUNT_ID:policy/NexusAI-SchoolServer-Policy
```

### 3.5 Create IAM User for School Servers (Alternative to Role)

If school servers are not EC2 instances, create IAM users with access keys:

```bash
# Create user
aws iam create-user --user-name nexusai-school-server

# Attach policy
aws iam attach-user-policy \
    --user-name nexusai-school-server \
    --policy-arn arn:aws:iam::ACCOUNT_ID:policy/NexusAI-SchoolServer-Policy

# Create access key
aws iam create-access-key --user-name nexusai-school-server
```

**Save the output** - you'll need the AccessKeyId and SecretAccessKey for school server configuration.

### 3.6 Verify IAM Setup

```bash
# List roles
aws iam list-roles | grep NexusAI

# Get role details
aws iam get-role --role-name NexusAI-Lambda-CurriculumProcessor
aws iam get-role --role-name NexusAI-SchoolServer-Role

# List attached policies
aws iam list-attached-role-policies --role-name NexusAI-Lambda-CurriculumProcessor
aws iam list-attached-role-policies --role-name NexusAI-SchoolServer-Role
```

## Step 4: Lambda Function Deployment

### 4.1 Prepare Lambda Function Code

Create directory structure:
```bash
mkdir -p lambda-curriculum-processor
cd lambda-curriculum-processor
```

Create `lambda_function.py`:
```python
import json
import boto3
import hashlib
from datetime import datetime
from io import BytesIO
from pypdf import PdfReader

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime', region_name='ap-southeast-1')

def lambda_handler(event, context):
    """
    Process PDF curriculum files and generate VKP packages
    """
    try:
        # Get S3 event details
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        print(f"Processing: s3://{bucket}/{key}")
        
        # Download PDF
        pdf_obj = s3.get_object(Bucket=bucket, Key=key)
        pdf_bytes = pdf_obj['Body'].read()
        
        # Extract text
        text = extract_text_from_pdf(pdf_bytes)
        print(f"Extracted {len(text)} characters")
        
        # Chunk text
        chunks = chunk_text(text, chunk_size=800, overlap=100)
        print(f"Created {len(chunks)} chunks")
        
        # Generate embeddings
        chunks_with_embeddings = generate_embeddings(chunks)
        print(f"Generated embeddings for {len(chunks_with_embeddings)} chunks")
        
        # Extract metadata from filename
        metadata = extract_metadata_from_key(key)
        
        # Package VKP
        vkp = create_vkp_package(chunks_with_embeddings, metadata)
        print(f"Created VKP version {vkp['version']}")
        
        # Upload to S3
        upload_vkp(vkp)
        print(f"Uploaded VKP to s3://nexusai-vkp-packages/")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'vkp_version': vkp['version'],
                'chunks': len(chunks_with_embeddings)
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF using pypdf"""
    reader = PdfReader(BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    return text.strip()

def chunk_text(text, chunk_size=800, overlap=100):
    """Chunk text with overlap"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunks.append({
            'chunk_id': f"chunk_{len(chunks):04d}",
            'text': ' '.join(chunk_words)
        })
    return chunks

def generate_embeddings(chunks):
    """Generate embeddings using Bedrock Titan"""
    for chunk in chunks:
        response = bedrock.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=json.dumps({'inputText': chunk['text']})
        )
        result = json.loads(response['body'].read())
        chunk['embedding'] = result['embedding']
    return chunks

def extract_metadata_from_key(key):
    """Extract metadata from S3 key: raw/matematika_kelas_10_v1.0.0.pdf"""
    filename = key.split('/')[-1].replace('.pdf', '')
    parts = filename.split('_')
    return {
        'subject': parts[0] if len(parts) > 0 else 'unknown',
        'grade': int(parts[2]) if len(parts) > 2 else 10,
        'version': parts[3] if len(parts) > 3 else '1.0.0',
        'source_file': filename + '.pdf'
    }

def create_vkp_package(chunks, metadata):
    """Create VKP package with checksum"""
    vkp = {
        'version': metadata['version'],
        'subject': metadata['subject'],
        'grade': metadata['grade'],
        'created_at': datetime.utcnow().isoformat(),
        'embedding_model': 'amazon.titan-embed-text-v1',
        'chunk_config': {'chunk_size': 800, 'chunk_overlap': 100},
        'chunks': chunks,
        'total_chunks': len(chunks),
        'source_files': [metadata['source_file']]
    }
    vkp['checksum'] = calculate_checksum(vkp)
    return vkp

def calculate_checksum(vkp):
    """Calculate SHA256 checksum"""
    vkp_copy = vkp.copy()
    vkp_copy.pop('checksum', None)
    vkp_json = json.dumps(vkp_copy, sort_keys=True)
    return 'sha256:' + hashlib.sha256(vkp_json.encode()).hexdigest()

def upload_vkp(vkp):
    """Upload VKP to S3"""
    key = f"{vkp['subject']}/kelas_{vkp['grade']}/v{vkp['version']}.vkp"
    s3.put_object(
        Bucket='nexusai-vkp-packages',
        Key=key,
        Body=json.dumps(vkp),
        ContentType='application/json',
        Metadata={
            'version': vkp['version'],
            'subject': vkp['subject'],
            'grade': str(vkp['grade'])
        }
    )
```

### 4.2 Create requirements.txt

```
pypdf==3.17.0
boto3==1.34.0
```

### 4.3 Package Lambda Function

```bash
# Install dependencies
pip install -r requirements.txt -t .

# Create deployment package
zip -r lambda-function.zip .

# Verify package size (should be < 50MB)
ls -lh lambda-function.zip
```

### 4.4 Deploy Lambda Function

```bash
aws lambda create-function \
    --function-name nexusai-curriculum-processor \
    --runtime python3.11 \
    --role arn:aws:iam::ACCOUNT_ID:role/NexusAI-Lambda-CurriculumProcessor \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda-function.zip \
    --timeout 300 \
    --memory-size 1024 \
    --environment Variables="{
        BEDROCK_MODEL_ID=amazon.titan-embed-text-v1,
        CHUNK_SIZE=800,
        CHUNK_OVERLAP=100,
        VKP_BUCKET=nexusai-vkp-packages
    }" \
    --region ap-southeast-1
```

Replace `ACCOUNT_ID` with your AWS account ID.

### 4.5 Configure S3 Event Trigger

Grant S3 permission to invoke Lambda:
```bash
aws lambda add-permission \
    --function-name nexusai-curriculum-processor \
    --statement-id s3-trigger \
    --action lambda:InvokeFunction \
    --principal s3.amazonaws.com \
    --source-arn arn:aws:s3:::nexusai-curriculum-raw \
    --region ap-southeast-1
```

Create S3 event notification:
```bash
aws s3api put-bucket-notification-configuration \
    --bucket nexusai-curriculum-raw \
    --notification-configuration '{
        "LambdaFunctionConfigurations": [
            {
                "Id": "curriculum-processor-trigger",
                "LambdaFunctionArn": "arn:aws:lambda:ap-southeast-1:ACCOUNT_ID:function:nexusai-curriculum-processor",
                "Events": ["s3:ObjectCreated:*"],
                "Filter": {
                    "Key": {
                        "FilterRules": [
                            {"Name": "prefix", "Value": "raw/"},
                            {"Name": "suffix", "Value": ".pdf"}
                        ]
                    }
                }
            }
        ]
    }' \
    --region ap-southeast-1
```

### 4.6 Test Lambda Function

Upload a test PDF:
```bash
# Create test PDF or use existing one
aws s3 cp test-curriculum.pdf s3://nexusai-curriculum-raw/raw/matematika_kelas_10_v1.0.0.pdf
```

Check Lambda logs:
```bash
aws logs tail /aws/lambda/nexusai-curriculum-processor --follow
```

Verify VKP created:
```bash
aws s3 ls s3://nexusai-vkp-packages/matematika/kelas_10/
```

### 4.7 Update Lambda Function (if needed)

```bash
# Update code
zip -r lambda-function.zip .

aws lambda update-function-code \
    --function-name nexusai-curriculum-processor \
    --zip-file fileb://lambda-function.zip \
    --region ap-southeast-1

# Update configuration
aws lambda update-function-configuration \
    --function-name nexusai-curriculum-processor \
    --timeout 300 \
    --memory-size 1024 \
    --region ap-southeast-1
```

## Step 5: CloudFront Distribution (Optional)

CloudFront provides CDN caching and faster VKP downloads for school servers.

### 5.1 Create CloudFront Distribution

```bash
aws cloudfront create-distribution \
    --distribution-config '{
        "CallerReference": "nexusai-vkp-'$(date +%s)'",
        "Comment": "NexusAI VKP Distribution",
        "Enabled": true,
        "Origins": {
            "Quantity": 1,
            "Items": [
                {
                    "Id": "S3-nexusai-vkp-packages",
                    "DomainName": "nexusai-vkp-packages.s3.ap-southeast-1.amazonaws.com",
                    "S3OriginConfig": {
                        "OriginAccessIdentity": ""
                    }
                }
            ]
        },
        "DefaultCacheBehavior": {
            "TargetOriginId": "S3-nexusai-vkp-packages",
            "ViewerProtocolPolicy": "redirect-to-https",
            "AllowedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            },
            "ForwardedValues": {
                "QueryString": false,
                "Cookies": {"Forward": "none"}
            },
            "MinTTL": 3600,
            "DefaultTTL": 86400,
            "MaxTTL": 31536000
        }
    }'
```

### 5.2 Create Origin Access Identity (OAI)

```bash
aws cloudfront create-cloud-front-origin-access-identity \
    --cloud-front-origin-access-identity-config '{
        "CallerReference": "nexusai-oai-'$(date +%s)'",
        "Comment": "OAI for NexusAI VKP bucket"
    }'
```

Save the OAI ID from the output.

### 5.3 Update S3 Bucket Policy for CloudFront

Add to `vkp-packages-policy.json`:
```json
{
  "Sid": "AllowCloudFrontOAI",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity OAI_ID"
  },
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::nexusai-vkp-packages/*"
}
```

Replace `OAI_ID` with your OAI ID and reapply the policy.

### 5.4 Get CloudFront Domain Name

```bash
aws cloudfront list-distributions --query 'DistributionList.Items[?Comment==`NexusAI VKP Distribution`].DomainName' --output text
```

Use this domain name in school server configuration for VKP downloads.

## Step 6: Bedrock Model Access

### 6.1 Enable Bedrock in Your Region

1. Go to AWS Console → Bedrock
2. Select region: `ap-southeast-1` (Singapore)
3. Click "Model access" in left sidebar
4. Click "Manage model access"
5. Enable: **Amazon Titan Text Embeddings v1**
6. Click "Save changes"

### 6.2 Verify Bedrock Access

```bash
aws bedrock list-foundation-models \
    --region ap-southeast-1 \
    --query 'modelSummaries[?contains(modelId, `titan-embed`)].modelId'
```

Expected output:
```json
[
    "amazon.titan-embed-text-v1"
]
```

### 6.3 Test Bedrock Embedding

Create `test-bedrock.py`:
```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='ap-southeast-1')

response = bedrock.invoke_model(
    modelId='amazon.titan-embed-text-v1',
    body=json.dumps({'inputText': 'Hello, world!'})
)

result = json.loads(response['body'].read())
print(f"Embedding dimension: {len(result['embedding'])}")
print(f"First 5 values: {result['embedding'][:5]}")
```

Run:
```bash
python test-bedrock.py
```

Expected output:
```
Embedding dimension: 1536
First 5 values: [0.123, -0.456, 0.789, ...]
```

## Step 7: Verification and Testing

### 7.1 End-to-End Test

**Test the complete pipeline:**

1. **Upload PDF to S3:**
```bash
aws s3 cp sample-curriculum.pdf s3://nexusai-curriculum-raw/raw/matematika_kelas_10_v1.0.0.pdf
```

2. **Monitor Lambda execution:**
```bash
aws logs tail /aws/lambda/nexusai-curriculum-processor --follow
```

3. **Verify VKP created:**
```bash
aws s3 ls s3://nexusai-vkp-packages/matematika/kelas_10/
```

4. **Download and inspect VKP:**
```bash
aws s3 cp s3://nexusai-vkp-packages/matematika/kelas_10/v1.0.0.vkp vkp-test.json
cat vkp-test.json | jq '.version, .total_chunks, .checksum'
```

### 7.2 Test DynamoDB Access

**Write test telemetry:**
```bash
aws dynamodb put-item \
    --table-name nexusai-metrics \
    --item '{
        "school_id": {"S": "school_test_001"},
        "timestamp": {"N": "'$(date +%s)'"},
        "ttl": {"N": "'$(($(date +%s) + 7776000))'"},
        "total_queries": {"N": "100"},
        "average_latency_ms": {"N": "4500"},
        "model_version": {"S": "llama-3.2-3b-q4"}
    }' \
    --region ap-southeast-1
```

**Read test telemetry:**
```bash
aws dynamodb get-item \
    --table-name nexusai-metrics \
    --key '{"school_id": {"S": "school_test_001"}, "timestamp": {"N": "TIMESTAMP"}}' \
    --region ap-southeast-1
```

Replace `TIMESTAMP` with the timestamp from the put-item command.

### 7.3 Test School Server Access

Create `test-school-server-access.py`:
```python
import boto3
import json

# Use school server credentials
s3 = boto3.client('s3', region_name='ap-southeast-1')
dynamodb = boto3.client('dynamodb', region_name='ap-southeast-1')

# Test S3 read
try:
    response = s3.list_objects_v2(Bucket='nexusai-vkp-packages', MaxKeys=5)
    print(f"✓ S3 access OK - Found {response.get('KeyCount', 0)} objects")
except Exception as e:
    print(f"✗ S3 access failed: {e}")

# Test DynamoDB write
try:
    dynamodb.put_item(
        TableName='nexusai-metrics',
        Item={
            'school_id': {'S': 'test_school'},
            'timestamp': {'N': str(int(time.time()))},
            'total_queries': {'N': '10'}
        }
    )
    print("✓ DynamoDB write OK")
except Exception as e:
    print(f"✗ DynamoDB write failed: {e}")
```

### 7.4 Verification Checklist

- [ ] S3 buckets created and configured
  - [ ] nexusai-curriculum-raw
  - [ ] nexusai-vkp-packages (with versioning)
  - [ ] nexusai-model-distribution
- [ ] DynamoDB tables created
  - [ ] nexusai-schools
  - [ ] nexusai-metrics (with TTL)
- [ ] IAM roles and policies configured
  - [ ] Lambda execution role
  - [ ] School server role/user
- [ ] Lambda function deployed and tested
  - [ ] Function code uploaded
  - [ ] S3 trigger configured
  - [ ] Test PDF processed successfully
- [ ] Bedrock access enabled
  - [ ] Titan embedding model accessible
  - [ ] Test embedding generated
- [ ] CloudFront distribution created (optional)
- [ ] End-to-end pipeline tested
  - [ ] PDF → Lambda → VKP → S3
  - [ ] VKP downloadable by school servers
  - [ ] Telemetry writable to DynamoDB

## Step 8: Monitoring and Maintenance

### 8.1 CloudWatch Dashboards

Create a monitoring dashboard:

```bash
aws cloudwatch put-dashboard \
    --dashboard-name NexusAI-Infrastructure \
    --dashboard-body '{
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
                        [".", "Errors", {"stat": "Sum"}],
                        [".", "Duration", {"stat": "Average"}]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "ap-southeast-1",
                    "title": "Lambda Metrics"
                }
            }
        ]
    }'
```

### 8.2 CloudWatch Alarms

**Lambda Error Alarm:**
```bash
aws cloudwatch put-metric-alarm \
    --alarm-name nexusai-lambda-errors \
    --alarm-description "Alert on Lambda errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --dimensions Name=FunctionName,Value=nexusai-curriculum-processor
```

**DynamoDB Throttle Alarm:**
```bash
aws cloudwatch put-metric-alarm \
    --alarm-name nexusai-dynamodb-throttles \
    --alarm-description "Alert on DynamoDB throttles" \
    --metric-name UserErrors \
    --namespace AWS/DynamoDB \
    --statistic Sum \
    --period 300 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --dimensions Name=TableName,Value=nexusai-metrics
```

### 8.3 Cost Monitoring

**Set up budget alerts:**
```bash
aws budgets create-budget \
    --account-id ACCOUNT_ID \
    --budget '{
        "BudgetName": "NexusAI-Monthly-Budget",
        "BudgetLimit": {
            "Amount": "50",
            "Unit": "USD"
        },
        "TimeUnit": "MONTHLY",
        "BudgetType": "COST"
    }' \
    --notifications-with-subscribers '[
        {
            "Notification": {
                "NotificationType": "ACTUAL",
                "ComparisonOperator": "GREATER_THAN",
                "Threshold": 80
            },
            "Subscribers": [
                {
                    "SubscriptionType": "EMAIL",
                    "Address": "admin@example.com"
                }
            ]
        }
    ]'
```

### 8.4 Regular Maintenance Tasks

**Weekly:**
- Review CloudWatch logs for errors
- Check Lambda execution metrics
- Verify VKP packages are being created
- Monitor DynamoDB item counts

**Monthly:**
- Review AWS costs in Cost Explorer
- Clean up old test data
- Update Lambda function if needed
- Review IAM permissions

**Quarterly:**
- Audit S3 bucket policies
- Review and optimize DynamoDB capacity
- Update Lambda runtime if new version available
- Review CloudWatch alarm thresholds

## Troubleshooting

### Lambda Function Issues

**Problem: Lambda times out**
- **Cause**: Large PDF files or slow Bedrock API
- **Solution**: Increase timeout to 5 minutes (300 seconds)
```bash
aws lambda update-function-configuration \
    --function-name nexusai-curriculum-processor \
    --timeout 300
```

**Problem: Lambda out of memory**
- **Cause**: Large PDF processing
- **Solution**: Increase memory to 2GB
```bash
aws lambda update-function-configuration \
    --function-name nexusai-curriculum-processor \
    --memory-size 2048
```

**Problem: Lambda can't access S3**
- **Cause**: Missing IAM permissions
- **Solution**: Verify IAM role has S3 read/write permissions
```bash
aws iam get-role-policy \
    --role-name NexusAI-Lambda-CurriculumProcessor \
    --policy-name NexusAI-Lambda-Execution-Policy
```

### S3 Issues

**Problem: Access Denied when uploading**
- **Cause**: Bucket policy or IAM permissions
- **Solution**: Check bucket policy and IAM user permissions
```bash
aws s3api get-bucket-policy --bucket nexusai-curriculum-raw
```

**Problem: S3 event not triggering Lambda**
- **Cause**: Missing Lambda permission or incorrect filter
- **Solution**: Verify Lambda permission and event configuration
```bash
aws lambda get-policy --function-name nexusai-curriculum-processor
aws s3api get-bucket-notification-configuration --bucket nexusai-curriculum-raw
```

### DynamoDB Issues

**Problem: ProvisionedThroughputExceededException**
- **Cause**: Too many writes (shouldn't happen with PAY_PER_REQUEST)
- **Solution**: Verify billing mode is PAY_PER_REQUEST
```bash
aws dynamodb describe-table --table-name nexusai-metrics \
    --query 'Table.BillingModeSummary'
```

**Problem: Items not expiring with TTL**
- **Cause**: TTL not enabled or incorrect attribute
- **Solution**: Verify TTL configuration
```bash
aws dynamodb describe-time-to-live --table-name nexusai-metrics
```

### Bedrock Issues

**Problem: AccessDeniedException**
- **Cause**: Model access not enabled or wrong region
- **Solution**: Enable model access in Bedrock console
```bash
aws bedrock list-foundation-models --region ap-southeast-1
```

**Problem: ThrottlingException**
- **Cause**: Too many requests
- **Solution**: Implement exponential backoff in Lambda code
```python
import time
from botocore.exceptions import ClientError

def invoke_bedrock_with_retry(text, max_retries=3):
    for attempt in range(max_retries):
        try:
            return bedrock.invoke_model(...)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                time.sleep(2 ** attempt)
            else:
                raise
```

### CloudFront Issues

**Problem: 403 Forbidden from CloudFront**
- **Cause**: S3 bucket policy doesn't allow OAI
- **Solution**: Update bucket policy with OAI permissions
```bash
aws s3api get-bucket-policy --bucket nexusai-vkp-packages
```

**Problem: Stale content served**
- **Cause**: CloudFront cache not invalidated
- **Solution**: Create invalidation
```bash
aws cloudfront create-invalidation \
    --distribution-id DISTRIBUTION_ID \
    --paths "/*"
```

### IAM Issues

**Problem: School server can't access S3**
- **Cause**: Missing permissions or incorrect credentials
- **Solution**: Verify IAM policy and test credentials
```bash
aws iam get-user-policy \
    --user-name nexusai-school-server \
    --policy-name NexusAI-SchoolServer-Policy

# Test with school server credentials
AWS_PROFILE=school-server aws s3 ls s3://nexusai-vkp-packages/
```

**Problem: Lambda can't invoke Bedrock**
- **Cause**: Missing bedrock:InvokeModel permission
- **Solution**: Add Bedrock permission to Lambda role
```json
{
  "Effect": "Allow",
  "Action": "bedrock:InvokeModel",
  "Resource": "arn:aws:bedrock:ap-southeast-1::foundation-model/amazon.titan-embed-text-v1"
}
```

## Cost Estimation

### Monthly Cost Breakdown (Estimated)

**Assumptions:**
- 100 schools
- 10 curriculum updates per month
- 1000 telemetry writes per school per month
- Average PDF size: 5MB
- Average VKP size: 10MB

#### S3 Storage
- **nexusai-curriculum-raw**: 50 PDFs × 5MB = 250MB
  - Cost: $0.023/GB × 0.25GB = **$0.006/month**
- **nexusai-vkp-packages**: 50 VKPs × 10MB = 500MB
  - Cost: $0.023/GB × 0.5GB = **$0.012/month**
- **nexusai-model-distribution**: 5GB (one-time)
  - Cost: $0.023/GB × 5GB = **$0.115/month**

**S3 Total: ~$0.13/month**

#### Lambda
- **Invocations**: 10 per month
- **Duration**: 60 seconds average × 1GB memory
- **Compute**: 10 × 60 × 1GB = 600 GB-seconds
  - Cost: $0.0000166667/GB-second × 600 = **$0.01/month**
- **Requests**: 10 requests
  - Cost: $0.20/1M requests × 0.00001M = **$0.000002/month**

**Lambda Total: ~$0.01/month**

#### Bedrock (Titan Embeddings)
- **Chunks per PDF**: ~100 chunks
- **Total chunks**: 10 PDFs × 100 = 1000 chunks
- **Tokens**: 1000 chunks × 200 tokens = 200K tokens
- **Cost**: $0.0001/1K tokens × 200 = **$0.02/month**

**Bedrock Total: ~$0.02/month**

#### DynamoDB
- **nexusai-schools**: 100 items, minimal reads/writes
  - Cost: **$0.01/month**
- **nexusai-metrics**: 100 schools × 1000 writes = 100K writes
  - Cost: $1.25/million writes × 0.1M = **$0.125/month**
  - Storage: 100K items × 1KB = 100MB
  - Cost: $0.25/GB × 0.1GB = **$0.025/month**

**DynamoDB Total: ~$0.16/month**

#### CloudFront (Optional)
- **Data transfer**: 100 schools × 10 downloads × 10MB = 10GB
- **Cost**: $0.085/GB × 10GB = **$0.85/month**
- **Requests**: 1000 requests
- **Cost**: $0.01/10K requests × 0.1 = **$0.001/month**

**CloudFront Total: ~$0.85/month** (optional)

### Total Monthly Cost

**Without CloudFront**: ~$0.33/month (~$4/year)
**With CloudFront**: ~$1.18/month (~$14/year)

**Note**: Costs scale with usage. Monitor actual costs in AWS Cost Explorer.

## Security Best Practices

### 1. Enable MFA for Root Account
```bash
# Enable MFA in AWS Console:
# Account → Security Credentials → Multi-factor authentication (MFA)
```

### 2. Use IAM Roles Instead of Access Keys
- For EC2 instances: Attach IAM role
- For Lambda: Use execution role
- For local development: Use temporary credentials with AWS SSO

### 3. Rotate Access Keys Regularly
```bash
# Create new access key
aws iam create-access-key --user-name nexusai-school-server

# Delete old access key
aws iam delete-access-key \
    --user-name nexusai-school-server \
    --access-key-id OLD_ACCESS_KEY_ID
```

### 4. Enable CloudTrail for Audit Logging
```bash
aws cloudtrail create-trail \
    --name nexusai-audit-trail \
    --s3-bucket-name nexusai-cloudtrail-logs

aws cloudtrail start-logging --name nexusai-audit-trail
```

### 5. Enable S3 Bucket Encryption
```bash
aws s3api put-bucket-encryption \
    --bucket nexusai-vkp-packages \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'
```

### 6. Restrict S3 Bucket Access
- Block all public access (already configured)
- Use bucket policies with least privilege
- Enable S3 access logging

### 7. Use VPC Endpoints (Optional)
For school servers in AWS VPC:
```bash
aws ec2 create-vpc-endpoint \
    --vpc-id vpc-XXXXXXXX \
    --service-name com.amazonaws.ap-southeast-1.s3 \
    --route-table-ids rtb-XXXXXXXX
```

### 8. Enable DynamoDB Point-in-Time Recovery
```bash
aws dynamodb update-continuous-backups \
    --table-name nexusai-metrics \
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

### 9. Review IAM Policies Regularly
```bash
# Use IAM Access Analyzer
aws accessanalyzer create-analyzer \
    --analyzer-name nexusai-analyzer \
    --type ACCOUNT
```

### 10. Enable AWS Config for Compliance
```bash
aws configservice put-configuration-recorder \
    --configuration-recorder name=nexusai-config,roleARN=arn:aws:iam::ACCOUNT_ID:role/config-role

aws configservice put-delivery-channel \
    --delivery-channel name=nexusai-channel,s3BucketName=nexusai-config-logs
```

## Automation Script

For convenience, here's a complete setup script that automates the entire AWS infrastructure setup.

### setup-aws-infrastructure.py

```python
#!/usr/bin/env python3
"""
AWS Infrastructure Setup Script for OpenClass Nexus AI
Automates creation of S3 buckets, DynamoDB tables, IAM roles, and Lambda function
"""

import boto3
import json
import time
import sys
from botocore.exceptions import ClientError

# Configuration
REGION = 'ap-southeast-1'
ACCOUNT_ID = boto3.client('sts').get_caller_identity()['Account']

# Initialize clients
s3 = boto3.client('s3', region_name=REGION)
dynamodb = boto3.client('dynamodb', region_name=REGION)
iam = boto3.client('iam')
lambda_client = boto3.client('lambda', region_name=REGION)

def print_step(step, message):
    print(f"\n{'='*70}")
    print(f"Step {step}: {message}")
    print('='*70)

def create_s3_buckets():
    """Create S3 buckets for curriculum and VKP storage"""
    print_step(1, "Creating S3 Buckets")
    
    buckets = [
        'nexusai-curriculum-raw',
        'nexusai-vkp-packages',
        'nexusai-model-distribution'
    ]
    
    for bucket in buckets:
        try:
            if REGION == 'us-east-1':
                s3.create_bucket(Bucket=bucket)
            else:
                s3.create_bucket(
                    Bucket=bucket,
                    CreateBucketConfiguration={'LocationConstraint': REGION}
                )
            print(f"✓ Created bucket: {bucket}")
            
            # Enable versioning for VKP packages
            if 'vkp' in bucket:
                s3.put_bucket_versioning(
                    Bucket=bucket,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                print(f"  ✓ Enabled versioning for {bucket}")
            
            # Block public access
            s3.put_public_access_block(
                Bucket=bucket,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            print(f"  ✓ Blocked public access for {bucket}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                print(f"⚠ Bucket {bucket} already exists")
            else:
                print(f"✗ Error creating {bucket}: {e}")
                return False
    
    return True
```

def create_dynamodb_tables():
    """Create DynamoDB tables for schools and metrics"""
    print_step(2, "Creating DynamoDB Tables")
    
    tables = [
        {
            'TableName': 'nexusai-schools',
            'KeySchema': [
                {'AttributeName': 'school_id', 'KeyType': 'HASH'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'school_id', 'AttributeType': 'S'}
            ]
        },
        {
            'TableName': 'nexusai-metrics',
            'KeySchema': [
                {'AttributeName': 'school_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'school_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ]
        }
    ]
    
    for table_config in tables:
        try:
            dynamodb.create_table(
                **table_config,
                BillingMode='PAY_PER_REQUEST'
            )
            print(f"✓ Created table: {table_config['TableName']}")
            
            # Wait for table to be active
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_config['TableName'])
            
            # Enable TTL for metrics table
            if table_config['TableName'] == 'nexusai-metrics':
                dynamodb.update_time_to_live(
                    TableName='nexusai-metrics',
                    TimeToLiveSpecification={
                        'Enabled': True,
                        'AttributeName': 'ttl'
                    }
                )
                print(f"  ✓ Enabled TTL for nexusai-metrics")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠ Table {table_config['TableName']} already exists")
            else:
                print(f"✗ Error creating table: {e}")
                return False
    
    return True

def create_iam_roles():
    """Create IAM roles for Lambda and school servers"""
    print_step(3, "Creating IAM Roles and Policies")
    
    # Lambda execution role
    lambda_trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        iam.create_role(
            RoleName='NexusAI-Lambda-CurriculumProcessor',
            AssumeRolePolicyDocument=json.dumps(lambda_trust_policy)
        )
        print("✓ Created Lambda execution role")
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("⚠ Lambda role already exists")
        else:
            print(f"✗ Error creating Lambda role: {e}")
            return False
    
    # Attach policies to Lambda role
    # (Implementation continues...)
    
    return True

if __name__ == '__main__':
    print("AWS Infrastructure Setup for OpenClass Nexus AI")
    print(f"Region: {REGION}")
    print(f"Account: {ACCOUNT_ID}")
    
    if not create_s3_buckets():
        sys.exit(1)
    
    if not create_dynamodb_tables():
        sys.exit(1)
    
    if not create_iam_roles():
        sys.exit(1)
    
    print("\n" + "="*70)
    print("✓ AWS Infrastructure Setup Complete!")
    print("="*70)
```

**Usage:**
```bash
python setup-aws-infrastructure.py
```

**Note**: This is a simplified version. The complete script is available in the repository at `scripts/setup_aws_infrastructure.py`.

## Related Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide for school servers
- **[CLOUD_EMBEDDING_GUIDE.md](CLOUD_EMBEDDING_GUIDE.md)** - Guide for generating embeddings with Bedrock
- **[AWS_CONSOLE_MONITORING.md](AWS_CONSOLE_MONITORING.md)** - Monitoring AWS services via console
- **[S3_SYNC_GUIDE.md](S3_SYNC_GUIDE.md)** - Syncing embeddings with S3
- **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - Overall system architecture

## Quick Reference

### AWS Service Endpoints
- **S3**: `https://s3.console.aws.amazon.com/s3/`
- **DynamoDB**: `https://console.aws.amazon.com/dynamodb/`
- **Lambda**: `https://console.aws.amazon.com/lambda/`
- **IAM**: `https://console.aws.amazon.com/iam/`
- **Bedrock**: `https://console.aws.amazon.com/bedrock/`
- **CloudWatch**: `https://console.aws.amazon.com/cloudwatch/`
- **Cost Explorer**: `https://console.aws.amazon.com/cost-management/`

### Key Resource Names
- **S3 Buckets**: 
  - `nexusai-curriculum-raw`
  - `nexusai-vkp-packages`
  - `nexusai-model-distribution`
- **DynamoDB Tables**:
  - `nexusai-schools`
  - `nexusai-metrics`
- **Lambda Function**: `nexusai-curriculum-processor`
- **IAM Roles**:
  - `NexusAI-Lambda-CurriculumProcessor`
  - `NexusAI-SchoolServer-Role`

### Common Commands

**List all resources:**
```bash
aws s3 ls
aws dynamodb list-tables --region ap-southeast-1
aws lambda list-functions --region ap-southeast-1
aws iam list-roles | grep NexusAI
```

**Check costs:**
```bash
aws ce get-cost-and-usage \
    --time-period Start=2026-02-20,End=2026-02-31 \
    --granularity MONTHLY \
    --metrics BlendedCost
```

**View Lambda logs:**
```bash
aws logs tail /aws/lambda/nexusai-curriculum-processor --follow
```

## Support and Feedback

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review AWS service health: https://status.aws.amazon.com/
3. Consult AWS documentation: https://docs.aws.amazon.com/
4. Open an issue in the project repository

---

**Last Updated**: Februari 2026  
**Version**: 1.0.0  
**Maintained by**: OpenClass Nexus AI Team
