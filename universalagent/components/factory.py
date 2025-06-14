"""
Component factory for creating LiveKit components from configuration.

This module provides the ComponentFactory class that creates actual LiveKit
components (LLM, TTS, STT, VAD, etc.) from our configuration objects.
"""

import logging
import os
from typing import Optional, Dict, Any

from livekit.agents import llm, stt, tts, vad, tokenize
from livekit.plugins import openai, deepgram, silero, sarvam
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import elevenlabs
from livekit.plugins import cartesia
from livekit.plugins import sarvam

from universalagent.core.config import LLMConfig, TTSConfig, STTConfig

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
        }
        
        self._tts_providers = {
            "elevenlabs": self._create_elevenlabs_tts,
            "cartesia": self._create_cartesia_tts,
            "openai": self._create_openai_tts,
            "deepgram": self._create_deepgram_tts,
            "sarvam": self._create_sarvam_tts,
        }
        
        self._stt_providers = {
            "elevenlabs": self._create_elevenlabs_stt,
            "deepgram": self._create_deepgram_stt,
            "openai": self._create_openai_stt,
            "sarvam": self._create_sarvam_stt,
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
            kwargs["max_completion_tokens"] = config.max_tokens
        
        if config.api_key:
            kwargs["api_key"] = config.api_key
        
        if config.base_url:
            kwargs["base_url"] = config.base_url
        
        # Add custom parameters
        kwargs.update(config.custom_params)
        
        return openai.LLM(**kwargs)
    
    # TTS provider implementations
    def _create_elevenlabs_tts(self, config: TTSConfig) -> tts.TTS:
        """Create ElevenLabs TTS instance."""
        
        kwargs = {}
        
        if config.voice_id:
            kwargs["voice_id"] = config.voice_id
        
        if config.model:
            kwargs["model"] = config.model
        
        if config.api_key:
            kwargs["api_key"] = config.api_key
        
        # Add custom parameters
        kwargs.update(config.custom_params)
        
        return elevenlabs.TTS(**kwargs)
    
    def _create_cartesia_tts(self, config: TTSConfig) -> tts.TTS:
        """Create Cartesia TTS instance."""
        
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

        if config.model:
            kwargs["model"] = config.model
            
        kwargs.update(config.custom_params)
        return deepgram.TTS(**kwargs)
    
    def _create_sarvam_tts(self, config: TTSConfig) -> tts.TTS:
        """Create Sarvam TTS instance."""
        kwargs = {}
        
        kwargs["api_key"] = config.api_key or os.getenv("SARVAM_API_KEY")
            
        if config.language:
            kwargs["target_language_code"] = config.language

        if config.model:
            kwargs["model"] = config.model
        
        if config.voice_id:
            kwargs["speaker"] = config.voice_id
        
        kwargs.update(config.custom_params)
        
        return sarvam.TTS(**kwargs)
    
    def _create_sarvam_stt(self, config: STTConfig) -> stt.STT:
        """Create Sarvam STT instance."""
        kwargs = {}
        
        kwargs["api_key"] = config.api_key or os.getenv("SARVAM_API_KEY")
        
        if config.language:
            kwargs["language"] = config.language
        
        if config.model:
            kwargs["model"] = config.model
        
        kwargs.update(config.custom_params)
        
        return sarvam.STT(**kwargs)
    
    # STT provider implementations
    def _create_elevenlabs_stt(self, config: STTConfig) -> stt.STT:
        """Create ElevenLabs STT instance."""
        
        kwargs = {}
        
        if config.language:
            kwargs["language_code"] = config.language

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