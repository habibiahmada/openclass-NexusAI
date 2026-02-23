"""
Embedding Strategy Manager for configurable embedding generation.
Manages strategy selection, fallback logic, and configuration.
"""

import logging
from typing import Dict, Optional
import yaml
import os
import threading

from .embedding_strategy import EmbeddingStrategy
from .bedrock_strategy import BedrockEmbeddingStrategy
from .local_minilm_strategy import LocalMiniLMEmbeddingStrategy

logger = logging.getLogger(__name__)


class EmbeddingStrategyManager:
    """Manager for embedding strategies with fallback support"""
    
    def __init__(self, config_path: str = None, default_strategy: str = 'bedrock', fallback_enabled: bool = True):
        """Initialize embedding strategy manager.
        
        Args:
            config_path: Path to configuration file (optional)
            default_strategy: Default strategy to use ('bedrock' or 'local')
            fallback_enabled: Enable automatic fallback to local on AWS failure
        """
        self.config_path = config_path
        self.fallback_enabled = fallback_enabled
        self.current_strategy = None
        self.strategies: Dict[str, EmbeddingStrategy] = {}
        self._lock = threading.RLock()  # Thread safety for strategy switching (reentrant)
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
        else:
            # Use default configuration
            self._initialize_default_strategies()
            self.set_strategy(default_strategy)
    
    def _load_config(self, config_path: str):
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            embedding_config = config.get('embedding', {})
            
            # Get configuration values
            default_strategy = embedding_config.get('default_strategy', 'bedrock')
            self.fallback_enabled = embedding_config.get('fallback_enabled', True)
            sovereign_mode = embedding_config.get('sovereign_mode', False)
            
            # If sovereign mode is enabled, force local strategy and disable fallback
            if sovereign_mode:
                logger.info("Sovereign mode enabled - using local embeddings only")
                default_strategy = 'local'
                self.fallback_enabled = False
            
            # Initialize Bedrock strategy (unless in sovereign mode)
            if not sovereign_mode:
                bedrock_config = embedding_config.get('bedrock', {})
                
                # Validate Bedrock configuration
                self._validate_bedrock_config(bedrock_config)
                
                try:
                    self.strategies['bedrock'] = BedrockEmbeddingStrategy(
                        model_id=bedrock_config.get('model_id', 'amazon.titan-embed-text-v1'),
                        region=bedrock_config.get('region', 'us-east-1'),
                        timeout=bedrock_config.get('timeout', 60)
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize Bedrock strategy: {e}")
            
            # Initialize local strategy
            local_config = embedding_config.get('local', {})
            
            # Validate local configuration
            self._validate_local_config(local_config)
            
            self.strategies['local'] = LocalMiniLMEmbeddingStrategy(
                model_path=local_config.get('model_path'),
                n_threads=local_config.get('n_threads', 4)
            )
            
            # Set default strategy
            self.set_strategy(default_strategy)
            
            logger.info(f"Loaded embedding configuration from {config_path}")
            logger.info(f"Default strategy: {default_strategy}, Fallback enabled: {self.fallback_enabled}")
            if sovereign_mode:
                logger.info("Running in sovereign mode (local embeddings only)")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            logger.info("Falling back to default configuration")
            self._initialize_default_strategies()
            self.set_strategy('bedrock')
    
    def _initialize_default_strategies(self):
        """Initialize strategies with default configuration"""
        try:
            # Initialize Bedrock strategy
            self.strategies['bedrock'] = BedrockEmbeddingStrategy()
            logger.info("Initialized Bedrock strategy with default configuration")
        except Exception as e:
            logger.warning(f"Failed to initialize Bedrock strategy: {e}")
        
        try:
            # Initialize local strategy
            self.strategies['local'] = LocalMiniLMEmbeddingStrategy()
            logger.info("Initialized local MiniLM strategy with default configuration")
        except Exception as e:
            logger.warning(f"Failed to initialize local strategy: {e}")
    
    def _validate_bedrock_config(self, config: dict):
        """Validate Bedrock configuration parameters.
        
        Args:
            config: Bedrock configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate region
        region = config.get('region', 'us-east-1')
        valid_regions = [
            'us-east-1', 'us-west-2', 'us-west-1', 'us-east-2',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2',
            'ap-south-1', 'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3',
            'ca-central-1', 'sa-east-1'
        ]
        if region not in valid_regions:
            raise ValueError(
                f"Invalid Bedrock region: {region}. "
                f"Valid regions: {', '.join(valid_regions)}"
            )
        
        # Validate timeout
        timeout = config.get('timeout', 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError(f"Invalid timeout: {timeout}. Must be a positive number")
        if timeout < 1:
            raise ValueError(f"Timeout {timeout}s is too low. Minimum: 1s")
        if timeout > 300:
            logger.warning(
                f"Timeout {timeout}s is very high (>5 minutes). "
                f"Recommended: 30-60s for production use"
            )
        
        # Validate model_id
        model_id = config.get('model_id', 'amazon.titan-embed-text-v1')
        valid_models = [
            'amazon.titan-embed-text-v1',
            'amazon.titan-embed-text-v2:0',
            'cohere.embed-english-v3',
            'cohere.embed-multilingual-v3'
        ]
        if model_id not in valid_models:
            logger.warning(
                f"Model ID '{model_id}' is not in the known list. "
                f"Known models: {', '.join(valid_models)}. "
                f"Proceeding anyway, but this may cause errors if the model doesn't exist."
            )
    
    def _validate_local_config(self, config: dict):
        """Validate local embedding configuration parameters.
        
        Args:
            config: Local configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate n_threads
        n_threads = config.get('n_threads', 4)
        if not isinstance(n_threads, int) or n_threads <= 0:
            raise ValueError(f"Invalid n_threads: {n_threads}. Must be a positive integer")
        if n_threads < 1:
            raise ValueError(f"n_threads must be at least 1")
        if n_threads > 16:
            logger.warning(
                f"n_threads {n_threads} is very high (>16). "
                f"Recommended: 4-8 for most systems. "
                f"Using too many threads may not improve performance."
            )
        
        # Validate model_path if provided
        model_path = config.get('model_path')
        if model_path:
            # Check if it's a local path
            if os.path.exists(model_path):
                if not os.path.isdir(model_path):
                    raise ValueError(
                        f"model_path must be a directory containing model files: {model_path}"
                    )
                logger.info(f"Using local model from: {model_path}")
            elif '/' in model_path:
                # Looks like a HuggingFace model name (e.g., "sentence-transformers/all-MiniLM-L6-v2")
                logger.info(
                    f"Using HuggingFace model: {model_path}. "
                    f"Model will be downloaded on first use."
                )
            else:
                raise ValueError(
                    f"Invalid model_path format: {model_path}. "
                    f"Must be either a local directory path or HuggingFace model name (e.g., 'org/model-name')"
                )
    
    def check_dimension_compatibility(self, collection_dimension: int, collection_name: str = None) -> bool:
        """Check if current strategy dimension matches collection dimension.
        
        Args:
            collection_dimension: Expected dimension from ChromaDB collection
            collection_name: Optional name of the collection for better error messages
            
        Returns:
            True if dimensions match, False otherwise
        """
        if not self.current_strategy:
            logger.error("No strategy configured")
            return False
        
        strategy_dimension = self.current_strategy.get_dimension()
        strategy_name = self.get_current_strategy_name()
        
        if strategy_dimension != collection_dimension:
            collection_info = f"collection '{collection_name}'" if collection_name else "collection"
            logger.error(
                f"❌ DIMENSION MISMATCH ERROR ❌\n"
                f"Current strategy '{strategy_name}' produces {strategy_dimension}d embeddings, "
                f"but {collection_info} expects {collection_dimension}d embeddings.\n"
                f"\n"
                f"This mismatch will cause errors when adding/querying embeddings!\n"
                f"\n"
                f"Solutions:\n"
                f"  1. Switch to a strategy with {collection_dimension}d embeddings:\n"
                f"     - Bedrock Titan: 1536d\n"
                f"     - Local MiniLM: 384d\n"
                f"  2. Create a new collection with {strategy_dimension}d dimension\n"
                f"  3. Migrate the collection using EmbeddingMigrationTool\n"
                f"\n"
                f"Example migration:\n"
                f"  from src.embeddings import EmbeddingMigrationTool\n"
                f"  tool = EmbeddingMigrationTool()\n"
                f"  tool.migrate_collection('{collection_name or 'old_collection'}', "
                f"'new_collection', old_strategy, new_strategy)"
            )
            return False
        
        logger.info(f"✓ Dimension compatibility check passed: {strategy_dimension}d")
        return True
    
    def get_strategy_dimension(self) -> Optional[int]:
        """Get the dimension of the current strategy.
        
        Returns:
            Dimension of current strategy, or None if no strategy set
        """
        if not self.current_strategy:
            return None
        return self.current_strategy.get_dimension()
    
    def get_strategy(self) -> EmbeddingStrategy:
        """Get the current embedding strategy with health check.
        
        Returns:
            Current embedding strategy
            
        Raises:
            Exception: If no healthy strategy is available
        """
        with self._lock:
            if not self.current_strategy:
                raise Exception("No embedding strategy configured")
            
            # Check if current strategy is healthy
            if not self.current_strategy.health_check():
                logger.warning("Current embedding strategy is unhealthy")
                
                # Attempt fallback if enabled
                if self.fallback_enabled:
                    logger.info("Attempting fallback to local strategy")
                    if self.fallback_to_local():
                        logger.info("Successfully fell back to local strategy")
                    else:
                        raise Exception("Fallback to local strategy failed")
                else:
                    raise Exception("Current embedding strategy is unhealthy and fallback is disabled")
            
            return self.current_strategy
    
    def set_strategy(self, strategy_name: str, force: bool = False) -> bool:
        """Set the active embedding strategy with dimension compatibility checking.
        
        Args:
            strategy_name: Name of strategy to activate ('bedrock' or 'local')
            force: If True, skip dimension compatibility warning (default: False)
            
        Returns:
            True if strategy was set successfully, False otherwise
        """
        with self._lock:
            if strategy_name not in self.strategies:
                logger.error(f"Unknown strategy: {strategy_name}")
                return False
            
            strategy = self.strategies[strategy_name]
            
            # Verify strategy is healthy before setting
            if not strategy.health_check():
                logger.warning(f"Strategy '{strategy_name}' failed health check")
                return False
            
            # Check dimension compatibility if switching strategies
            if self.current_strategy and not force:
                current_dim = self.current_strategy.get_dimension()
                new_dim = strategy.get_dimension()
                
                if current_dim != new_dim:
                    logger.warning(
                        f"⚠️  DIMENSION MISMATCH WARNING ⚠️\n"
                        f"Switching from {self.get_current_strategy_name()} ({current_dim}d) "
                        f"to {strategy_name} ({new_dim}d).\n"
                        f"This will cause errors if you try to add embeddings to existing collections!\n"
                        f"You must either:\n"
                        f"  1. Create a new collection with the new dimension, OR\n"
                        f"  2. Migrate existing collections using EmbeddingMigrationTool\n"
                        f"To suppress this warning, use set_strategy('{strategy_name}', force=True)"
                    )
            
            self.current_strategy = strategy
            logger.info(f"Active embedding strategy: {strategy_name} ({strategy.get_dimension()}d)")
            return True
    
    def fallback_to_local(self) -> bool:
        """Fallback from AWS Bedrock to local strategy.
        
        Returns:
            True if fallback was successful, False otherwise
        """
        # Check if already using local strategy
        if self.current_strategy == self.strategies.get('local'):
            logger.warning("Already using local strategy, cannot fallback")
            return False
        
        # Check if local strategy is available
        if 'local' not in self.strategies:
            logger.error("Local strategy not available for fallback")
            return False
        
        # Attempt to set local strategy
        logger.info("Falling back to local embedding strategy")
        return self.set_strategy('local')
    
    def get_current_strategy_name(self) -> Optional[str]:
        """Get the name of the current strategy.
        
        Returns:
            Name of current strategy or None if not set
        """
        if not self.current_strategy:
            return None
        
        for name, strategy in self.strategies.items():
            if strategy == self.current_strategy:
                return name
        
        return None
    
    def get_available_strategies(self) -> Dict[str, bool]:
        """Get list of available strategies and their health status.
        
        Returns:
            Dictionary mapping strategy names to health status
        """
        return {
            name: strategy.health_check()
            for name, strategy in self.strategies.items()
        }
    
    def get_all_metrics(self) -> Dict[str, dict]:
        """Get performance metrics for all strategies.
        
        Returns:
            Dictionary mapping strategy names to their metrics
        """
        metrics = {}
        for name, strategy in self.strategies.items():
            if hasattr(strategy, 'get_metrics'):
                metrics[name] = strategy.get_metrics().to_dict()
            else:
                metrics[name] = None
        return metrics
