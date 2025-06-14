"""
Universal Agent Config Builder

A user-friendly Streamlit web interface for creating Universal Agent configurations
without writing code. This application provides a 4-step wizard to configure:

1. Basic Agent Information
2. AI Providers (LLM, TTS, STT)  
3. Advanced Features (RAG, Memory, Runtime)
4. Save & Export

Usage:
    streamlit run agent_config_builder.py
"""

import streamlit as st
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Import utility modules
from utils.validation import safe_import, validate_configuration, format_error_message, safe_get_providers
from utils.form_helpers import (
    initialize_session_state, update_session_state, get_session_value,
    build_config_dict, apply_agent_type_preset, render_progress_bar,
    render_step_navigation, save_configuration_to_file, extract_jinja_variables
)
from utils.defaults import (
    AGENT_TYPE_PRESETS, NOISE_CANCELLATION_OPTIONS, COMMON_LANGUAGES,
    get_provider_defaults
)


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Universal Agent Config Builder",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Safe import of universalagent
    ComponentFactory, AgentConfig, import_error = safe_import()
    
    # Handle import errors gracefully
    if import_error:
        if "main thread" in import_error:
            st.warning("⚠️ **Fallback Mode**: Running with limited provider detection due to LiveKit plugin restrictions.")
            st.info("💡 **Note**: All core functionality works, but provider detection is limited. You can still create valid configurations.")
            # Continue with fallback mode
            ComponentFactory = None
            AgentConfig = None
        else:
            st.error(import_error)
            st.stop()
    
    # Load providers safely
    if st.session_state.providers is None:
        try:
            st.session_state.providers = safe_get_providers(ComponentFactory)
            
            # Show mode indicator
            if ComponentFactory is None:
                st.info("🔄 **Fallback Mode**: Using standard provider list. All configurations will be valid.")
            else:
                st.success("✅ **Full Mode**: Dynamic provider detection active.")
                
        except Exception as e:
            st.error(f"Failed to load AI providers: {str(e)}")
            st.stop()
    
    # Header
    st.title("🤖 Universal Agent Config Builder")
    st.markdown("Create professional voice AI agents through an intuitive step-by-step interface.")
    
    # Progress bar
    render_progress_bar(st.session_state.current_step)
    st.divider()
    
    # Sidebar navigation
    render_sidebar_navigation()
    
    # Main content based on current step
    if st.session_state.current_step == 1:
        step1_basic_info()
    elif st.session_state.current_step == 2:
        step2_ai_providers()
    elif st.session_state.current_step == 3:
        step3_advanced_features()
    elif st.session_state.current_step == 4:
        step4_save_export(AgentConfig)
    
    # Navigation buttons
    st.divider()
    render_step_navigation(st.session_state.current_step)


def render_sidebar_navigation():
    """Render sidebar with step navigation and quick actions."""
    with st.sidebar:
        st.title("📋 Navigation")
        
        # Step buttons
        steps = [
            ("Basic Info", "📝"),
            ("AI Providers", "🧠"),
            ("Advanced Features", "⚙️"),
            ("Save & Export", "💾")
        ]
        
        for i, (step_name, icon) in enumerate(steps, 1):
            if st.button(f"{icon} {i}. {step_name}", key=f"sidebar_nav_{i}"):
                st.session_state.current_step = i
                st.rerun()
        
        st.divider()
        
        # Quick actions
        st.subheader("🚀 Quick Actions")
        
        # Agent type presets
        st.write("**Agent Type Presets:**")
        preset_options = list(AGENT_TYPE_PRESETS.keys())
        selected_preset = st.selectbox(
            "Load preset",
            preset_options,
            index=0,
            key="preset_selector"
        )
        
        if st.button("Apply Preset", key="apply_preset"):
            apply_agent_type_preset(selected_preset)
            update_session_state({'agent_type': selected_preset})
            st.success(f"Applied {selected_preset} preset!")
            st.rerun()
        
        # Reset configuration
        if st.button("🔄 Reset All", key="reset_config"):
            st.session_state.config_data = {}
            initialize_session_state()
            st.success("Configuration reset!")
            st.rerun()


