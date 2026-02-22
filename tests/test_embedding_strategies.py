"""
Unit tests for embedding strategies.
Tests Bedrock strategy, local MiniLM strategy, strategy manager, and fallback behavior.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from src.embeddings.embedding_strategy import EmbeddingStrategy
from src.embeddings.bedrock_strategy import BedrockEmbeddingStrategy
from src.embeddings.local_minilm_strategy import LocalMiniLMEmbeddingStrategy
from src.embeddings.strategy_manager import EmbeddingStrategyManager


class TestEmbeddingStrategy:
    """Test abstract base class interface"""
    
    def test_abstract_methods_defined(self):
        """Test that abstract methods are defined"""
        assert hasattr(EmbeddingStrategy, 'generate_embedding')
        assert hasattr(EmbeddingStrategy, 'batch_generate')
        assert hasattr(EmbeddingStrategy, 'get_dimension')
        assert hasattr(EmbeddingStrategy, 'health_check')
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated"""
        with pytest.raises(TypeError):
            EmbeddingStrategy()


class TestBedrockEmbeddingStrategy:
    """Test Bedrock embedding strategy"""
    
    @patch('boto3.client')
    def test_initialization(self, mock_boto_client):
        """Test Bedrock strategy initialization"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        strategy = BedrockEmbeddingStrategy(
            model_id='amazon.titan-embed-text-v1',
            region='us-east-1',
            timeout=30
        )
        
        assert strategy.model_id == 'amazon.titan-embed-text-v1'
        assert strategy.region == 'us-east-1'
        assert strategy.timeout == 30
        assert strategy.client == mock_client
    
    @patch('boto3.client')
    def test_generate_embedding_success(self, mock_boto_client):
        """Test successful embedding generation"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock response
        mock_embedding = [0.1] * 1536
        mock_response = {
            'body': Mock(read=lambda: json.dumps({'embedding': mock_embedding}).encode())
        }
        mock_client.invoke_model.return_value = mock_response
        
        strategy = BedrockEmbeddingStrategy()
        result = strategy.generate_embedding("test text")
        
        assert len(result) == 1536
        assert result == mock_embedding
    
    @patch('boto3.client')
    def test_generate_embedding_empty_text(self, mock_boto_client):
        """Test embedding generation with empty text"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        strategy = BedrockEmbeddingStrategy()
        
        with pytest.raises(ValueError, match="Input text cannot be empty"):
            strategy.generate_embedding("")
    
    @patch('boto3.client')
    def test_batch_generate(self, mock_boto_client):
        """Test batch embedding generation"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock response
        mock_embedding = [0.1] * 1536
        mock_response = {
            'body': Mock(read=lambda: json.dumps({'embedding': mock_embedding}).encode())
        }
        mock_client.invoke_model.return_value = mock_response
        
        strategy = BedrockEmbeddingStrategy()
        texts = ["text1", "text2", "text3"]
        
        with patch('time.sleep'):  # Skip sleep delays in tests
            results = strategy.batch_generate(texts)
        
        assert len(results) == 3
        assert all(len(emb) == 1536 for emb in results)
    
    @patch('boto3.client')
    def test_get_dimension(self, mock_boto_client):
        """Test get_dimension returns correct value"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        strategy = BedrockEmbeddingStrategy()
        assert strategy.get_dimension() == 1536
    
    @patch('boto3.client')
    def test_health_check_success(self, mock_boto_client):
        """Test health check with healthy service"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock successful response
        mock_embedding = [0.1] * 1536
        mock_response = {
            'body': Mock(read=lambda: json.dumps({'embedding': mock_embedding}).encode())
        }
        mock_client.invoke_model.return_value = mock_response
        
        strategy = BedrockEmbeddingStrategy()
        assert strategy.health_check() is True
    
    @patch('boto3.client')
    def test_health_check_failure(self, mock_boto_client):
        """Test health check with unhealthy service"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        mock_client.invoke_model.side_effect = Exception("Service unavailable")
        
        strategy = BedrockEmbeddingStrategy()
        assert strategy.health_check() is False


class TestLocalMiniLMEmbeddingStrategy:
    """Test local MiniLM embedding strategy"""
    
    @patch('src.embeddings.local_minilm_strategy.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.embeddings.local_minilm_strategy.SentenceTransformer')
    def test_initialization(self, mock_sentence_transformer):
        """Test local strategy initialization"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer.return_value = mock_model
        
        strategy = LocalMiniLMEmbeddingStrategy(
            model_path='sentence-transformers/all-MiniLM-L6-v2',
            n_threads=4
        )
        
        assert strategy.model_path == 'sentence-transformers/all-MiniLM-L6-v2'
        assert strategy.n_threads == 4
        assert strategy.embedding_dim == 384
    
    @patch('src.embeddings.local_minilm_strategy.SENTENCE_TRANSFORMERS_AVAILABLE', False)
    def test_initialization_without_library(self):
        """Test initialization fails without sentence-transformers"""
        with pytest.raises(ImportError, match="sentence-transformers not installed"):
            LocalMiniLMEmbeddingStrategy()
    
    @patch('src.embeddings.local_minilm_strategy.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.embeddings.local_minilm_strategy.SentenceTransformer')
    def test_generate_embedding_success(self, mock_sentence_transformer):
        """Test successful embedding generation"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1] * 384
        mock_model.encode.return_value = mock_embedding
        mock_sentence_transformer.return_value = mock_model
        
        strategy = LocalMiniLMEmbeddingStrategy()
        result = strategy.generate_embedding("test text")
        
        assert len(result) == 384
    
    @patch('src.embeddings.local_minilm_strategy.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.embeddings.local_minilm_strategy.SentenceTransformer')
    def test_generate_embedding_empty_text(self, mock_sentence_transformer):
        """Test embedding generation with empty text"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer.return_value = mock_model
        
        strategy = LocalMiniLMEmbeddingStrategy()
        
        with pytest.raises(ValueError, match="Input text cannot be empty"):
            strategy.generate_embedding("")
    
    @patch('src.embeddings.local_minilm_strategy.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.embeddings.local_minilm_strategy.SentenceTransformer')
    def test_batch_generate(self, mock_sentence_transformer):
        """Test batch embedding generation"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        
        # Create a proper numpy-like mock that has tolist() and len()
        import numpy as np
        mock_embeddings = np.array([[0.1] * 384, [0.2] * 384, [0.3] * 384])
        mock_model.encode.return_value = mock_embeddings
        mock_sentence_transformer.return_value = mock_model
        
        strategy = LocalMiniLMEmbeddingStrategy()
        texts = ["text1", "text2", "text3"]
        results = strategy.batch_generate(texts)
        
        assert len(results) == 3
        assert all(len(emb) == 384 for emb in results)
    
    @patch('src.embeddings.local_minilm_strategy.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.embeddings.local_minilm_strategy.SentenceTransformer')
    def test_get_dimension(self, mock_sentence_transformer):
        """Test get_dimension returns correct value"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer.return_value = mock_model
        
        strategy = LocalMiniLMEmbeddingStrategy()
        assert strategy.get_dimension() == 384
    
    @patch('src.embeddings.local_minilm_strategy.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.embeddings.local_minilm_strategy.SentenceTransformer')
    def test_health_check_success(self, mock_sentence_transformer):
        """Test health check with loaded model"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1] * 384
        mock_model.encode.return_value = mock_embedding
        mock_sentence_transformer.return_value = mock_model
        
        strategy = LocalMiniLMEmbeddingStrategy()
        assert strategy.health_check() is True


class TestEmbeddingStrategyManager:
    """Test embedding strategy manager"""
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_initialization_default(self, mock_local, mock_bedrock):
        """Test manager initialization with defaults"""
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        assert 'bedrock' in manager.strategies
        assert 'local' in manager.strategies
        assert manager.current_strategy == mock_bedrock_instance
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_set_strategy(self, mock_local, mock_bedrock):
        """Test setting active strategy"""
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        # Switch to local
        result = manager.set_strategy('local')
        assert result is True
        assert manager.current_strategy == mock_local_instance
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_set_invalid_strategy(self, mock_local, mock_bedrock):
        """Test setting invalid strategy"""
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        result = manager.set_strategy('invalid')
        assert result is False
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_fallback_to_local(self, mock_local, mock_bedrock):
        """Test fallback from Bedrock to local"""
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock', fallback_enabled=True)
        
        # Fallback to local
        result = manager.fallback_to_local()
        assert result is True
        assert manager.current_strategy == mock_local_instance
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_get_strategy_with_health_check(self, mock_local, mock_bedrock):
        """Test get_strategy performs health check"""
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.side_effect = [True, True]  # Initial and get_strategy calls
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        strategy = manager.get_strategy()
        assert strategy == mock_bedrock_instance
        assert mock_bedrock_instance.health_check.call_count >= 1
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_automatic_fallback_on_unhealthy(self, mock_local, mock_bedrock):
        """Test automatic fallback when strategy becomes unhealthy"""
        mock_bedrock_instance = Mock()
        # First call (initialization) succeeds, second call (get_strategy) fails
        # Add more True values in case there are additional health checks
        mock_bedrock_instance.health_check.side_effect = [True, False, False, False]
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock', fallback_enabled=True)
        
        # Get strategy should trigger fallback
        strategy = manager.get_strategy()
        assert strategy == mock_local_instance
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_get_current_strategy_name(self, mock_local, mock_bedrock):
        """Test getting current strategy name"""
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        assert manager.get_current_strategy_name() == 'bedrock'
        
        manager.set_strategy('local')
        assert manager.get_current_strategy_name() == 'local'
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_get_available_strategies(self, mock_local, mock_bedrock):
        """Test getting available strategies with health status"""
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        strategies = manager.get_available_strategies()
        assert 'bedrock' in strategies
        assert 'local' in strategies
        assert strategies['bedrock'] is True
        assert strategies['local'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
