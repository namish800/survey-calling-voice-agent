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
from supabase import create_client
from universalagent.core.config import AgentConfig

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
            with open(file_path, "r") as f:
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
    

class AgentConfigLoaderFromSupabase:
    """Utility class for loading agent configurations from Supabase."""

    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize agent configuration loader from Supabase.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key (anon key)
        """
        self.supabase = create_client(supabase_url, supabase_key)

    def load_by_agent_id(self, agent_id: str) -> Optional[AgentConfig]:
        """Load agent configuration by agent ID.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            AgentConfig instance or None if not found
        """
        try:
            logger.info(f"Loading configuration for agent_id: {agent_id}")
            response = self.supabase.table('agent_configurations').select('config').eq('agent_id', agent_id).single().execute()
            logger.info(f"Response: {response}")

            if response.data and response.data.get('config'):
                logger.info(f"Loaded configuration for agent_id: {agent_id}")
                return AgentConfig.from_dict(response.data['config'])
            else:
                logger.warning(f"No configuration found for agent_id: {agent_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading configuration for agent_id {agent_id}: {e}")
            return None

# Convenience functions for common operations
def load_config_from_file(file_path: str) -> Optional[AgentConfig]:
    """Load configuration from a single file."""
    loader = ConfigurationLoader()
    return loader.load_from_file(file_path)


def load_config_by_id(agent_id: str) -> Optional[AgentConfig]:
    """Load configuration by agent ID from file system."""
    loader = ConfigurationLoader()
    return loader.load_by_agent_id(agent_id)


def load_config_from_supabase(agent_id: str, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None) -> Optional[AgentConfig]:
    """Load configuration by agent ID from Supabase.
    
    Args:
        agent_id: Unique identifier for the agent
        supabase_url: Supabase project URL (defaults to SUPABASE_URL env var)
        supabase_key: Supabase API key (defaults to SUPABASE_ANON_KEY env var)
    
    Returns:
        AgentConfig instance or None if not found
    """
    if not supabase_url:
        supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_key:
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL and key must be provided or set as environment variables")
    
    loader = AgentConfigLoaderFromSupabase(supabase_url, supabase_key)
    return loader.load_by_agent_id(agent_id)


def create_supabase_loader(supabase_url: Optional[str] = None, supabase_key: Optional[str] = None) -> AgentConfigLoaderFromSupabase:
    """Create a Supabase loader with environment variable fallbacks.
    
    Args:
        supabase_url: Supabase project URL (defaults to SUPABASE_URL env var)
        supabase_key: Supabase API key (defaults to SUPABASE_ANON_KEY env var)
    
    Returns:
        AgentConfigLoaderFromSupabase instance
    """
    if not supabase_url:
        supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_key:
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL and key must be provided or set as environment variables")
    
    return AgentConfigLoaderFromSupabase(supabase_url, supabase_key)