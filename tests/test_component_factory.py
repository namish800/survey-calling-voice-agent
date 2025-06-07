"""
Tests for the component factory module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.components.factory import ComponentFactory, ComponentCreationError
from src.core.config import LLMConfig, TTSConfig, STTConfig


class TestComponentFactory:
    """Test ComponentFactory class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = ComponentFactory()
    
    def test_factory_initialization(self):
        """Test factory initializes with correct providers."""
        supported = self.factory.get_supported_providers()
        
        assert "llm" in supported
        assert "tts" in supported
        assert "stt" in supported
        
        assert "openai" in supported["llm"]
        assert "elevenlabs" in supported["tts"]
        assert "deepgram" in supported["stt"]
    
    def test_provider_availability_check(self):
        """Test provider availability checking."""
        availability = self.factory.validate_provider_availability()
        
        # OpenAI should always be available
        assert availability["llm"]["openai"] is True
        assert availability["tts"]["openai"] is True
        assert availability["stt"]["openai"] is True
        
        # Deepgram should be available with base install
        assert availability["stt"]["deepgram"] is True


class TestLLMCreation:
    """Test LLM component creation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = ComponentFactory()
    
    @patch('src.components.factory.openai.LLM')
    def test_create_openai_llm_basic(self, mock_llm_class):
        """Test creating basic OpenAI LLM."""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        config = LLMConfig(
            provider="openai",
            model="gpt-4-turbo",
            temperature=0.7
        )
        
        result = self.factory.create_llm(config)
        
        assert result == mock_llm
        mock_llm_class.assert_called_once_with(
            model="gpt-4-turbo",
            temperature=0.7
        )
    
    @patch('src.components.factory.openai.LLM')
    def test_create_openai_llm_with_options(self, mock_llm_class):
        """Test creating OpenAI LLM with all options."""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        config = LLMConfig(
            provider="openai",
            model="gpt-4-turbo",
            temperature=0.8,
            max_tokens=1000,
            api_key="test-key",
            base_url="https://custom.openai.com",
            custom_params={"stream": True, "top_p": 0.9}
        )
        
        result = self.factory.create_llm(config)
        
        assert result == mock_llm
        mock_llm_class.assert_called_once_with(
            model="gpt-4-turbo",
            temperature=0.8,
            max_tokens=1000,
            api_key="test-key",
            base_url="https://custom.openai.com",
            stream=True,
            top_p=0.9
        )
    
    @patch('src.components.factory.ANTHROPIC_AVAILABLE', True)
    def test_create_anthropic_llm(self):
        """Test creating Anthropic LLM when available."""
        mock_llm = Mock()
        
        # Mock the factory's internal method instead of the plugin
        with patch.object(self.factory, '_create_anthropic_llm', return_value=mock_llm) as mock_create:
            config = LLMConfig(
                provider="anthropic",
                model="claude-3-sonnet",
                temperature=0.6,
                api_key="test-anthropic-key"
            )
            
            result = self.factory.create_llm(config)
            
            assert result == mock_llm
            mock_create.assert_called_once_with(config)
    
    @patch('src.components.factory.ANTHROPIC_AVAILABLE', False)
    def test_create_anthropic_llm_not_available(self):
        """Test creating Anthropic LLM when not available."""
        config = LLMConfig(
            provider="anthropic",
            model="claude-3-sonnet"
        )
        
        with pytest.raises(ComponentCreationError, match="Anthropic plugin not available"):
            self.factory.create_llm(config)
    
    def test_create_llm_unknown_provider(self):
        """Test creating LLM with unknown provider."""
        config = LLMConfig(
            provider="unknown",
            model="some-model"
        )
        
        with pytest.raises(ComponentCreationError, match="Unknown LLM provider: unknown"):
            self.factory.create_llm(config)
    
    @patch('src.components.factory.openai.LLM')
    def test_create_llm_with_exception(self, mock_llm_class):
        """Test LLM creation handles exceptions."""
        mock_llm_class.side_effect = Exception("API error")
        
        config = LLMConfig(
            provider="openai",
            model="gpt-4"
        )
        
        with pytest.raises(ComponentCreationError, match="Failed to create LLM"):
            self.factory.create_llm(config)


class TestTTSCreation:
    """Test TTS component creation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = ComponentFactory()
    
    @patch('src.components.factory.ELEVENLABS_AVAILABLE', True)
    def test_create_elevenlabs_tts(self):
        """Test creating ElevenLabs TTS."""
        mock_tts = Mock()
        
        # Mock the factory's internal method instead of the plugin
        with patch.object(self.factory, '_create_elevenlabs_tts', return_value=mock_tts) as mock_create:
            config = TTSConfig(
                provider="elevenlabs",
                voice_id="test-voice-id",
                model="eleven_flash_v2_5",
                api_key="test-key"
            )
            
            result = self.factory.create_tts(config)
            
            assert result == mock_tts
            mock_create.assert_called_once_with(config)
    
    @patch('src.components.factory.ELEVENLABS_AVAILABLE', False)
    def test_create_elevenlabs_tts_not_available(self):
        """Test creating ElevenLabs TTS when not available."""
        config = TTSConfig(
            provider="elevenlabs",
            voice_id="test-voice"
        )
        
        with pytest.raises(ComponentCreationError, match="ElevenLabs plugin not available"):
            self.factory.create_tts(config)
    
    @patch('src.components.factory.openai.TTS')
    def test_create_openai_tts(self, mock_tts_class):
        """Test creating OpenAI TTS."""
        mock_tts = Mock()
        mock_tts_class.return_value = mock_tts
        
        config = TTSConfig(
            provider="openai",
            voice_id="alloy",
            model="tts-1",
            custom_params={"speed": 1.2}
        )
        
        result = self.factory.create_tts(config)
        
        assert result == mock_tts
        mock_tts_class.assert_called_once_with(
            voice="alloy",
            model="tts-1",
            speed=1.2
        )
    
    @patch('src.components.factory.CARTESIA_AVAILABLE', True)
    def test_create_cartesia_tts(self):
        """Test creating Cartesia TTS."""
        mock_tts = Mock()
        
        # Mock the factory's internal method instead of the plugin
        with patch.object(self.factory, '_create_cartesia_tts', return_value=mock_tts) as mock_create:
            config = TTSConfig(
                provider="cartesia",
                voice_id="cartesia-voice",
                language="en"
            )
            
            result = self.factory.create_tts(config)
            
            assert result == mock_tts
            mock_create.assert_called_once_with(config)
    
    def test_create_tts_unknown_provider(self):
        """Test creating TTS with unknown provider."""
        config = TTSConfig(
            provider="unknown",
            voice_id="some-voice"
        )
        
        with pytest.raises(ComponentCreationError, match="Unknown TTS provider: unknown"):
            self.factory.create_tts(config)


