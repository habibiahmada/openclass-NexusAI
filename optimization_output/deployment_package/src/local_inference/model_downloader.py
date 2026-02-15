"""
Model downloader with HuggingFace integration for Phase 3 local inference.

This module provides robust model downloading capabilities with resume support,
progress tracking, and bandwidth optimization for the OpenClass Nexus AI system.
"""

import os
import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable, Iterator
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm

from .model_config import ModelConfig
from .hf_client import HuggingFaceClient, get_hf_client
from .error_handler import handle_network_error, ErrorCategory, ErrorContext

# Configure logging
logger = logging.getLogger(__name__)


class DownloadProgress:
    """Progress tracking for model downloads."""
    
    def __init__(self, total_size: int, filename: str):
        self.total_size = total_size
        self.filename = filename
        self.downloaded = 0
        self.start_time = time.time()
        self.last_update = time.time()
        self.speed_samples = []
        
    def update(self, chunk_size: int) -> None:
        """Update progress with downloaded chunk size."""
        self.downloaded += chunk_size
        current_time = time.time()
        
        # Calculate speed (bytes per second)
        if current_time - self.last_update >= 1.0:  # Update speed every second
            elapsed = current_time - self.last_update
            speed = chunk_size / elapsed if elapsed > 0 else 0
            self.speed_samples.append(speed)
            
            # Keep only last 10 samples for average
            if len(self.speed_samples) > 10:
                self.speed_samples.pop(0)
            
            self.last_update = current_time
    
    def get_progress_info(self) -> Dict[str, Any]:
        """Get current progress information."""
        elapsed_time = time.time() - self.start_time
        progress_percent = (self.downloaded / self.total_size * 100) if self.total_size > 0 else 0
        
        # Calculate average speed
        avg_speed = sum(self.speed_samples) / len(self.speed_samples) if self.speed_samples else 0
        
        # Estimate remaining time
        remaining_bytes = self.total_size - self.downloaded
        eta_seconds = remaining_bytes / avg_speed if avg_speed > 0 else 0
        
        return {
            'filename': self.filename,
            'total_size_mb': round(self.total_size / (1024 * 1024), 2),
            'downloaded_mb': round(self.downloaded / (1024 * 1024), 2),
            'progress_percent': round(progress_percent, 1),
            'speed_mbps': round(avg_speed / (1024 * 1024), 2),
            'elapsed_seconds': round(elapsed_time, 1),
            'eta_seconds': round(eta_seconds, 1),
            'is_complete': self.downloaded >= self.total_size
        }


