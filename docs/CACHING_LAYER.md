# Caching Layer Documentation

## Overview

The caching layer provides optional Redis caching with LRU (Least Recently Used) fallback for repeated questions. This reduces CPU load and improves response time by caching RAG pipeline responses.

## Features

- **Automatic Fallback**: Uses Redis if available, automatically falls back to in-memory LRU cache
- **Fast Performance**: Cache hits complete in < 500ms (typically < 1ms)
- **Smart Key Generation**: SHA256-based deterministic keys with question normalization
- **Cache Invalidation**: Automatic invalidation on VKP updates
- **Thread-Safe**: LRU cache uses thread-safe operations
- **Statistics Tracking**: Monitors hits, misses, and hit rate

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   CacheManager                          │
│  (Unified interface with automatic fallback)           │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ RedisCache   │  │  LRUCache    │
│ (Optional)   │  │  (Fallback)  │
└──────────────┘  └──────────────┘
```

## Configuration

### Environment Variables

```bash
# Optional: Redis URL (if not set, uses LRU fallback)
REDIS_URL=redis://localhost:6379/0
```

### Default Settings

- **TTL**: 24 hours (86400 seconds)
- **LRU Max Size**: 1000 items
- **Cache Key Format**: `cache:response:{sha256_hash}`

## Usage

### Basic Usage

```python
from src.persistence.cache_manager import CacheManager
from src.persistence.cache_utils import generate_cache_key

# Initialize cache manager
cache_manager = CacheManager(redis_url=None)  # Uses LRU fallback

# Generate cache key
cache_key = generate_cache_key(
    question="What is Python?",
    subject_id=5,
    vkp_version="1.0.0"
)

# Check cache
cached_response = cache_manager.get(cache_key)

if cached_response:
    # Cache hit - use cached response
    response = cached_response
else:
    # Cache miss - run RAG pipeline
    response = rag_pipeline.process_query(question)
    
    # Store in cache
    cache_manager.set(cache_key, response, ttl_seconds=86400)
```

### Integration with RAG Pipeline

```python
from src.persistence.cache_integration import CachedRAGPipeline

# Wrap RAG pipeline with caching
cached_pipeline = CachedRAGPipeline(
    rag_pipeline=rag_pipeline,
    cache_manager=cache_manager,
    ttl_seconds=86400
)

# Process query with caching
result = cached_pipeline.process_query_with_cache(
    query="What is machine learning?",
    subject_id=5,
    vkp_version="1.0.0"
)
```

### Cache Invalidation

```python
from src.persistence.cache_invalidation import invalidate_cache_on_vkp_update

# Invalidate cache when VKP is updated
deleted_count = invalidate_cache_on_vkp_update(
    subject="matematika",
    grade=10,
    new_version="1.1.0",
    old_version="1.0.0",
    cache_manager=cache_manager
)

print(f"Invalidated {deleted_count} cache entries")
```

## API Endpoints

### Get Cache Statistics

```http
GET /api/cache/stats
Authorization: Bearer <admin_token>
```

Response:
```json
{
  "backend": "lru",
  "hits": 150,
  "misses": 50,
  "hit_rate": 0.75,
  "total_keys": 100,
  "status": "operational"
}
```

### Invalidate Cache

```http
POST /api/cache/invalidate?pattern=cache:response:*
Authorization: Bearer <admin_token>
```

Response:
```json
{
  "status": "success",
  "pattern": "cache:response:*",
  "deleted_count": 100,
  "message": "Invalidated 100 cache entries"
}
```

### Clear Cache Statistics

```http
POST /api/cache/clear-stats
Authorization: Bearer <admin_token>
```

Response:
```json
{
  "status": "success",
  "message": "Cache statistics cleared"
}
```

## Cache Key Generation

Cache keys are generated using SHA256 hash with the following components:

1. **Question Text**: Normalized (lowercase, stripped whitespace)
2. **Subject ID**: Integer identifier
3. **VKP Version**: Semantic version string

### Example

```python
# Input
question = "  What is Pythagoras Theorem?  "
subject_id = 5
vkp_version = "1.2.0"

# Normalized
normalized = "what is pythagoras theorem?"

# Key input
key_input = "what is pythagoras theorem?:5:1.2.0"

# SHA256 hash
hash_value = sha256(key_input).hexdigest()

