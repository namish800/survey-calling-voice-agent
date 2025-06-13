"""
Tests for the configuration module.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

from universalagent.core.config import (
    AgentConfig,
    LLMConfig,
    TTSConfig,
    STTConfig,
    RAGConfig,
    MemoryConfig,
    ToolConfig,
    WebhookConfig,
    AgentType,
    LLMProvider,
    TTSProvider,
    STTProvider,
)
from universalagent.core.config_loader import ConfigurationLoader, load_config_from_file


class TestLLMConfig:
    """Test LLMConfig dataclass."""
    
    def test_valid_llm_config(self):
        """Test creating a valid LLM configuration."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4-turbo",
            temperature=0.7
        )
        assert config.provider == "openai"
        assert config.model == "gpt-4-turbo"
        assert config.temperature == 0.7
        assert config.max_tokens is None
    
    def test_invalid_temperature(self):
        """Test that invalid temperature raises error."""
        with pytest.raises(ValueError, match="Temperature must be between 0 and 2"):
            LLMConfig(
                provider="openai",
                model="gpt-4",
                temperature=3.0
            )
    
    def test_custom_params(self):
        """Test custom parameters are stored correctly."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            custom_params={"stream": True, "top_p": 0.9}
        )
        assert config.custom_params["stream"] is True
        assert config.custom_params["top_p"] == 0.9


class TestTTSConfig:
    """Test TTSConfig dataclass."""
    
    def test_valid_tts_config(self):
        """Test creating a valid TTS configuration."""
        config = TTSConfig(
            provider="elevenlabs",
            voice_id="test-voice-id",
            model="eleven_flash_v2_5"
        )
        assert config.provider == "elevenlabs"
        assert config.voice_id == "test-voice-id"
        assert config.language == "en"
        assert config.speed == 1.0
    
    def test_invalid_speed(self):
        """Test that invalid speed raises error."""
        with pytest.raises(ValueError, match="Speed must be between 0.25 and 4.0"):
            TTSConfig(
                provider="elevenlabs",
                speed=5.0
            )


class TestRAGConfig:
    """Test RAGConfig dataclass."""
    
    def test_disabled_rag_config(self):
        """Test RAG configuration when disabled."""
        config = RAGConfig(enabled=False)
        assert config.enabled is False
        assert config.provider == "pinecone"
        assert config.top_k == 5
    
    def test_enabled_rag_config(self):
        """Test RAG configuration when enabled."""
        config = RAGConfig(
            enabled=True,
            provider="pinecone",
            index_name="test-index",
            similarity_threshold=0.8,
            top_k=3
        )
        assert config.enabled is True
        assert config.index_name == "test-index"
        assert config.similarity_threshold == 0.8
        assert config.top_k == 3
    
    def test_invalid_similarity_threshold(self):
        """Test invalid similarity threshold."""
        with pytest.raises(ValueError, match="Similarity threshold must be between 0 and 1"):
            RAGConfig(similarity_threshold=1.5)
    
    def test_invalid_top_k(self):
        """Test invalid top_k value."""
        with pytest.raises(ValueError, match="top_k must be between 1 and 100"):
            RAGConfig(top_k=0)


class TestMemoryConfig:
    """Test MemoryConfig dataclass."""
    
    def test_valid_memory_config(self):
        """Test creating a valid memory configuration."""
        config = MemoryConfig(
            enabled=True,
            type="conversation",
            max_history=100
        )
        assert config.enabled is True
        assert config.type == "conversation"
        assert config.max_history == 100
    
    def test_invalid_memory_type(self):
        """Test invalid memory type."""
        with pytest.raises(ValueError, match="Memory type must be one of"):
            MemoryConfig(type="invalid_type")
    
    def test_invalid_max_history(self):
        """Test invalid max_history."""
        with pytest.raises(ValueError, match="max_history must be positive"):
            MemoryConfig(max_history=0)


class TestToolConfig:
    """Test ToolConfig dataclass."""
    
    def test_builtin_tool_config(self):
        """Test built-in tool configuration."""
        config = ToolConfig(
            name="record_answer",
            enabled=True
        )
        assert config.name == "record_answer"
        assert config.enabled is True
        assert config.module_path is None
    
    def test_custom_tool_config(self):
        """Test custom tool configuration."""
        config = ToolConfig(
            name="custom_tool",
            module_path="custom.tools",
            function_name="my_tool",
            async_execution=True
        )
        assert config.name == "custom_tool"
        assert config.module_path == "custom.tools"
        assert config.function_name == "my_tool"
        assert config.async_execution is True
    
    def test_invalid_custom_tool_config(self):
        """Test invalid custom tool configuration."""
        with pytest.raises(ValueError, match="function_name required when module_path is specified"):
            ToolConfig(
                name="custom_tool",
                module_path="custom.tools"
                # Missing function_name
            )


class TestWebhookConfig:
    """Test WebhookConfig dataclass."""
    
    def test_valid_webhook_config(self):
        """Test creating a valid webhook configuration."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            timeout=30,
            retry_count=3
        )
        assert config.url == "https://example.com/webhook"
        assert config.timeout == 30
        assert config.retry_count == 3
        assert config.enabled is True
    
    def test_invalid_webhook_url(self):
        """Test invalid webhook URL."""
        with pytest.raises(ValueError, match="Webhook URL must start with http:// or https://"):
            WebhookConfig(url="ftp://example.com/webhook")
    
    def test_invalid_timeout(self):
        """Test invalid timeout."""
        with pytest.raises(ValueError, match="Timeout must be between 1 and 300 seconds"):
            WebhookConfig(
                url="https://example.com/webhook",
                timeout=500
            )