class ModelDownloader:
    """
    Model downloader with HuggingFace integration and resume capability.
    
    This class handles downloading GGUF models from HuggingFace Hub with
    robust error handling, progress tracking, and bandwidth optimization.
    """
    
    def __init__(self, cache_dir: str = "./models", chunk_size: int = 8192):
        """
        Initialize the model downloader.
        
        Args:
            cache_dir: Directory for caching downloaded models
            chunk_size: Size of download chunks in bytes (default 8KB)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_size = chunk_size
        
        # Initialize HuggingFace client
        self.hf_client = get_hf_client(cache_dir=str(cache_dir))
        
        # Setup requests session with retry logic and timeout
        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set reasonable timeout
        self.session.timeout = (30, 300)  # (connect, read) timeout in seconds
    
    def get_remote_file_info(self, model_config: ModelConfig) -> Dict[str, Any]:
        """
        Get information about the remote file without downloading it.
        
        Args:
            model_config: Configuration for the model to check
            
        Returns:
            Dict containing file information
            
        Raises:
            requests.RequestException: If unable to access the remote file
        """
        try:
            # First try to get info from HuggingFace API
            try:
                hf_info = self.hf_client.get_model_info(model_config)
                if hf_info.get('size_bytes', 0) > 0:
                    return {
                        'size_bytes': hf_info['size_bytes'],
                        'size_mb': hf_info['size_mb'],
                        'checksum': hf_info.get('sha'),
                        'last_modified': hf_info.get('last_modified'),
                        'source': 'hf_api'
                    }
            except Exception as e:
                logger.warning(f"Could not get file info from HF API: {e}")
            
            # Fallback to HEAD request
            url = model_config.get_download_url()
            headers = self.hf_client.get_download_headers()
            
            response = self.session.head(url, headers=headers, allow_redirects=True)
            response.raise_for_status()
            
            # Get file size from headers
            content_length = response.headers.get('content-length')
            if not content_length:
                raise ValueError("Remote file size not available")
            
            size_bytes = int(content_length)
            size_mb = round(size_bytes / (1024 * 1024), 2)
            
            # Get last modified date if available
            last_modified = response.headers.get('last-modified')
            
            # Get ETag as a form of checksum
            etag = response.headers.get('etag', '').strip('"')
            
            return {
                'size_bytes': size_bytes,
                'size_mb': size_mb,
                'checksum': etag,
                'last_modified': last_modified,
                'source': 'http_head'
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to get remote file info: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting file info: {e}")
            raise
    
    def calculate_file_checksum(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """
        Calculate checksum of a local file.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use (default: sha256)
            
        Returns:
            Hexadecimal checksum string
        """
        hash_obj = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                while chunk := f.read(self.chunk_size * 1024):  # Use larger chunks for hashing
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            raise
    
    def check_existing_file(self, model_config: ModelConfig) -> Dict[str, Any]:
        """
        Check if a model file already exists and validate it.
        
        Args:
            model_config: Configuration for the model to check
            
        Returns:
            Dict containing file status information
        """
        model_path = model_config.get_model_path()
        
        if not model_path.exists():
            return {
                'exists': False,
                'valid': False,
                'size_bytes': 0,
                'needs_download': True,
                'resume_possible': False
            }
        
        try:
            # Get local file size
            local_size = model_path.stat().st_size
            
            # Get remote file info for comparison
            try:
                remote_info = self.get_remote_file_info(model_config)
                remote_size = remote_info['size_bytes']
                
                # Check if file is complete
                is_complete = local_size == remote_size
                resume_possible = local_size < remote_size and local_size > 0
                
                return {
                    'exists': True,
                    'valid': is_complete,
                    'size_bytes': local_size,
                    'expected_size_bytes': remote_size,
                    'needs_download': not is_complete,
                    'resume_possible': resume_possible,
                    'resume_from_byte': local_size if resume_possible else 0
                }
                
            except Exception as e:
                logger.warning(f"Could not verify file against remote: {e}")
                # If we can't check remote, assume local file is valid if it has reasonable size
                is_reasonable_size = local_size > 100 * 1024 * 1024  # > 100MB
                
                return {
                    'exists': True,
                    'valid': is_reasonable_size,
                    'size_bytes': local_size,
                    'needs_download': not is_reasonable_size,
                    'resume_possible': False
                }
                
        except Exception as e:
            logger.error(f"Error checking existing file: {e}")
            return {
                'exists': True,
                'valid': False,
                'size_bytes': 0,
                'needs_download': True,
                'resume_possible': False
            }
    
    def download_model(self, 
                      model_config: ModelConfig, 
                      progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                      force_redownload: bool = False,
                      max_retries: int = 3) -> Path:
        """
        Download a model with resume capability, progress tracking, and comprehensive error handling.
        
        Args:
            model_config: Configuration for the model to download
            progress_callback: Optional callback function for progress updates
            force_redownload: Force redownload even if file exists
            max_retries: Maximum number of retry attempts
            
        Returns:
            Path to the downloaded model file
            
        Raises:
            requests.RequestException: If download fails after all retries
            IOError: If file operations fail
        """
        model_path = model_config.get_model_path()
        
        # Check existing file unless forced redownload
        if not force_redownload:
            file_status = self.check_existing_file(model_config)
            
            if file_status['valid']:
                logger.info(f"Model already exists and is valid: {model_path}")
                return model_path
            
            if not file_status['needs_download']:
                logger.info(f"Model file exists but validation unclear: {model_path}")
                return model_path
        
        # Attempt download with retry logic
        for retry_count in range(max_retries + 1):
            try:
                return self._attempt_download(model_config, progress_callback, force_redownload, retry_count)
                
            except Exception as e:
                # Use comprehensive error handling
                error_result = handle_network_error(
                    error=e,
                    operation=f"download_model_{model_config.gguf_filename}",
                    url=model_config.get_download_url(),
                    retry_count=retry_count
                )
                
                logger.error(f"Download attempt {retry_count + 1} failed: {error_result.message}")
                
                # If retry is recommended and we haven't exceeded max retries
                if error_result.retry_recommended and retry_count < max_retries:
                    # Apply any delay suggested by error handler
                    delay = error_result.additional_info.get('delay_seconds', 0)
                    if delay > 0:
                        logger.info(f"Waiting {delay} seconds before retry...")
                        time.sleep(delay)
                    continue
                else:
                    # No more retries or retry not recommended
                    if error_result.fallback_available:
                        logger.error(f"Download failed after {retry_count + 1} attempts. Check if model exists locally.")
                    
                    # Re-raise the original exception with context
                    raise Exception(f"Download failed after {retry_count + 1} attempts: {error_result.message}") from e
        
        # This should never be reached due to the loop logic above
        raise Exception(f"Download failed after {max_retries + 1} attempts")
    
    def _attempt_download(self, 
                         model_config: ModelConfig, 
                         progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                         force_redownload: bool = False,
                         retry_count: int = 0) -> Path:
        """
        Single attempt to download a model.
        
        Args:
            model_config: Configuration for the model to download
            progress_callback: Optional callback function for progress updates
            force_redownload: Force redownload even if file exists
            retry_count: Current retry attempt number
            
        Returns:
            Path to the downloaded model file
        """
        model_path = model_config.get_model_path()
        
        # Get remote file information
        try:
            remote_info = self.get_remote_file_info(model_config)
            total_size = remote_info['size_bytes']
            
            logger.info(f"Starting download of {model_config.gguf_filename} ({remote_info['size_mb']} MB) - attempt {retry_count + 1}")
            
        except Exception as e:
            logger.error(f"Failed to get remote file info: {e}")
            raise
        
        # Determine resume position
        resume_from = 0
        if not force_redownload and model_path.exists():
            file_status = self.check_existing_file(model_config)
            if file_status.get('resume_possible', False):
                resume_from = file_status['resume_from_byte']
                logger.info(f"Resuming download from byte {resume_from}")
        
        # Setup download request
        url = model_config.get_download_url()
        headers = self.hf_client.get_download_headers()
        
        # Add range header for resume
        if resume_from > 0:
            headers['Range'] = f'bytes={resume_from}-'
        
        # Initialize progress tracking
        progress = DownloadProgress(total_size, model_config.gguf_filename)
        progress.downloaded = resume_from
        
        try:
            # Start download
            response = self.session.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Verify partial content response for resume
            if resume_from > 0 and response.status_code != 206:
                logger.warning("Server doesn't support resume, starting from beginning")
                resume_from = 0
                progress.downloaded = 0
                # Restart without range header
                headers.pop('Range', None)
                response = self.session.get(url, headers=headers, stream=True)
                response.raise_for_status()
            
            # Open file for writing (append mode if resuming)
            file_mode = 'ab' if resume_from > 0 else 'wb'
            
            with open(model_path, file_mode) as f:
                # Download with progress tracking
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
                        progress.update(len(chunk))
                        
                        # Call progress callback if provided
                        if progress_callback:
                            try:
                                progress_callback(progress.get_progress_info())
                            except Exception as callback_error:
                                logger.warning(f"Progress callback error: {callback_error}")
            
            # Verify final file size
            final_size = model_path.stat().st_size
            if final_size != total_size:
                raise IOError(f"Download incomplete: expected {total_size} bytes, got {final_size} bytes")
            
            logger.info(f"Successfully downloaded {model_config.gguf_filename}")
            return model_path
            
        except requests.RequestException as e:
            logger.error(f"Download failed: {e}")
            # Clean up partial file if it's a new download (not resume)
            if resume_from == 0 and model_path.exists():
                try:
                    model_path.unlink()
                    logger.info("Cleaned up partial download file")
                except Exception as cleanup_error:
                    logger.warning(f"Could not clean up partial file: {cleanup_error}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            raise
    
    def download_with_progress_bar(self, model_config: ModelConfig, force_redownload: bool = False) -> Path:
        """
        Download a model with a visual progress bar.
        
        Args:
            model_config: Configuration for the model to download
            force_redownload: Force redownload even if file exists
            
        Returns:
            Path to the downloaded model file
        """
        progress_bar = None
        
        def progress_callback(progress_info: Dict[str, Any]) -> None:
            nonlocal progress_bar
            
            if progress_bar is None:
                progress_bar = tqdm(
                    total=progress_info['total_size_mb'],
                    unit='MB',
                    desc=f"Downloading {progress_info['filename']}",
                    initial=progress_info['downloaded_mb']
                )
            
            # Update progress bar
            progress_bar.n = progress_info['downloaded_mb']
            progress_bar.set_postfix({
                'speed': f"{progress_info['speed_mbps']:.1f} MB/s",
                'eta': f"{progress_info['eta_seconds']:.0f}s"
            })
            progress_bar.refresh()
        
        try:
            result = self.download_model(model_config, progress_callback, force_redownload)
            
            if progress_bar:
                progress_bar.close()
            
            return result
            
        except Exception as e:
            if progress_bar:
                progress_bar.close()
            raise
    
    def verify_download(self, model_config: ModelConfig, expected_checksum: Optional[str] = None) -> bool:
        """
        Verify the integrity of a downloaded model.
        
        Args:
            model_config: Configuration for the model to verify
            expected_checksum: Expected checksum (optional)
            
        Returns:
            bool: True if verification passes, False otherwise
        """
        model_path = model_config.get_model_path()
        
        if not model_path.exists():
            logger.error(f"Model file does not exist: {model_path}")
            return False
        
        try:
            # Check file size first (quick check)
            file_size = model_path.stat().st_size
            
            # Get expected size from remote if possible
            try:
                remote_info = self.get_remote_file_info(model_config)
                expected_size = remote_info['size_bytes']
                
                if file_size != expected_size:
                    logger.error(f"File size mismatch: expected {expected_size}, got {file_size}")
                    return False
                    
            except Exception as e:
                logger.warning(f"Could not verify file size: {e}")
            
            # Verify checksum if provided
            if expected_checksum:
                logger.info("Calculating file checksum for verification...")
                actual_checksum = self.calculate_file_checksum(model_path)
                
                if actual_checksum.lower() != expected_checksum.lower():
                    logger.error(f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}")
                    return False
                
                logger.info("Checksum verification passed")
            
            logger.info(f"Model verification successful: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    def get_download_status(self, model_config: ModelConfig) -> Dict[str, Any]:
        """
        Get comprehensive download status for a model.
        
        Args:
            model_config: Configuration for the model to check
            
        Returns:
            Dict containing detailed status information
        """
        try:
            # Check local file
            file_status = self.check_existing_file(model_config)
            
            # Get remote info
            remote_info = None
            try:
                remote_info = self.get_remote_file_info(model_config)
            except Exception as e:
                logger.warning(f"Could not get remote info: {e}")
            
            # Compile status
            status = {
                'model_id': model_config.model_id,
                'filename': model_config.gguf_filename,
                'local_path': str(model_config.get_model_path()),
                'file_exists': file_status['exists'],
                'file_valid': file_status['valid'],
                'needs_download': file_status['needs_download'],
                'resume_possible': file_status.get('resume_possible', False),
                'local_size_mb': round(file_status['size_bytes'] / (1024 * 1024), 2),
                'remote_available': remote_info is not None
            }
            
            if remote_info:
                status.update({
                    'remote_size_mb': remote_info['size_mb'],
                    'download_url': model_config.get_download_url(),
                    'last_modified': remote_info.get('last_modified')
                })
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting download status: {e}")
            return {
                'model_id': model_config.model_id,
                'filename': model_config.gguf_filename,
                'error': str(e),
                'status': 'error'
            }