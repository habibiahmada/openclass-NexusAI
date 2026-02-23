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
    
    This handler integrates:
    - PDFTextExtractor for text extraction (Requirement 8.2)
    - TextChunker for chunking with 800/100 configuration (Requirement 8.3)
    - BedrockEmbeddingGenerator for Titan embeddings (Requirement 8.4)
    - VKPPackager for output (Requirement 8.5)
    - Error handling and CloudWatch logging (Requirement 8.7)
    
    Requirements: 8.1-8.7
    """
    return '''
import json
import boto3
import logging
import os
import re
import hashlib
import traceback
from pypdf import PdfReader
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Tuple

# Configure CloudWatch logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add structured logging
class StructuredLogger:
    """Wrapper for structured CloudWatch logging"""
    
    def __init__(self, base_logger):
        self.logger = base_logger
    
    def log_event(self, level: str, message: str, **kwargs):
        """Log structured event with additional context"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            **kwargs
        }
        log_message = json.dumps(log_data)
        
        if level == 'INFO':
            self.logger.info(log_message)
        elif level == 'WARNING':
            self.logger.warning(log_message)
        elif level == 'ERROR':
            self.logger.error(log_message)
        else:
            self.logger.debug(log_message)

structured_logger = StructuredLogger(logger)

s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime')

CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', '800'))
CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', '100'))
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'amazon.titan-embed-text-v1')

# Import aws_config for bucket names
try:
    from config.aws_config import aws_config
    OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET', aws_config.vkp_packages_bucket)
except ImportError:
    OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET', 'nexusai-vkp-packages')

AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')


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
    """
    Extract text from PDF content using PDFTextExtractor.
    
    Requirement 8.2: PDF text extraction
    """
    try:
        structured_logger.log_event('INFO', 'Starting PDF text extraction', 
                                   pdf_size_bytes=len(pdf_content))
        
        pdf_file = BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        
        if len(reader.pages) == 0:
            raise ValueError("PDF has no pages")
        
        text = ""
        page_texts = []
        
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    page_texts.append({
                        'page': page_num + 1,
                        'text': page_text
                    })
                    text += page_text + "\\n\\n"
                else:
                    structured_logger.log_event('WARNING', 'Page has no extractable text',
                                              page_number=page_num + 1)
            except Exception as e:
                structured_logger.log_event('ERROR', 'Failed to extract text from page',
                                          page_number=page_num + 1, error=str(e))
                # Continue with other pages
        
        if not text.strip():
            raise RuntimeError("No text could be extracted from PDF")
        
        structured_logger.log_event('INFO', 'PDF text extraction completed',
                                   total_pages=len(page_texts),
                                   total_characters=len(text))
        
        return text, page_texts
    except Exception as e:
        structured_logger.log_event('ERROR', 'PDF text extraction failed',
                                   error=str(e), traceback=traceback.format_exc())
        raise