class TestAgentConfig:
    """Test AgentConfig dataclass."""
    
    def test_minimal_agent_config(self):
        """Test creating a minimal agent configuration."""
        llm_config = LLMConfig(provider="openai", model="gpt-4")
        
        config = AgentConfig(
            agent_id="test-agent",
            name="Test Agent",
            description="A test agent",
            llm_config=llm_config,
            system_instructions="You are a test agent."
        )
        
        assert config.agent_id == "test-agent"
        assert config.name == "Test Agent"
        assert config.agent_type == "assistant"  # default
        assert config.llm_config == llm_config
        assert config.is_valid()
    
    def test_full_agent_config(self):
        """Test creating a full agent configuration."""
        llm_config = LLMConfig(provider="openai", model="gpt-4")
        tts_config = TTSConfig(provider="elevenlabs", voice_id="test-voice")
        stt_config = STTConfig(provider="elevenlabs")
        rag_config = RAGConfig(enabled=True, provider="pinecone")
        memory_config = MemoryConfig(enabled=True, type="conversation")
        webhook_config = WebhookConfig(url="https://example.com/webhook")
        
        tools = [
            ToolConfig(name="tool1"),
            ToolConfig(name="tool2", enabled=False)
        ]
        
        config = AgentConfig(
            agent_id="full-test-agent",
            name="Full Test Agent",
            description="A full test agent",
            agent_type="survey",
            system_instructions="You are a survey agent.",
            llm_config=llm_config,
            tts_config=tts_config,
            stt_config=stt_config,
            rag_config=rag_config,
            memory_config=memory_config,
            tools=tools,
            completion_webhook=webhook_config,
            max_conversation_duration=1800
        )
        
        assert config.agent_type == "survey"
        assert config.tts_config == tts_config
        assert config.rag_config == rag_config
        assert len(config.tools) == 2
        assert config.tools[0].name == "tool1"
        assert config.tools[1].enabled is False
        assert config.is_valid()
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        with pytest.raises(ValueError, match="agent_id is required"):
            AgentConfig(
                agent_id="",
                name="Test",
                description="Test",
                llm_config=LLMConfig(provider="openai", model="gpt-4")
            )
        
        with pytest.raises(ValueError, match="name is required"):
            AgentConfig(
                agent_id="test",
                name="",
                description="Test",
                llm_config=LLMConfig(provider="openai", model="gpt-4")
            )
    
    def test_duplicate_tool_names(self):
        """Test validation fails with duplicate tool names."""
        llm_config = LLMConfig(provider="openai", model="gpt-4")
        tools = [
            ToolConfig(name="duplicate_tool"),
            ToolConfig(name="duplicate_tool")
        ]
        
        with pytest.raises(ValueError, match="Tool names must be unique"):
            AgentConfig(
                agent_id="test",
                name="Test",
                description="Test",
                llm_config=llm_config,
                tools=tools
            )
    
    def test_config_serialization(self):
        """Test configuration serialization to/from dict and JSON."""
        llm_config = LLMConfig(provider="openai", model="gpt-4")
        tools = [ToolConfig(name="test_tool")]
        
        config = AgentConfig(
            agent_id="serialization-test",
            name="Serialization Test",
            description="Test serialization",
            llm_config=llm_config,
            tools=tools,
            system_instructions="Test instructions"
        )
        
        # Test to_dict
        config_dict = config.to_dict()
        assert config_dict["agent_id"] == "serialization-test"
        assert config_dict["llm_config"]["provider"] == "openai"
        assert len(config_dict["tools"]) == 1
        
        # Test to_json
        config_json = config.to_json()
        assert isinstance(config_json, str)
        
        # Test from_dict
        restored_config = AgentConfig.from_dict(config_dict)
        assert restored_config.agent_id == config.agent_id
        assert restored_config.llm_config.provider == config.llm_config.provider
        assert len(restored_config.tools) == len(config.tools)
        
        # Test from_json
        restored_from_json = AgentConfig.from_json(config_json)
        assert restored_from_json.agent_id == config.agent_id
    
    def test_get_tool_by_name(self):
        """Test getting tool by name."""
        llm_config = LLMConfig(provider="openai", model="gpt-4")
        tools = [
            ToolConfig(name="tool1"),
            ToolConfig(name="tool2")
        ]
        
        config = AgentConfig(
            agent_id="test",
            name="Test",
            description="Test",
            llm_config=llm_config,
            tools=tools
        )
        
        tool1 = config.get_tool_by_name("tool1")
        assert tool1 is not None
        assert tool1.name == "tool1"
        
        nonexistent = config.get_tool_by_name("nonexistent")
        assert nonexistent is None


