"""
Bedrock embedding strategy using AWS Bedrock Titan model.
"""

import json
import time
from typing import List
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.exceptions import ClientError

from .embedding_strategy import EmbeddingStrategy
from .strategy_metrics import StrategyMetrics, MetricsTracker

logger = logging.getLogger(__name__)


class BedrockEmbeddingStrategy(EmbeddingStrategy):
    """Embedding strategy using AWS Bedrock Titan Text Embeddings model"""
    
    def __init__(self, model_id: str = 'amazon.titan-embed-text-v1', region: str = 'us-east-1', timeout: int = 30):
        """Initialize Bedrock embedding strategy.
        
        Args:
            model_id: Bedrock model identifier (default: amazon.titan-embed-text-v1)
            region: AWS region (default: us-east-1)
            timeout: Request timeout in seconds (default: 30)
        """
        self.model_id = model_id
        self.region = region
        self.timeout = timeout
        self.max_retries = 3
        self.metrics = StrategyMetrics()
        
        # Initialize Bedrock client
        try:
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=region
            )
            logger.info(f"Initialized BedrockEmbeddingStrategy with model: {model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            self.client = None
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text using Bedrock Titan.
        
        Args:
            text: Input text to embed
            
        Returns:
            1536-dimensional embedding vector
            
        Raises:
            ValueError: If text is empty
            Exception: If API call fails after retries
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")
        
        if not self.client:
            raise Exception("Bedrock client not initialized")
        
        # Track metrics
        with MetricsTracker(self.metrics):
            # Prepare request body
            body = json.dumps({
                "inputText": text
            })
            
            # Try with exponential backoff
            for attempt in range(self.max_retries):
                try:
                    response = self.client.invoke_model(
                        modelId=self.model_id,
                        body=body,
                        contentType='application/json',
                        accept='application/json'
                    )
                    
                    # Parse response
                    response_body = json.loads(response['body'].read())
                    embedding = response_body.get('embedding')
                    
                    if not embedding:
                        raise Exception("No embedding in response")
                    
                    return embedding
                    
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    
                    # Handle throttling with exponential backoff
                    if error_code == 'ThrottlingException':
                        if attempt < self.max_retries - 1:
                            wait_time = 2 ** attempt  # 1, 2, 4 seconds
                            logger.warning(
                                f"Rate limited, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                            )
                            time.sleep(wait_time)
                            continue
                        else:
                            raise Exception(f"Rate limit exceeded after {self.max_retries} retries") from e
                    
                    # Handle other service errors
                    elif error_code in ['ServiceException', 'InternalServerException']:
                        if attempt < self.max_retries - 1:
                            wait_time = 2 ** attempt
                            logger.warning(
                                f"Service error, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                            )
                            time.sleep(wait_time)
                            continue
                        else:
                            raise Exception(f"Service error after {self.max_retries} retries: {e}") from e
                    
                    # Other errors - don't retry
                    else:
                        raise Exception(f"Bedrock API error: {e}") from e
                
                except Exception as e:
                    # Network timeouts and other errors
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Error occurred, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries}): {e}"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"Failed after {self.max_retries} retries: {e}") from e
            
            raise Exception("Unexpected error: max retries reached without success")
    
    def batch_generate(self, texts: List[str], max_workers: int = 10) -> List[List[float]]:
        """Generate embeddings for multiple texts with parallel processing.
        
        Args:
            texts: List of input texts to embed
            max_workers: Maximum number of parallel workers (default: 10)
            
        Returns:
            List of 1536-dimensional embedding vectors
            
        Raises:
            ValueError: If texts list is empty
            Exception: If API calls fail
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        logger.info(f"Processing {len(texts)} texts with Bedrock Titan using {max_workers} parallel workers")
        
        embeddings = [None] * len(texts)
        
        def process_text(index: int, text: str):
            """Process a single text and return its index and embedding"""
            try:
                embedding = self.generate_embedding(text)
                return index, embedding, None
            except Exception as e:
                return index, None, e
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(process_text, i, text): i 
                for i, text in enumerate(texts)
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(futures):
                index, embedding, error = future.result()
                
                if error:
                    logger.error(f"Failed to generate embedding for text {index}: {error}")
                    raise error
                
                embeddings[index] = embedding
                completed += 1
                
                if completed % 10 == 0:
                    logger.info(f"Progress: {completed}/{len(texts)} embeddings generated")
        
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings
    
    def get_dimension(self) -> int:
        """Get the dimensionality of Bedrock Titan embeddings.
        
        Returns:
            1536 (Titan embedding dimension)
        """
        return 1536
    
    def health_check(self) -> bool:
        """Check if Bedrock service is accessible.
        
        Returns:
            True if Bedrock is accessible, False otherwise
        """
        if not self.client:
            logger.warning("Bedrock client not initialized")
            return False
        
        try:
            # Try to generate a test embedding
            test_text = "health check"
            embedding = self.generate_embedding(test_text)
            
            # Verify embedding has correct dimension
            if len(embedding) == 1536:
                logger.info("Bedrock health check passed")
                return True
            else:
                logger.warning(f"Bedrock health check failed: unexpected dimension {len(embedding)}")
                return False
                
        except Exception as e:
            logger.warning(f"Bedrock health check failed: {e}")
            return False
    
    def get_metrics(self) -> StrategyMetrics:
        """Get performance metrics for this strategy.
        
        Returns:
            StrategyMetrics instance with current metrics
        """
        return self.metrics