class TestSTTCreation:
    """Test STT component creation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = ComponentFactory()
    
    @patch('src.components.factory.deepgram.STT')
    def test_create_deepgram_stt(self, mock_stt_class):
        """Test creating Deepgram STT."""
        mock_stt = Mock()
        mock_stt_class.return_value = mock_stt
        
        config = STTConfig(
            provider="deepgram",
            language="en",
            model="nova-2",
            api_key="test-deepgram-key"
        )
        
        result = self.factory.create_stt(config)
        
        assert result == mock_stt
        mock_stt_class.assert_called_once_with(
            language="en",
            model="nova-2",
            api_key="test-deepgram-key"
        )
    
    @patch('src.components.factory.ELEVENLABS_AVAILABLE', True)
    def test_create_elevenlabs_stt(self):
        """Test creating ElevenLabs STT."""
        mock_stt = Mock()
        
        # Mock the factory's internal method instead of the plugin
        with patch.object(self.factory, '_create_elevenlabs_stt', return_value=mock_stt) as mock_create:
            config = STTConfig(
                provider="elevenlabs",
                language="multi",
                custom_params={"stability": 0.8}
            )
            
            result = self.factory.create_stt(config)
            
            assert result == mock_stt
            mock_create.assert_called_once_with(config)
    
    @patch('src.components.factory.openai.STT')
    def test_create_openai_stt(self, mock_stt_class):
        """Test creating OpenAI STT."""
        mock_stt = Mock()
        mock_stt_class.return_value = mock_stt
        
        config = STTConfig(
            provider="openai",
            model="whisper-1",
            language="en"
        )
        
        result = self.factory.create_stt(config)
        
        assert result == mock_stt
        mock_stt_class.assert_called_once_with(
            model="whisper-1",
            language="en"
        )
    
    def test_create_stt_unknown_provider(self):
        """Test creating STT with unknown provider."""
        config = STTConfig(
            provider="unknown",
            language="en"
        )
        
        with pytest.raises(ComponentCreationError, match="Unknown STT provider: unknown"):
            self.factory.create_stt(config)


class TestVADAndTurnDetection:
    """Test VAD and turn detection creation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = ComponentFactory()
    
    @patch('src.components.factory.silero.VAD.load')
    def test_create_vad(self, mock_vad_load):
        """Test creating VAD."""
        mock_vad = Mock()
        mock_vad_load.return_value = mock_vad
        
        result = self.factory.create_vad()
        
        assert result == mock_vad
        mock_vad_load.assert_called_once()
    
    @patch('src.components.factory.silero.VAD.load')
    def test_create_vad_with_config(self, mock_vad_load):
        """Test creating VAD with configuration."""
        mock_vad = Mock()
        mock_vad_load.return_value = mock_vad
        
        config = {"threshold": 0.5}
        result = self.factory.create_vad(config)
        
        assert result == mock_vad
        mock_vad_load.assert_called_once()
    
    @patch('src.components.factory.MultilingualModel')
    def test_create_turn_detection(self, mock_turn_detection_class):
        """Test creating turn detection."""
        mock_turn_detection = Mock()
        mock_turn_detection_class.return_value = mock_turn_detection
        
        result = self.factory.create_turn_detection()
        
        assert result == mock_turn_detection
        mock_turn_detection_class.assert_called_once()
    
    @patch('src.components.factory.silero.VAD.load')
    def test_create_vad_handles_exception(self, mock_vad_load):
        """Test VAD creation handles exceptions."""
        mock_vad_load.side_effect = Exception("VAD loading error")
        
        with pytest.raises(ComponentCreationError, match="Failed to create VAD"):
            self.factory.create_vad()
    
    @patch('src.components.factory.MultilingualModel')
    def test_create_turn_detection_handles_exception(self, mock_turn_detection_class):
        """Test turn detection creation handles exceptions."""
        mock_turn_detection_class.side_effect = Exception("Turn detection error")
        
        with pytest.raises(ComponentCreationError, match="Failed to create turn detection"):
            self.factory.create_turn_detection()


