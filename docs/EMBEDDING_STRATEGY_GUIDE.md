# Embedding Strategy Guide

Complete guide for using and managing embedding strategies in NexusAI.

## Table of Contents

1. [Overview](#overview)
2. [Available Strategies](#available-strategies)
3. [Switching Strategies](#switching-strategies)
4. [Dimension Compatibility](#dimension-compatibility)
5. [Migration Guide](#migration-guide)
6. [Configuration](#configuration)
7. [Performance Comparison](#performance-comparison)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Overview

NexusAI supports multiple embedding strategies for generating vector embeddings from text. Each strategy has different characteristics in terms of:

- **Dimension**: Size of the embedding vector
- **Performance**: Speed and latency
- **Cost**: Cloud API costs vs local compute
- **Availability**: Network dependency vs offline capability

The system provides automatic fallback, health checking, and migration tools to ensure smooth operation.

## Available Strategies

### 1. Bedrock Strategy (AWS Titan)

**Model**: Amazon Titan Text Embeddings v1/v2  
**Dimension**: 1536  
**Type**: Cloud-based (AWS Bedrock)

**Pros**:
- High quality embeddings
- Scalable (no local compute needed)
- Regularly updated models
- Supports large batches

**Cons**:
- Requires AWS credentials
- Network latency (~100-200ms per request)
- API costs apply
- Rate limits

**Best for**:
- Production deployments
- Large-scale processing
- When quality is critical

### 2. Local MiniLM Strategy

**Model**: sentence-transformers/all-MiniLM-L6-v2  
**Dimension**: 384  
**Type**: Local CPU inference

**Pros**:
- No API costs
- Works offline (sovereign mode)
- Fast inference (~50ms per request)
- No rate limits
- Privacy (data stays local)

**Cons**:
- Requires local compute
- Lower dimension (384d vs 1536d)
- Requires model download (~80MB)
- CPU-bound

**Best for**:
- Development and testing
- Offline deployments
- Privacy-sensitive applications
- Cost optimization

## Switching Strategies

### Basic Usage

```python
from src.embeddings import EmbeddingStrategyManager

# Initialize manager
manager = EmbeddingStrategyManager(default_strategy='bedrock')

# Switch to local strategy
manager.set_strategy('local')

# Get current strategy
strategy = manager.get_strategy()
embedding = strategy.generate_embedding("Hello world")
```

### Dimension Warning

When switching between strategies with different dimensions, you'll see a warning:

```
⚠️  DIMENSION MISMATCH WARNING ⚠️
Switching from bedrock (1536d) to local (384d).
This will cause errors if you try to add embeddings to existing collections!
```

To suppress this warning (if you know what you're doing):

```python
manager.set_strategy('local', force=True)
```

### Checking Compatibility

Before adding embeddings to a collection, check dimension compatibility:

```python
# Get collection dimension
collection = chroma_client.get_collection("my_collection")
sample = collection.get(limit=1, include=['embeddings'])
collection_dim = len(sample['embeddings'][0])

# Check compatibility
if manager.check_dimension_compatibility(collection_dim, 'my_collection'):
    # Safe to proceed
    strategy = manager.get_strategy()
    embedding = strategy.generate_embedding(text)
else:
    # Dimension mismatch - need to migrate or create new collection
    print("Cannot use this strategy with existing collection")
```

## Dimension Compatibility

### The Problem

ChromaDB collections are created with a fixed embedding dimension. If you try to add embeddings with a different dimension, you'll get an error:

```
chromadb.errors.InvalidDimensionException: 
Embedding dimension 384 does not match collection dimension 1536
```

### Solutions

#### Option 1: Create New Collection

Create a new collection with the correct dimension:

```python
# Switch to local strategy (384d)
manager.set_strategy('local')

# Create new collection
new_collection = chroma_client.create_collection(
    name="my_collection_local",
    metadata={"dimension": 384}
)

# Add embeddings
strategy = manager.get_strategy()
embeddings = strategy.batch_generate(texts)
new_collection.add(ids=ids, documents=texts, embeddings=embeddings)
```

#### Option 2: Migrate Existing Collection

Use the migration tool to re-embed all documents:

```python
from src.embeddings import EmbeddingMigrationTool

# Initialize migration tool
migration_tool = EmbeddingMigrationTool()

# Get strategies
old_strategy = manager.strategies['bedrock']  # 1536d
new_strategy = manager.strategies['local']    # 384d

# Check if migration is needed
if migration_tool.check_migration_needed('old_collection', new_strategy):
    # Estimate time
    estimated_time = migration_tool.estimate_migration_time(
        'old_collection', 
        new_strategy
    )
    print(f"Estimated migration time: {estimated_time:.1f} seconds")
    
    # Perform migration
    success = migration_tool.migrate_collection(
        source_collection_name='old_collection',
        target_collection_name='new_collection',
        source_strategy=old_strategy,
        target_strategy=new_strategy,
        batch_size=100
    )
    
    if success:
        # Verify migration
        if migration_tool.verify_migration('old_collection', 'new_collection'):
            print("Migration successful!")
            # Optionally delete old collection
            chroma_client.delete_collection('old_collection')
    else:
        # Rollback on failure
        migration_tool.rollback_migration('new_collection')
```

## Migration Guide

### Step-by-Step Migration Process

1. **Backup your data** (always!)
   ```bash
   python scripts/run_backup.py
   ```

2. **Check current collection info**
   ```python
   info = migration_tool.get_collection_info('my_collection')
   print(f"Collection: {info['name']}")
   print(f"Documents: {info['count']}")
   print(f"Metadata: {info['metadata']}")
   ```

3. **Estimate migration time**
   ```python
   estimated_time = migration_tool.estimate_migration_time(
       'my_collection',
       new_strategy
   )
   print(f"This will take approximately {estimated_time/60:.1f} minutes")
   ```

4. **Perform migration**
   ```python
   success = migration_tool.migrate_collection(
       source_collection_name='my_collection',
       target_collection_name='my_collection_v2',
       source_strategy=old_strategy,
       target_strategy=new_strategy,
       batch_size=100  # Adjust based on memory
   )
   ```

5. **Verify and switch**
   ```python
   if migration_tool.verify_migration('my_collection', 'my_collection_v2'):
       # Update your code to use new collection
       # Delete old collection when confident
       chroma_client.delete_collection('my_collection')
   ```

### Migration Performance Tips

- **Batch size**: Larger batches (100-500) are faster but use more memory
- **Local strategy**: Faster for migration (no API rate limits)
- **Timing**: Run migrations during low-traffic periods
- **Monitoring**: Watch logs for progress and errors

## Configuration

### YAML Configuration

Configure strategies in `config/embedding_config.yaml`:

```yaml
embedding:
  default_strategy: bedrock  # or 'local'
  fallback_enabled: true
  sovereign_mode: false  # Set true for local-only
  
  bedrock:
    model_id: amazon.titan-embed-text-v1
    region: us-east-1
    timeout: 30  # seconds (1-300)
  
  local:
    model_path: sentence-transformers/all-MiniLM-L6-v2
    n_threads: 4  # CPU threads (1-16)
```

### Configuration Validation

The system validates all configuration parameters:

**Bedrock validation**:
- Region must be valid AWS region
- Timeout must be 1-300 seconds
- Model ID is checked against known models (warning if unknown)

**Local validation**:
- n_threads must be 1-16 (warning if >16)
- model_path must be valid directory or HuggingFace model name

### Sovereign Mode

For complete data sovereignty (no cloud dependencies):

```yaml
embedding:
  sovereign_mode: true
```

This forces local strategy and disables fallback to cloud services.

## Performance Comparison

### Latency

| Strategy | Single Request | Batch (100) | Notes |
|----------|---------------|-------------|-------|
| Bedrock  | ~100-200ms    | ~50-60s     | Network latency, rate limits |
| Local    | ~50ms         | ~5s         | CPU-bound, no rate limits |

### Throughput

| Strategy | Requests/sec | Batch Efficiency |
|----------|-------------|------------------|
| Bedrock  | ~5-10       | Good (with delays) |
| Local    | ~20         | Excellent |

### Cost

| Strategy | Cost per 1M tokens | Notes |
|----------|-------------------|-------|
| Bedrock  | ~$0.10-0.30       | AWS pricing |
| Local    | $0 (compute only) | One-time model download |

### Quality

Both strategies produce high-quality embeddings suitable for semantic search:

- **Bedrock (1536d)**: Slightly better for complex queries, more nuanced
- **Local (384d)**: Excellent for most use cases, faster retrieval

## Troubleshooting

### Common Errors

#### 1. Dimension Mismatch

**Error**: `InvalidDimensionException: Embedding dimension X does not match collection dimension Y`

**Solution**: 
- Check current strategy dimension: `manager.get_strategy_dimension()`
- Either switch strategy or migrate collection (see Migration Guide)

#### 2. Strategy Health Check Failed

**Error**: `Strategy 'bedrock' failed health check`

**Causes**:
- AWS credentials not configured
- Network connectivity issues
- Bedrock service unavailable
- Invalid region/model configuration

**Solution**:
```python
# Check strategy health
health = manager.get_available_strategies()
print(health)  # {'bedrock': False, 'local': True}

# Enable fallback
manager.fallback_enabled = True
strategy = manager.get_strategy()  # Auto-falls back to local
```

#### 3. Rate Limiting

**Error**: `Rate limit exceeded after 3 retries`

**Solution**:
- Strategies automatically retry with exponential backoff
- Reduce batch size
- Add delays between requests
- Consider switching to local strategy for bulk operations

#### 4. Model Not Found

**Error**: `Failed to load local embedding model`

**Solution**:
```python
# Check model path
import os
model_path = "sentence-transformers/all-MiniLM-L6-v2"
if not os.path.exists(model_path):
    print("Model will be downloaded on first use")
    # Ensure internet connection for download
```

### Debugging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('src.embeddings')
logger.setLevel(logging.DEBUG)
```

Check metrics:

```python
# Get metrics for all strategies
metrics = manager.get_all_metrics()
for strategy_name, strategy_metrics in metrics.items():
    print(f"\n{strategy_name}:")
    print(f"  Total calls: {strategy_metrics['total_calls']}")
    print(f"  Avg time: {strategy_metrics['avg_time_ms']:.1f}ms")
    print(f"  Errors: {strategy_metrics['error_count']}")
    if strategy_metrics['last_error']:
        print(f"  Last error: {strategy_metrics['last_error']}")
```

## Best Practices

### 1. Strategy Selection

**Use Bedrock when**:
- Running in production
- Quality is critical
- Processing large volumes with good infrastructure
- Cost is not primary concern

**Use Local when**:
- Developing/testing
- Running offline
- Privacy is critical
- Cost optimization is important
- Processing small to medium volumes

### 2. Dimension Management

- **Plan ahead**: Choose strategy before creating collections
- **Document dimension**: Store dimension in collection metadata
- **Validate early**: Check compatibility before bulk operations
- **Test migrations**: Always test migration process on small dataset first

### 3. Error Handling

```python
from src.embeddings import EmbeddingStrategyManager

manager = EmbeddingStrategyManager(
    default_strategy='bedrock',
    fallback_enabled=True  # Enable automatic fallback
)

try:
    strategy = manager.get_strategy()
    embedding = strategy.generate_embedding(text)
except Exception as e:
    # Fallback already attempted if enabled
    logger.error(f"Embedding generation failed: {e}")
    # Handle error appropriately
```

### 4. Performance Optimization

**For Bedrock**:
- Use batch operations when possible
- Implement request pooling
- Cache embeddings for repeated texts
- Monitor rate limits

**For Local**:
- Adjust n_threads based on CPU cores
- Use batch operations (much faster)
- Consider GPU acceleration for large volumes
- Cache model in memory

### 5. Monitoring

Track strategy performance:

```python
# Periodic health checks
health = manager.get_available_strategies()
if not health[manager.get_current_strategy_name()]:
    logger.warning("Current strategy unhealthy, consider switching")

# Monitor metrics
metrics = manager.get_all_metrics()
for name, m in metrics.items():
    if m['error_count'] > 10:
        logger.warning(f"Strategy {name} has high error rate")
```

### 6. Testing

Always test strategy changes:

```python
# Test with sample data
test_texts = ["test 1", "test 2", "test 3"]

# Test new strategy
manager.set_strategy('local', force=True)
strategy = manager.get_strategy()

try:
    embeddings = strategy.batch_generate(test_texts)
    print(f"✓ Generated {len(embeddings)} embeddings")
    print(f"✓ Dimension: {len(embeddings[0])}")
except Exception as e:
    print(f"✗ Test failed: {e}")
```

### 7. Production Deployment

Recommended production configuration:

```yaml
embedding:
  default_strategy: bedrock
  fallback_enabled: true  # Auto-fallback to local on AWS issues
  
  bedrock:
    model_id: amazon.titan-embed-text-v1
    region: us-east-1
    timeout: 60  # Higher timeout for production
  
  local:
    model_path: sentence-transformers/all-MiniLM-L6-v2
    n_threads: 8  # Adjust based on server
```

Monitor and alert:
- Strategy health checks
- Error rates
- Latency metrics
- Fallback events

## Advanced Topics

### Custom Strategies

To implement a custom embedding strategy:

```python
from src.embeddings import EmbeddingStrategy

class CustomEmbeddingStrategy(EmbeddingStrategy):
    def generate_embedding(self, text: str) -> List[float]:
        # Your implementation
        pass
    
    def batch_generate(self, texts: List[str]) -> List[List[float]]:
        # Your implementation
        pass
    
    def get_dimension(self) -> int:
        return 768  # Your dimension
    
    def health_check(self) -> bool:
        # Your health check
        return True
    
    def get_metrics(self):
        # Optional: return StrategyMetrics instance
        return self.metrics

# Register with manager
manager.strategies['custom'] = CustomEmbeddingStrategy()
manager.set_strategy('custom')
```

### Hybrid Approach

Use different strategies for different purposes:

```python
# Use Bedrock for user queries (quality)
query_manager = EmbeddingStrategyManager(default_strategy='bedrock')

# Use Local for bulk indexing (speed/cost)
index_manager = EmbeddingStrategyManager(default_strategy='local')

# Query
query_embedding = query_manager.get_strategy().generate_embedding(user_query)

# Index
doc_embeddings = index_manager.get_strategy().batch_generate(documents)
```

Note: This requires separate collections with different dimensions!

## Support

For issues or questions:
- Check logs: `logs/embedding_strategy.log`
- Run diagnostics: `python scripts/check_embeddings.py`
- Review metrics: `manager.get_all_metrics()`
- See examples: `examples/rag_pipeline_example.py`

## References

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Sentence Transformers](https://www.sbert.net/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [NexusAI Architecture](SYSTEM_ARCHITECTURE.md)
