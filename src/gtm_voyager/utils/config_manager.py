import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Configuration manager for GTM Voyager Platform."""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize the configuration manager."""
        self.config_file = Path(config_file)
        self.config = {}
        self.logger = self._setup_logger()
        self._load_config()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for ConfigManager operations."""
        logger = logging.getLogger('ConfigManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self.config = self._get_default_config()
                self.save_config()
                self.logger.info("Default configuration created")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "app": {
                "name": "GTM Voyager Platform",
                "version": "1.0.0",
                "debug": False
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000
            },
            "database": {
                "path": "gtm_voyager.db"
            },
            "openai": {
                "model": "whisper-1",
                "temperature": 0.0
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value by key."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