class TestFactoryIntegration:
    """Integration tests for the ComponentFactory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = ComponentFactory()
    
    @patch('src.components.factory.openai.LLM')
    @patch('src.components.factory.openai.TTS')
    @patch('src.components.factory.deepgram.STT')
    @patch('src.components.factory.silero.VAD.load')
    @patch('src.components.factory.MultilingualModel')
    def test_create_full_pipeline(self, mock_turn_det, mock_vad, mock_stt, mock_tts, mock_llm):
        """Test creating a complete pipeline from configurations."""
        # Set up mocks
        mock_llm_instance = Mock()
        mock_tts_instance = Mock()
        mock_stt_instance = Mock()
        mock_vad_instance = Mock()
        mock_turn_det_instance = Mock()
        
        mock_llm.return_value = mock_llm_instance
        mock_tts.return_value = mock_tts_instance
        mock_stt.return_value = mock_stt_instance
        mock_vad.return_value = mock_vad_instance
        mock_turn_det.return_value = mock_turn_det_instance
        
        # Create configurations
        llm_config = LLMConfig(provider="openai", model="gpt-4-turbo")
        tts_config = TTSConfig(provider="openai", voice_id="alloy")
        stt_config = STTConfig(provider="deepgram", model="nova-2")
        
        # Create components
        llm = self.factory.create_llm(llm_config)
        tts = self.factory.create_tts(tts_config)
        stt = self.factory.create_stt(stt_config)
        vad = self.factory.create_vad()
        turn_detection = self.factory.create_turn_detection()
        
        # Verify all components were created
        assert llm == mock_llm_instance
        assert tts == mock_tts_instance
        assert stt == mock_stt_instance
        assert vad == mock_vad_instance
        assert turn_detection == mock_turn_det_instance
        
        # Verify all mocks were called
        mock_llm.assert_called_once()
        mock_tts.assert_called_once()
        mock_stt.assert_called_once()
        mock_vad.assert_called_once()
        mock_turn_det.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__]) 