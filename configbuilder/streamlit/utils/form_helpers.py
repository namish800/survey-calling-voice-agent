"""
Form helpers for the Universal Agent Config Builder.

This module provides utilities for managing Streamlit forms, session state,
and building the final configuration dictionary.
"""

import streamlit as st
import re
from typing import Dict, Any, Optional, List, Set
from .defaults import get_default_config, AGENT_TYPE_PRESETS


def initialize_session_state():
    """Initialize Streamlit session state with default values."""
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    if 'config_data' not in st.session_state:
        st.session_state.config_data = get_default_config()
    
    if 'providers' not in st.session_state:
        st.session_state.providers = None


def update_session_state(data_dict: Dict[str, Any]):
    """
    Update session state with form data.
    
    Args:
        data_dict: Dictionary of form data to update
    """
    for key, value in data_dict.items():
        st.session_state.config_data[key] = value


def get_session_value(key: str, default: Any = None) -> Any:
    """
    Get a value from session state config_data.
    
    Args:
        key: Key to retrieve
        default: Default value if key not found
        
    Returns:
        Value from session state or default
    """
    return st.session_state.config_data.get(key, default)


def build_config_dict() -> Dict[str, Any]:
    """
    Build final configuration dictionary from session state.
    
    Returns:
        Complete configuration dictionary ready for AgentConfig.from_dict()
    """
    config = st.session_state.config_data.copy()
    
    # Build nested LLM configuration
    llm_config = {
        'provider': config.get('llm_provider', 'openai'),
        'model': config.get('llm_model', 'gpt-4o'),
        'temperature': config.get('llm_temperature', 0.7),
    }
    
    # Add optional LLM fields
    if config.get('llm_max_tokens'):
        llm_config['max_tokens'] = config.get('llm_max_tokens')
    
    config['llm_config'] = llm_config
    
    # Process Jinja template variables in system instructions
    system_instructions = config.get('system_instructions', '')
    if system_instructions:
        jinja_vars = extract_jinja_variables(system_instructions)
        if jinja_vars:
            # Initialize metadata dict if not present
            if 'metadata' not in config or not isinstance(config['metadata'], dict):
                config['metadata'] = {}
            
            # Add all detected variables with empty values in metadata
            for var_name in jinja_vars:
                if var_name not in config['metadata']:
                    config['metadata'][var_name] = ""
    
    # Build TTS configuration (if enabled)
    if config.get('tts_enabled', True):
        tts_config = {
            'provider': config.get('tts_provider', 'sarvam'),
            'language': config.get('tts_language', 'en-IN'),
        }
        
        # Add optional TTS fields
        if config.get('tts_model'):
            tts_config['model'] = config.get('tts_model')
        if config.get('tts_voice_id'):
            tts_config['voice_id'] = config.get('tts_voice_id')
        
        config['tts_config'] = tts_config
    else:
        config['tts_config'] = None
    
    # Build STT configuration (if enabled)
    if config.get('stt_enabled', True):
        stt_config = {
            'provider': config.get('stt_provider', 'sarvam'),
            'language': config.get('stt_language', 'en-IN'),
        }
        
        # Add optional STT fields
        if config.get('stt_model'):
            stt_config['model'] = config.get('stt_model')
        
        config['stt_config'] = stt_config
    else:
        config['stt_config'] = None
    
    # Build RAG configuration
    rag_config = {
        'enabled': config.get('rag_enabled', False),
    }
    if config.get('rag_enabled', False):
        rag_config['namespace'] = config.get('rag_namespace', 'default')
    
    config['rag_config'] = rag_config
    
    # Build Memory configuration
    if config.get('memory_enabled', True):
        memory_config = {
            'enabled': True,
            'max_history': config.get('memory_max_history', 5),
            'summarize_threshold': config.get('memory_summarize_threshold', 100),
        }
        config['memory_config'] = memory_config
    else:
        config['memory_config'] = {'enabled': False}
    
    # Clean up temporary form fields
    form_fields_to_remove = [
        'llm_provider', 'llm_model', 'llm_temperature', 'llm_max_tokens',
        'tts_enabled', 'tts_provider', 'tts_language', 'tts_model', 'tts_voice_id',
        'stt_enabled', 'stt_provider', 'stt_language', 'stt_model',
        'rag_enabled', 'rag_namespace',
        'memory_enabled', 'memory_max_history', 'memory_summarize_threshold',
    ]
    
    for field in form_fields_to_remove:
        config.pop(field, None)
    
    return config


