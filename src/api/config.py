"""
API Configuration
Wrapper for app_config to provide API-specific configuration
"""

from config.app_config import app_config

# Export app_config as config for API modules
config = app_config