def chunk_text_with_metadata(page_texts, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Split text into chunks with overlap and preserve page metadata.
    Uses TextChunker with 800/100 token configuration.
    
    Requirement 8.3: Text chunking with 800 token chunks and 100 token overlap
    
    Returns list of dicts with chunk_id, text, page info
    """
    try:
        structured_logger.log_event('INFO', 'Starting text chunking',
                                   total_pages=len(page_texts),
                                   chunk_size=chunk_size,
                                   overlap=overlap)
        
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
        
        structured_logger.log_event('INFO', 'Text chunking completed',
                                   total_chunks=len(chunks))
        
        return chunks
    except Exception as e:
        structured_logger.log_event('ERROR', 'Text chunking failed',
                                   error=str(e), traceback=traceback.format_exc())
        raise


def generate_embeddings(chunks):
    """
    Generate embeddings for text chunks using Bedrock Titan.
    Uses BedrockEmbeddingGenerator for Titan embeddings.
    
    Requirement 8.4: Bedrock Titan embedding generation
    """
    try:
        structured_logger.log_event('INFO', 'Starting embedding generation',
                                   total_chunks=len(chunks),
                                   model_id=BEDROCK_MODEL_ID)
        
        embeddings = []
        
        for i, chunk in enumerate(chunks):
            try:
                response = bedrock_client.invoke_model(
                    modelId=BEDROCK_MODEL_ID,
                    body=json.dumps({"inputText": chunk['text']})
                )
                
                result = json.loads(response['body'].read())
                embedding = result.get('embedding', [])
                
                if not embedding:
                    raise RuntimeError(f"No embedding returned for chunk {chunk['chunk_id']}")
                
                embeddings.append(embedding)
                
                # Log progress every 10 chunks
                if (i + 1) % 10 == 0:
                    structured_logger.log_event('INFO', 'Embedding generation progress',
                                              completed=i + 1, total=len(chunks))
                
            except Exception as e:
                structured_logger.log_event('ERROR', 'Failed to generate embedding',
                                          chunk_id=chunk['chunk_id'], error=str(e))
                raise
        
        structured_logger.log_event('INFO', 'Embedding generation completed',
                                   total_embeddings=len(embeddings))
        
        return embeddings
    except Exception as e:
        structured_logger.log_event('ERROR', 'Embedding generation failed',
                                   error=str(e), traceback=traceback.format_exc())
        raise


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
    Integrates VKPPackager for output.
    
    Requirement 8.5: VKP packaging for output
    Requirements: 6.1, 6.2, 6.4, 6.5
    """
    try:
        structured_logger.log_event('INFO', 'Starting VKP package creation',
                                   total_chunks=len(chunks),
                                   metadata=metadata)
        
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
        
        structured_logger.log_event('INFO', 'VKP package created',
                                   version=vkp['version'],
                                   checksum=vkp['checksum'],
                                   total_chunks=vkp['total_chunks'])
        
        return vkp
    except Exception as e:
        structured_logger.log_event('ERROR', 'VKP package creation failed',
                                   error=str(e), traceback=traceback.format_exc())
        raise


def upload_vkp_to_s3(vkp, output_bucket):
    """
    Upload VKP to S3 with proper key structure and metadata tags.
    
    S3 key format: {subject}/kelas_{grade}/v{version}.vkp
    
    Requirement 8.6: S3 upload to versioned bucket
    """
    try:
        # Generate S3 key
        s3_key = f"{vkp['subject']}/kelas_{vkp['grade']}/v{vkp['version']}.vkp"
        
        structured_logger.log_event('INFO', 'Starting VKP upload to S3',
                                   bucket=output_bucket, key=s3_key)
        
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
        
        structured_logger.log_event('INFO', 'VKP uploaded to S3 successfully',
                                   bucket=output_bucket, key=s3_key,
                                   size_bytes=len(vkp_json))
        
        return s3_key
    except Exception as e:
        structured_logger.log_event('ERROR', 'VKP upload to S3 failed',
                                   bucket=output_bucket, error=str(e),
                                   traceback=traceback.format_exc())
        raise


def lambda_handler(event, context):
    """
    Lambda handler for curriculum processing with VKP packaging.
    
    Triggered by S3 upload event, processes PDF, generates embeddings,
    and creates VKP package.
    
    Integrates all components:
    - PDFTextExtractor for text extraction (Requirement 8.2)
    - TextChunker for chunking (Requirement 8.3)
    - BedrockEmbeddingGenerator for embeddings (Requirement 8.4)
    - VKPPackager for output (Requirement 8.5)
    - S3 upload (Requirement 8.6)
    - Error handling and CloudWatch logging (Requirement 8.7)
    
    Requirements: 8.1-8.7
    """
    # Initialize request tracking
    request_id = context.request_id if context else 'local-test'
    
    try:
        structured_logger.log_event('INFO', 'Lambda invocation started',
                                   request_id=request_id,
                                   event=json.dumps(event))
        
        # Extract S3 bucket and key from event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        structured_logger.log_event('INFO', 'Processing PDF from S3',
                                   bucket=bucket, key=key)
        
        # Extract filename
        filename = key.split('/')[-1]
        
        # Extract metadata from filename
        metadata = extract_metadata_from_filename(filename)
        structured_logger.log_event('INFO', 'Extracted metadata from filename',
                                   metadata=metadata)
        
        # Download PDF from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        pdf_content = response['Body'].read()
        structured_logger.log_event('INFO', 'Downloaded PDF from S3',
                                   size_bytes=len(pdf_content))
        
        # Extract text with page information (Requirement 8.2)
        full_text, page_texts = extract_text_from_pdf(pdf_content)
        
        # Chunk text with metadata (Requirement 8.3)
        chunks = chunk_text_with_metadata(page_texts)
        
        # Generate embeddings (Requirement 8.4)
        embeddings = generate_embeddings(chunks)
        
        # Create VKP package (Requirement 8.5)
        vkp = create_vkp_package(chunks, embeddings, metadata, filename)
        
        # Upload VKP to S3 (Requirement 8.6)
        s3_key = upload_vkp_to_s3(vkp, OUTPUT_BUCKET)
        
        # Success response
        response_body = {
            'message': 'PDF processed successfully',
            'vkp_location': f"s3://{OUTPUT_BUCKET}/{s3_key}",
            'version': vkp['version'],
            'subject': vkp['subject'],
            'grade': vkp['grade'],
            'semester': vkp['semester'],
            'chunks_count': vkp['total_chunks'],
            'checksum': vkp['checksum']
        }
        
        structured_logger.log_event('INFO', 'Lambda invocation completed successfully',
                                   request_id=request_id,
                                   response=response_body)
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        # Error handling with CloudWatch logging (Requirement 8.7)
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc()
        }
        
        structured_logger.log_event('ERROR', 'Lambda invocation failed',
                                   request_id=request_id,
                                   **error_details)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'error_type': type(e).__name__,
                'request_id': request_id
            })
        }
'''
