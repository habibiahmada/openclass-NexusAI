"""Unit tests for Bedrock embeddings client.

Tests API error handling, retry logic, and edge cases.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from src.embeddings.bedrock_client import BedrockEmbeddingsClient, BedrockAPIError


class TestBedrockEmbeddingsClient:
    """Unit tests for BedrockEmbeddingsClient"""
    
    def test_initialization(self):
        """Test client initialization with default and custom model IDs"""
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_config.get_bedrock_client.return_value = Mock()
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            # Test with default model
            client = BedrockEmbeddingsClient()
            assert client.model_id == "amazon.titan-embed-text-v2:0"
            assert client.total_tokens_processed == 0
            assert client.max_retries == 3
            
            # Test with custom model
            client = BedrockEmbeddingsClient(model_id="custom-model")
            assert client.model_id == "custom-model"
    
    def test_generate_embedding_success(self):
        """Test successful embedding generation"""
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_bedrock_client = Mock()
            mock_config.get_bedrock_client.return_value = mock_bedrock_client
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            # Mock successful response
            mock_embedding = [0.1] * 1024
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'embedding': mock_embedding
            }).encode('utf-8')
            
            mock_bedrock_client.invoke_model.return_value = mock_response
            
            client = BedrockEmbeddingsClient()
            result = client.generate_embedding("Test text")
            
            assert len(result) == 1024
            assert result == mock_embedding
            assert client.total_tokens_processed > 0
    
    def test_generate_embedding_empty_text(self):
        """Test that empty text raises ValueError"""
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_config.get_bedrock_client.return_value = Mock()
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            client = BedrockEmbeddingsClient()
            
            with pytest.raises(ValueError, match="Input text cannot be empty"):
                client.generate_embedding("")
            
            with pytest.raises(ValueError, match="Input text cannot be empty"):
                client.generate_embedding("   ")
    
    def test_rate_limiting_with_exponential_backoff(self):
        """Test rate limiting with exponential backoff retry logic
        
        Requirements: 4.3
        """
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_bedrock_client = Mock()
            mock_config.get_bedrock_client.return_value = mock_bedrock_client
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            # Mock throttling error on first two calls, success on third
            throttling_error = ClientError(
                {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                'InvokeModel'
            )
            
            mock_embedding = [0.1] * 1024
            success_response = {
                'body': MagicMock()
            }
            success_response['body'].read.return_value = json.dumps({
                'embedding': mock_embedding
            }).encode('utf-8')
            
            mock_bedrock_client.invoke_model.side_effect = [
                throttling_error,
                throttling_error,
                success_response
            ]
            
            client = BedrockEmbeddingsClient()
            
            # Should succeed after retries
            with patch('time.sleep'):  # Mock sleep to speed up test
                result = client.generate_embedding("Test text")
            
            assert len(result) == 1024
            assert mock_bedrock_client.invoke_model.call_count == 3
    
    def test_rate_limiting_exhausted_retries(self):
        """Test that rate limiting raises error after max retries
        
        Requirements: 4.3
        """
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_bedrock_client = Mock()
            mock_config.get_bedrock_client.return_value = mock_bedrock_client
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            # Mock throttling error on all calls
            throttling_error = ClientError(
                {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                'InvokeModel'
            )
            
            mock_bedrock_client.invoke_model.side_effect = throttling_error
            
            client = BedrockEmbeddingsClient()
            
            # Should raise error after max retries
            with patch('time.sleep'):  # Mock sleep to speed up test
                with pytest.raises(BedrockAPIError, match="Rate limit exceeded"):
                    client.generate_embedding("Test text")
            
            assert mock_bedrock_client.invoke_model.call_count == 3
    
    def test_service_errors_with_retry(self):
        """Test service errors with retry logic
        
        Requirements: 4.3
        """
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_bedrock_client = Mock()
            mock_config.get_bedrock_client.return_value = mock_bedrock_client
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            # Mock service error on first call, success on second
            service_error = ClientError(
                {'Error': {'Code': 'ServiceException', 'Message': 'Internal error'}},
                'InvokeModel'
            )
            
            mock_embedding = [0.1] * 1024
            success_response = {
                'body': MagicMock()
            }
            success_response['body'].read.return_value = json.dumps({
                'embedding': mock_embedding
            }).encode('utf-8')
            
            mock_bedrock_client.invoke_model.side_effect = [
                service_error,
                success_response
            ]
            
            client = BedrockEmbeddingsClient()
            
            # Should succeed after retry
            with patch('time.sleep'):
                result = client.generate_embedding("Test text")
            
            assert len(result) == 1024
            assert mock_bedrock_client.invoke_model.call_count == 2
    
    def test_service_errors_exhausted_retries(self):
        """Test service errors raise error after max retries
        
        Requirements: 4.3
        """
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_bedrock_client = Mock()
            mock_config.get_bedrock_client.return_value = mock_bedrock_client
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            # Mock service error on all calls
            service_error = ClientError(
                {'Error': {'Code': 'InternalServerException', 'Message': 'Internal error'}},
                'InvokeModel'
            )
            
            mock_bedrock_client.invoke_model.side_effect = service_error
            
            client = BedrockEmbeddingsClient()
            
            # Should raise error after max retries
            with patch('time.sleep'):
                with pytest.raises(BedrockAPIError, match="Service error after"):
                    client.generate_embedding("Test text")
            
            assert mock_bedrock_client.invoke_model.call_count == 3
    
    def test_network_timeout_with_retry(self):
        """Test network timeouts with retry logic
        
        Requirements: 4.3
        """
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_bedrock_client = Mock()
            mock_config.get_bedrock_client.return_value = mock_bedrock_client
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            # Mock timeout on first call, success on second
            mock_embedding = [0.1] * 1024
            success_response = {
                'body': MagicMock()
            }
            success_response['body'].read.return_value = json.dumps({
                'embedding': mock_embedding
            }).encode('utf-8')
            
            mock_bedrock_client.invoke_model.side_effect = [
                Exception("Connection timeout"),
                success_response
            ]
            
            client = BedrockEmbeddingsClient()
            
            # Should succeed after retry
            with patch('time.sleep'):
                result = client.generate_embedding("Test text")
            
            assert len(result) == 1024
            assert mock_bedrock_client.invoke_model.call_count == 2
    
    def test_non_retryable_errors(self):
        """Test that non-retryable errors fail immediately"""
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_bedrock_client = Mock()
            mock_config.get_bedrock_client.return_value = mock_bedrock_client
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            # Mock validation error (non-retryable)
            validation_error = ClientError(
                {'Error': {'Code': 'ValidationException', 'Message': 'Invalid input'}},
                'InvokeModel'
            )
            
            mock_bedrock_client.invoke_model.side_effect = validation_error
            
            client = BedrockEmbeddingsClient()
            
            # Should fail immediately without retries
            with pytest.raises(BedrockAPIError, match="Bedrock API error"):
                client.generate_embedding("Test text")
            
            assert mock_bedrock_client.invoke_model.call_count == 1
    
    def test_generate_batch_success(self):
        """Test successful batch processing"""
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_bedrock_client = Mock()
            mock_config.get_bedrock_client.return_value = mock_bedrock_client
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            # Mock successful response
            mock_embedding = [0.1] * 1024
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'embedding': mock_embedding
            }).encode('utf-8')
            
            mock_bedrock_client.invoke_model.return_value = mock_response
            
            client = BedrockEmbeddingsClient()
            texts = [f"Text {i}" for i in range(10)]
            results = client.generate_batch(texts, batch_size=5)
            
            assert len(results) == 10
            assert all(len(emb) == 1024 for emb in results)
            assert mock_bedrock_client.invoke_model.call_count == 10
    
    def test_generate_batch_empty_list(self):
        """Test batch processing with empty list"""
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_config.get_bedrock_client.return_value = Mock()
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            client = BedrockEmbeddingsClient()
            results = client.generate_batch([])
            
            assert results == []
    
    def test_token_usage_tracking(self):
        """Test token usage tracking for cost calculation"""
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_bedrock_client = Mock()
            mock_config.get_bedrock_client.return_value = mock_bedrock_client
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            # Mock successful response
            mock_embedding = [0.1] * 1024
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'embedding': mock_embedding
            }).encode('utf-8')
            
            mock_bedrock_client.invoke_model.return_value = mock_response
            
            client = BedrockEmbeddingsClient()
            
            # Generate embedding for text
            text = "A" * 400  # 400 characters = ~100 tokens
            client.generate_embedding(text)
            
            # Check token usage
            assert client.get_token_usage() == 100
            
            # Generate another embedding
            client.generate_embedding(text)
            assert client.get_token_usage() == 200
    
    def test_cost_calculation(self):
        """Test cost calculation based on token usage"""
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_bedrock_client = Mock()
            mock_config.get_bedrock_client.return_value = mock_bedrock_client
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            # Mock successful response
            mock_embedding = [0.1] * 1024
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'embedding': mock_embedding
            }).encode('utf-8')
            
            mock_bedrock_client.invoke_model.return_value = mock_response
            
            client = BedrockEmbeddingsClient()
            
            # Process 4000 characters = 1000 tokens
            text = "A" * 4000
            client.generate_embedding(text)
            
            # Cost should be (1000 / 1000) * $0.0001 = $0.0001
            cost = client.calculate_cost()
            assert abs(cost - 0.0001) < 0.000001
    
    def test_reset_usage(self):
        """Test resetting token usage counter"""
        with patch('src.embeddings.bedrock_client.aws_config') as mock_config:
            mock_bedrock_client = Mock()
            mock_config.get_bedrock_client.return_value = mock_bedrock_client
            mock_config.bedrock_model_id = "amazon.titan-embed-text-v2:0"
            
            # Mock successful response
            mock_embedding = [0.1] * 1024
            mock_response = {
                'body': MagicMock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'embedding': mock_embedding
            }).encode('utf-8')
            
            mock_bedrock_client.invoke_model.return_value = mock_response
            
            client = BedrockEmbeddingsClient()
            
            # Generate embedding
            client.generate_embedding("Test text")
            assert client.get_token_usage() > 0
            
            # Reset usage
            client.reset_usage()
            assert client.get_token_usage() == 0
