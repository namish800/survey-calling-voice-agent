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
    
    def __init__(self, config_dir: str = "configs"):
        """Initialize configuration loader.
        
        Args:
            config_dir: Base directory for configuration files
        """
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
    
    def load_by_agent_id(self, agent_id: str, environment: Optional[str] = None) -> Optional[AgentConfig]:
        """Load agent configuration by agent ID from environment-specific directory.
        
        Args:
            agent_id: Unique identifier for the agent
            environment: Environment name (defaults to current environment)
            
        Returns:
            AgentConfig instance or None if not found
        """
        env = environment or self.environment
        config_file = self.config_dir / env / f"{agent_id}.json"
        
        logger.info(f"Looking for configuration: {config_file}")
        return self.load_from_file(str(config_file))
    
    def load_default_config(self, environment: Optional[str] = None) -> Optional[AgentConfig]:
        """Load default agent configuration.
        
        Args:
            environment: Environment name (defaults to current environment)
            
        Returns:
            AgentConfig instance or None if not found
        """
        env = environment or self.environment
        default_config_file = self.config_dir / env / "default.json"
        
        logger.info(f"Loading default configuration: {default_config_file}")
        return self.load_from_file(str(default_config_file))
    
    def list_available_configs(self, environment: Optional[str] = None) -> List[str]:
        """List all available configuration files in an environment.
        
        Args:
            environment: Environment name (defaults to current environment)
            
        Returns:
            List of available agent IDs
        """
        env = environment or self.environment
        env_dir = self.config_dir / env
        
        if not env_dir.exists():
            logger.warning(f"Environment directory not found: {env_dir}")
            return []
        
        config_files = list(env_dir.glob("*.json"))
        agent_ids = [f.stem for f in config_files if f.stem != "default"]
        
        logger.info(f"Found {len(agent_ids)} configurations in {env}")
        return agent_ids
    
    def validate_config_file(self, file_path: str) -> List[str]:
        """Validate a configuration file and return any issues.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            List of validation issues (empty if valid)
        """
        config = self.load_from_file(file_path)
        if not config:
            return ["Failed to load configuration"]
        
        return config.validate()
    
    def create_config_from_template(self, 
                                   agent_id: str, 
                                   template_name: str,
                                   output_file: Optional[str] = None,
                                   **kwargs) -> Optional[AgentConfig]:
        """Create a new configuration from a template.
        
        Args:
            agent_id: ID for the new agent
            template_name: Name of the template to use
            output_file: Optional file path to save the configuration
            **kwargs: Additional parameters to customize the template
            
        Returns:
            AgentConfig instance or None if template not found
        """
        template_file = self.config_dir / "templates" / f"{template_name}.json"
        
        if not template_file.exists():
            logger.error(f"Template not found: {template_file}")
            return None
        
        try:
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            
            # Customize template with provided parameters
            template_data["agent_id"] = agent_id
            template_data.update(kwargs)
            
            config = AgentConfig.from_dict(template_data)
            
            # Save to file if requested
            if output_file:
                self.save_config(config, output_file)
            
            logger.info(f"Created configuration from template {template_name}")
            return config
            
        except Exception as e:
            logger.error(f"Error creating configuration from template: {e}")
            return None
    
    def save_config(self, config: AgentConfig, file_path: str) -> bool:
        """Save an agent configuration to a file.
        
        Args:
            config: AgentConfig instance to save
            file_path: Path where to save the configuration
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(config.to_json())
            
            logger.info(f"Saved configuration to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration to {file_path}: {e}")
            return False


class RemoteConfigurationService:
    """Client for loading configurations from remote service."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """Initialize remote configuration service.
        
        Args:
            base_url: Base URL of the configuration service
            api_key: Optional API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key
    
    async def load_agent_config(self, 
                               agent_id: str, 
                               metadata: Optional[Dict[str, Any]] = None) -> Optional[AgentConfig]:
        """Load agent configuration from remote service.
        
        Args:
            agent_id: Unique identifier for the agent
            metadata: Optional metadata for configuration selection
            
        Returns:
            AgentConfig instance or None if loading fails
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                payload = {
                    "agent_id": agent_id,
                    "metadata": metadata or {}
                }
                
                async with session.post(
                    f"{self.base_url}/agent-config",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        config_data = await response.json()
                        logger.info(f"Loaded configuration for {agent_id} from remote service")
                        return AgentConfig.from_dict(config_data)
                    else:
                        logger.error(f"Failed to load config from remote service: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error loading configuration from remote service: {e}")
            return None
    
    async def list_available_configs(self) -> List[str]:
        """List available configurations from remote service.
        
        Returns:
            List of available agent IDs
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                async with session.get(
                    f"{self.base_url}/configs",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("agent_ids", [])
                    else:
                        logger.error(f"Failed to list configs from remote service: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error listing configurations from remote service: {e}")
            return []


class HybridConfigurationLoader:
    """Configuration loader that tries multiple sources in order."""
    
    def __init__(self, 
                 config_dir: str = "configs",
                 remote_service_url: Optional[str] = None,
                 remote_api_key: Optional[str] = None):
        """Initialize hybrid configuration loader.
        
        Args:
            config_dir: Local configuration directory
            remote_service_url: Optional remote service URL
            remote_api_key: Optional API key for remote service
        """
        self.local_loader = ConfigurationLoader(config_dir)
        
        self.remote_service = None
        if remote_service_url:
            self.remote_service = RemoteConfigurationService(
                remote_service_url, 
                remote_api_key
            )
    
    async def load_configuration(self, 
                               agent_id: str, 
                               metadata: Optional[Dict[str, Any]] = None) -> Optional[AgentConfig]:
        """Load configuration using multiple sources in priority order.
        
        Priority:
        1. Remote service (if configured)
        2. Local file by agent ID
        3. Default local configuration
        
        Args:
            agent_id: Agent identifier
            metadata: Optional metadata for configuration selection
            
        Returns:
            AgentConfig instance or None if not found
        """
        logger.info(f"Loading configuration for agent: {agent_id}")
        
        # Try remote service first (if configured)
        if self.remote_service:
            try:
                config = await self.remote_service.load_agent_config(agent_id, metadata)
                if config:
                    logger.info(f"Loaded {agent_id} configuration from remote service")
                    return config
            except Exception as e:
                logger.warning(f"Remote service failed, falling back to local: {e}")
        
        # Try local configuration by agent ID
        config = self.local_loader.load_by_agent_id(agent_id)
        if config:
            logger.info(f"Loaded {agent_id} configuration from local file")
            return config
        
        # Fall back to default configuration
        config = self.local_loader.load_default_config()
        if config:
            logger.info(f"Loaded default configuration for {agent_id}")
            # Update agent_id to match request
            config.agent_id = agent_id
            return config
        
        logger.error(f"No configuration found for agent: {agent_id}")
        return None
    
    def validate_all_configs(self, environment: Optional[str] = None) -> Dict[str, List[str]]:
        """Validate all local configuration files.
        
        Args:
            environment: Environment to validate (defaults to current)
            
        Returns:
            Dictionary mapping config names to validation issues
        """
        results = {}
        
        agent_ids = self.local_loader.list_available_configs(environment)
        
        for agent_id in agent_ids:
            config_file = self.local_loader.config_dir / (environment or self.local_loader.environment) / f"{agent_id}.json"
            issues = self.local_loader.validate_config_file(str(config_file))
            results[agent_id] = issues
        
        # Also validate default config
        default_config_file = self.local_loader.config_dir / (environment or self.local_loader.environment) / "default.json"
        if default_config_file.exists():
            issues = self.local_loader.validate_config_file(str(default_config_file))
            results["default"] = issues
        
        return results


# Convenience functions for common operations
def load_config_from_file(file_path: str) -> Optional[AgentConfig]:
    """Load configuration from a single file."""
    loader = ConfigurationLoader()
    return loader.load_from_file(file_path)


def load_config_by_id(agent_id: str, environment: Optional[str] = None) -> Optional[AgentConfig]:
    """Load configuration by agent ID."""
    loader = ConfigurationLoader()
    return loader.load_by_agent_id(agent_id, environment)


async def load_config_hybrid(agent_id: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> Optional[AgentConfig]:
    """Load configuration using hybrid approach (remote + local fallback)."""
    remote_url = os.getenv("CONFIG_SERVICE_URL")
    remote_key = os.getenv("CONFIG_SERVICE_API_KEY")
    
    loader = HybridConfigurationLoader()
    
    return await loader.load_configuration(agent_id, metadata)


def list_available_configs(environment: str = "development") -> List[str]:
    """List all available configuration IDs in an environment.
    
    Args:
        environment: Environment to list configs from
        
    Returns:
        List of configuration IDs
    """
    loader = ConfigurationLoader()
    return loader.list_available_configs(environment) 