"""
Tests for Phase 10 embedding strategy improvements.
Tests dimension compatibility, configuration validation, retry logic, and metrics.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import time
from botocore.exceptions import ClientError

from src.embeddings.strategy_manager import EmbeddingStrategyManager
from src.embeddings.bedrock_strategy import BedrockEmbeddingStrategy
from src.embeddings.local_minilm_strategy import LocalMiniLMEmbeddingStrategy
from src.embeddings.migration_tool import EmbeddingMigrationTool
from src.embeddings.strategy_metrics import StrategyMetrics, MetricsTracker


class TestDimensionCompatibility:
    """Test dimension compatibility checking"""
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_dimension_mismatch_warning_on_switch(self, mock_local, mock_bedrock):
        """Test that switching strategies with different dimensions shows warning"""
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        # Switch to local should log warning
        with patch('src.embeddings.strategy_manager.logger') as mock_logger:
            result = manager.set_strategy('local')
            assert result is True
            # Check that warning was logged
            assert mock_logger.warning.called
            warning_msg = mock_logger.warning.call_args[0][0]
            assert 'DIMENSION MISMATCH WARNING' in warning_msg
            assert '1536d' in warning_msg
            assert '384d' in warning_msg
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_dimension_mismatch_force_skip_warning(self, mock_local, mock_bedrock):
        """Test that force=True skips dimension warning"""
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        # Switch with force=True should not log warning
        with patch('src.embeddings.strategy_manager.logger') as mock_logger:
            result = manager.set_strategy('local', force=True)
            assert result is True
            # Warning should not be called
            assert not mock_logger.warning.called
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_check_dimension_compatibility_match(self, mock_local, mock_bedrock):
        """Test dimension compatibility check with matching dimensions"""
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        # Check with matching dimension
        result = manager.check_dimension_compatibility(1536, 'test_collection')
        assert result is True
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_check_dimension_compatibility_mismatch(self, mock_local, mock_bedrock):
        """Test dimension compatibility check with mismatched dimensions"""
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        # Check with mismatched dimension
        with patch('src.embeddings.strategy_manager.logger') as mock_logger:
            result = manager.check_dimension_compatibility(384, 'test_collection')
            assert result is False
            # Check error message
            assert mock_logger.error.called
            error_msg = mock_logger.error.call_args[0][0]
            assert 'DIMENSION MISMATCH ERROR' in error_msg
            assert 'test_collection' in error_msg


class TestConfigurationValidation:
    """Test configuration validation"""
    
    def test_bedrock_config_invalid_region(self):
        """Test Bedrock config validation with invalid region"""
        manager = EmbeddingStrategyManager.__new__(EmbeddingStrategyManager)
        
        config = {'region': 'invalid-region', 'timeout': 30}
        
        with pytest.raises(ValueError, match="Invalid Bedrock region"):
            manager._validate_bedrock_config(config)
    
    def test_bedrock_config_invalid_timeout(self):
        """Test Bedrock config validation with invalid timeout"""
        manager = EmbeddingStrategyManager.__new__(EmbeddingStrategyManager)
        
        config = {'region': 'us-east-1', 'timeout': -5}
        
        with pytest.raises(ValueError, match="Invalid timeout"):
            manager._validate_bedrock_config(config)
    
    def test_bedrock_config_timeout_too_low(self):
        """Test Bedrock config validation with timeout too low"""
        manager = EmbeddingStrategyManager.__new__(EmbeddingStrategyManager)
        
        config = {'region': 'us-east-1', 'timeout': 0.5}
        
        with pytest.raises(ValueError, match="too low"):
            manager._validate_bedrock_config(config)
    
    def test_bedrock_config_unknown_model_warning(self):
        """Test Bedrock config validation warns for unknown model"""
        manager = EmbeddingStrategyManager.__new__(EmbeddingStrategyManager)
        
        config = {
            'region': 'us-east-1',
            'timeout': 30,
            'model_id': 'unknown-model-id'
        }
        
        with patch('src.embeddings.strategy_manager.logger') as mock_logger:
            manager._validate_bedrock_config(config)
            assert mock_logger.warning.called
            warning_msg = mock_logger.warning.call_args[0][0]
            assert 'not in the known list' in warning_msg
    
    def test_local_config_invalid_threads(self):
        """Test local config validation with invalid n_threads"""
        manager = EmbeddingStrategyManager.__new__(EmbeddingStrategyManager)
        
        config = {'n_threads': -1}
        
        with pytest.raises(ValueError, match="Invalid n_threads"):
            manager._validate_local_config(config)
    
    def test_local_config_threads_too_high_warning(self):
        """Test local config validation warns for high thread count"""
        manager = EmbeddingStrategyManager.__new__(EmbeddingStrategyManager)
        
        config = {'n_threads': 32}
        
        with patch('src.embeddings.strategy_manager.logger') as mock_logger:
            manager._validate_local_config(config)
            assert mock_logger.warning.called
            warning_msg = mock_logger.warning.call_args[0][0]
            assert 'very high' in warning_msg
    
    def test_local_config_invalid_model_path(self):
        """Test local config validation with invalid model path"""
        manager = EmbeddingStrategyManager.__new__(EmbeddingStrategyManager)
        
        config = {'n_threads': 4, 'model_path': 'invalid-path-format'}
        
        with pytest.raises(ValueError, match="Invalid model_path format"):
            manager._validate_local_config(config)


class TestRetryLogic:
    """Test retry logic in strategies"""
    
    @patch('boto3.client')
    @patch('time.sleep')
    def test_bedrock_retry_on_throttling(self, mock_sleep, mock_boto_client):
        """Test Bedrock retries on throttling"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # First two calls fail with throttling, third succeeds
        mock_embedding = [0.1] * 1536
        mock_response = {
            'body': Mock(read=lambda: json.dumps({'embedding': mock_embedding}).encode())
        }
        
        throttle_error = ClientError(
            {'Error': {'Code': 'ThrottlingException'}},
            'invoke_model'
        )
        
        mock_client.invoke_model.side_effect = [
            throttle_error,
            throttle_error,
            mock_response
        ]
        
        strategy = BedrockEmbeddingStrategy()
        result = strategy.generate_embedding("test text")
        
        assert len(result) == 1536
        assert mock_client.invoke_model.call_count == 3
        assert mock_sleep.call_count == 2  # Two retries
    
    @patch('boto3.client')
    @patch('time.sleep')
    def test_bedrock_max_retries_exceeded(self, mock_sleep, mock_boto_client):
        """Test Bedrock fails after max retries"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        throttle_error = ClientError(
            {'Error': {'Code': 'ThrottlingException'}},
            'invoke_model'
        )
        
        mock_client.invoke_model.side_effect = throttle_error
        
        strategy = BedrockEmbeddingStrategy()
        
        with pytest.raises(Exception, match="Rate limit exceeded"):
            strategy.generate_embedding("test text")
        
        assert mock_client.invoke_model.call_count == 3  # Max retries
    
    @patch('src.embeddings.local_minilm_strategy.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.embeddings.local_minilm_strategy.SentenceTransformer')
    @patch('time.sleep')
    def test_local_retry_on_error(self, mock_sleep, mock_sentence_transformer):
        """Test local strategy retries on error"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        
        # First two calls fail, third succeeds
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1] * 384
        
        mock_model.encode.side_effect = [
            Exception("Temporary error"),
            Exception("Temporary error"),
            mock_embedding
        ]
        
        mock_sentence_transformer.return_value = mock_model
        
        strategy = LocalMiniLMEmbeddingStrategy()
        result = strategy.generate_embedding("test text")
        
        assert len(result) == 384
        assert mock_model.encode.call_count == 3
        assert mock_sleep.call_count == 2


