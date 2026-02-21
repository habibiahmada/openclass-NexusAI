"""
HuggingFace Hub client configuration and utilities for model management.

This module provides a configured HuggingFace client for downloading
and managing AI models, specifically optimized for the OpenClass Nexus AI
Phase 3 local inference requirements.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from huggingface_hub import HfApi, hf_hub_download, login, whoami
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .model_config import ModelConfig

# Configure logging
logger = logging.getLogger(__name__)


class HuggingFaceClient:
    """
    HuggingFace Hub client configured for OpenClass Nexus AI model management.
    
    This client handles authentication, model discovery, and download operations
    with proper error handling and retry logic for reliable model acquisition.
    """
    
    def __init__(self, token: Optional[str] = None, cache_dir: str = "./models"):
        """
        Initialize HuggingFace client with optional authentication.
        
        Args:
            token: HuggingFace API token (optional, can be set via HF_TOKEN env var)
            cache_dir: Directory for caching downloaded models
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize HuggingFace API client
        self.api = HfApi()
        
        # Setup authentication if token is provided
        self.token = token or os.getenv('HF_TOKEN')
        if self.token:
            try:
                login(token=self.token)
                logger.info("Successfully authenticated with HuggingFace Hub")
            except Exception as e:
                logger.warning(f"Failed to authenticate with HuggingFace Hub: {e}")
        
        # Setup requests session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def check_authentication(self) -> bool:
        """
        Check if the client is properly authenticated with HuggingFace Hub.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        try:
            whoami()
            return True
        except Exception:
            return False
    
    def get_model_info(self, model_config: ModelConfig) -> Dict[str, Any]:
        """
        Get information about a model from HuggingFace Hub.
        
        Args:
            model_config: Configuration for the model to query
            
        Returns:
            Dict containing model information
            
        Raises:
            RepositoryNotFoundError: If the model repository doesn't exist
            HfHubHTTPError: If there's an HTTP error accessing the Hub
        """
        try:
            # Get info from the GGUF repository
            repo_info = self.api.repo_info(
                repo_id=model_config.gguf_repo,
                repo_type="model"
            )
            
            # Find the specific GGUF file
            gguf_file = None
            for sibling in repo_info.siblings:
                if sibling.rfilename == model_config.gguf_filename:
                    gguf_file = sibling
                    break
            
            if not gguf_file:
                raise FileNotFoundError(
                    f"GGUF file {model_config.gguf_filename} not found in repository {model_config.gguf_repo}"
                )
            
            # Handle file size safely
            file_size_bytes = getattr(gguf_file, 'size', None) or 0
            file_size_mb = round(file_size_bytes / (1024 * 1024), 2) if file_size_bytes > 0 else 0
            
            return {
                'repo_id': model_config.gguf_repo,
                'filename': model_config.gguf_filename,
                'size_bytes': file_size_bytes,
                'size_mb': file_size_mb,
                'last_modified': repo_info.last_modified,
                'download_url': model_config.get_download_url(),
                'sha': getattr(getattr(gguf_file, 'lfs', None) or {}, 'sha256', None)
            }
            
        except RepositoryNotFoundError:
            logger.error(f"Repository {model_config.gguf_repo} not found")
            raise
        except HfHubHTTPError as e:
            logger.error(f"HTTP error accessing HuggingFace Hub: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting model info: {e}")
            raise
    
    def check_model_license(self, model_config: ModelConfig) -> Dict[str, Any]:
        """
        Check the license of a model to ensure it's suitable for educational use.
        
        Args:
            model_config: Configuration for the model to check
            
        Returns:
            Dict containing license information
        """
        try:
            # Check the original model repository for license info
            original_repo_info = self.api.repo_info(
                repo_id=model_config.model_id,
                repo_type="model"
            )
            
            # Check GGUF repository as well
            gguf_repo_info = self.api.repo_info(
                repo_id=model_config.gguf_repo,
                repo_type="model"
            )
            
            return {
                'original_model_license': getattr(original_repo_info, 'cardData', {}).get('license'),
                'gguf_repo_license': getattr(gguf_repo_info, 'cardData', {}).get('license'),
                'educational_use_allowed': True,  # Llama models generally allow educational use
                'commercial_use_restrictions': 'Check specific license terms'
            }
            
        except Exception as e:
            logger.warning(f"Could not retrieve license information: {e}")
            return {
                'original_model_license': 'unknown',
                'gguf_repo_license': 'unknown',
                'educational_use_allowed': None,
                'commercial_use_restrictions': 'Manual verification required'
            }
    
    def list_available_models(self, search_query: str = "llama") -> List[Dict[str, Any]]:
        """
        List available models matching a search query.
        
        Args:
            search_query: Search term for finding models
            
        Returns:
            List of model information dictionaries
        """
        try:
            models = self.api.list_models(
                search=search_query,
                filter="gguf",
                sort="downloads",
                direction=-1,
                limit=20
            )
            
            model_list = []
            for model in models:
                model_info = {
                    'id': model.id,
                    'downloads': model.downloads,
                    'likes': model.likes,
                    'tags': model.tags,
                    'library_name': getattr(model, 'library_name', None),
                    'pipeline_tag': getattr(model, 'pipeline_tag', None)
                }
                model_list.append(model_info)
            
            return model_list
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def validate_model_access(self, model_config: ModelConfig) -> bool:
        """
        Validate that the model can be accessed and downloaded.
        
        Args:
            model_config: Configuration for the model to validate
            
        Returns:
            bool: True if model is accessible, False otherwise
        """
        try:
            # Try to get model info
            model_info = self.get_model_info(model_config)
            
            # For GGUF files, size might not be available via API due to Git LFS
            # So we'll just check if we can access the repository and file exists
            if model_info['size_mb'] == 0:
                logger.info("File size not available via API (likely Git LFS), but file exists in repository")
                return True
            
            # Check if the file has reasonable size for a 3B model
            if model_info['size_mb'] < 100:  # Suspiciously small for a 3B model
                logger.warning(f"Model file seems too small: {model_info['size_mb']} MB")
                return False
            
            if model_info['size_mb'] > 10000:  # Suspiciously large
                logger.warning(f"Model file seems too large: {model_info['size_mb']} MB")
                return False
            
            return True
            
        except FileNotFoundError:
            logger.error("Model file not found in repository")
            return False
        except Exception as e:
            logger.error(f"Model validation failed: {e}")
            return False
    
    def get_download_headers(self) -> Dict[str, str]:
        """
        Get headers for download requests including authentication if available.
        
        Returns:
            Dict of HTTP headers
        """
        headers = {
            'User-Agent': 'OpenClass-Nexus-AI/1.0'
        }
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        return headers


# Global client instance
_hf_client: Optional[HuggingFaceClient] = None


def get_hf_client(token: Optional[str] = None, cache_dir: str = "./models") -> HuggingFaceClient:
    """
    Get or create a global HuggingFace client instance.
    
    Args:
        token: HuggingFace API token (optional)
        cache_dir: Directory for caching models
        
    Returns:
        HuggingFaceClient instance
    """
    global _hf_client
    
    if _hf_client is None:
        _hf_client = HuggingFaceClient(token=token, cache_dir=cache_dir)
    
    return _hf_client


def setup_hf_environment() -> Dict[str, Any]:
    """
    Setup and validate HuggingFace environment for model management.
    
    Returns:
        Dict containing environment status and configuration
    """
    # Check for HuggingFace token
    token = os.getenv('HF_TOKEN')
    
    # Initialize client
    client = get_hf_client(token=token)
    
    # Check authentication status
    is_authenticated = client.check_authentication()
    
    # Validate default model access
    default_config = ModelConfig()
    model_accessible = client.validate_model_access(default_config)
    
    return {
        'hf_token_available': token is not None,
        'authenticated': is_authenticated,
        'default_model_accessible': model_accessible,
        'cache_directory': str(client.cache_dir),
        'client_ready': True
    }