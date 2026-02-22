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
    Create the Lambda handler code for curriculum processing with VKP packaging.
    Returns Python code as string.
    
    Requirements: 8.5, 8.6
    """
    return '''
import json
import boto3
import logging
import os
import re
import hashlib
from pypdf import PdfReader
from io import BytesIO
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime')

CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', '800'))
CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', '100'))
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'amazon.titan-embed-text-v1')
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET', 'nexusai-vkp-packages')


def extract_metadata_from_filename(filename):
    """
    Extract metadata from PDF filename.
    
    Expected format: {Subject}_Kelas_{Grade}_Semester_{Semester}_v{Version}.pdf
    Example: Matematika_Kelas_10_Semester_1_v1.0.0.pdf
    
    Returns dict with subject, grade, semester, version
    """
    try:
        # Remove .pdf extension
        name = filename.replace('.pdf', '')
        
        # Try to extract using regex pattern
        pattern = r'([A-Za-z]+)_Kelas_(\d+)_Semester_(\d+)_v(\d+\.\d+\.\d+)'
        match = re.match(pattern, name)
        
        if match:
            subject = match.group(1).lower()
            grade = int(match.group(2))
            semester = int(match.group(3))
            version = match.group(4)
            
            return {
                'subject': subject,
                'grade': grade,
                'semester': semester,
                'version': version
            }
        else:
            # Fallback to defaults if pattern doesn't match
            logger.warning(f"Could not parse filename: {filename}, using defaults")
            return {
                'subject': 'unknown',
                'grade': 10,
                'semester': 1,
                'version': '1.0.0'
            }
    except Exception as e:
        logger.error(f"Error extracting metadata from filename: {e}")
        return {
            'subject': 'unknown',
            'grade': 10,
            'semester': 1,
            'version': '1.0.0'
        }


def extract_text_from_pdf(pdf_content):
    """Extract text from PDF content"""
    try:
        pdf_file = BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        text = ""
        page_texts = []
        
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            page_texts.append({
                'page': page_num + 1,
                'text': page_text
            })
            text += page_text + "\\n\\n"
        
        return text, page_texts
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise


def chunk_text_with_metadata(page_texts, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Split text into chunks with overlap and preserve page metadata.
    
    Returns list of dicts with chunk_id, text, page info
    """
    chunks = []
    chunk_id = 0
    
    for page_info in page_texts:
        page_num = page_info['page']
        text = page_info['text']
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_text = ' '.join(words[i:i + chunk_size])
            if chunk_text.strip():
                chunks.append({
                    'chunk_id': f"chunk_{chunk_id:04d}",
                    'text': chunk_text,
                    'page': page_num
                })
                chunk_id += 1
    
    return chunks


def generate_embeddings(chunks):
    """Generate embeddings for text chunks using Bedrock"""
    embeddings = []
    
    for chunk in chunks:
        try:
            response = bedrock_client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=json.dumps({"inputText": chunk['text']})
            )
            
            result = json.loads(response['body'].read())
            embedding = result.get('embedding', [])
            embeddings.append(embedding)
        except Exception as e:
            logger.error(f"Failed to generate embedding for chunk {chunk['chunk_id']}: {e}")
            raise
    
    return embeddings


def calculate_vkp_checksum(vkp_dict):
    """
    Calculate SHA256 checksum for VKP integrity verification.
    
    Checksum is calculated from JSON with sorted keys, excluding checksum field.
    """
    # Remove checksum field if present
    vkp_copy = vkp_dict.copy()
    vkp_copy.pop('checksum', None)
    
    # Serialize with sorted keys
    vkp_json = json.dumps(vkp_copy, sort_keys=True, ensure_ascii=False)
    
    # Calculate SHA256
    hash_obj = hashlib.sha256(vkp_json.encode('utf-8'))
    checksum = f"sha256:{hash_obj.hexdigest()}"
    
    return checksum