def step1_basic_info():
    """Step 1: Basic Agent Information form."""
    st.header("📝 Step 1: Basic Agent Information")
    st.markdown("Define your agent's identity, purpose, and core instructions.")
    
    # Two column layout for basic info
    col1, col2 = st.columns(2)
    
    with col1:
        agent_id = st.text_input(
            "Agent ID*",
            value=get_session_value('agent_id', ''),
            help="Unique identifier for your agent (letters, numbers, hyphens, underscores only)",
            placeholder="my_clinic_agent"
        )
        
        name = st.text_input(
            "Agent Name*",
            value=get_session_value('name', ''),
            help="Human-readable name for your agent",
            placeholder="Clinic Receptionist Maya"
        )
        
        agent_type = st.selectbox(
            "Agent Type",
            options=list(AGENT_TYPE_PRESETS.keys()),
            index=list(AGENT_TYPE_PRESETS.keys()).index(get_session_value('agent_type', 'assistant')),
            help="Type of agent - affects default instructions"
        )
    
    with col2:
        version = st.text_input(
            "Version",
            value=get_session_value('version', '1.0'),
            help="Version number for your agent"
        )
        
        description = st.text_area(
            "Description*",
            value=get_session_value('description', ''),
            help="Brief description of what your agent does",
            placeholder="A professional and empathetic AI receptionist for medical clinics."
        )
    
    st.subheader("💬 Conversation Settings")
    
    # First message and greeting
    col1, col2 = st.columns(2)
    
    with col1:
        first_message = st.text_input(
            "First Message (optional)",
            value=get_session_value('first_message', '') or '',
            help="Specific first message (leave empty for greeting instructions)",
            placeholder="Hello! How can I help you today?"
        )
    
    with col2:
        greeting_instructions = st.text_area(
            "Greeting Instructions",
            value=get_session_value('greeting_instructions', ''),
            help="Instructions for how the agent should greet users",
            height=100
        )
    
    # Main instructions
    system_instructions = st.text_area(
        "System Instructions*",
        value=get_session_value('system_instructions', ''),
        help="Core instructions that define your agent's behavior and personality",
        height=200,
        placeholder="You are a professional and empathetic AI assistant..."
    )
    
    # Optional fields
    with st.expander("🛡️ Additional Settings", expanded=False):
        guardrails = st.text_area(
            "Guardrails",
            value=get_session_value('guardrails', ''),
            help="Safety guidelines and limitations for your agent",
            height=100,
            placeholder="Stay focused on your role and do not provide medical advice..."
        )
        
        initial_context = st.text_area(
            "Initial Context",
            value=get_session_value('initial_context', ''),
            help="Any initial context or background information",
            height=100
        )
    
    # Check for Jinja template variables in system instructions
    if system_instructions:
        jinja_vars = extract_jinja_variables(system_instructions)
        
        if jinja_vars:
            with st.expander("🔄 Template Variables", expanded=True):
                st.markdown("""
                **Template Variables Detected**
                
                These variables were found in your system instructions and will be replaced at runtime:
                """)
                
                # Get existing metadata
                metadata = get_session_value('metadata', {}) or {}
                metadata_updated = metadata.copy()
                
                # Create input fields for each variable
                for var_name in jinja_vars:
                    var_value = metadata.get(var_name, "")
                    new_value = st.text_input(
                        f"Variable: {var_name}",
                        value=var_value,
                        help=f"Default value for {{{{ {var_name} }}}} in the system instructions",
                        key=f"metadata_{var_name}"
                    )
                    metadata_updated[var_name] = new_value
                
                st.info("💡 These variables will be stored in metadata and can be overridden at runtime.")
                
                # Update metadata in session state
                if metadata != metadata_updated:
                    update_session_state({'metadata': metadata_updated})
    
    # Update session state
    update_session_state({
        'agent_id': agent_id,
        'name': name,
        'agent_type': agent_type,
        'version': version,
        'description': description,
        'first_message': first_message if first_message else None,
        'greeting_instructions': greeting_instructions,
        'system_instructions': system_instructions,
        'guardrails': guardrails,
        'initial_context': initial_context,
    })
    
    # Validation feedback
    if agent_id or name or description or system_instructions:
        errors = []
        if not agent_id.strip():
            errors.append("Agent ID is required")
        elif not agent_id.replace('_', '').replace('-', '').isalnum():
            errors.append("Agent ID can only contain letters, numbers, hyphens, and underscores")
        
        if not name.strip():
            errors.append("Agent Name is required")
        if not description.strip():
            errors.append("Description is required")
        if not system_instructions.strip():
            errors.append("System Instructions are required")
        
        if errors:
            for error in errors:
                st.error(f"• {error}")
        else:
            st.success("✅ Basic information looks good!")


