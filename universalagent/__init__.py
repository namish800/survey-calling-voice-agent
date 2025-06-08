"""
Universal Agent - A flexible, configuration-driven voice AI agent system built on LiveKit.

This package provides tools for creating, configuring, and deploying
intelligent voice agents with minimal code.
"""

# Core configuration and utilities
from .core import (
    AgentConfig,
    LLMConfig,
    TTSConfig,
    STTConfig,
    ConfigurationLoader,
    generate_system_instructions,
)

# Agent implementations
from .agents import (
    ConfigurableAgent,
    create_entrypoint,
)

# Component factories
from .components import (
    ComponentFactory,
    ComponentCreationError,
)

__version__ = "1.0.0"

__all__ = [
    # Core configuration
    "AgentConfig",
    "LLMConfig",
    "TTSConfig", 
    "STTConfig",
    "ConfigurationLoader",
    "generate_system_instructions",
    
    # Agents
    "ConfigurableAgent",
    "create_entrypoint",
    
    # Components
    "ComponentFactory",
    "ComponentCreationError",
    
    # Package info
    "__version__",
] 