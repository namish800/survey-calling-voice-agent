# UniversalAgent - Configurable LiveKit Voice AI System

A flexible, configuration-driven voice AI agent system built on LiveKit that can adapt to different use cases (surveys, sales, support, etc.) through configuration rather than hardcoded logic.

## 🚀 Features

- **Configuration-Driven Architecture**: Define agent behavior through JSON configurations
- **Multi-Provider Support**: OpenAI, ElevenLabs, Deepgram, Cartesia, and more
- **Dynamic Tool System**: Built-in and custom tools for various use cases
- **RAG Integration**: Knowledge base integration with Pinecone and LlamaIndex
- **Flexible Component Factory**: Automatic component creation from configurations
- **Production Ready**: Comprehensive error handling, logging, and monitoring

## 📋 Requirements

- Python 3.9+
- LiveKit Cloud account or self-hosted LiveKit server
- API keys for chosen providers (OpenAI, ElevenLabs, etc.)
- Optional: Pinecone for RAG functionality

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd livekit-voice-agents
```

2. **Create virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -e .
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

## ⚡ Quick Start

### 1. Configure Your Agent

Agent configurations are stored in JSON files that define the complete behavior of your voice agent. Here's a basic example:

```json
{
  "agent_id": "my_assistant",
  "name": "My Voice Assistant",
  "description": "A helpful voice assistant",
  "agent_type": "assistant",
  "system_instructions": "You are a helpful voice AI assistant. Be friendly, professional, and helpful in all interactions.",
  "greeting_instructions": "Greet the user warmly and offer your assistance",
  
  "personality_traits": {
    "helpful": true,
    "friendly": true,
    "professional": true
  },
  "conversation_style": "professional",
  
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.7
  },
  
  "tts_config": {
    "provider": "deepgram"
  },
  
  "stt_config": {
    "provider": "deepgram",
    "language": "en"
  },
  
  "tools": ["end_call"],
  "max_conversation_duration": 900,
  "silence_timeout": 15,
  "noise_cancellation": "BVC"
}
```

Save this as `configs/development/my_assistant.json`.

### 2. Run Your Agent in Development

Start the agent in development mode:

```bash
python universal_agent.py dev
```

This command:
- Registers your agent with the LiveKit server
- Makes it available for dispatch using the `agent_id`
- Runs in development mode with enhanced logging

### 3. How Agent Dispatch Works

Once your agent is running, it's registered with LiveKit and can be dispatched:

1. **Agent Registration**: When you run `python universal_agent.py dev`, your agent registers with the LiveKit server
2. **Agent Dispatch**: When a call comes in, you specify the `agent_id` in the dispatch metadata
3. **Config Loading**: The system loads the configuration file matching the `agent_id`
4. **Agent Creation**: A configured agent instance is created with the specified behavior

For more details about LiveKit dispatch and room management, check the [LiveKit documentation](https://docs.livekit.io/).

## 📁 Project Structure

```
universalagent/
├── core/                    # Core configuration and session management
│   ├── config.py           # Configuration dataclasses
│   ├── config_loader.py    # Configuration loading utilities
│   └── session.py          # Enhanced AgentSession wrapper
├── components/              # Component factory for LLM/TTS/STT
│   └── factory.py          # ComponentFactory class
├── agents/                  # Agent implementations
│   ├── configurable_agent.py  # Main configurable agent
│   └── entrypoint.py       # Universal entrypoint
└── tools/                   # Tool system
    ├── tool_holder.py      # Tool wrapper class
    ├── call_management_tools.py  # Built-in call tools
    └── knowledge/          # RAG and knowledge tools
        └── rag_tool.py     # Pinecone RAG integration
