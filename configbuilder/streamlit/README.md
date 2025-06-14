# 🤖 Universal Agent Config Builder

A user-friendly web interface for creating Universal Agent configurations without writing code.

## 🌟 Features

- **4-Step Wizard**: Intuitive step-by-step configuration process
- **Dynamic Provider Selection**: Automatically detects available AI providers
- **Agent Type Presets**: Pre-configured templates for common use cases
- **Real-time Validation**: Instant feedback on configuration issues
- **Visual Progress Tracking**: Clear indication of completion status
- **Export Options**: Save to file or download directly
- **Professional UI**: Modern, responsive design with helpful tooltips
- **Fallback Mode**: Works even when plugin registration fails

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** installed on your system
2. **Universal Agent repository** cloned locally
3. **Dependencies** installed for the main project

### Installation

1. **Navigate to the config builder directory:**
   ```bash
   cd configbuilder/streamlit
   ```

2. **Install Streamlit dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the Universal Agent package** (from repo root):
   ```bash
   cd ../../
   pip install -e .
   ```

### Launch the Application

```bash
cd configbuilder/streamlit
streamlit run agent_config_builder.py
```

The application will open in your browser at `http://localhost:8501`

## 🔄 Operating Modes

The config builder has two operating modes:

### **Full Mode** ✅
- Dynamic provider detection from your installation
- Real-time validation using AgentConfig classes
- All features available

### **Fallback Mode** ⚠️
- Used when LiveKit plugin registration fails
- Standard provider list (still fully functional)
- Basic validation (configurations remain valid)
- All core functionality works

**Note**: If you see "Fallback Mode", don't worry! You can still create perfectly valid configurations. The only difference is that provider detection is static rather than dynamic.

## 📱 Usage Guide

### Step 1: Basic Agent Information
- **Agent ID**: Unique identifier (letters, numbers, hyphens, underscores only)
- **Agent Name**: Human-readable display name
- **Agent Type**: Choose from preset types (assistant, customer_service, etc.)
- **Description**: Brief description of your agent's purpose
- **Instructions**: Core system instructions defining behavior
- **Guardrails**: Safety guidelines and limitations

### Step 2: AI Providers
- **LLM Configuration**: 
  - Provider (OpenAI, Anthropic)
  - Model selection and temperature control
- **TTS Configuration**: 
  - Provider (Sarvam, ElevenLabs, Cartesia, etc.)
  - Language and voice settings
- **STT Configuration**:
  - Provider (Sarvam, Deepgram, OpenAI, etc.)
  - Language and model settings

### Step 3: Advanced Features
- **RAG (Knowledge Retrieval)**:
  - Enable/disable Pinecone integration
  - Namespace configuration
- **Memory Management**:
  - Conversation memory settings
  - History limits and summarization
- **Runtime Settings**:
  - Conversation duration limits
  - Noise cancellation options
  - Interruption handling

### Step 4: Save & Export
- **Validation**: Check configuration for errors
- **Preview**: Review complete JSON configuration
- **Save**: Export to custom file path
- **Download**: Get configuration file directly

## 🛠️ Supported Providers

### Language Models (LLM)
- **OpenAI**: GPT-4o, GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3 models (when available)

### Text-to-Speech (TTS)
- **Sarvam**: Multi-language support, optimized for Indian languages
- **ElevenLabs**: High-quality voice synthesis
- **Cartesia**: Real-time voice generation
- **OpenAI**: TTS-1 and TTS-HD models
- **Deepgram**: Aura voice models

### Speech-to-Text (STT)
- **Sarvam**: Multi-language recognition
- **Deepgram**: Nova-3 and Whisper models
- **OpenAI**: Whisper-1 model
- **ElevenLabs**: Multilingual recognition

## 🎨 Agent Type Presets

The config builder includes several pre-configured agent types:

| Type | Description | Use Cases |
|------|-------------|-----------|
| **assistant** | General purpose AI assistant | Help desk, general queries |
| **customer_service** | Customer service representative | Support, troubleshooting |
| **sales_agent** | Sales and lead qualification | Lead generation, product info |
| **clinic_receptionist** | Medical clinic receptionist | Appointment scheduling, clinic info |
| **restaurant_host** | Restaurant host and reservations | Table bookings, menu questions |

## 🔧 Configuration Examples

