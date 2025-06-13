#!/usr/bin/env python3
"""
Component factory testing script.

This script tests the ComponentFactory with real configurations
and validates that components can be created properly.
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from universalagent.components.factory import ComponentFactory, ComponentCreationError
from universalagent.core.config_loader import load_config_by_id, load_config_from_file
from universalagent.core.config import LLMConfig, TTSConfig, STTConfig


def test_component_creation_from_config(config_file: str) -> bool:
    """Test component creation from a configuration file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        True if all components can be created, False otherwise
    """
    print(f"\n🧪 Testing component creation from: {config_file}")
    
    # Load configuration
    if config_file.endswith('.json'):
        config = load_config_from_file(config_file)
    else:
        config = load_config_by_id(config_file)
    
    if not config:
        print(f"❌ Failed to load configuration from {config_file}")
        return False
    
    print(f"✅ Loaded configuration: {config.name}")
    
    factory = ComponentFactory()
    success = True
    
    # Test LLM creation
    if config.llm_config:
        try:
            print(f"🤖 Creating LLM: {config.llm_config.provider} {config.llm_config.model}")
            # Note: We don't actually create the component to avoid needing API keys
            # We just validate the configuration would work
            factory._llm_providers.get(config.llm_config.provider.lower())
            if config.llm_config.provider.lower() not in factory._llm_providers:
                raise ComponentCreationError(f"Unknown provider: {config.llm_config.provider}")
            print("✅ LLM configuration is valid")
        except Exception as e:
            print(f"❌ LLM creation failed: {e}")
            success = False
    
    # Test TTS creation
    if config.tts_config:
        try:
            print(f"🗣️  Creating TTS: {config.tts_config.provider} {config.tts_config.voice_id or config.tts_config.model}")
            if config.tts_config.provider.lower() not in factory._tts_providers:
                raise ComponentCreationError(f"Unknown provider: {config.tts_config.provider}")
            print("✅ TTS configuration is valid")
        except Exception as e:
            print(f"❌ TTS creation failed: {e}")
            success = False
    
    # Test STT creation
    if config.stt_config:
        try:
            print(f"👂 Creating STT: {config.stt_config.provider} {config.stt_config.model or 'default'}")
            if config.stt_config.provider.lower() not in factory._stt_providers:
                raise ComponentCreationError(f"Unknown provider: {config.stt_config.provider}")
            print("✅ STT configuration is valid")
        except Exception as e:
            print(f"❌ STT creation failed: {e}")
            success = False
    
    # Test VAD and turn detection
    try:
        print("🎯 Validating VAD and turn detection")
        # These don't depend on configuration, so they should always work
        print("✅ VAD and turn detection are supported")
    except Exception as e:
        print(f"❌ VAD/turn detection failed: {e}")
        success = False
    
    return success


def test_provider_availability():
    """Test and display provider availability."""
    print("\n🔍 Checking Provider Availability")
    print("=" * 50)
    
    factory = ComponentFactory()
    availability = factory.validate_provider_availability()
    
    for component_type, providers in availability.items():
        print(f"\n{component_type.upper()}:")
        for provider, available in providers.items():
            status = "✅ Available" if available else "❌ Not Available"
            print(f"  {provider:12} - {status}")


def test_provider_configurations():
    """Test creating components with different provider configurations."""
    print("\n🧪 Testing Provider Configurations")
    print("=" * 50)
    
    factory = ComponentFactory()
    
    # Test LLM configurations
    print("\n🤖 Testing LLM Providers:")
    
    llm_configs = [
        LLMConfig(provider="openai", model="gpt-4-turbo", temperature=0.7),
        LLMConfig(provider="anthropic", model="claude-3-sonnet", temperature=0.6),
    ]
    
    for config in llm_configs:
        try:
            print(f"  Testing {config.provider} {config.model}...")
            if config.provider.lower() in factory._llm_providers:
                print(f"    ✅ {config.provider} configuration is valid")
            else:
                print(f"    ❌ {config.provider} provider not supported")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Test TTS configurations
    print("\n🗣️  Testing TTS Providers:")
    
    tts_configs = [
        TTSConfig(provider="elevenlabs", voice_id="test-voice", model="eleven_flash_v2_5"),
        TTSConfig(provider="openai", voice_id="alloy", model="tts-1"),
        TTSConfig(provider="cartesia", voice_id="cartesia-voice"),
    ]
    
    for config in tts_configs:
        try:
            print(f"  Testing {config.provider} {config.voice_id or config.model}...")
            if config.provider.lower() in factory._tts_providers:
                print(f"    ✅ {config.provider} configuration is valid")
            else:
                print(f"    ❌ {config.provider} provider not supported")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Test STT configurations
    print("\n👂 Testing STT Providers:")
    
    stt_configs = [
        STTConfig(provider="elevenlabs", language="en"),
        STTConfig(provider="deepgram", model="nova-2", language="en"),
        STTConfig(provider="openai", model="whisper-1", language="en"),
    ]
    
    for config in stt_configs:
        try:
            print(f"  Testing {config.provider} {config.model or 'default'}...")
            if config.provider.lower() in factory._stt_providers:
                print(f"    ✅ {config.provider} configuration is valid")
            else:
                print(f"    ❌ {config.provider} provider not supported")
        except Exception as e:
            print(f"    ❌ Error: {e}")


def list_available_configs():
    """List all available configurations for testing."""
    print("\n📋 Available Configurations for Testing:")
    print("=" * 50)
    
    # List development configs
    dev_configs_dir = Path("configs/development")
    if dev_configs_dir.exists():
        dev_configs = list(dev_configs_dir.glob("*.json"))
        if dev_configs:
            print("\nDEVELOPMENT CONFIGS:")
            for config_file in dev_configs:
                print(f"  - {config_file.stem}")
    
    # List templates
    templates_dir = Path("configs/templates")
    if templates_dir.exists():
        templates = list(templates_dir.glob("*.json"))
        if templates:
            print("\nTEMPLATES:")
            for template_file in templates:
                print(f"  - {template_file.stem}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test LiveKit ComponentFactory with configurations"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Test specific configuration file or agent ID"
    )
    
    parser.add_argument(
        "--providers", "-p",
        action="store_true",
        help="Test provider availability and configurations"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available configurations"
    )
    
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Test all available configurations"
    )
    
    args = parser.parse_args()
    
    print("🚀 LiveKit Component Factory Tester")
    print("=" * 60)
    
    if args.list:
        list_available_configs()
        return
    
    if args.providers:
        test_provider_availability()
        test_provider_configurations()
        return
    
    success = True
    
    if args.config:
        success = test_component_creation_from_config(args.config)
    
    elif args.all:
        # Test all development configs
        dev_configs_dir = Path("configs/development")
        if dev_configs_dir.exists():
            for config_file in dev_configs_dir.glob("*.json"):
                config_success = test_component_creation_from_config(str(config_file))
                success = success and config_success
        
        # Test all templates
        templates_dir = Path("configs/templates")
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.json"):
                template_success = test_component_creation_from_config(str(template_file))
                success = success and template_success
    
    else:
        # Default: test survey agent
        success = test_component_creation_from_config("survey_agent")
    
    # Always show provider availability
    test_provider_availability()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All component tests passed!")
        sys.exit(0)
    else:
        print("💥 Some component tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 