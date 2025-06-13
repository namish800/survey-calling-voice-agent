"""
Configuration loading utilities for LiveKit Configurable Agents.

This module provides utilities for loading agent configurations from various sources
including local files and remote services, with support for different environments.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import aiohttp

from .config import AgentConfig

logger = logging.getLogger(__name__)


class ConfigurationLoader:
    """Utility class for loading agent configurations from various sources."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration loader.
        
        Args:
            config_dir: Base directory for configuration files
        """
        if config_dir is None:
            config_dir = os.getenv("AGENT_CONFIG_DIR")
            if config_dir is None:
                raise ValueError("AGENT_CONFIG_DIR environment variable is not set")
            
        self.config_dir = Path(config_dir)
        self.environment = os.getenv("ENVIRONMENT", "development")
    
    def load_from_file(self, file_path: str) -> Optional[AgentConfig]:
        """Load agent configuration from a local JSON file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            AgentConfig instance or None if loading fails
        """
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            
            logger.info(f"Loaded configuration from {file_path}")
            return AgentConfig.from_dict(config_data)
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading configuration from {file_path}: {e}")
            return None
    
    def load_by_agent_id(self, agent_id: str) -> Optional[AgentConfig]:
        """Load agent configuration by agent ID from environment-specific directory.
        
        Args:
            agent_id: Unique identifier for the agent
            environment: Environment name (defaults to current environment)
            
        Returns:
            AgentConfig instance or None if not found
        """
        config_file = self.config_dir / f"{agent_id}.json"
        
        logger.info(f"Looking for configuration: {config_file}")
        return self.load_from_file(str(config_file))

# Convenience functions for common operations
def load_config_from_file(file_path: str) -> Optional[AgentConfig]:
    """Load configuration from a single file."""
    loader = ConfigurationLoader()
    return loader.load_from_file(file_path)


def load_config_by_id(agent_id: str) -> Optional[AgentConfig]:
    """Load configuration by agent ID."""
    loader = ConfigurationLoader()
    return loader.load_by_agent_id(agent_id)