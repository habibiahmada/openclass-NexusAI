"""
Demo script showcasing Phase 10 embedding strategy improvements.

This script demonstrates:
1. Dimension compatibility checking
2. Configuration validation
3. Performance metrics tracking
4. Migration tool usage
5. Retry logic
"""

import logging
from unittest.mock import Mock, patch
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.embeddings import (
    EmbeddingStrategyManager,
    EmbeddingMigrationTool,
    StrategyMetrics,
    MetricsTracker
)

print("=" * 80)
print("Phase 10 Embedding Strategy Improvements Demo")
print("=" * 80)

# ============================================================================
# Demo 1: Dimension Compatibility Checking
# ============================================================================
print("\n" + "=" * 80)
print("Demo 1: Dimension Compatibility Checking")
print("=" * 80)

# Mock the strategies to avoid AWS/model dependencies
with patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy') as mock_bedrock, \
     patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy') as mock_local:
    
    # Setup mocks
    mock_bedrock_instance = Mock()
    mock_bedrock_instance.health_check.return_value = True
    mock_bedrock_instance.get_dimension.return_value = 1536
    mock_bedrock.return_value = mock_bedrock_instance
    
    mock_local_instance = Mock()
    mock_local_instance.health_check.return_value = True
    mock_local_instance.get_dimension.return_value = 384
    mock_local.return_value = mock_local_instance
    
    # Initialize manager with Bedrock
    print("\n1. Initialize manager with Bedrock strategy (1536d)")
    manager = EmbeddingStrategyManager(default_strategy='bedrock')
    print(f"   Current strategy: {manager.get_current_strategy_name()}")
    print(f"   Dimension: {manager.get_strategy_dimension()}d")
    
    # Try to switch to local (different dimension)
    print("\n2. Switch to local strategy (384d) - should show warning")
    manager.set_strategy('local')
    print(f"   Current strategy: {manager.get_current_strategy_name()}")
    print(f"   Dimension: {manager.get_strategy_dimension()}d")
    
    # Switch back with force=True to skip warning
    print("\n3. Switch back to Bedrock with force=True (skip warning)")
    manager.set_strategy('bedrock', force=True)
    print(f"   Current strategy: {manager.get_current_strategy_name()}")
    
    # Check dimension compatibility
    print("\n4. Check dimension compatibility with collection")
    print("   Checking 1536d collection with Bedrock (1536d):")
    compatible = manager.check_dimension_compatibility(1536, 'test_collection')
    print(f"   Compatible: {compatible}")
    
    print("\n   Checking 384d collection with Bedrock (1536d):")
    compatible = manager.check_dimension_compatibility(384, 'test_collection')
    print(f"   Compatible: {compatible}")

# ============================================================================
# Demo 2: Configuration Validation
# ============================================================================
print("\n" + "=" * 80)
print("Demo 2: Configuration Validation")
print("=" * 80)

print("\n1. Valid Bedrock configuration")
manager_instance = EmbeddingStrategyManager.__new__(EmbeddingStrategyManager)
try:
    config = {
        'region': 'us-east-1',
        'timeout': 30,
        'model_id': 'amazon.titan-embed-text-v1'
    }
    manager_instance._validate_bedrock_config(config)
    print("   ✓ Configuration valid")
except ValueError as e:
    print(f"   ✗ Configuration invalid: {e}")

print("\n2. Invalid Bedrock configuration (bad region)")
try:
    config = {
        'region': 'invalid-region',
        'timeout': 30
    }
    manager_instance._validate_bedrock_config(config)
    print("   ✓ Configuration valid")
except ValueError as e:
    print(f"   ✗ Configuration invalid: {e}")

print("\n3. Valid local configuration")
try:
    config = {
        'n_threads': 4,
        'model_path': 'sentence-transformers/all-MiniLM-L6-v2'
    }
    manager_instance._validate_local_config(config)
    print("   ✓ Configuration valid")
except ValueError as e:
    print(f"   ✗ Configuration invalid: {e}")

print("\n4. Invalid local configuration (bad threads)")
try:
    config = {
        'n_threads': -1
    }
    manager_instance._validate_local_config(config)
    print("   ✓ Configuration valid")
except ValueError as e:
    print(f"   ✗ Configuration invalid: {e}")

# ============================================================================
# Demo 3: Performance Metrics
# ============================================================================
print("\n" + "=" * 80)
print("Demo 3: Performance Metrics Tracking")
print("=" * 80)

print("\n1. Create metrics instance")
metrics = StrategyMetrics()
print(f"   Initial state: {metrics.to_dict()}")

print("\n2. Record successful calls")
metrics.record_call(100.0)  # 100ms
metrics.record_call(150.0)  # 150ms
metrics.record_call(120.0)  # 120ms
print(f"   After 3 calls: {metrics.to_dict()}")

print("\n3. Record an error")
metrics.record_error("Test error message")
print(f"   After error: {metrics.to_dict()}")

print("\n4. Using MetricsTracker context manager")
import time
test_metrics = StrategyMetrics()
print("   Simulating operation...")
with MetricsTracker(test_metrics):
    time.sleep(0.05)  # Simulate 50ms operation
print(f"   Metrics: {test_metrics.to_dict()}")