def apply_agent_type_preset(agent_type: str):
    """
    Apply preset values for the selected agent type to session state.
    
    Args:
        agent_type: Type of agent to apply presets for
    """
    if agent_type in AGENT_TYPE_PRESETS:
        preset = AGENT_TYPE_PRESETS[agent_type]
        
        # Update session state with preset values
        update_session_state({
            'description': preset.get('description', ''),
            'system_instructions': preset.get('system_instructions', ''),
            'greeting_instructions': preset.get('greeting_instructions', ''),
        })


def render_progress_bar(current_step: int, total_steps: int = 4):
    """
    Render a progress bar showing current step.
    
    Args:
        current_step: Current step number (1-based)
        total_steps: Total number of steps
    """
    progress = current_step / total_steps
    st.progress(progress)
    
    # Step indicator
    cols = st.columns(total_steps)
    step_names = ["Basic Info", "AI Providers", "Advanced", "Save & Export"]
    
    for i, (col, name) in enumerate(zip(cols, step_names), 1):
        with col:
            if i == current_step:
                st.markdown(f"**{i}. {name}** ← Current")
            elif i < current_step:
                st.markdown(f"✅ {i}. {name}")
            else:
                st.markdown(f"{i}. {name}")


def render_step_navigation(current_step: int, total_steps: int = 4):
    """
    Render navigation buttons for moving between steps.
    
    Args:
        current_step: Current step number
        total_steps: Total number of steps
    """
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if current_step > 1:
            if st.button("← Previous", key="nav_prev"):
                st.session_state.current_step -= 1
                st.rerun()
    
    with col3:
        if current_step < total_steps:
            if st.button("Next →", key="nav_next"):
                st.session_state.current_step += 1
                st.rerun()


def save_configuration_to_file(config_dict: Dict[str, Any], file_path: str, AgentConfig) -> bool:
    """
    Save configuration to a JSON file.
    
    Args:
        config_dict: Configuration dictionary
        file_path: Path to save the file
        AgentConfig: AgentConfig class for serialization (may be None)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if AgentConfig is not None:
            # Use AgentConfig for proper serialization
            config = AgentConfig.from_dict(config_dict)
            content = config.to_json(indent=2)
        else:
            # Fallback: direct JSON serialization
            import json
            content = json.dumps(config_dict, indent=2)
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        st.error(f"Failed to save configuration: {str(e)}")
        return False


def load_example_configs() -> Dict[str, Dict[str, Any]]:
    """
    Load example configurations for reference.
    
    Returns:
        Dictionary of example configurations
    """
    examples = {}
    
    # Add built-in examples based on agent type presets
    for agent_type, preset in AGENT_TYPE_PRESETS.items():
        config = get_default_config()
        config.update({
            'agent_id': f"{agent_type}_example",
            'name': f"{preset['description']}",
            'agent_type': agent_type,
            'description': preset['description'],
            'system_instructions': preset['system_instructions'],
            'greeting_instructions': preset['greeting_instructions'],
        })
        examples[agent_type] = config
    
    return examples


def extract_jinja_variables(text: str) -> Set[str]:
    """
    Extract variable names from Jinja template syntax in text.
    
    Args:
        text: Text containing Jinja template variables like {{variable_name}}
        
    Returns:
        Set of variable names found in the text
    """
    if not text:
        return set()
        
    # Pattern to match {{variable_name}} with possible whitespace
    pattern = r'\{\{\s*([a-zA-Z0-9_]+)\s*\}\}'
    
    # Find all matches and extract the variable names
    variables = re.findall(pattern, text)
    
    return set(variables) 