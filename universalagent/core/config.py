"""
Configuration dataclasses for configurable agents.

This module defines all configuration structures needed to set up
and run configurable voice AI agents with LiveKit.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class TTSProvider(Enum):
    """Supported TTS providers."""

    ELEVENLABS = "elevenlabs"
    CARTESIA = "cartesia"
    OPENAI = "openai"


class STTProvider(Enum):
    """Supported STT providers."""

    ELEVENLABS = "elevenlabs"
    DEEPGRAM = "deepgram"
    OPENAI = "openai"


class RAGProvider(Enum):
    """Supported RAG providers."""

    PINECONE = "pinecone"
    CHROMA = "chroma"
    LLAMAINDEX = "llamaindex"


class NoiseCancellationType(Enum):
    """Noise cancellation types."""

    BVC = "BVC"
    BVC_TELEPHONY = "BVCTelephony"
    NONE = "none"


class ToolType(Enum):
    """Tool types."""

    DEFAULT = "default"
    WEBHOOK = "webhook"


@dataclass
class ApiSpec:
    """API specification."""

    url: str
    method: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None


@dataclass
class LLMConfig:
    """Configuration for Language Model providers."""

    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.provider not in [p.value for p in LLMProvider]:
            logger.warning(f"Unknown LLM provider: {self.provider}")

        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")


@dataclass
class TTSConfig:
    """Configuration for Text-to-Speech providers."""

    provider: str
    voice_id: Optional[str] = None
    model: Optional[str] = None
    language: str = "en"
    speed: float = 1.0
    api_key: Optional[str] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.provider not in [p.value for p in TTSProvider]:
            logger.warning(f"Unknown TTS provider: {self.provider}")

        if self.speed < 0.25 or self.speed > 4.0:
            raise ValueError("Speed must be between 0.25 and 4.0")


@dataclass
class STTConfig:
    """Configuration for Speech-to-Text providers."""

    provider: str
    language: str = "en"
    model: Optional[str] = None
    api_key: Optional[str] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.provider not in [p.value for p in STTProvider]:
            logger.warning(f"Unknown STT provider: {self.provider}")


@dataclass
class RAGConfig:
    """Configuration for Retrieval-Augmented Generation."""

    enabled: bool = False
    namespace: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = None


@dataclass
class MemoryConfig:
    """Configuration for conversation memory management."""

    enabled: bool = False
    type: str = "conversation"  # "conversation", "user", "global"
    max_history: int = 50
    summarize_threshold: int = 100
    provider: Optional[str] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        valid_types = ["conversation", "user", "global"]
        if self.type not in valid_types:
            raise ValueError(f"Memory type must be one of: {valid_types}")

        if self.max_history < 1:
            raise ValueError("max_history must be positive")

        if self.summarize_threshold < self.max_history:
            raise ValueError("summarize_threshold must be >= max_history")


@dataclass
class ToolConfig:
    """Configuration for individual tools."""

    id: str
    name: str
    enabled: bool = True
    async_execution: bool = False
    description: Optional[str] = None
    type: ToolType = ToolType.DEFAULT
    api_spec: Optional[ApiSpec] = None


@dataclass
class EvaluationCriteria:
    """Configuration for evaluation criteria."""

    name: str
    description: str


@dataclass
class WebhookConfig:
    """Configuration for webhook integrations."""

    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    enabled: bool = True

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("Webhook URL must start with http:// or https://")

        if self.timeout < 1 or self.timeout > 300:
            raise ValueError("Timeout must be between 1 and 300 seconds")

        if self.retry_count < 0 or self.retry_count > 10:
            raise ValueError("Retry count must be between 0 and 10")


@dataclass
class AgentConfig:
    """Main configuration for a configurable agent."""

    # Core Identity (Required fields first)
    agent_id: str
    name: str
    description: str
    llm_config: LLMConfig

    # Optional Core Identity
    agent_type: str = "assistant"
    version: str = "1.0"

    # Interaction Configuration
    first_message: Optional[str] = None
    greeting_instructions: Optional[str] = None
    system_instructions: str = ""
    guardrails: str = ""
    initial_context: str = ""

    # AI Component Configuration
    tts_config: Optional[TTSConfig] = None
    stt_config: Optional[STTConfig] = None
    vad_config: Dict[str, Any] = field(default_factory=dict)
    turn_detection_config: Dict[str, Any] = field(default_factory=dict)

    # Advanced Features
    rag_config: Optional[RAGConfig] = None
    memory_config: Optional[MemoryConfig] = None

    # Tools & Capabilities
    tools: List[ToolConfig] = field(default_factory=list)

    # evaluation criteria
    evaluation_criteria: List[EvaluationCriteria] = field(default_factory=list)

    # Webhook Integration
    evaluation_webhook: Optional[WebhookConfig] = None
    metrics_webhook: Optional[WebhookConfig] = None
    completion_webhook: Optional[WebhookConfig] = None

    # Runtime Settings
    max_conversation_duration: Optional[int] = None  # seconds
    silence_timeout: Optional[int] = None
    interruption_handling: bool = True
    noise_cancellation: str = "BVC"

    # Agent-specific Data
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.agent_id:
            raise ValueError("agent_id is required")

        if not self.name:
            raise ValueError("name is required")

        if not self.system_instructions:
            logger.warning("No system instructions provided")

        if self.noise_cancellation not in [nc.value for nc in NoiseCancellationType]:
            logger.warning(f"Unknown noise cancellation type: {self.noise_cancellation}")

        if self.max_conversation_duration and self.max_conversation_duration < 30:
            raise ValueError("max_conversation_duration must be at least 30 seconds")

        # Validate tool names are unique
        tool_names = [tool.name for tool in self.tools]
        if len(tool_names) != len(set(tool_names)):
            raise ValueError("Tool names must be unique")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""

        def convert_value(value):
            if hasattr(value, "__dict__"):
                return {k: convert_value(v) for k, v in value.__dict__.items()}
            elif isinstance(value, list):
                return [convert_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            else:
                return value

        return convert_value(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """Create AgentConfig from dictionary."""
        # Parse nested configurations
        llm_config = LLMConfig(**data["llm_config"])

        tts_config = None
        if data.get("tts_config"):
            tts_config = TTSConfig(**data["tts_config"])

        stt_config = None
        if data.get("stt_config"):
            stt_config = STTConfig(**data["stt_config"])

        rag_config = None
        if data.get("rag_config"):
            rag_config = RAGConfig(**data["rag_config"])

        memory_config = None
        if data.get("memory_config"):
            memory_config = MemoryConfig(**data["memory_config"])

        # Parse tools
        tools = []
        for tool_data in data.get("tools", []):
            tools.append(ToolConfig(**tool_data))

        # Parse webhooks
        evaluation_webhook = None
        if data.get("evaluation_webhook"):
            evaluation_webhook = WebhookConfig(**data["evaluation_webhook"])

        metrics_webhook = None
        if data.get("metrics_webhook"):
            metrics_webhook = WebhookConfig(**data["metrics_webhook"])

        completion_webhook = None
        if data.get("completion_webhook"):
            completion_webhook = WebhookConfig(**data["completion_webhook"])

        # Create the configuration
        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            description=data["description"],
            llm_config=llm_config,
            agent_type=data.get("agent_type", "assistant"),
            version=data.get("version", "1.0"),
            first_message=data.get("first_message"),
            greeting_instructions=data.get("greeting_instructions"),
            system_instructions=data.get("system_instructions", ""),
            guardrails=data.get("guardrails", ""),
            initial_context=data.get("initial_context", ""),
            tts_config=tts_config,
            stt_config=stt_config,
            vad_config=data.get("vad_config", {}),
            turn_detection_config=data.get("turn_detection_config", {}),
            rag_config=rag_config,
            memory_config=memory_config,
            tools=tools,
            evaluation_webhook=evaluation_webhook,
            metrics_webhook=metrics_webhook,
            completion_webhook=completion_webhook,
            max_conversation_duration=data.get("max_conversation_duration"),
            silence_timeout=data.get("silence_timeout"),
            interruption_handling=data.get("interruption_handling", True),
            noise_cancellation=data.get("noise_cancellation", "BVC"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "AgentConfig":
        """Create AgentConfig from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> List[str]:
        """Validate the configuration and return list of issues."""
        issues = []

        # Check required fields
        if not self.agent_id:
            issues.append("agent_id is required")

        if not self.name:
            issues.append("name is required")

        if not self.system_instructions:
            issues.append("system_instructions is recommended")

        # Validate LLM config
        if not self.llm_config:
            issues.append("llm_config is required")

        # Check tool dependencies
        for tool in self.tools:
            if tool.async_execution and not tool.continue_conversation:
                issues.append(
                    f"Tool {tool.name}: async_execution requires continue_conversation=True"
                )

        # Check webhook configurations
        webhooks = [self.evaluation_webhook, self.metrics_webhook, self.completion_webhook]
        for webhook in webhooks:
            if webhook and webhook.enabled and not webhook.url:
                issues.append("Enabled webhook missing URL")

        return issues

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0

    def get_tool_by_name(self, name: str) -> Optional[ToolConfig]:
        """Get tool configuration by name."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None
