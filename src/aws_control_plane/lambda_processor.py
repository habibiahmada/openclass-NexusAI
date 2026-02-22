"""
Lambda Curriculum Processor Module

Handles Lambda function packaging and deployment for PDF processing.
"""

import json
import logging
import os
import zipfile
import tempfile
from typing import Optional, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class LambdaProcessorPackager:
    """Packages Lambda function with dependencies"""

    def __init__(self, region: str):
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.region = region

    def create_lambda_package(
        self,
        output_path: str,
        handler_code: str,
        dependencies: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Create a zip package for Lambda deployment.
        
        Args:
            output_path: Path where to save the zip file
            handler_code: Python code for lambda_function.py
            dependencies: Dict of {package_name: version} to include
        """
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write handler code
                handler_path = os.path.join(tmpdir, 'lambda_function.py')
                with open(handler_path, 'w') as f:
                    f.write(handler_code)

                # Create zip file
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(handler_path, 'lambda_function.py')

                logger.info(f"Created Lambda package at {output_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to create Lambda package: {e}")
            return False

    def deploy_lambda_function(
        self,
        function_name: str,
        role_arn: str,
        zip_file_path: str,
        handler: str = "lambda_function.lambda_handler",
        runtime: str = "python3.11",
        timeout: int = 300,
        memory_size: int = 1024,
        environment_variables: Optional[Dict[str, str]] = None
    ) -> bool:
        """Deploy Lambda function"""
        try:
            # Check if function exists
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                logger.info(f"Lambda function '{function_name}' already exists")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise

            # Read zip file
            if not os.path.exists(zip_file_path):
                logger.error(f"Zip file not found: {zip_file_path}")
                return False

            with open(zip_file_path, 'rb') as f:
                zip_content = f.read()

            # Create function
            params = {
                'FunctionName': function_name,
                'Runtime': runtime,
                'Role': role_arn,
                'Handler': handler,
                'Code': {'ZipFile': zip_content},
                'Timeout': timeout,
                'MemorySize': memory_size,
                'Description': 'Curriculum PDF processor'
            }

            if environment_variables:
                params['Environment'] = {'Variables': environment_variables}

            self.lambda_client.create_function(**params)
            logger.info(f"Deployed Lambda function '{function_name}'")
            return True
        except ClientError as e:
            logger.error(f"Failed to deploy Lambda function: {e}")
            return False

    def update_lambda_environment(
        self,
        function_name: str,
        environment_variables: Dict[str, str]
    ) -> bool:
        """Update Lambda function environment variables"""
        try:
            self.lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={'Variables': environment_variables}
            )
            logger.info(f"Updated environment variables for '{function_name}'")
            return True
        except ClientError as e:
            logger.error(f"Failed to update Lambda environment: {e}")
            return False


def create_curriculum_processor_handler() -> str:
    """
    Create the Lambda handler code for curriculum processing.
    Returns Python code as string.
    """
    return '''
import json
import boto3
import logging
from pypdf import PdfReader
from io import BytesIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime')

CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', '800'))
CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', '100'))
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'amazon.titan-embed-text-v1')
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET', 'nexusai-vkp-packages')


def extract_text_from_pdf(pdf_content):
    """Extract text from PDF content"""
    try:
        pdf_file = BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into chunks with overlap"""
    chunks = []
    words = text.split()
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks


def generate_embeddings(chunks):
    """Generate embeddings for text chunks using Bedrock"""
    embeddings = []
    
    for chunk in chunks:
        try:
            response = bedrock_client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=json.dumps({"inputText": chunk})
            )
            
            result = json.loads(response['body'].read())
            embedding = result.get('embedding', [])
            embeddings.append(embedding)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    return embeddings


def create_vkp_package(chunks, embeddings, metadata):
    """Create VKP package"""
    vkp = {
        "version": metadata.get('version', '1.0.0'),
        "subject": metadata.get('subject', 'unknown'),
        "grade": metadata.get('grade', 0),
        "semester": metadata.get('semester', 1),
        "created_at": metadata.get('created_at', ''),
        "embedding_model": BEDROCK_MODEL_ID,
        "chunk_config": {
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP
        },
        "chunks": [
            {
                "chunk_id": f"chunk_{i}",
                "text": chunk,
                "embedding": embedding,
                "metadata": {
                    "page": i,
                    "section": metadata.get('section', 'general')
                }
            }
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ],
        "total_chunks": len(chunks),
        "source_files": metadata.get('source_files', [])
    }
    
    # Calculate checksum
    import hashlib
    vkp_json = json.dumps(vkp, sort_keys=True)
    checksum = hashlib.sha256(vkp_json.encode()).hexdigest()
    vkp['checksum'] = f"sha256:{checksum}"
    
    return vkp


def lambda_handler(event, context):
    """Lambda handler for curriculum processing"""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract S3 bucket and key from event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        logger.info(f"Processing PDF: s3://{bucket}/{key}")
        
        # Download PDF from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        pdf_content = response['Body'].read()
        
        # Extract text
        text = extract_text_from_pdf(pdf_content)
        logger.info(f"Extracted {len(text)} characters from PDF")
        
        # Chunk text
        chunks = chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Generate embeddings
        embeddings = generate_embeddings(chunks)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Extract metadata from filename
        filename = key.split('/')[-1]
        metadata = {
            'source_files': [filename],
            'subject': 'curriculum',
            'grade': 11,
            'semester': 1,
            'section': 'general'
        }
        
        # Create VKP package
        vkp = create_vkp_package(chunks, embeddings, metadata)
        
        # Upload VKP to output bucket
        output_key = f"vkp/{filename.replace('.pdf', '.json')}"
        s3_client.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=output_key,
            Body=json.dumps(vkp),
            ContentType='application/json'
        )
        
        logger.info(f"Uploaded VKP to s3://{OUTPUT_BUCKET}/{output_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'PDF processed successfully',
                'vkp_location': f"s3://{OUTPUT_BUCKET}/{output_key}",
                'chunks_count': len(chunks)
            })
        }
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
'''
