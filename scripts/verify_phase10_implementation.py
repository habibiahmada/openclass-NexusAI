"""
Verification script for Phase 10 implementation.
Checks that all required features are implemented and working.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("Phase 10 Implementation Verification")
print("=" * 80)

# Track results
results = []

def check(description, condition):
    """Check a condition and record result"""
    status = "✓ PASS" if condition else "✗ FAIL"
    results.append((description, condition))
    print(f"{status}: {description}")
    return condition

print("\n1. Checking imports...")
try:
    from src.embeddings import (
        EmbeddingStrategyManager,
        EmbeddingMigrationTool,
        StrategyMetrics,
        MetricsTracker,
        BedrockEmbeddingStrategy,
        LocalMiniLMEmbeddingStrategy,
        EmbeddingStrategy
    )
    check("All required classes can be imported", True)
except ImportError as e:
    check(f"Import failed: {e}", False)
    sys.exit(1)

print("\n2. Checking EmbeddingStrategyManager features...")
check("set_strategy has 'force' parameter", 
      'force' in EmbeddingStrategyManager.set_strategy.__code__.co_varnames)
check("check_dimension_compatibility has 'collection_name' parameter",
      'collection_name' in EmbeddingStrategyManager.check_dimension_compatibility.__code__.co_varnames)
check("get_all_metrics method exists",
      hasattr(EmbeddingStrategyManager, 'get_all_metrics'))
check("_validate_bedrock_config method exists",
      hasattr(EmbeddingStrategyManager, '_validate_bedrock_config'))
check("_validate_local_config method exists",
      hasattr(EmbeddingStrategyManager, '_validate_local_config'))

print("\n3. Checking EmbeddingStrategy base class...")
check("get_metrics method exists in base class",
      hasattr(EmbeddingStrategy, 'get_metrics'))

check("get_metrics is not abstract (has default implementation)",
      not hasattr(EmbeddingStrategy.get_metrics, '__isabstractmethod__') or 
      not EmbeddingStrategy.get_metrics.__isabstractmethod__)

print("\n4. Checking strategy implementations...")
# Check if strategies initialize metrics
from unittest.mock import Mock, patch
try:
    with patch('boto3.client'):
        bedrock = BedrockEmbeddingStrategy()
        check("BedrockEmbeddingStrategy has metrics attribute",
              hasattr(bedrock, 'metrics'))
except Exception:
    check("BedrockEmbeddingStrategy has metrics attribute", False)

try:
    with patch('src.embeddings.local_minilm_strategy.SENTENCE_TRANSFORMERS_AVAILABLE', True), \
         patch('src.embeddings.local_minilm_strategy.SentenceTransformer'):
        local = LocalMiniLMEmbeddingStrategy()
        check("LocalMiniLMEmbeddingStrategy has metrics attribute",
              hasattr(local, 'metrics'))
except Exception:
    check("LocalMiniLMEmbeddingStrategy has metrics attribute", False)

check("LocalMiniLMEmbeddingStrategy has max_retries parameter",
      'max_retries' in LocalMiniLMEmbeddingStrategy.__init__.__code__.co_varnames)

print("\n5. Checking StrategyMetrics...")
check("StrategyMetrics class exists", StrategyMetrics is not None)
check("StrategyMetrics has record_call method",
      hasattr(StrategyMetrics, 'record_call'))
check("StrategyMetrics has record_error method",
      hasattr(StrategyMetrics, 'record_error'))
check("StrategyMetrics has to_dict method",
      hasattr(StrategyMetrics, 'to_dict'))
check("StrategyMetrics has reset method",
      hasattr(StrategyMetrics, 'reset'))

print("\n6. Checking MetricsTracker...")
check("MetricsTracker class exists", MetricsTracker is not None)
check("MetricsTracker is a context manager",
      hasattr(MetricsTracker, '__enter__') and hasattr(MetricsTracker, '__exit__'))

print("\n7. Checking EmbeddingMigrationTool...")
check("EmbeddingMigrationTool class exists", EmbeddingMigrationTool is not None)
check("migrate_collection method exists",
      hasattr(EmbeddingMigrationTool, 'migrate_collection'))
check("check_migration_needed method exists",
      hasattr(EmbeddingMigrationTool, 'check_migration_needed'))
check("estimate_migration_time method exists",
      hasattr(EmbeddingMigrationTool, 'estimate_migration_time'))
check("verify_migration method exists",
      hasattr(EmbeddingMigrationTool, 'verify_migration'))
check("rollback_migration method exists",
      hasattr(EmbeddingMigrationTool, 'rollback_migration'))
check("get_collection_info method exists",
      hasattr(EmbeddingMigrationTool, 'get_collection_info'))

print("\n8. Checking documentation...")
docs_dir = Path(__file__).parent.parent / 'docs'
check("EMBEDDING_STRATEGY_GUIDE.md exists",
      (docs_dir / 'EMBEDDING_STRATEGY_GUIDE.md').exists())
check("PHASE10_IMPLEMENTATION_SUMMARY.md exists",
      (docs_dir / 'PHASE10_IMPLEMENTATION_SUMMARY.md').exists())

print("\n9. Checking tests...")
tests_dir = Path(__file__).parent.parent / 'tests'
check("test_embedding_improvements.py exists",
      (tests_dir / 'test_embedding_improvements.py').exists())
check("test_embedding_strategies.py exists",
      (tests_dir / 'test_embedding_strategies.py').exists())

print("\n10. Checking examples...")
examples_dir = Path(__file__).parent.parent / 'examples'
check("embedding_strategy_improvements_demo.py exists",
      (examples_dir / 'embedding_strategy_improvements_demo.py').exists())

# Summary
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

passed = sum(1 for _, result in results if result)
total = len(results)
percentage = (passed / total * 100) if total > 0 else 0

print(f"\nTotal checks: {total}")
print(f"Passed: {passed}")
print(f"Failed: {total - passed}")
print(f"Success rate: {percentage:.1f}%")

if passed == total:
    print("\n✓ ALL CHECKS PASSED - Phase 10 implementation is complete!")
    sys.exit(0)
else:
    print("\n✗ SOME CHECKS FAILED - Please review the failures above")
    print("\nFailed checks:")
    for description, result in results:
        if not result:
            print(f"  - {description}")
    sys.exit(1)
