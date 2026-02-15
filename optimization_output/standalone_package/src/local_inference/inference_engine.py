"""
Local inference engine for OpenClass Nexus AI Phase 3.

This module provides the core inference engine that loads and runs
Llama-3.2-3B-Instruct model locally with memory management optimized
for 4GB RAM systems.
"""

import gc
import logging
import psutil
from pathlib import Path
from typing import Iterator, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

from .model_config import InferenceConfig
from .graceful_degradation import GracefulDegradationManager
from .error_handler import handle_model_error, handle_inference_error, ErrorCategory, ErrorContext


logger = logging.getLogger(__name__)


@dataclass
class InferenceMetrics:
    """Metrics for tracking inference performance."""
    response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    tokens_per_second: float
    context_tokens: int
    response_tokens: int
    timestamp: datetime
    
    def is_within_targets(self) -> bool:
        """Check if metrics meet performance targets."""
        return (
            self.response_time_ms < 10000 and  # < 10 seconds
            self.memory_usage_mb < 3072 and    # < 3GB
            self.tokens_per_second > 5         # > 5 tokens/sec
        )


class InferenceEngine:
    """
    Local inference engine for Llama-3.2-3B-Instruct model.
    
    This engine is optimized for 4GB RAM systems and provides:
    - Memory-efficient model loading
    - Streaming response generation
    - Graceful resource management
    - Performance monitoring
    """
    
    def __init__(self, model_path: str, config: InferenceConfig, 
                 degradation_manager: Optional[GracefulDegradationManager] = None):
        """
        Initialize the inference engine.
        
        Args:
            model_path: Path to the GGUF model file
            config: Inference configuration with optimization settings
            degradation_manager: Optional graceful degradation manager
        """
        self.model_path = Path(model_path)
        self.config = config
        self.degradation_manager = degradation_manager
        self.llm: Optional[Llama] = None
        self.is_loaded = False
        self.process = psutil.Process()
        
        # Validate dependencies
        if Llama is None:
            raise ImportError(
                "llama-cpp-python is not installed. "
                "Please install it with: pip install llama-cpp-python"
            )
        
        # Validate model file exists
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        logger.info(f"Initialized InferenceEngine with model: {self.model_path}")
        logger.info(f"Configuration: {config}")
    
    def load_model(self) -> bool:
        """
        Load the GGUF model with optimal configuration for 4GB systems.
        
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        if self.is_loaded:
            logger.warning("Model is already loaded")
            return True
        
        try:
            # Check available memory before loading
            available_memory = self._get_available_memory_mb()
            if available_memory < 2000:  # Need at least 2GB free
                logger.error(f"Insufficient memory: {available_memory}MB available, need at least 2000MB")
                return False
            
            logger.info(f"Loading model from {self.model_path}")
            logger.info(f"Available memory: {available_memory}MB")
            
            # Get llama.cpp parameters with degradation adjustments
            llama_params = self.config.get_llama_cpp_params()
            
            # Apply degradation adjustments if available
            if self.degradation_manager:
                adjustments = self.degradation_manager.get_inference_config_adjustments()
                llama_params.update({
                    'n_ctx': adjustments.get('n_ctx', llama_params.get('n_ctx', 4096)),
                    'n_threads': adjustments.get('n_threads', llama_params.get('n_threads', 4))
                })
                logger.info(f"Applied degradation adjustments: {adjustments}")
            
            # Load the model
            self.llm = Llama(
                model_path=str(self.model_path),
                **llama_params
            )
            
            self.is_loaded = True
            
            # Log memory usage after loading
            memory_usage = self._get_memory_usage_mb()
            logger.info(f"Model loaded successfully. Memory usage: {memory_usage}MB")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            
            # Use comprehensive error handling
            error_result = handle_model_error(
                error=e,
                operation="load_model",
                model_path=str(self.model_path)
            )
            
            logger.error(f"Model loading error: {error_result.message}")
            
            # Apply recovery actions if suggested
            if error_result.recovery_action == "optimize_memory_usage":
                # Force garbage collection and try again with reduced settings
                gc.collect()
                
                # Try with reduced context window
                if hasattr(self.config, 'n_ctx') and self.config.n_ctx > 2048:
                    logger.info("Retrying with reduced context window")
                    original_ctx = self.config.n_ctx
                    self.config.n_ctx = 2048
                    
                    try:
                        llama_params = self.config.get_llama_cpp_params()
                        self.llm = Llama(
                            model_path=str(self.model_path),
                            **llama_params
                        )
                        self.is_loaded = True
                        logger.info("Model loaded successfully with reduced context window")
                        return True
                    except Exception as retry_error:
                        logger.error(f"Retry with reduced context failed: {retry_error}")
                        self.config.n_ctx = original_ctx  # Restore original setting
            
            self.llm = None
            self.is_loaded = False
            return False
    
    def generate_response(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Generate streaming response with memory management and error handling.
        
        Args:
            prompt: Input prompt for generation
            max_tokens: Maximum tokens to generate (overrides config)
            **kwargs: Additional generation parameters
            
        Yields:
            str: Generated text chunks
            
        Raises:
            RuntimeError: If model is not loaded
            MemoryError: If insufficient memory for generation
        """
        if not self.is_loaded or self.llm is None:
            raise RuntimeError("Model is not loaded. Call load_model() first.")
        
        # Check memory before generation
        if not self._check_memory_available(512):  # Need 512MB free
            raise MemoryError("Insufficient memory for generation")
        
        # Prepare generation parameters
        gen_params = self.config.get_generation_params()
        if max_tokens is not None:
            gen_params['max_tokens'] = max_tokens
        gen_params.update(kwargs)
        
        start_time = datetime.now()
        response_tokens = 0
        
        try:
            logger.debug(f"Generating response for prompt length: {len(prompt)}")
            
            # Generate streaming response
            for output in self.llm(prompt, **gen_params):
                if 'choices' in output and len(output['choices']) > 0:
                    choice = output['choices'][0]
                    if 'text' in choice:
                        text_chunk = choice['text']
                        response_tokens += 1
                        yield text_chunk
                    
                    # Check if generation is complete
                    if choice.get('finish_reason') is not None:
                        break
            
            # Log performance metrics
            end_time = datetime.now()
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            tokens_per_second = response_tokens / (response_time_ms / 1000) if response_time_ms > 0 else 0
            
            logger.debug(f"Generation completed: {response_tokens} tokens in {response_time_ms:.1f}ms ({tokens_per_second:.1f} tokens/sec)")
            
        except Exception as e:
            logger.error(f"Error during response generation: {e}")
            
            # Use comprehensive error handling
            current_memory = self._get_memory_usage_mb()
            error_result = handle_inference_error(
                error=e,
                operation="generate_response",
                query=prompt[:100] if len(prompt) > 100 else prompt,
                memory_usage=current_memory
            )
            
            logger.error(f"Inference error: {error_result.message}")
            
            # Apply recovery actions if suggested
            if error_result.recovery_action == "reduce_context_length":
                # Try with shorter prompt
                if len(prompt) > 1000:
                    logger.info("Retrying with truncated prompt")
                    truncated_prompt = prompt[:1000] + "..."
                    try:
                        for output in self.llm(truncated_prompt, **gen_params):
                            if 'choices' in output and len(output['choices']) > 0:
                                choice = output['choices'][0]
                                if 'text' in choice:
                                    yield choice['text']
                                if choice.get('finish_reason') is not None:
                                    break
                        return
                    except Exception as retry_error:
                        logger.error(f"Retry with truncated prompt failed: {retry_error}")
            
            elif error_result.recovery_action == "optimize_inference_speed":
                # Try with faster settings
                logger.info("Retrying with optimized settings")
                fast_params = gen_params.copy()
                fast_params['max_tokens'] = min(fast_params.get('max_tokens', 512), 256)
                fast_params['temperature'] = 0.1  # Lower temperature for faster generation
                
                try:
                    for output in self.llm(prompt, **fast_params):
                        if 'choices' in output and len(output['choices']) > 0:
                            choice = output['choices'][0]
                            if 'text' in choice:
                                yield choice['text']
                            if choice.get('finish_reason') is not None:
                                break
                    return
                except Exception as retry_error:
                    logger.error(f"Retry with optimized settings failed: {retry_error}")
            
            # If all recovery attempts fail, provide fallback response
            if error_result.fallback_available:
                fallback_message = error_result.additional_info.get(
                    'fallback_response', 
                    "Maaf, terjadi kesalahan saat menghasilkan respons. Silakan coba dengan pertanyaan yang lebih sederhana."
                )
                yield fallback_message
            else:
                # Re-raise the original exception
                raise
            
            logger.debug(f"Generation completed: {response_tokens} tokens in {response_time_ms:.1f}ms "
                        f"({tokens_per_second:.1f} tokens/sec)")
            
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            raise
    
    def unload_model(self) -> None:
        """
        Safely unload model to free memory.
        """
        if self.llm is not None:
            logger.info("Unloading model")
            del self.llm
            self.llm = None
        
        self.is_loaded = False
        
        # Force garbage collection to free memory
        gc.collect()
        
        memory_usage = self._get_memory_usage_mb()
        logger.info(f"Model unloaded. Memory usage: {memory_usage}MB")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        
        Returns:
            Dict containing memory usage, CPU usage, and model status
        """
        return {
            'is_loaded': self.is_loaded,
            'memory_usage_mb': self._get_memory_usage_mb(),
            'cpu_usage_percent': self.process.cpu_percent(),
            'available_memory_mb': self._get_available_memory_mb(),
            'model_path': str(self.model_path),
            'config': self.config.__dict__
        }
    
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert bytes to MB
        except Exception:
            return 0.0
    
    def _get_available_memory_mb(self) -> float:
        """Get available system memory in MB."""
        try:
            memory = psutil.virtual_memory()
            return memory.available / (1024 * 1024)  # Convert bytes to MB
        except Exception:
            return 0.0
    
    def _check_memory_available(self, required_mb: int) -> bool:
        """
        Check if enough memory is available.
        
        Args:
            required_mb: Required memory in MB
            
        Returns:
            bool: True if enough memory is available
        """
        available = self._get_available_memory_mb()
        return available >= required_mb
    
    def __enter__(self):
        """Context manager entry."""
        self.load_model()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.unload_model()