def step2_ai_providers():
    """Step 2: AI Providers configuration."""
    st.header("🧠 Step 2: AI Providers")
    st.markdown("Configure the AI models that power your agent's capabilities.")
    
    providers = st.session_state.providers
    
    # LLM Configuration
    st.subheader("🧠 Language Model (LLM)")
    llm_col1, llm_col2 = st.columns(2)
    
    with llm_col1:
        llm_provider = st.selectbox(
            "LLM Provider",
            options=providers['llm'],
            index=0,
            help="Choose your language model provider"
        )
        
        # Get provider defaults
        llm_defaults = get_provider_defaults(llm_provider, 'llm')
        
        llm_model = st.text_input(
            "Model",
            value=get_session_value('llm_model', llm_defaults.get('model', 'gpt-4o')),
            help="Specific model name"
        )
    
    with llm_col2:
        llm_temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=get_session_value('llm_temperature', 0.7),
            step=0.1,
            help="Controls randomness (0.0 = deterministic, 1.0 = creative)"
        )
        
        llm_max_tokens = st.number_input(
            "Max Tokens (optional)",
            min_value=1,
            max_value=4000,
            value=get_session_value('llm_max_tokens', None) or 1000,
            help="Maximum response length"
        )
    
    # TTS Configuration
    st.subheader("🗣️ Text-to-Speech (TTS)")
    tts_enabled = st.checkbox(
        "Enable TTS",
        value=get_session_value('tts_enabled', True),
        help="Enable text-to-speech for agent responses"
    )
    
    if tts_enabled:
        tts_col1, tts_col2 = st.columns(2)
        
        with tts_col1:
            tts_provider = st.selectbox(
                "TTS Provider",
                options=providers['tts'],
                index=providers['tts'].index('sarvam') if 'sarvam' in providers['tts'] else 0,
                help="Choose your text-to-speech provider"
            )
            
            # Get provider defaults
            tts_defaults = get_provider_defaults(tts_provider, 'tts')
            
            tts_language = st.selectbox(
                "Language",
                options=COMMON_LANGUAGES,
                index=COMMON_LANGUAGES.index(get_session_value('tts_language', tts_defaults.get('language', 'en-IN'))),
                help="Language for speech synthesis"
            )
        
        with tts_col2:
            tts_model = st.text_input(
                "Model (optional)",
                value=get_session_value('tts_model', tts_defaults.get('model', '')),
                help="Specific TTS model name"
            )
            
            tts_voice_id = st.text_input(
                "Voice ID (optional)",
                value=get_session_value('tts_voice_id', tts_defaults.get('voice_id', '')),
                help="Specific voice identifier"
            )
    
    # STT Configuration
    st.subheader("🎤 Speech-to-Text (STT)")
    stt_enabled = st.checkbox(
        "Enable STT",
        value=get_session_value('stt_enabled', True),
        help="Enable speech-to-text for user input"
    )
    
    if stt_enabled:
        stt_col1, stt_col2 = st.columns(2)
        
        with stt_col1:
            stt_provider = st.selectbox(
                "STT Provider",
                options=providers['stt'],
                index=providers['stt'].index('sarvam') if 'sarvam' in providers['stt'] else 0,
                help="Choose your speech-to-text provider"
            )
            
            # Get provider defaults
            stt_defaults = get_provider_defaults(stt_provider, 'stt')
            
            stt_language = st.selectbox(
                "Language",
                options=COMMON_LANGUAGES,
                index=COMMON_LANGUAGES.index(get_session_value('stt_language', stt_defaults.get('language', 'en-IN'))),
                help="Language for speech recognition"
            )
        
        with stt_col2:
            stt_model = st.text_input(
                "Model (optional)",
                value=get_session_value('stt_model', stt_defaults.get('model', '')),
                help="Specific STT model name"
            )
    
    # Update session state
    update_session_state({
        'llm_provider': llm_provider,
        'llm_model': llm_model,
        'llm_temperature': llm_temperature,
        'llm_max_tokens': llm_max_tokens if llm_max_tokens > 0 else None,
        'tts_enabled': tts_enabled,
        'tts_provider': tts_provider if tts_enabled else None,
        'tts_language': tts_language if tts_enabled else None,
        'tts_model': tts_model if tts_enabled and tts_model else None,
        'tts_voice_id': tts_voice_id if tts_enabled and tts_voice_id else None,
        'stt_enabled': stt_enabled,
        'stt_provider': stt_provider if stt_enabled else None,
        'stt_language': stt_language if stt_enabled else None,
        'stt_model': stt_model if stt_enabled and stt_model else None,
    })
    
    # Show current configuration summary
    with st.expander("📋 Current Configuration Summary", expanded=False):
        config_summary = {
            "LLM": f"{llm_provider} - {llm_model} (temp: {llm_temperature})",
            "TTS": f"{tts_provider} - {tts_language}" if tts_enabled else "Disabled",
            "STT": f"{stt_provider} - {stt_language}" if stt_enabled else "Disabled"
        }
        st.json(config_summary)


