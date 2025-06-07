livekit-configurable-agents/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── setup.py
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py                    # ConfigurableAgent base class
│   │   ├── session.py                  # Enhanced AgentSession wrapper
│   │   ├── config.py                   # All configuration dataclasses
│   │   └── entrypoint.py              # Universal configurable entrypoint
│   │
│   ├── components/
│   │   ├── __init__.py
│   │   ├── factory.py                  # ComponentFactory for creating LLM/TTS/STT
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── openai_provider.py
│   │   │   ├── anthropic_provider.py
│   │   │   └── local_provider.py
│   │   ├── tts/
│   │   │   ├── __init__.py
│   │   │   ├── elevenlabs_provider.py
│   │   │   ├── cartesia_provider.py
│   │   │   └── openai_provider.py
│   │   └── stt/
│   │       ├── __init__.py
│   │       ├── elevenlabs_provider.py
│   │       ├── deepgram_provider.py
│   │       └── openai_provider.py
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── manager.py                  # ToolManager for dynamic tool loading
│   │   ├── registry.py                 # Tool registry and discovery
│   │   ├── builtin/
│   │   │   ├── __init__.py
│   │   │   ├── communication.py        # end_call, say, etc.
│   │   │   ├── data_collection.py      # record_answer, save_data
│   │   │   ├── scheduling.py           # handle_is_busy, schedule_callback
│   │   │   └── knowledge.py            # search_knowledge_base
│   │   └── custom/
│   │       ├── __init__.py
│   │       └── example_tools.py        # Example custom tools
│   │
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── rag_manager.py             # RAG orchestration
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── pinecone_provider.py
│   │   │   ├── chroma_provider.py
│   │   │   └── llamaindex_provider.py
│   │   └── embeddings/
│   │       ├── __init__.py
│   │       ├── openai_embeddings.py
│   │       └── local_embeddings.py
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── manager.py                  # MemoryManager
│   │   ├── conversation_memory.py      # Conversation-level memory
│   │   ├── user_memory.py             # User-level memory
│   │   └── global_memory.py           # Global/session memory
│   │
│   ├── webhooks/
│   │   ├── __init__.py
│   │   ├── client.py                   # WebhookClient for all webhook types
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── evaluation.py           # Evaluation webhook handling
│   │   │   ├── metrics.py              # Metrics webhook handling
│   │   │   └── completion.py           # Completion webhook handling
│   │   └── formatters/
│   │       ├── __init__.py
│   │       ├── transcript_formatter.py
│   │       └── metrics_formatter.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── service.py                  # ConfigurationService client
│   │   ├── loader.py                   # Configuration loading utilities
│   │   ├── validator.py                # Configuration validation
│   │   └── templates/
│   │       ├── __init__.py
│   │       ├── survey_agent.json       # Survey agent template
│   │       ├── sales_agent.json        # Sales agent template
│   │       └── support_agent.json      # Support agent template
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py                  # Enhanced logging utilities
│       ├── metrics.py                  # Metrics collection
│       ├── errors.py                   # Custom exceptions
│       └── helpers.py                  # General utility functions
│
├── agents/
│   ├── __init__.py
│   ├── configurable_agent.py          # Main configurable agent entry point
│   ├── survey_agent.py                # Specialized survey agent (legacy)
│   └── examples/
│       ├── __init__.py
│       ├── simple_agent.py            # Basic example
│       ├── rag_agent.py               # RAG-enabled example
│       └── multi_tool_agent.py        # Complex tool example
│
├── scripts/
│   ├── dispatch_agent.py              # Agent dispatch utilities
│   ├── test_agent.py                  # Agent testing utilities
│   ├── config_generator.py            # Generate configuration templates
│   └── migration/
│       ├── __init__.py
│       └── migrate_from_v0.py         # Migration from existing agents
│
├── configs/
│   ├── development/
│   │   ├── survey_agent.json
│   │   ├── sales_agent.json
│   │   └── support_agent.json
│   ├── staging/
│   │   └── ...
│   └── production/
│       └── ...
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # pytest configuration
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_components.py
│   │   ├── test_tools.py
│   │   ├── test_rag.py
│   │   └── test_memory.py
│   ├── integration/
│   │   ├── test_agent_session.py
│   │   ├── test_webhooks.py
│   │   └── test_end_to_end.py
│   └── fixtures/
│       ├── sample_configs.json
│       └── mock_responses.json
│
├── docs/
│   ├── README.md
│   ├── CONFIGURATION.md               # Configuration guide
│   ├── TOOLS.md                       # Custom tools guide
│   ├── RAG.md                         # RAG setup guide
│   ├── DEPLOYMENT.md                  # Deployment guide
│   ├── MIGRATION.md                   # Migration from v0 guide
│   └── examples/
│       ├── basic_setup.md
│       ├── advanced_configuration.md
│       └── custom_tools.md
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
│
└── deployment/
    ├── kubernetes/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── terraform/
    │   ├── main.tf
    │   └── variables.tf
    └── helm/
        └── configurable-agent/
            ├── Chart.yaml
            ├── values.yaml
            └── templates/


# configs/development/survey_agent.json
{
  "agent_id": "survey_agent_v1",
  "name": "Survey Agent",
  "description": "Automated survey conducting agent",
  "agent_type": "survey",
  "version": "1.0",
  "system_instructions": "You are Jhanvi, an automated survey assistant. You conduct surveys in a warm, empathetic, and professional manner.",
  "first_message": "Hi! I'm Jhanvi calling from our survey team. Is this a good time to speak with you?",
  "greeting_instructions": "Greet the user warmly and confirm if it's a good time for the survey.",
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4-turbo",
    "temperature": 0.7,
    "max_tokens": 500
  },
  "tts_config": {
    "provider": "elevenlabs",
    "voice_id": "MzqUf1HbJ8UmQ0wUsx2p",
    "model": "eleven_flash_v2_5",
    "language": "en"
  },
  "stt_config": {
    "provider": "elevenlabs", 
    "language": "en"
  },
  "rag_config": {
    "enabled": false
  },
  "memory_config": {
    "enabled": true,
    "type": "conversation",
    "max_history": 50
  },
  "tools": [
    {
      "name": "record_answer",
      "enabled": true,
      "async_execution": false
    },
    {
      "name": "handle_is_busy",
      "enabled": true,
      "async_execution": false
    },
    {
      "name": "end_call",
      "enabled": true,
      "async_execution": false
    }
  ],
  "completion_webhook": {
    "url": "https://your-webhook-endpoint.com/survey-complete",
    "headers": {
      "Content-Type": "application/json"
    },
    "timeout": 30,
    "enabled": true
  },
  "max_conversation_duration": 1800,
  "silence_timeout": 10,
  "interruption_handling": true,
  "noise_cancellation": "BVCTelephony",
  "agent_data": {
    "survey_config": {
      "company_name": "Unacademy",
      "survey_goal": "Collect learning experience feedback",
      "questions": [
        {
          "id": "satisfaction",
          "text": "How satisfied are you with our service?",
          "type": "rating",
          "min_value": 1,
          "max_value": 5
        }
      ]
    }
  }
} 