def create_vkp_package(chunks, embeddings, metadata, filename):
    """
    Create VKP package with proper structure and checksum.
    
    Requirements: 6.1, 6.2, 6.4, 6.5
    """
    # Build chunks with embeddings
    vkp_chunks = []
    for chunk, embedding in zip(chunks, embeddings):
        vkp_chunks.append({
            'chunk_id': chunk['chunk_id'],
            'text': chunk['text'],
            'embedding': embedding,
            'metadata': {
                'page': chunk['page'],
                'section': metadata.get('section', 'general'),
                'topic': metadata.get('topic', 'general')
            }
        })
    
    # Create VKP structure
    vkp = {
        'version': metadata['version'],
        'subject': metadata['subject'],
        'grade': metadata['grade'],
        'semester': metadata['semester'],
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'embedding_model': BEDROCK_MODEL_ID,
        'chunk_config': {
            'chunk_size': CHUNK_SIZE,
            'chunk_overlap': CHUNK_OVERLAP
        },
        'chunks': vkp_chunks,
        'total_chunks': len(vkp_chunks),
        'source_files': [filename],
        'checksum': ''  # Will be calculated
    }
    
    # Calculate and set checksum
    vkp['checksum'] = calculate_vkp_checksum(vkp)
    
    return vkp


def upload_vkp_to_s3(vkp, output_bucket):
    """
    Upload VKP to S3 with proper key structure and metadata tags.
    
    S3 key format: {subject}/kelas_{grade}/v{version}.vkp
    Requirements: 8.6
    """
    # Generate S3 key
    s3_key = f"{vkp['subject']}/kelas_{vkp['grade']}/v{vkp['version']}.vkp"
    
    # Serialize VKP
    vkp_json = json.dumps(vkp, indent=2, ensure_ascii=False)
    
    # Upload with metadata tags
    s3_client.put_object(
        Bucket=output_bucket,
        Key=s3_key,
        Body=vkp_json.encode('utf-8'),
        ContentType='application/json',
        Metadata={
            'version': vkp['version'],
            'subject': vkp['subject'],
            'grade': str(vkp['grade']),
            'semester': str(vkp['semester']),
            'total_chunks': str(vkp['total_chunks']),
            'checksum': vkp['checksum']
        }
    )
    
    logger.info(f"Uploaded VKP to s3://{output_bucket}/{s3_key}")
    return s3_key


def lambda_handler(event, context):
    """
    Lambda handler for curriculum processing with VKP packaging.
    
    Triggered by S3 upload event, processes PDF, generates embeddings,
    and creates VKP package.
    
    Requirements: 8.1-8.7
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract S3 bucket and key from event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        logger.info(f"Processing PDF: s3://{bucket}/{key}")
        
        # Extract filename
        filename = key.split('/')[-1]
        
        # Extract metadata from filename
        metadata = extract_metadata_from_filename(filename)
        logger.info(f"Extracted metadata: {metadata}")
        
        # Download PDF from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        pdf_content = response['Body'].read()
        logger.info(f"Downloaded PDF ({len(pdf_content)} bytes)")
        
        # Extract text with page information
        full_text, page_texts = extract_text_from_pdf(pdf_content)
        logger.info(f"Extracted {len(full_text)} characters from {len(page_texts)} pages")
        
        # Chunk text with metadata
        chunks = chunk_text_with_metadata(page_texts)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Generate embeddings
        embeddings = generate_embeddings(chunks)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Create VKP package
        vkp = create_vkp_package(chunks, embeddings, metadata, filename)
        logger.info(f"Created VKP package v{vkp['version']} with checksum {vkp['checksum']}")
        
        # Upload VKP to S3
        s3_key = upload_vkp_to_s3(vkp, OUTPUT_BUCKET)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'PDF processed successfully',
                'vkp_location': f"s3://{OUTPUT_BUCKET}/{s3_key}",
                'version': vkp['version'],
                'subject': vkp['subject'],
                'grade': vkp['grade'],
                'semester': vkp['semester'],
                'chunks_count': vkp['total_chunks'],
                'checksum': vkp['checksum']
            })
        }
    except Exception as e:
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
'''
