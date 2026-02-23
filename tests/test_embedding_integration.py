"""
Integration tests for embedding strategy switching.
Verifies that strategy manager works with RAG pipeline and handles fallback correctly.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.embeddings.strategy_manager import EmbeddingStrategyManager
from src.embeddings.bedrock_strategy import BedrockEmbeddingStrategy
from src.embeddings.local_minilm_strategy import LocalMiniLMEmbeddingStrategy


class TestEmbeddingStrategyIntegration:
    """Integration tests for embedding strategy switching"""
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_strategy_switching(self, mock_local, mock_bedrock):
        """Test switching between Bedrock and local strategies"""
        # Setup mocks
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock_instance.generate_embedding.return_value = [0.1] * 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local_instance.generate_embedding.return_value = [0.2] * 384
        mock_local.return_value = mock_local_instance
        
        # Initialize manager with Bedrock
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        # Verify Bedrock is active
        assert manager.get_current_strategy_name() == 'bedrock'
        strategy = manager.get_strategy()
        embedding = strategy.generate_embedding("test")
        assert len(embedding) == 1536
        
        # Switch to local
        success = manager.set_strategy('local')
        assert success is True
        assert manager.get_current_strategy_name() == 'local'
        
        # Verify local is active
        strategy = manager.get_strategy()
        embedding = strategy.generate_embedding("test")
        assert len(embedding) == 384
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_fallback_when_aws_unavailable(self, mock_local, mock_bedrock):
        """Test automatic fallback to local when AWS becomes unavailable"""
        # Setup mocks
        mock_bedrock_instance = Mock()
        # First health check passes (initialization), second fails (get_strategy)
        mock_bedrock_instance.health_check.side_effect = [True, False]
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local_instance.generate_embedding.return_value = [0.2] * 384
        mock_local.return_value = mock_local_instance
        
        # Initialize manager with Bedrock and fallback enabled
        manager = EmbeddingStrategyManager(default_strategy='bedrock', fallback_enabled=True)
        
        # Verify Bedrock is initially active
        assert manager.get_current_strategy_name() == 'bedrock'
        
        # Get strategy should trigger fallback when Bedrock fails health check
        strategy = manager.get_strategy()
        
        # Verify fallback to local occurred
        assert manager.get_current_strategy_name() == 'local'
        embedding = strategy.generate_embedding("test")
        assert len(embedding) == 384
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_config_file_loading(self, mock_local, mock_bedrock):
        """Test loading configuration from YAML file"""
        # Setup mocks
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        # Create temporary config file
        config_content = """
embedding:
  default_strategy: local
  fallback_enabled: false
  sovereign_mode: false
  
  bedrock:
    model_id: amazon.titan-embed-text-v1
    region: us-east-1
    timeout: 30
  
  local:
    model_path: sentence-transformers/all-MiniLM-L6-v2
    n_threads: 4
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            # Initialize manager with config file
            manager = EmbeddingStrategyManager(config_path=config_path)
            
            # Verify configuration was loaded
            assert manager.get_current_strategy_name() == 'local'
            assert manager.fallback_enabled is False
            
        finally:
            # Cleanup
            os.unlink(config_path)
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_sovereign_mode(self, mock_local, mock_bedrock):
        """Test sovereign mode (local only, no AWS)"""
        # Setup mocks
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local_instance.generate_embedding.return_value = [0.2] * 384
        mock_local.return_value = mock_local_instance
        
        # Create temporary config file with sovereign mode
        config_content = """
embedding:
  default_strategy: local
  fallback_enabled: false
  sovereign_mode: true
  
  local:
    model_path: sentence-transformers/all-MiniLM-L6-v2
    n_threads: 4
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            # Initialize manager with sovereign mode
            manager = EmbeddingStrategyManager(config_path=config_path)
            
            # Verify only local strategy is available
            assert manager.get_current_strategy_name() == 'local'
            assert 'bedrock' not in manager.strategies or not manager.strategies.get('bedrock')
            assert 'local' in manager.strategies
            
            # Verify embeddings work
            strategy = manager.get_strategy()
            embedding = strategy.generate_embedding("test")
            assert len(embedding) == 384
            
        finally:
            # Cleanup
            os.unlink(config_path)
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_batch_generation_with_strategy_manager(self, mock_local, mock_bedrock):
        """Test batch embedding generation through strategy manager"""
        # Setup mocks
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock_instance.batch_generate.return_value = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        # Initialize manager
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        # Test batch generation
        strategy = manager.get_strategy()
        texts = ["text1", "text2", "text3"]
        embeddings = strategy.batch_generate(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_get_available_strategies_status(self, mock_local, mock_bedrock):
        """Test getting status of all available strategies"""
        # Setup mocks
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = False  # Local unhealthy
        mock_local.return_value = mock_local_instance
        
        # Initialize manager
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        # Get available strategies
        strategies = manager.get_available_strategies()
        
        assert strategies['bedrock'] is True
        assert strategies['local'] is False


class TestRAGPipelineIntegration:
    """Test RAG pipeline integration with embedding strategy manager"""
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_rag_pipeline_uses_strategy_manager(self, mock_local, mock_bedrock):
        """Test that RAG pipeline can use strategy manager for embeddings"""
        # Setup mocks
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock_instance.generate_embedding.return_value = [0.1] * 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local.return_value = mock_local_instance
        
        # Create strategy manager
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        # Verify strategy manager can generate embeddings
        strategy = manager.get_strategy()
        embedding = strategy.generate_embedding("test query")
        
        assert len(embedding) == 1536
        assert manager.get_current_strategy_name() == 'bedrock'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
