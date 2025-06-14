"""
Default values and presets for the Universal Agent Config Builder.

This module contains sensible defaults based on the example configuration
and common use cases for Universal Agents.
"""

from typing import Dict, Any

# Default values for basic agent information
DEFAULT_AGENT_CONFIG = {
    'agent_type': 'assistant',
    'version': '1.0',
    'first_message': None,
    'greeting_instructions': 'Greet the user warmly and offer your assistance.',
    'system_instructions': 'You are a helpful AI assistant. Be professional, friendly, and provide accurate information.',
    'guardrails': 'Stay focused on your role and do not provide information outside your expertise.',
    'initial_context': '',
}

# Default AI provider configurations
DEFAULT_LLM_CONFIG = {
    'provider': 'openai',
    'model': 'gpt-4o',
    'temperature': 0.7,
}

DEFAULT_TTS_CONFIG = {
    'provider': 'sarvam',
    'language': 'en-IN',
    'model': '',
    'voice_id': '',
}

DEFAULT_STT_CONFIG = {
    'provider': 'sarvam', 
    'language': 'en-IN',
    'model': '',
}

# Default advanced features
DEFAULT_RAG_CONFIG = {
    'enabled': False,
    'namespace': 'default',
}

DEFAULT_MEMORY_CONFIG = {
    'enabled': True,
    'max_history': 5,
    'summarize_threshold': 100,
}

# Default runtime settings
DEFAULT_RUNTIME_CONFIG = {
    'max_conversation_duration': 1800,  # 30 minutes
    'silence_timeout': 10,
    'interruption_handling': True,
    'noise_cancellation': 'BVCTelephony',
}

# Noise cancellation options
NOISE_CANCELLATION_OPTIONS = ['BVC', 'BVCTelephony', 'none']

# Common language codes for TTS/STT
COMMON_LANGUAGES = [
    'en-US', 'en-IN', 'en-GB', 'en-AU',
    'es-ES', 'es-MX', 'fr-FR', 'de-DE',
    'it-IT', 'pt-BR', 'zh-CN', 'ja-JP',
    'ko-KR', 'ar-SA', 'hi-IN', 'ru-RU'
]

# Agent type presets
AGENT_TYPE_PRESETS = {
    'assistant': {
        'description': 'General purpose AI assistant',
        'system_instructions': 'You are a helpful AI assistant. Be professional, friendly, and provide accurate information.',
        'greeting_instructions': 'Greet the user warmly and offer your assistance.',
    },
    'customer_service': {
        'description': 'Customer service representative',
        'system_instructions': 'You are a professional customer service representative. Help customers with their inquiries, be patient and understanding.',
        'greeting_instructions': 'Thank you for contacting us. How may I help you today?',
    },
    'sales_agent': {
        'description': 'Sales and lead qualification agent',
        'system_instructions': 'You are a friendly sales representative. Help qualify leads and provide information about our products and services.',
        'greeting_instructions': 'Hello! Thank you for your interest. How can I help you learn more about our offerings?',
    },
    'clinic_receptionist': {
        'description': 'Medical clinic receptionist',
        'system_instructions': 'You are a professional and empathetic clinic receptionist. Help patients schedule appointments and provide general information.',
        'greeting_instructions': 'Thank you for calling our clinic. How may I help you today?',
    },
    'restaurant_host': {
        'description': 'Restaurant host and reservation agent',
        'system_instructions': 'You are a friendly restaurant host. Help customers make reservations and answer questions about our menu and services.',
        'greeting_instructions': 'Hello! Thank you for calling. How can I help you today?',
    }
}

def get_default_config() -> Dict[str, Any]:
    """
    Get a complete default configuration dictionary.
    
    Returns:
        Dictionary with all default configuration values
    """
    return {
        **DEFAULT_AGENT_CONFIG,
        'llm_config': DEFAULT_LLM_CONFIG.copy(),
        'tts_config': DEFAULT_TTS_CONFIG.copy(),
        'stt_config': DEFAULT_STT_CONFIG.copy(),
        'rag_config': DEFAULT_RAG_CONFIG.copy(),
        'memory_config': DEFAULT_MEMORY_CONFIG.copy(),
        **DEFAULT_RUNTIME_CONFIG,
        'tools': [],
        'evaluation_criteria': [],
    }

def apply_agent_type_preset(agent_type: str) -> Dict[str, str]:
    """
    Get preset values for a specific agent type.
    
    Args:
        agent_type: Type of agent to get presets for
        
    Returns:
        Dictionary with preset values for the agent type
    """
    return AGENT_TYPE_PRESETS.get(agent_type, AGENT_TYPE_PRESETS['assistant'])

def get_provider_defaults(provider: str, component_type: str) -> Dict[str, Any]:
    """
    Get default configuration for a specific provider.
    
    Args:
        provider: Provider name (e.g., 'openai', 'sarvam')
        component_type: Type of component ('llm', 'tts', 'stt')
        
    Returns:
        Dictionary with default values for the provider
    """
    provider_defaults = {
        'llm': {
            'openai': {'model': 'gpt-4o', 'temperature': 0.7},
            'anthropic': {'model': 'claude-3-sonnet', 'temperature': 0.7},
        },
        'tts': {
            'openai': {'model': 'tts-1', 'voice_id': 'alloy'},
            'elevenlabs': {'model': 'eleven_multilingual_v2', 'voice_id': ''},
            'cartesia': {'model': 'sonic-english', 'voice_id': ''},
            'sarvam': {'language': 'en-IN', 'model': ''},
            'deepgram': {'model': 'aura-asteria-en', 'language': 'en'},
        },
        'stt': {
            'openai': {'model': 'whisper-1', 'language': 'en'},
            'deepgram': {'model': 'nova-3', 'language': 'en'},
            'elevenlabs': {'model': '', 'language': 'en'},
            'sarvam': {'language': 'en-IN', 'model': ''},
        }
    }
    
    return provider_defaults.get(component_type, {}).get(provider, {}) 