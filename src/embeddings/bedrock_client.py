import json
import time
from typing import List, Dict, Any
import logging

import boto3
from botocore.exceptions import ClientError

from config.aws_config import aws_config

logger = logging.getLogger(__name__)


class BedrockAPIError(Exception):
    """Exception raised for Bedrock API errors"""
    pass


class BedrockEmbeddingsClient:
    """Client for generating embeddings using AWS Bedrock Titan Text Embeddings v2 model"""
    
    def __init__(self, model_id: str = None):
        """Initialize Bedrock client.
        
        Args:
            model_id: Bedrock model identifier (defaults to config value)
        """
        self.model_id = model_id or aws_config.bedrock_model_id
        self.client = aws_config.get_bedrock_client()
        self.total_tokens_processed = 0
        self.max_retries = 3
        
        logger.info(f"Initialized BedrockEmbeddingsClient with model: {self.model_id}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Input text (max 8192 tokens)
            
        Returns:
            1024-dimensional embedding vector
            
        Raises:
            BedrockAPIError: If API call fails after retries
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")
        
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
                    raise BedrockAPIError("No embedding in response")
                
                # Track token usage (approximate: 1 token ≈ 4 characters)
                tokens = len(text) // 4
                self.total_tokens_processed += tokens
                
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
                        raise BedrockAPIError(f"Rate limit exceeded after {self.max_retries} retries") from e
                
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
                        raise BedrockAPIError(f"Service error after {self.max_retries} retries: {e}") from e
                
                # Other errors - don't retry
                else:
                    raise BedrockAPIError(f"Bedrock API error: {e}") from e
            
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
                    raise BedrockAPIError(f"Failed after {self.max_retries} retries: {e}") from e
        
        raise BedrockAPIError("Unexpected error: max retries reached without success")
    
    def generate_batch(self, texts: List[str], batch_size: int = 25) -> List[List[float]]:
        """Generate embeddings for multiple texts with batching.
        
        Args:
            texts: List of input texts
            batch_size: Number of texts per batch (default 25 for optimization)
            
        Returns:
            List of embedding vectors
            
        Raises:
            BedrockAPIError: If API calls fail
        """
        if not texts:
            return []
        
        embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        logger.info(f"Processing {len(texts)} texts in {total_batches} batches of {batch_size}")
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.debug(f"Processing batch {batch_num}/{total_batches}")
            
            # Process each text in the batch
            for text in batch:
                try:
                    embedding = self.generate_embedding(text)
                    embeddings.append(embedding)
                except BedrockAPIError as e:
                    logger.error(f"Failed to generate embedding for text: {e}")
                    raise
        
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings
    
    def get_token_usage(self) -> int:
        """Get total tokens processed for cost calculation.
        
        Returns:
            Total number of tokens processed
        """
        return self.total_tokens_processed
    
    def calculate_cost(self) -> float:
        """Calculate estimated cost based on token usage.
        
        Titan Text Embeddings v2 pricing: $0.0001 per 1K tokens
        
        Returns:
            Estimated cost in USD
        """
        cost_per_1k_tokens = 0.0001
        return (self.total_tokens_processed / 1000) * cost_per_1k_tokens
    
    def reset_usage(self):
        """Reset token usage counter"""
        self.total_tokens_processed = 0