# Final cache key
cache_key = f"cache:response:{hash_value}"
# Result: "cache:response:abc123def456..."
```

### Key Properties

- **Deterministic**: Same input always produces same key
- **Case-Insensitive**: "Python" and "python" produce same key
- **Whitespace-Normalized**: "  Python  " and "Python" produce same key
- **Version-Specific**: Different VKP versions produce different keys
- **Subject-Specific**: Different subjects produce different keys

## Performance

### Benchmarks

- **Cache Hit Time**: < 1ms (typically 0.01ms)
- **Cache Miss Time**: < 1ms
- **Target**: < 500ms (easily achieved)

### Performance Benefits

```
Without Cache:
- RAG Pipeline: ~5 seconds
- Total: ~5 seconds

With Cache (Hit):
- Cache Lookup: ~0.01ms
- Total: ~0.01ms

Speedup: 500,000x faster!
```

## Cache Invalidation Strategy

### When to Invalidate

1. **VKP Update**: When curriculum content is updated
2. **Manual Invalidation**: Admin-triggered cache clear
3. **TTL Expiration**: Automatic after 24 hours

### Invalidation Pattern

```python
# Invalidate all response cache
pattern = "cache:response:*"
deleted_count = cache_manager.invalidate_pattern(pattern)
```

## Monitoring

### Health Check

The `/api/health` endpoint includes cache statistics:

```json
{
  "status": "healthy",
  "cache": true,
  "cache_stats": {
    "backend": "lru",
    "hits": 150,
    "misses": 50,
    "hit_rate": 0.75,
    "total_keys": 100
  }
}
```

### Logging

Cache operations are logged at DEBUG level:

```
2026-02-20 10:30:00 - src.persistence.cache_manager - DEBUG - Cache hit: cache:response:abc123...
2026-02-20 10:30:05 - src.persistence.cache_manager - DEBUG - Cache miss: cache:response:def456...
2026-02-20 10:30:10 - src.persistence.cache_manager - DEBUG - Cache set: cache:response:ghi789... (TTL: 86400s)
```

## Testing

### Unit Tests

```bash
# Run unit tests
pytest tests/unit/test_caching_layer.py -v

# 26 tests covering:
# - CacheManager operations
# - LRUCache eviction and TTL
# - Cache utilities
# - Cache invalidation
# - Integration scenarios
```

### Property Tests

```bash
# Run property tests
pytest tests/property/test_cache_*.py -v

# 28 tests covering:
# - Cache key consistency (Property 27)
# - Cache hit performance (Property 28)
# - Cache invalidation (Property 29)
# - Repeated question caching (Property 30)
```

### Integration Test

```bash
# Run integration test
python scripts/test_cache_integration.py

# Tests:
# - Basic operations
# - Performance benchmarks
# - Cache invalidation
# - Key consistency
# - Repeated question caching
```

## Troubleshooting

### Redis Connection Failed

If Redis is unavailable, the system automatically falls back to LRU cache:

```
WARNING - Redis connection failed: Connection refused. Falling back to LRU cache.
INFO - CacheManager initialized with LRU backend
```

### Cache Not Working

1. Check if cache is initialized:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. Verify cache statistics:
   ```bash
   curl -H "Authorization: Bearer <admin_token>" \
        http://localhost:8000/api/cache/stats
   ```

3. Check logs for errors:
   ```bash
   grep "cache" logs/app.log
   ```

### Low Hit Rate

If cache hit rate is low:

1. Check TTL settings (may be too short)
2. Verify questions are being normalized correctly
3. Check if cache is being invalidated too frequently
4. Monitor cache size (LRU may be evicting too aggressively)

## Best Practices

1. **Use Redis in Production**: For better performance and persistence
2. **Monitor Hit Rate**: Aim for > 50% hit rate
3. **Adjust TTL**: Based on curriculum update frequency
4. **Invalidate on Updates**: Always invalidate cache when VKP is updated
5. **Monitor Cache Size**: Ensure LRU cache doesn't evict too frequently

## Requirements Validation

Phase 11 implementation validates the following requirements:

- **Requirement 12.1**: Optional Redis caching with LRU fallback ✓
- **Requirement 12.2**: SHA256-based cache key generation ✓
- **Requirement 12.3**: Cache hit performance < 500ms ✓
- **Requirement 12.4**: 24-hour TTL ✓
- **Requirement 12.5**: Thread-safe LRU cache (max 1000 items) ✓
- **Requirement 12.6**: Cache invalidation on VKP update ✓

All 54 tests pass successfully!
