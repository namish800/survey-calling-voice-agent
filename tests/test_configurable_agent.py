"""
Tests for configurable agent functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from src.agents.configurable_agent import ConfigurableAgent
from src.agents.entrypoint import (
    create_entrypoint,
    create_room_input_options, 
    handle_initial_greeting,
    start_agent_session
)
from src.core.config import AgentConfig, LLMConfig, TTSConfig, STTConfig


class TestConfigurableAgent:
    """Test ConfigurableAgent class."""
    
    @pytest.fixture
    def sample_config(self):
        """Create sample agent configuration for testing."""
        return AgentConfig(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent for unit testing",
            system_instructions="You are a helpful test agent.",
            agent_type="assistant",
            first_message="Hello! I'm here to help you.",
            greeting_instructions="Greet the user warmly",
            personality_traits={"helpful": True, "friendly": True},
            conversation_style="professional",
            llm_config=LLMConfig(provider="openai", model="gpt-4"),
            tts_config=TTSConfig(provider="elevenlabs", voice_id="test-voice"),
            stt_config=STTConfig(provider="deepgram", model="nova-2"),
            agent_data={
                "survey_config": {
                    "company_name": "Test Company",
                    "survey_goal": "Test survey",
                    "questions": [
                        {"question_id": "q1", "text": "How are you?", "type": "open_text"}
                    ]
                }
            },
            metadata={"test_key": "test_value"}
        )
    
    def test_agent_initialization(self, sample_config):
        """Test agent initialization with configuration."""
        agent = ConfigurableAgent(sample_config)
        
        assert agent.agent_id == "test_agent"
        assert agent.agent_name == "Test Agent"
        assert agent.agent_type == "assistant"
        assert agent.description == "A test agent for unit testing"
        assert agent.config == sample_config
        assert agent.factory is not None
    
    def test_agent_properties(self, sample_config):
        """Test agent property accessors."""
        agent = ConfigurableAgent(sample_config)
        
        assert agent.get_first_message() == "Hello! I'm here to help you."
        assert agent.get_greeting_instructions() == "Greet the user warmly"
        assert agent.get_personality_traits() == {"helpful": True, "friendly": True}
        assert agent.get_conversation_style() == "professional"
        assert agent.get_agent_data()["survey_config"]["company_name"] == "Test Company"
        assert agent.get_metadata() == {"test_key": "test_value"}
    
    def test_agent_boolean_properties(self, sample_config):
        """Test agent boolean property checks."""
        agent = ConfigurableAgent(sample_config)
        
        # Default values for optional configs
        assert not agent.should_use_rag()  # No RAG config
        assert not agent.should_use_memory()  # No memory config
        assert agent.should_handle_interruptions()  # Default True
        assert agent.get_noise_cancellation_type() == "BVC"  # Default
    
    def test_chat_context_creation(self, sample_config):
        """Test chat context creation with system instructions."""
        agent = ConfigurableAgent(sample_config)
        context = agent.create_chat_context()
        
        # Should have system instructions
        assert context is not None
        # Check for correct ChatContext attributes - it has 'items' not 'messages'
        assert hasattr(context, 'items')
        # Verify we can access the items
        items = context.items
        assert isinstance(items, list)
    
    def test_personality_prompt_building(self, sample_config):
        """Test personality prompt building."""
        agent = ConfigurableAgent(sample_config)
        personality_prompt = agent._build_personality_prompt()
        
        assert "professional" in personality_prompt.lower()
        assert "helpful" in personality_prompt.lower()
        assert "friendly" in personality_prompt.lower()
    
    def test_survey_context_building(self, sample_config):
        """Test survey-specific context building."""
        sample_config.agent_type = "survey"
        agent = ConfigurableAgent(sample_config)
        
        survey_config = sample_config.agent_data["survey_config"]
        context = agent._build_survey_context(survey_config)
        
        assert "Test Company" in context
        assert "Test survey" in context
    
    def test_sales_context_building(self):
        """Test sales-specific context building."""
        config = AgentConfig(
            agent_id="sales_test",
            name="Sales Agent",
            description="Test sales agent",
            agent_type="sales",
            system_instructions="You are a sales agent.",
            llm_config=LLMConfig(provider="openai", model="gpt-4"),
            agent_data={
                "sales_config": {
                    "company_name": "Sales Corp",
                    "product_name": "Amazing Product",
                    "value_proposition": "Saves time and money",
                    "qualification_criteria": {
                        "budget": "$1000+",
                        "timeline": "3 months"
                    }
                }
            }
        )
        
        agent = ConfigurableAgent(config)
        sales_config = config.agent_data["sales_config"]
        context = agent._build_sales_context(sales_config)
        
        assert "Sales Corp" in context
        assert "Amazing Product" in context
        assert "Saves time and money" in context
        assert "budget" in context.lower()
    
    def test_agent_string_representation(self, sample_config):
        """Test agent string representations."""
        agent = ConfigurableAgent(sample_config)
        
        str_repr = str(agent)
        assert "test_agent" in str_repr
        assert "Test Agent" in str_repr
        assert "assistant" in str_repr
        
        repr_str = repr(agent)
        assert "ConfigurableAgent" in repr_str
        assert "test_agent" in repr_str


class TestEntrypointFunctions:
    """Test entrypoint and helper functions."""
    
    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return AgentConfig(
            agent_id="test_entrypoint",
            name="Test Entrypoint Agent",
            description="Agent for entrypoint testing",
            system_instructions="You are a test agent.",
            llm_config=LLMConfig(provider="openai", model="gpt-4"),
            tts_config=TTSConfig(provider="elevenlabs", voice_id="test-voice"),
            stt_config=STTConfig(provider="deepgram", model="nova-2"),
            noise_cancellation="BVC"
        )
    
    @pytest.fixture
    def mock_job_context(self):
        """Create mock JobContext for testing."""
        mock_ctx = Mock()
        mock_ctx.room = Mock()
        mock_ctx.room.name = "test-room"
        mock_ctx.job = Mock()
        mock_ctx.job.metadata = {"agent_id": "test_agent"}
        mock_ctx.connect = AsyncMock()
        return mock_ctx
    
    def test_create_entrypoint(self, sample_config):
        """Test custom entrypoint creation."""
        entrypoint = create_entrypoint("test_agent", config=sample_config)
        
        assert callable(entrypoint)
        assert entrypoint.__name__ == "custom_entrypoint"
    
    def test_create_room_input_options_with_bvc(self, sample_config):
        """Test room input options creation with BVC."""
        with patch('src.agents.entrypoint.NOISE_CANCELLATION_AVAILABLE', True):
            with patch('src.agents.entrypoint.noise_cancellation') as mock_nc:
                mock_nc.BVC.return_value = Mock()
                
                options = create_room_input_options(sample_config)
                
                assert options is not None
                mock_nc.BVC.assert_called_once()
    
    def test_create_room_input_options_with_bvc_telephony(self, sample_config):
        """Test room input options creation with BVC Telephony."""
        sample_config.noise_cancellation = "BVCTelephony"
        
        with patch('src.agents.entrypoint.NOISE_CANCELLATION_AVAILABLE', True):
            with patch('src.agents.entrypoint.noise_cancellation') as mock_nc:
                mock_nc.BVCTelephony.return_value = Mock()
                
                options = create_room_input_options(sample_config)
                
                assert options is not None
                mock_nc.BVCTelephony.assert_called_once()
    
    def test_create_room_input_options_unavailable(self, sample_config):
        """Test room input options when noise cancellation unavailable."""
        with patch('src.agents.entrypoint.NOISE_CANCELLATION_AVAILABLE', False):
            options = create_room_input_options(sample_config)
            assert options is None
    
    @pytest.mark.asyncio
    async def test_handle_initial_greeting_with_first_message(self, sample_config):
        """Test initial greeting handling with first message."""
        sample_config.first_message = "Hello, welcome!"
        agent = ConfigurableAgent(sample_config)
        
        mock_session = Mock()
        mock_session.generate_reply = AsyncMock()
        
        await handle_initial_greeting(mock_session, agent)
        
        mock_session.generate_reply.assert_called_once()
        call_args = mock_session.generate_reply.call_args[1]
        assert "Say: Hello, welcome!" in call_args["instructions"]
    
    @pytest.mark.asyncio
    async def test_handle_initial_greeting_with_greeting_instructions(self, sample_config):
        """Test initial greeting handling with greeting instructions."""
        sample_config.first_message = None
        sample_config.greeting_instructions = "Greet warmly and ask how you can help"
        agent = ConfigurableAgent(sample_config)
        
        mock_session = Mock()
        mock_session.generate_reply = AsyncMock()
        
        await handle_initial_greeting(mock_session, agent)
        
        mock_session.generate_reply.assert_called_once()
        call_args = mock_session.generate_reply.call_args[1]
        assert "Greet warmly and ask how you can help" in call_args["instructions"]
    
    @pytest.mark.asyncio
    async def test_handle_initial_greeting_default(self, sample_config):
        """Test initial greeting handling with default greeting."""
        sample_config.first_message = None
        sample_config.greeting_instructions = None
        agent = ConfigurableAgent(sample_config)
        
        mock_session = Mock()
        mock_session.generate_reply = AsyncMock()
        
        await handle_initial_greeting(mock_session, agent)
        
        mock_session.generate_reply.assert_called_once()
        call_args = mock_session.generate_reply.call_args[1]
        assert "Greet the user warmly" in call_args["instructions"]


class TestSessionIntegration:
    """Test agent session integration."""
    
    @pytest.fixture
    def sample_config(self):
        """Create sample configuration."""
        return AgentConfig(
            agent_id="integration_test",
            name="Integration Test Agent",
            description="Agent for integration testing",
            system_instructions="You are an integration test agent.",
            llm_config=LLMConfig(provider="openai", model="gpt-4"),
            tts_config=TTSConfig(provider="elevenlabs", voice_id="test-voice"),
            stt_config=STTConfig(provider="deepgram", model="nova-2")
        )
    
    @pytest.fixture
    def mock_job_context(self):
        """Create mock JobContext."""
        mock_ctx = Mock()
        mock_ctx.room = Mock()
        mock_ctx.room.name = "integration-test-room"
        mock_ctx.job = Mock()
        mock_ctx.job.metadata = {"agent_id": "integration_test"}
        mock_ctx.connect = AsyncMock()
        return mock_ctx
    
    @pytest.mark.asyncio
    async def test_start_agent_session_success(self, sample_config, mock_job_context):
        """Test successful agent session start."""
        with patch('src.agents.entrypoint.ComponentFactory') as mock_factory_class:
            # Mock factory instance and component creation
            mock_factory = Mock()
            mock_factory_class.return_value = mock_factory
            
            # Mock component creation
            mock_llm = Mock()
            mock_tts = Mock()
            mock_stt = Mock()
            mock_vad = Mock()
            mock_turn_detection = Mock()
            
            mock_factory.create_llm.return_value = mock_llm
            mock_factory.create_tts.return_value = mock_tts
            mock_factory.create_stt.return_value = mock_stt
            mock_factory.create_vad.return_value = mock_vad
            mock_factory.create_turn_detection.return_value = mock_turn_detection
            
            # Mock AgentSession
            with patch('src.agents.entrypoint.AgentSession') as mock_session_class:
                mock_session = Mock()
                mock_session.start = AsyncMock()
                mock_session_class.return_value = mock_session
                
                # Mock greeting handling
                with patch('src.agents.entrypoint.handle_initial_greeting') as mock_greeting:
                    mock_greeting.return_value = AsyncMock()
                    
                    # Call the function
                    await start_agent_session(mock_job_context, sample_config)
                    
                    # Verify components were created
                    mock_factory.create_llm.assert_called_once_with(sample_config.llm_config)
                    mock_factory.create_tts.assert_called_once_with(sample_config.tts_config)
                    mock_factory.create_stt.assert_called_once_with(sample_config.stt_config)
                    mock_factory.create_vad.assert_called_once()
                    mock_factory.create_turn_detection.assert_called_once()
                    
                    # Verify session was created and started
                    mock_session_class.assert_called_once()
                    mock_session.start.assert_called_once()
                    
                    # Verify greeting was handled
                    mock_greeting.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__]) 