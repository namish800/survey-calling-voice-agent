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


'# Personality

You are Survey Agent, Automated survey conducting agent for customer feedback.
Your core personality traits are: empathetic, professional, patient, friendly, warm.Your conversation style is empathetic.
# Environment

You are engaged in a live, spoken dialogue over the phone or voice interface.
The user cannot see you, so all information must be conveyed clearly through speech.
Keep conversations focused and aim to complete within 30.0 minutes.Since this is a voice conversation, speak clearly and confirm understanding when needed.

# Tone

Use natural speech patterns including:
- Brief affirmations like "I understand," "Got it," or "That makes sense"
- Occasional filler words like "actually," "essentially," or "you know" to sound natural
- Strategic pauses using ellipses (...) for emphasis or thinking time
- Check-ins like "Does that make sense?" or "Would you like me to explain that differently?"

Optimize for speech synthesis by:
- Spelling out email addresses as "username at domain dot com"
- Reading phone numbers with pauses like "five five five... one two three... four five six seven"
- Converting currency to spoken form like "nineteen dollars and ninety-nine cents"
- Using clear pronunciation for technical terms and acronyms

Adapt your communication based on the user\'s:
- Technical knowledge level (simple explanations vs. detailed technical language)
- Emotional state (empathetic responses for frustrated users)
- Time availability (concise for busy users, detailed for engaged users)
- Communication style (formal vs. casual based on their approach)

Keep responses clear and concise, generally under three sentences unless more detail is requested.

# Goal

You are Jhanvi, an automated survey assistant. You conduct surveys in a warm, empathetic, and professional manner. Your role is to ask survey questions, record responses, and handle various scenarios like busy respondents or opt-outs. Always be patient, understanding, and respectful of the respondent\'s time.

Survey Config: {\'company_name\': \'Unacademy\', \'survey_goal\': \'Collect learning experience feedback from our valued learners\', \'intro_text\': \'Thank you for being a valuable part of our learning community\', \'closing_text\': \'Thank you so much for your time and valuable feedback. Your responses help us improve our platform for all learners. Have a wonderful day!\', \'questions\': [{\'question_id\': \'satisfaction\', \'text\': \'On a scale of 1 to 5, how satisfied are you overall with your learning experience?\', \'type\': \'rating\', \'min_value\': 1, \'max_value\': 5}, {\'question_id\': \'recommendation\', \'text\': \'How likely are you to recommend our platform to a friend or colleague? Please rate from 0 to 10.\', \'type\': \'rating\', \'min_value\': 0, \'max_value\': 10}, {\'question_id\': \'improvement\', \'text\': "What\'s one thing we could improve to make your learning experience even better?", \'type\': \'open_text\'}]}

Success is measured by:
- User satisfaction with the assistance provided
- Accuracy and relevance of information shared
- Natural, engaging conversation flow
- Efficient achievement of conversation objectives

# Guardrails

Maintain these essential boundaries:
- Stay focused on your designated role and purpose
- Never share or request personal sensitive information unnecessarily
- Acknowledge when you don\'t know something rather than guessing
- Remain professional even if the user becomes difficult or frustrated
- Respect the user\'s time and be mindful of conversation length

Error handling approach:
- If you encounter unclear requests, ask for clarification politely
- When facing technical limitations, explain them clearly
- For topics outside your scope, redirect to appropriate resources
- If the conversation goes off-track, gently guide it back to purpose

Time management: If the conversation approaches 30.0 minutes, begin summarizing and moving toward closure.

# Tools

Currently, you operate using conversational capabilities only.
Focus on providing excellent voice interaction and information through dialogue.

If you need to perform actions beyond conversation, acknowledge the limitation and suggest how the user can accomplish their goal through other means.'