### Basic Assistant
```json
{
  "agent_id": "helpful_assistant",
  "name": "AI Assistant",
  "agent_type": "assistant",
  "description": "A helpful AI assistant for general queries",
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7
  }
}
```

### Clinic Receptionist
```json
{
  "agent_id": "clinic_maya",
  "name": "Maya - Clinic Receptionist",
  "agent_type": "clinic_receptionist",
  "description": "Professional clinic receptionist for appointment scheduling",
  "memory_config": {
    "enabled": true,
    "max_history": 5
  },
  "noise_cancellation": "BVCTelephony"
}
```

## 🚨 Troubleshooting

### Plugin Registration Errors

**Problem**: "Plugins must be registered on the main thread"

**Explanation**: This is a known compatibility issue between LiveKit and Streamlit's multi-threaded environment.

**Solutions**:
1. **Use Fallback Mode** (Recommended): The app automatically switches to fallback mode, which is fully functional
2. **Run from Terminal**: Launch from command line rather than an IDE
3. **Restart Environment**: Close all Python processes and restart your terminal
4. **Check Process Conflicts**: Ensure no other LiveKit processes are running

**Good News**: Fallback mode provides all functionality you need! Your configurations will be 100% valid.

### Import Errors

**Problem**: "Cannot import universalagent package"

**Solutions**:
1. Ensure you're in the correct directory structure
2. Install the package: `pip install -e .` from repo root
3. Check Python path and virtual environment

### Provider Not Available

**Problem**: "Provider X not available"

**Solutions**:
1. Install required plugin: `pip install livekit-plugins-{provider}`
2. Check the ComponentFactory for supported providers
3. Update dependencies in main project
4. Use fallback mode (providers are still available)

### Validation Failures

**Problem**: Configuration validation errors

**Solutions**:
1. Check required fields (marked with *)
2. Verify Agent ID format (alphanumeric, hyphens, underscores only)
3. Ensure all nested configurations are complete
4. Review error messages for specific issues

### File Save Issues

**Problem**: Cannot save configuration file

**Solutions**:
1. Check file path permissions
2. Ensure directory exists or can be created
3. Verify disk space availability
4. Use download option as alternative

## 🔧 Advanced Usage

### Custom Presets

You can modify the preset configurations in `utils/defaults.py`:

```python
AGENT_TYPE_PRESETS['my_custom_type'] = {
    'description': 'My custom agent type',
    'system_instructions': 'Custom instructions here...',
    'greeting_instructions': 'Custom greeting...',
}
```

### Provider Defaults

Customize default settings for providers in `utils/defaults.py`:

```python
def get_provider_defaults(provider: str, component_type: str):
    # Add your custom defaults here
    pass
```

### Environment Variables

The following environment variables are recommended:

```bash
# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
DEEPGRAM_API_KEY=your_deepgram_key
ELEVENLABS_API_KEY=your_elevenlabs_key
CARTESIA_API_KEY=your_cartesia_key
SARVAM_API_KEY=your_sarvam_key

# LiveKit Configuration
LIVEKIT_API_KEY=your_livekit_key
LIVEKIT_API_SECRET=your_livekit_secret
LIVEKIT_URL=your_livekit_url

# Optional: RAG Configuration
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=your_index_name
```

## 📖 Next Steps

After creating your configuration:

1. **Set up environment variables** for your chosen providers
2. **Test the configuration** using the Universal Agent runner
3. **Deploy to production** following the deployment guide
4. **Monitor performance** using LiveKit analytics

## 🤝 Contributing

To contribute to the config builder:

1. Fork the repository
2. Create a feature branch
3. Make your changes in the `configbuilder/streamlit/` directory
4. Test thoroughly with different configurations
5. Submit a pull request

## 📚 Documentation

- [Universal Agent Documentation](../../README.md)
- [LiveKit Agents Guide](https://docs.livekit.io/agents/)
- [Configuration Reference](../../universalagent/core/config.py)

## 🐛 Issues & Support

If you encounter issues:

1. Check this troubleshooting guide
2. Review the console output for detailed errors
3. Check the [GitHub Issues](../../issues) page
4. Create a new issue with:
   - Steps to reproduce
   - Error messages
   - Your configuration (sanitized)
   - Environment details

## 📝 License

This config builder is part of the Universal Agent project and follows the same license terms. 