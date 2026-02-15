# Embeddings Module
# Handles vector embeddings creation using AWS Bedrock

from .bedrock_client import BedrockEmbeddingsClient, BedrockAPIError
from .chroma_manager import ChromaDBManager, SearchResult

__all__ = ['BedrockEmbeddingsClient', 'BedrockAPIError', 'ChromaDBManager', 'SearchResult']