class TestConfigurationLoader:
    """Test ConfigurationLoader class."""
    
    def test_load_from_file(self):
        """Test loading configuration from file."""
        # Create a temporary config file
        config_data = {
            "agent_id": "file-test",
            "name": "File Test Agent",
            "description": "Test loading from file",
            "system_instructions": "Test instructions",
            "llm_config": {
                "provider": "openai",
                "model": "gpt-4"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        try:
            loader = ConfigurationLoader()
            config = loader.load_from_file(temp_file)
            
            assert config is not None
            assert config.agent_id == "file-test"
            assert config.name == "File Test Agent"
            assert config.llm_config.provider == "openai"
        finally:
            os.unlink(temp_file)
    
    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file."""
        loader = ConfigurationLoader()
        config = loader.load_from_file("nonexistent.json")
        assert config is None
    
    def test_save_config(self):
        """Test saving configuration to file."""
        llm_config = LLMConfig(provider="openai", model="gpt-4")
        config = AgentConfig(
            agent_id="save-test",
            name="Save Test",
            description="Test saving",
            llm_config=llm_config,
            system_instructions="Test"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            loader = ConfigurationLoader()
            success = loader.save_config(config, temp_file)
            assert success
            
            # Verify file was created and is valid
            assert os.path.exists(temp_file)
            
            # Load it back and verify
            loaded_config = loader.load_from_file(temp_file)
            assert loaded_config is not None
            assert loaded_config.agent_id == "save-test"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


@pytest.fixture
def sample_config_file():
    """Fixture that creates a sample configuration file."""
    config_data = {
        "agent_id": "test-fixture",
        "name": "Test Fixture Agent",
        "description": "A test agent for fixtures",
        "system_instructions": "You are a test agent.",
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4-turbo",
            "temperature": 0.7
        },
        "tts_config": {
            "provider": "elevenlabs",
            "voice_id": "test-voice"
        },
        "tools": [
            {
                "name": "test_tool",
                "enabled": True
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


def test_load_config_from_file_convenience_function(sample_config_file):
    """Test the convenience function for loading configs."""
    config = load_config_from_file(sample_config_file)
    
    assert config is not None
    assert config.agent_id == "test-fixture"
    assert config.name == "Test Fixture Agent"
    assert config.llm_config.provider == "openai"
    assert config.tts_config.provider == "elevenlabs"
    assert len(config.tools) == 1
    assert config.tools[0].name == "test_tool"


if __name__ == "__main__":
    pytest.main([__file__]) 