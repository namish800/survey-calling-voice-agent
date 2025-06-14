"""
Validation utilities for the Universal Agent Config Builder.

This module provides safe import handling, configuration validation,
and error message formatting for user-friendly feedback.
"""

import sys
import os
from typing import Tuple, Optional, List, Dict, Any

def safe_import():
    """
    Safely import universalagent with user-friendly error handling.
    
    Returns:
        Tuple[ComponentFactory, AgentConfig, Optional[str]]: 
        ComponentFactory class, AgentConfig class, and error message if any
    """
    try:
        # Add the parent directory to Python path for importing universalagent
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.join(current_dir, '..', '..', '..')
        sys.path.insert(0, parent_dir)
        
        from universalagent.components.factory import ComponentFactory
        from universalagent.core.config import AgentConfig
        return ComponentFactory, AgentConfig, None
        
    except ImportError as e:
        error_msg = f"""
        ❌ **Import Error**: Cannot import universalagent package.
        
        **Solution**: Make sure you have:
        1. Cloned the entire repository
        2. Installed dependencies: `pip install -e .` (from repo root)
        3. Are running from the correct directory
        
        **Error Details**: {str(e)}
        """
        return None, None, error_msg
    except Exception as e:
        if "main thread" in str(e).lower():
            error_msg = f"""
            ❌ **Plugin Registration Error**: LiveKit plugins must be registered on the main thread.
            
            **Solution**: This is a known issue with Streamlit and LiveKit. Try:
            1. Run the app from the command line (not from an IDE)
            2. Restart your terminal/command prompt
            3. Make sure no other Python processes are running
            
            **Alternative**: Use the fallback mode (providers will be limited but functional)
            
            **Error Details**: {str(e)}
            """
        else:
            error_msg = f"""
            ❌ **Unexpected Error**: {str(e)}
            
            Please check your installation and try again.
            """
        return None, None, error_msg


def get_fallback_providers() -> Dict[str, List[str]]:
    """
    Get fallback provider information when ComponentFactory is not available.
    
    Returns:
        Dictionary with fallback provider lists
    """
    return {
        'llm': ['openai'],  # Only OpenAI is always available
        'tts': ['openai', 'deepgram', 'elevenlabs', 'cartesia', 'sarvam'],
        'stt': ['openai', 'deepgram', 'elevenlabs', 'sarvam']
    }


def safe_get_providers(ComponentFactory):
    """
    Safely get providers from ComponentFactory with fallback.
    
    Args:
        ComponentFactory: ComponentFactory class (may be None)
        
    Returns:
        Dictionary of providers
    """
    if ComponentFactory is None:
        return get_fallback_providers()
    
    try:
        factory = ComponentFactory()
        return factory.get_supported_providers()
    except Exception as e:
        if "main thread" in str(e).lower():
            # Return fallback providers for plugin registration issues
            return get_fallback_providers()
        else:
            # Re-raise other exceptions
            raise e


def validate_required_fields(config_data: Dict[str, Any]) -> List[str]:
    """
    Validate required fields in configuration data.
    
    Args:
        config_data: Configuration dictionary to validate
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    # Required fields
    required_fields = {
        'agent_id': 'Agent ID',
        'name': 'Agent Name', 
        'description': 'Description',
        'system_instructions': 'System Instructions'
    }
    
    for field, display_name in required_fields.items():
        if not config_data.get(field, '').strip():
            errors.append(f"{display_name} is required")
    
    # Validate agent_id format (no spaces, special chars)
    agent_id = config_data.get('agent_id', '')
    if agent_id and not agent_id.replace('_', '').replace('-', '').isalnum():
        errors.append("Agent ID can only contain letters, numbers, hyphens, and underscores")
    
    return errors


def validate_configuration(config_dict: Dict[str, Any], AgentConfig) -> Tuple[bool, List[str]]:
    """
    Validate complete configuration using AgentConfig class.
    
    Args:
        config_dict: Configuration dictionary
        AgentConfig: AgentConfig class for validation (may be None)
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    try:
        # First check required fields
        field_errors = validate_required_fields(config_dict)
        if field_errors:
            return False, field_errors
        
        # If AgentConfig is not available, do basic validation only
        if AgentConfig is None:
            # Basic validation without AgentConfig class
            issues = []
            
            # Check LLM config
            if not config_dict.get('llm_config'):
                issues.append("LLM configuration is required")
            
            # Check that at least one of TTS or STT is configured
            if not config_dict.get('tts_config') and not config_dict.get('stt_config'):
                issues.append("At least one of TTS or STT configuration is required")
            
            return len(issues) == 0, issues
        
        # Try to create AgentConfig object
        config = AgentConfig.from_dict(config_dict)
        
        # Use built-in validation
        issues = config.validate()
        
        if issues:
            return False, issues
        else:
            return True, []
            
    except Exception as e:
        return False, [f"Configuration Error: {str(e)}"]


def format_error_message(error: str) -> str:
    """
    Format error messages for better display in Streamlit.
    
    Args:
        error: Raw error message
        
    Returns:
        Formatted error message
    """
    # Remove common prefixes and make more user-friendly
    if "Configuration Error:" in error:
        return error.replace("Configuration Error:", "⚠️")
    elif "Validation Error:" in error:
        return error.replace("Validation Error:", "🔍")
    else:
        return f"• {error}" 