class TestPerformanceMetrics:
    """Test performance metrics tracking"""
    
    def test_metrics_record_call(self):
        """Test recording successful calls"""
        metrics = StrategyMetrics()
        
        metrics.record_call(100.0)
        assert metrics.total_calls == 1
        assert metrics.total_time_ms == 100.0
        assert metrics.avg_time_ms == 100.0
        
        metrics.record_call(200.0)
        assert metrics.total_calls == 2
        assert metrics.total_time_ms == 300.0
        assert metrics.avg_time_ms == 150.0
    
    def test_metrics_record_error(self):
        """Test recording errors"""
        metrics = StrategyMetrics()
        
        metrics.record_error("Test error")
        assert metrics.error_count == 1
        assert metrics.last_error == "Test error"
        assert metrics.last_error_time is not None
    
    def test_metrics_reset(self):
        """Test resetting metrics"""
        metrics = StrategyMetrics()
        metrics.record_call(100.0)
        metrics.record_error("Test error")
        
        metrics.reset()
        assert metrics.total_calls == 0
        assert metrics.total_time_ms == 0.0
        assert metrics.error_count == 0
        assert metrics.last_error is None
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary"""
        metrics = StrategyMetrics()
        metrics.record_call(100.0)
        
        result = metrics.to_dict()
        assert result['total_calls'] == 1
        assert result['total_time_ms'] == 100.0
        assert result['avg_time_ms'] == 100.0
    
    def test_metrics_tracker_success(self):
        """Test MetricsTracker context manager on success"""
        metrics = StrategyMetrics()
        
        with MetricsTracker(metrics):
            time.sleep(0.01)  # Small delay
        
        assert metrics.total_calls == 1
        assert metrics.total_time_ms > 0
        assert metrics.error_count == 0
    
    def test_metrics_tracker_error(self):
        """Test MetricsTracker context manager on error"""
        metrics = StrategyMetrics()
        
        try:
            with MetricsTracker(metrics):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        assert metrics.error_count == 1
        assert metrics.last_error == "Test error"
    
    @patch('boto3.client')
    def test_bedrock_strategy_has_metrics(self, mock_boto_client):
        """Test Bedrock strategy tracks metrics"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        mock_embedding = [0.1] * 1536
        mock_response = {
            'body': Mock(read=lambda: json.dumps({'embedding': mock_embedding}).encode())
        }
        mock_client.invoke_model.return_value = mock_response
        
        strategy = BedrockEmbeddingStrategy()
        strategy.generate_embedding("test text")
        
        metrics = strategy.get_metrics()
        assert metrics is not None
        assert metrics.total_calls == 1
    
    @patch('src.embeddings.local_minilm_strategy.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.embeddings.local_minilm_strategy.SentenceTransformer')
    def test_local_strategy_has_metrics(self, mock_sentence_transformer):
        """Test local strategy tracks metrics"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1] * 384
        mock_model.encode.return_value = mock_embedding
        mock_sentence_transformer.return_value = mock_model
        
        strategy = LocalMiniLMEmbeddingStrategy()
        strategy.generate_embedding("test text")
        
        metrics = strategy.get_metrics()
        assert metrics is not None
        assert metrics.total_calls == 1
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_manager_get_all_metrics(self, mock_local, mock_bedrock):
        """Test getting metrics from all strategies"""
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        bedrock_metrics = StrategyMetrics()
        bedrock_metrics.record_call(100.0)
        mock_bedrock_instance.get_metrics.return_value = bedrock_metrics
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        local_metrics = StrategyMetrics()
        local_metrics.record_call(50.0)
        mock_local_instance.get_metrics.return_value = local_metrics
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        all_metrics = manager.get_all_metrics()
        assert 'bedrock' in all_metrics
        assert 'local' in all_metrics
        assert all_metrics['bedrock']['total_calls'] == 1
        assert all_metrics['local']['total_calls'] == 1


class TestMigrationTool:
    """Test embedding migration tool"""
    
    @patch('chromadb.Client')
    def test_check_migration_needed_different_dimensions(self, mock_client_class):
        """Test check_migration_needed with different dimensions"""
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.get.return_value = {
            'embeddings': [[0.1] * 384]  # 384d embeddings
        }
        mock_client.get_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        tool = EmbeddingMigrationTool(chroma_client=mock_client)
        
        mock_strategy = Mock()
        mock_strategy.get_dimension.return_value = 1536  # Different dimension
        
        result = tool.check_migration_needed('test_collection', mock_strategy)
        assert result is True
    
    @patch('chromadb.Client')
    def test_check_migration_needed_same_dimensions(self, mock_client_class):
        """Test check_migration_needed with same dimensions"""
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.get.return_value = {
            'embeddings': [[0.1] * 384]  # 384d embeddings
        }
        mock_client.get_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        tool = EmbeddingMigrationTool(chroma_client=mock_client)
        
        mock_strategy = Mock()
        mock_strategy.get_dimension.return_value = 384  # Same dimension
        
        result = tool.check_migration_needed('test_collection', mock_strategy)
        assert result is False
    
    @patch('chromadb.Client')
    def test_estimate_migration_time(self, mock_client_class):
        """Test migration time estimation"""
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.count.return_value = 1000
        mock_client.get_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client
        
        tool = EmbeddingMigrationTool(chroma_client=mock_client)
        
        mock_strategy = Mock()
        mock_strategy.get_dimension.return_value = 1536
        mock_metrics = StrategyMetrics()
        mock_metrics.record_call(100.0)  # 100ms per call
        mock_strategy.get_metrics.return_value = mock_metrics
        
        estimated_time = tool.estimate_migration_time('test_collection', mock_strategy)
        
        assert estimated_time is not None
        assert estimated_time > 0
        # Should be roughly 1000 docs * 0.1s * 1.2 buffer = 120s
        assert 100 < estimated_time < 150


class TestConcurrentAccess:
    """Test concurrent access and thread safety"""
    
    @patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy')
    @patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy')
    def test_concurrent_strategy_switching(self, mock_local, mock_bedrock):
        """Test concurrent strategy switching is thread-safe"""
        import threading
        
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.health_check.return_value = True
        mock_bedrock_instance.get_dimension.return_value = 1536
        mock_bedrock.return_value = mock_bedrock_instance
        
        mock_local_instance = Mock()
        mock_local_instance.health_check.return_value = True
        mock_local_instance.get_dimension.return_value = 384
        mock_local.return_value = mock_local_instance
        
        manager = EmbeddingStrategyManager(default_strategy='bedrock')
        
        results = []
        
        def switch_strategy(strategy_name):
            result = manager.set_strategy(strategy_name, force=True)
            results.append(result)
        
        # Create multiple threads switching strategies
        threads = []
        for i in range(10):
            strategy = 'local' if i % 2 == 0 else 'bedrock'
            t = threading.Thread(target=switch_strategy, args=(strategy,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # All switches should succeed
        assert all(results)
        # Manager should be in a valid state
        assert manager.current_strategy is not None
    
    @patch('boto3.client')
    def test_concurrent_embedding_generation(self, mock_boto_client):
        """Test concurrent embedding generation"""
        import threading
        
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        mock_embedding = [0.1] * 1536
        mock_response = {
            'body': Mock(read=lambda: json.dumps({'embedding': mock_embedding}).encode())
        }
        mock_client.invoke_model.return_value = mock_response
        
        strategy = BedrockEmbeddingStrategy()
        
        results = []
        
        def generate_embedding(text):
            try:
                embedding = strategy.generate_embedding(text)
                results.append(len(embedding))
            except Exception as e:
                results.append(None)
        
        # Create multiple threads generating embeddings
        threads = []
        for i in range(5):
            t = threading.Thread(target=generate_embedding, args=(f"text {i}",))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # All should succeed
        assert len(results) == 5
        assert all(r == 1536 for r in results)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