print("\n5. Get metrics from all strategies")
with patch('src.embeddings.strategy_manager.BedrockEmbeddingStrategy') as mock_bedrock, \
     patch('src.embeddings.strategy_manager.LocalMiniLMEmbeddingStrategy') as mock_local:
    
    # Setup mocks with metrics
    mock_bedrock_instance = Mock()
    mock_bedrock_instance.health_check.return_value = True
    mock_bedrock_instance.get_dimension.return_value = 1536
    bedrock_metrics = StrategyMetrics()
    bedrock_metrics.record_call(100.0)
    bedrock_metrics.record_call(120.0)
    mock_bedrock_instance.get_metrics.return_value = bedrock_metrics
    mock_bedrock.return_value = mock_bedrock_instance
    
    mock_local_instance = Mock()
    mock_local_instance.health_check.return_value = True
    mock_local_instance.get_dimension.return_value = 384
    local_metrics = StrategyMetrics()
    local_metrics.record_call(50.0)
    local_metrics.record_call(45.0)
    mock_local_instance.get_metrics.return_value = local_metrics
    mock_local.return_value = mock_local_instance
    
    manager = EmbeddingStrategyManager(default_strategy='bedrock')
    all_metrics = manager.get_all_metrics()
    
    print("\n   Bedrock metrics:")
    for key, value in all_metrics['bedrock'].items():
        print(f"     {key}: {value}")
    
    print("\n   Local metrics:")
    for key, value in all_metrics['local'].items():
        print(f"     {key}: {value}")

# ============================================================================
# Demo 4: Migration Tool
# ============================================================================
print("\n" + "=" * 80)
print("Demo 4: Migration Tool")
print("=" * 80)

with patch('chromadb.Client') as mock_client_class:
    # Setup mock ChromaDB client
    mock_client = Mock()
    mock_collection = Mock()
    mock_collection.get.return_value = {
        'embeddings': [[0.1] * 384]  # 384d embeddings
    }
    mock_collection.count.return_value = 1000
    mock_client.get_collection.return_value = mock_collection
    mock_client_class.return_value = mock_client
    
    print("\n1. Initialize migration tool")
    migration_tool = EmbeddingMigrationTool(chroma_client=mock_client)
    print("   ✓ Migration tool initialized")
    
    print("\n2. Get collection info")
    info = migration_tool.get_collection_info('test_collection')
    if info:
        print(f"   Collection: {info['name']}")
        print(f"   Documents: {info['count']}")
    
    print("\n3. Check if migration is needed")
    mock_strategy = Mock()
    mock_strategy.get_dimension.return_value = 1536  # Different dimension
    
    needs_migration = migration_tool.check_migration_needed(
        'test_collection',
        mock_strategy
    )
    print(f"   Migration needed: {needs_migration}")
    print(f"   Reason: Collection has 384d embeddings, strategy produces 1536d")
    
    print("\n4. Estimate migration time")
    mock_metrics = StrategyMetrics()
    mock_metrics.record_call(100.0)  # 100ms per call
    mock_strategy.get_metrics.return_value = mock_metrics
    
    estimated_time = migration_tool.estimate_migration_time(
        'test_collection',
        mock_strategy
    )
    print(f"   Estimated time: {estimated_time:.1f} seconds")
    print(f"   For 1000 documents at ~100ms each")

# ============================================================================
# Demo 5: Retry Logic
# ============================================================================
print("\n" + "=" * 80)
print("Demo 5: Retry Logic")
print("=" * 80)

print("\n1. Bedrock strategy with retry on throttling")
with patch('boto3.client') as mock_boto_client, \
     patch('time.sleep') as mock_sleep:
    
    from src.embeddings import BedrockEmbeddingStrategy
    from botocore.exceptions import ClientError
    
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
    print("   Attempting to generate embedding (will retry on throttling)...")
    
    try:
        result = strategy.generate_embedding("test text")
        print(f"   ✓ Success after {mock_client.invoke_model.call_count} attempts")
        print(f"   ✓ Retried {mock_sleep.call_count} times")
        print(f"   ✓ Generated {len(result)}d embedding")
    except Exception as e:
        print(f"   ✗ Failed: {e}")

print("\n2. Local strategy with retry on error")
with patch('src.embeddings.local_minilm_strategy.SENTENCE_TRANSFORMERS_AVAILABLE', True), \
     patch('src.embeddings.local_minilm_strategy.SentenceTransformer') as mock_st, \
     patch('time.sleep') as mock_sleep:
    
    from src.embeddings import LocalMiniLMEmbeddingStrategy
    
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
    
    mock_st.return_value = mock_model
    
    strategy = LocalMiniLMEmbeddingStrategy()
    print("   Attempting to generate embedding (will retry on error)...")
    
    try:
        result = strategy.generate_embedding("test text")
        print(f"   ✓ Success after {mock_model.encode.call_count} attempts")
        print(f"   ✓ Retried {mock_sleep.call_count} times")
        print(f"   ✓ Generated {len(result)}d embedding")
    except Exception as e:
        print(f"   ✗ Failed: {e}")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("Demo Complete!")
print("=" * 80)
print("\nKey Features Demonstrated:")
print("  ✓ Dimension compatibility checking with warnings")
print("  ✓ Configuration validation with clear error messages")
print("  ✓ Performance metrics tracking and reporting")
print("  ✓ Migration tool for strategy transitions")
print("  ✓ Automatic retry logic with exponential backoff")
print("\nFor more information, see:")
print("  - docs/EMBEDDING_STRATEGY_GUIDE.md")
print("  - docs/PHASE10_IMPLEMENTATION_SUMMARY.md")
print("  - tests/test_embedding_improvements.py")
print("=" * 80)