def step3_advanced_features():
    """Step 3: Advanced Features configuration."""
    st.header("⚙️ Step 3: Advanced Features")
    st.markdown("Configure advanced capabilities like knowledge retrieval, memory, and runtime settings.")
    
    # RAG Configuration
    st.subheader("📚 Knowledge Retrieval (RAG)")
    rag_enabled = st.checkbox(
        "Enable RAG",
        value=get_session_value('rag_enabled', False),
        help="Enable Retrieval-Augmented Generation for knowledge base integration"
    )
    
    rag_namespace = None
    if rag_enabled:
        rag_namespace = st.text_input(
            "Namespace",
            value=get_session_value('rag_namespace', 'default'),
            help="Namespace in your vector database"
        )
        
        st.info("💡 RAG requires Pinecone setup and knowledge base indexing. See documentation for details.")
    
    # Memory Configuration
    st.subheader("🧠 Memory Management")
    memory_enabled = st.checkbox(
        "Enable Memory",
        value=get_session_value('memory_enabled', True),
        help="Enable conversation memory for personalized interactions"
    )
    
    if memory_enabled:
        mem_col1, mem_col2 = st.columns(2)
        
        with mem_col1:
            memory_max_history = st.number_input(
                "Max History",
                min_value=1,
                max_value=100,
                value=get_session_value('memory_max_history', 5),
                help="Maximum number of conversation turns to remember"
            )
        
        with mem_col2:
            memory_summarize_threshold = st.number_input(
                "Summarize Threshold",
                min_value=1,
                max_value=1000,
                value=get_session_value('memory_summarize_threshold', 100),
                help="Conversation length before summarization"
            )
        
        st.info("💡 Memory requires Mem0 setup. See documentation for configuration details.")
    
    # Runtime Settings
    st.subheader("⚙️ Runtime Settings")
    
    runtime_col1, runtime_col2 = st.columns(2)
    
    with runtime_col1:
        max_conversation_duration = st.number_input(
            "Max Conversation Duration (seconds)",
            min_value=30,
            max_value=7200,  # 2 hours
            value=get_session_value('max_conversation_duration', 1800),
            help="Maximum conversation length before automatic termination"
        )
        
        silence_timeout = st.number_input(
            "Silence Timeout (seconds)",
            min_value=1,
            max_value=60,
            value=get_session_value('silence_timeout', 10),
            help="Seconds of silence before prompting user"
        )
    
    with runtime_col2:
        interruption_handling = st.checkbox(
            "Interruption Handling",
            value=get_session_value('interruption_handling', True),
            help="Allow users to interrupt agent responses"
        )
        
        noise_cancellation = st.selectbox(
            "Noise Cancellation",
            options=NOISE_CANCELLATION_OPTIONS,
            index=NOISE_CANCELLATION_OPTIONS.index(get_session_value('noise_cancellation', 'BVCTelephony')),
            help="Noise cancellation type (BVCTelephony recommended for phone calls)"
        )
    
    # Update session state
    update_session_state({
        'rag_enabled': rag_enabled,
        'rag_namespace': rag_namespace,
        'memory_enabled': memory_enabled,
        'memory_max_history': memory_max_history if memory_enabled else None,
        'memory_summarize_threshold': memory_summarize_threshold if memory_enabled else None,
        'max_conversation_duration': max_conversation_duration,
        'silence_timeout': silence_timeout,
        'interruption_handling': interruption_handling,
        'noise_cancellation': noise_cancellation,
    })
    
    # Feature summary
    with st.expander("📋 Advanced Features Summary", expanded=False):
        features = {
            "RAG": "Enabled" if rag_enabled else "Disabled",
            "Memory": "Enabled" if memory_enabled else "Disabled",
            "Max Duration": f"{max_conversation_duration} seconds",
            "Noise Cancellation": noise_cancellation
        }
        st.json(features)


