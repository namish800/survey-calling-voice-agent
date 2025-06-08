"""
Component factory for creating LiveKit components from configuration.

This module provides the ComponentFactory class that creates actual LiveKit
components (LLM, TTS, STT, VAD, etc.) from our configuration objects.
"""

import logging
from typing import Optional, Dict, Any

from livekit.agents import llm, stt, tts, vad, tokenize
from livekit.plugins import openai, deepgram, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Try to import optional providers
try:
    from livekit.plugins import elevenlabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    logging.warning("ElevenLabs plugin not available")

try:
    from livekit.plugins import cartesia
    CARTESIA_AVAILABLE = True
except ImportError:
    CARTESIA_AVAILABLE = False
    logging.warning("Cartesia plugin not available")

try:
    from livekit.plugins import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("Anthropic plugin not available")

from core.config import LLMConfig, TTSConfig, STTConfig

logger = logging.getLogger(__name__)


class ComponentCreationError(Exception):
    """Exception raised when component creation fails."""
    pass


class ComponentFactory:
    """Factory class for creating LiveKit components from configuration."""
    
    def __init__(self):
        """Initialize the component factory."""
        self._llm_providers = {
            "openai": self._create_openai_llm,
            "anthropic": self._create_anthropic_llm,
        }
        
        self._tts_providers = {
            "elevenlabs": self._create_elevenlabs_tts,
            "cartesia": self._create_cartesia_tts,
            "openai": self._create_openai_tts,
            "deepgram": self._create_deepgram_tts,
        }
        
        self._stt_providers = {
            "elevenlabs": self._create_elevenlabs_stt,
            "deepgram": self._create_deepgram_stt,
            "openai": self._create_openai_stt,
        }
    
    def create_llm(self, config: LLMConfig) -> llm.LLM:
        """Create an LLM instance from configuration.
        
        Args:
            config: LLM configuration
            
        Returns:
            Configured LLM instance
            
        Raises:
            ComponentCreationError: If LLM creation fails
        """
        try:
            provider = config.provider.lower()
            
            if provider not in self._llm_providers:
                raise ComponentCreationError(f"Unknown LLM provider: {provider}")
            
            logger.info(f"Creating LLM: {provider} {config.model}")
            return self._llm_providers[provider](config)
            
        except Exception as e:
            raise ComponentCreationError(f"Failed to create LLM: {e}") from e
    
    def create_tts(self, config: TTSConfig) -> tts.TTS:
        """Create a TTS instance from configuration.
        
        Args:
            config: TTS configuration
            
        Returns:
            Configured TTS instance
            
        Raises:
            ComponentCreationError: If TTS creation fails
        """
        try:
            provider = config.provider.lower()
            
            if provider not in self._tts_providers:
                raise ComponentCreationError(f"Unknown TTS provider: {provider}")
            
            logger.info(f"Creating TTS: {provider} {config.voice_id or config.model}")
            return self._tts_providers[provider](config)
            
        except Exception as e:
            raise ComponentCreationError(f"Failed to create TTS: {e}") from e
    
    def create_stt(self, config: STTConfig) -> stt.STT:
        """Create an STT instance from configuration.
        
        Args:
            config: STT configuration
            
        Returns:
            Configured STT instance
            
        Raises:
            ComponentCreationError: If STT creation fails
        """
        try:
            provider = config.provider.lower()
            
            if provider not in self._stt_providers:
                raise ComponentCreationError(f"Unknown STT provider: {provider}")
            
            logger.info(f"Creating STT: {provider} {config.model or 'default'}")
            return self._stt_providers[provider](config)
            
        except Exception as e:
            raise ComponentCreationError(f"Failed to create STT: {e}") from e
    
    def create_vad(self, config: Optional[Dict[str, Any]] = None) -> vad.VAD:
        """Create a VAD (Voice Activity Detection) instance.
        
        Args:
            config: Optional VAD configuration
            
        Returns:
            Configured VAD instance
        """
        try:
            logger.info("Creating VAD: silero")
            return silero.VAD.load()
        except Exception as e:
            raise ComponentCreationError(f"Failed to create VAD: {e}") from e
    
    def create_turn_detection(self, config: Optional[Dict[str, Any]] = None):
        """Create a turn detection instance.
        
        Args:
            config: Optional turn detection configuration
            
        Returns:
            Configured turn detection instance
        """
        try:
            logger.info("Creating turn detection: multilingual")
            return MultilingualModel()
        except Exception as e:
            raise ComponentCreationError(f"Failed to create turn detection: {e}") from e
    
    # LLM provider implementations
    def _create_openai_llm(self, config: LLMConfig) -> llm.LLM:
        """Create OpenAI LLM instance."""
        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
        }
        
        if config.max_tokens:
            kwargs["max_tokens"] = config.max_tokens
        
        if config.api_key:
            kwargs["api_key"] = config.api_key
        
        if config.base_url:
            kwargs["base_url"] = config.base_url
        
        # Add custom parameters
        kwargs.update(config.custom_params)
        
        return openai.LLM(**kwargs)
    
    def _create_anthropic_llm(self, config: LLMConfig) -> llm.LLM:
        """Create Anthropic LLM instance."""
        if not ANTHROPIC_AVAILABLE:
            raise ComponentCreationError("Anthropic plugin not available")
        
        kwargs = {
            "model": config.model,
            "temperature": config.temperature,
        }
        
        if config.max_tokens:
            kwargs["max_tokens"] = config.max_tokens
        
        if config.api_key:
            kwargs["api_key"] = config.api_key
        
        # Add custom parameters
        kwargs.update(config.custom_params)
        
        return anthropic.LLM(**kwargs)
    
    # TTS provider implementations
    def _create_elevenlabs_tts(self, config: TTSConfig) -> tts.TTS:
        """Create ElevenLabs TTS instance."""
        if not ELEVENLABS_AVAILABLE:
            raise ComponentCreationError("ElevenLabs plugin not available")
        
        kwargs = {}
        
        if config.voice_id:
            kwargs["voice"] = config.voice_id
        
        if config.model:
            kwargs["model"] = config.model
        
        if config.api_key:
            kwargs["api_key"] = config.api_key
        
        # Add custom parameters
        kwargs.update(config.custom_params)
        
        return elevenlabs.TTS(**kwargs)
    
    def _create_cartesia_tts(self, config: TTSConfig) -> tts.TTS:
        """Create Cartesia TTS instance."""
        if not CARTESIA_AVAILABLE:
            raise ComponentCreationError("Cartesia plugin not available")
        
        kwargs = {}
        
        if config.voice_id:
            kwargs["voice"] = config.voice_id
        
        if config.model:
            kwargs["model"] = config.model
        
        if config.api_key:
            kwargs["api_key"] = config.api_key
        
        if config.language:
            kwargs["language"] = config.language
        
        # Add custom parameters
        kwargs.update(config.custom_params)
        
        return cartesia.TTS(**kwargs)
    
    def _create_openai_tts(self, config: TTSConfig) -> tts.TTS:
        """Create OpenAI TTS instance."""
        kwargs = {}
        
        if config.voice_id:
            kwargs["voice"] = config.voice_id
        
        if config.model:
            kwargs["model"] = config.model
        
        if config.api_key:
            kwargs["api_key"] = config.api_key
        
        # Add custom parameters
        kwargs.update(config.custom_params)
        
        return openai.TTS(**kwargs)
    
    def _create_deepgram_tts(self, config: TTSConfig) -> tts.TTS:
        """Create Deepgram TTS instance."""
        kwargs = {}
        
        if config.api_key:
            kwargs["api_key"] = config.api_key

        return deepgram.TTS(**kwargs)
            
    
    # STT provider implementations
    def _create_elevenlabs_stt(self, config: STTConfig) -> stt.STT:
        """Create ElevenLabs STT instance."""
        if not ELEVENLABS_AVAILABLE:
            raise ComponentCreationError("ElevenLabs plugin not available")
        
        kwargs = {}
        
        if config.language:
            kwargs["language"] = config.language
        
        if config.model:
            kwargs["model"] = config.model
        
        if config.api_key:
            kwargs["api_key"] = config.api_key
        
        # Add custom parameters
        kwargs.update(config.custom_params)
        
        return elevenlabs.STT(**kwargs)
    
    def _create_deepgram_stt(self, config: STTConfig) -> stt.STT:
        """Create Deepgram STT instance."""
        kwargs = {}
        
        if config.language:
            kwargs["language"] = config.language
        
        if config.model:
            kwargs["model"] = config.model
        
        if config.api_key:
            kwargs["api_key"] = config.api_key
        
        # Add custom parameters
        kwargs.update(config.custom_params)
        
        return deepgram.STT(**kwargs)
    
    def _create_openai_stt(self, config: STTConfig) -> stt.STT:
        """Create OpenAI STT instance."""
        kwargs = {}
        
        if config.language:
            kwargs["language"] = config.language
        
        if config.model:
            kwargs["model"] = config.model
        
        if config.api_key:
            kwargs["api_key"] = config.api_key
        
        # Add custom parameters
        kwargs.update(config.custom_params)
        
        return openai.STT(**kwargs)
    
    def get_supported_providers(self) -> Dict[str, list]:
        """Get list of supported providers for each component type.
        
        Returns:
            Dictionary mapping component types to supported providers
        """
        return {
            "llm": list(self._llm_providers.keys()),
            "tts": list(self._tts_providers.keys()),
            "stt": list(self._stt_providers.keys()),
        }
    
    def validate_provider_availability(self) -> Dict[str, Dict[str, bool]]:
        """Check which providers are actually available.
        
        Returns:
            Dictionary mapping component types to provider availability
        """
        return {
            "llm": {
                "openai": True,  # Always available with base livekit-agents
                "anthropic": ANTHROPIC_AVAILABLE,
            },
            "tts": {
                "elevenlabs": ELEVENLABS_AVAILABLE,
                "cartesia": CARTESIA_AVAILABLE,
                "openai": True,
            },
            "stt": {
                "elevenlabs": ELEVENLABS_AVAILABLE,
                "deepgram": True,  # Available with base install
                "openai": True,
            },
        } 