```

## 🔧 Agent Configuration Deep Dive

### Core Agent Properties

- **`agent_id`**: Unique identifier used for dispatch
- **`name`**: Human-readable agent name
- **`description`**: Agent description for documentation
- **`agent_type`**: Category of agent (assistant, survey, sales, support)
- **`system_instructions`**: Core behavioral instructions for the LLM
- **`greeting_instructions`**: How the agent should greet users

### Personality & Behavior

```json
{
  "personality_traits": {
    "helpful": true,
    "friendly": true,
    "professional": true,
    "patient": "with confused users"
  },
  "conversation_style": "professional",
  "max_conversation_duration": 1800,
  "silence_timeout": 15
}
```

### Component Configuration

```json
{
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 500
  },
  "tts_config": {
    "provider": "elevenlabs",
    "voice_id": "your-voice-id",
    "model": "eleven_flash_v2_5"
  },
  "stt_config": {
    "provider": "deepgram",
    "model": "nova-2",
    "language": "en"
  }
}
```

### Environment Variables

```bash
# LiveKit
LIVEKIT_URL=wss://your-livekit-url
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# AI Providers
OPENAI_API_KEY=your-openai-key
ELEVENLABS_API_KEY=your-elevenlabs-key
DEEPGRAM_API_KEY=your-deepgram-key

# RAG (Optional)
PINECONE_API_KEY=your-pinecone-key
```

## 🛠️ Built-in Tools

The system comes with several built-in tools that are automatically available:

### Default Tools (Always Available)

- **`end_call`**: Gracefully terminate the current call
  - Usage: When conversation is complete or user requests to end
  - Description: Ensures proper call cleanup and resource management

### Optional Tools (Enable in Config)

Add these to your `"tools"` array in the configuration:

- **`search_knowledge_base`**: Search Pinecone knowledge base
  - Requires: RAG configuration with Pinecone setup
  - Usage: Answer questions using your knowledge base

- **`schedule_callback`**: Schedule follow-up calls
  - Usage: When user is busy or requests a callback

- **`record_answer`**: Save structured data responses
  - Usage: For surveys or data collection scenarios

### Tool Configuration Examples

```json
{
  "tools": ["end_call", "search_knowledge_base"],
  "rag_config": {
    "enabled": true,
    "provider": "pinecone",
    "index_name": "knowledge-base",
    "namespace": "default",
    "similarity_top_k": 5
  }
}
```

## 🔌 Custom Tools

Create custom tools by extending the ToolHolder class:

```python
from universalagent.tools.tool_holder import ToolHolder
from livekit.agents import RunContext

async def my_custom_tool(ctx: RunContext, query: str) -> str:
    """My custom tool description"""
    # Your tool logic here
    return "Tool response"

# Create a standalone function (not a method) for LiveKit compatibility
async def search_database(context: RunContext, query: str) -> str:
    """Search our internal database for information"""
    # Your database search logic
    return f"Database results for: {query}"

# Register the tool
tool = ToolHolder(search_database, name="search_database")
```

## 🧠 RAG Integration

### Setup Pinecone

```python
from universalagent.tools.knowledge.rag_tool import RAGToolConfig, LlamaIndexPineconeRagTool

config = RAGToolConfig(
    openai_api_key="your-key",
    pinecone_api_key="your-key", 
    index_name="knowledge-base",
    namespace="default"
)

rag_tool = LlamaIndexPineconeRagTool(config)
```

### Use in Agent Configuration

```json
{
  "tools": ["search_knowledge_base"],
  "rag_config": {
    "enabled": true,
    "provider": "pinecone",
    "index_name": "knowledge-base",
    "namespace": "default",
    "similarity_top_k": 5
  }
}
```

## 📊 Configuration Examples

### Survey Agent
See `configs/development/survey_agent.json` for a complete survey agent configuration.

### Default Assistant  
See `configs/development/default.json` for a basic assistant setup.

### Test Agent
See `configs/development/test_agent.json` for testing configuration.

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=universalagent

# Run specific test file
pytest tests/test_config.py
```

## 🚀 Development Status

### ✅ Phase 1 Complete: Core Foundation
- Configuration system with validation
- Component factory for all providers
- Basic configurable agent with LiveKit integration

### 🚧 Phase 2 In Progress: Tool System
- Dynamic tool loading and management
- Built-in tools for common operations
- Custom tool development framework

### 📋 Upcoming: Advanced Features
- Memory management system
- Webhook integrations
- Template inheritance
- Performance optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `docs/` directory
- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions for questions

## 🔗 Related Projects

- [LiveKit](https://github.com/livekit/livekit) - Real-time communication platform
- [LiveKit Agents](https://github.com/livekit/agents) - AI agent framework
- [KB Retriever](https://github.com/kb-retriever/kb-retriever) - Knowledge base retrieval
