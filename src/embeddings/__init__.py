# Embeddings Module
# Handles vector embeddings creation using AWS Bedrock and local strategies

from .bedrock_client import BedrockEmbeddingsClient, BedrockAPIError
from .chroma_manager import ChromaDBManager, SearchResult
from .embedding_strategy import EmbeddingStrategy
from .bedrock_strategy import BedrockEmbeddingStrategy
from .local_minilm_strategy import LocalMiniLMEmbeddingStrategy
from .strategy_manager import EmbeddingStrategyManager
from .strategy_metrics import StrategyMetrics, MetricsTracker
from .migration_tool import EmbeddingMigrationTool

__all__ = [
    'BedrockEmbeddingsClient',
    'BedrockAPIError',
    'ChromaDBManager',
    'SearchResult',
    'EmbeddingStrategy',
    'BedrockEmbeddingStrategy',
    'LocalMiniLMEmbeddingStrategy',
    'EmbeddingStrategyManager',
    'StrategyMetrics',
    'MetricsTracker',
    'EmbeddingMigrationTool'
]