def step4_save_export(AgentConfig):
    """Step 4: Save & Export configuration."""
    st.header("💾 Step 4: Save & Export")
    st.markdown("Review, validate, and save your agent configuration.")
    
    # Build configuration
    try:
        config_dict = build_config_dict()
    except Exception as e:
        st.error(f"Error building configuration: {str(e)}")
        return
    
    # File path input
    st.subheader("💾 Save Location")
    
    default_filename = f"{config_dict.get('agent_id', 'agent_config')}.json"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        save_directory = st.text_input(
            "Directory Path",
            value="./configs",
            help="Directory where the configuration file will be saved (you can edit this)"
        )
    
    with col2:
        save_filename = st.text_input(
            "Filename",
            value=default_filename,
            help="Filename for the configuration (you can edit this)"
        )
    
    save_path = os.path.join(save_directory, save_filename)
    st.info(f"Your configuration will be saved to: **{save_path}**")
    
    # Configuration preview
    st.subheader("📋 Configuration Preview")
    
    # Show key details in a nice format
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Agent ID", config_dict.get('agent_id', 'N/A'))
        st.metric("Agent Name", config_dict.get('name', 'N/A'))
        st.metric("Agent Type", config_dict.get('agent_type', 'N/A'))
    
    with col2:
        llm_config = config_dict.get('llm_config', {})
        st.metric("LLM Provider", llm_config.get('provider', 'N/A'))
        st.metric("LLM Model", llm_config.get('model', 'N/A'))
        st.metric("Temperature", llm_config.get('temperature', 'N/A'))
    
    # Full JSON preview
    with st.expander("🔍 Full Configuration (JSON)", expanded=False):
        st.json(config_dict)
    
    # Validation
    st.subheader("✅ Validation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Validate Configuration", type="secondary"):
            is_valid, issues = validate_configuration(config_dict, AgentConfig)
            
            if is_valid:
                st.success("✅ Configuration is valid!")
            else:
                st.error("❌ Validation Issues Found:")
                for issue in issues:
                    st.error(format_error_message(issue))
    
    with col2:
        if st.button("💾 Save Configuration", type="primary"):
            try:
                # Validate first
                is_valid, issues = validate_configuration(config_dict, AgentConfig)
                
                if not is_valid:
                    st.error("❌ Cannot save invalid configuration:")
                    for issue in issues:
                        st.error(format_error_message(issue))
                    return
                
                # Validate directory path
                if not save_directory.strip():
                    st.error("❌ Directory path cannot be empty.")
                    return
                    
                if not save_filename.strip():
                    st.error("❌ Filename cannot be empty.")
                    return
                
                # Save to file
                if save_configuration_to_file(config_dict, save_path, AgentConfig):
                    st.success(f"✅ Configuration saved to {save_path}")
                    
                    # Show download button
                    config_json = json.dumps(config_dict, indent=2)
                    st.download_button(
                        label="📥 Download Configuration",
                        data=config_json,
                        file_name=save_filename,
                        mime="application/json",
                        help="Download the configuration file to your computer"
                    )
                    
                    # Success message with next steps
                    st.balloons()
                    st.info("""
                    🎉 **Success!** Your agent configuration has been created.
                    
                    **Next Steps:**
                    1. Set up your environment variables (API keys)
                    2. Run your agent with: `python universal_agent.py`
                    3. Test your agent in the LiveKit playground
                    """)
                
            except Exception as e:
                st.error(f"❌ Failed to save configuration: {str(e)}")
    
    # Additional actions
    st.subheader("🚀 Additional Actions")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("🔄 Start Over"):
            st.session_state.clear()
            initialize_session_state()
            st.rerun()
    
    with action_col2:
        if st.button("📝 Edit Basic Info"):
            st.session_state.current_step = 1
            st.rerun()
    
    with action_col3:
        if st.button("🧠 Edit AI Providers"):
            st.session_state.current_step = 2
            st.rerun()


if __name__ == "__main__":
    main() 