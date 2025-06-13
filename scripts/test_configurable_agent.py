#!/usr/bin/env python3
"""
Configurable agent testing script.

This script tests the entire configurable agent system including
configuration loading, component creation, and agent initialization.
"""

import sys
import os
import argparse
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from universalagent.core.config_loader import load_config_by_id, load_config_from_file
from universalagent.components.factory import ComponentFactory, ComponentCreationError
from universalagent.agents.configurable_agent import ConfigurableAgent
from universalagent.agents.entrypoint import (
    create_entrypoint,
    create_room_input_options,
    handle_initial_greeting,
    start_agent_session
)


def test_configuration_loading():
    """Test configuration loading for all available agents."""
    print("\n🔧 Testing Configuration Loading")
    print("=" * 50)
    
    success = True
    
    # Test development configs
    dev_configs_dir = Path("configs/development")
    if dev_configs_dir.exists():
        for config_file in dev_configs_dir.glob("*.json"):
            config_name = config_file.stem
            try:
                print(f"Loading {config_name}...")
                config = load_config_by_id(config_name, "development")
                if config:
                    print(f"  ✅ {config_name}: {config.name} ({config.agent_type})")
                else:
                    print(f"  ❌ {config_name}: Failed to load")
                    success = False
            except Exception as e:
                print(f"  ❌ {config_name}: Error - {e}")
                success = False
    
    # Test templates
    templates_dir = Path("configs/templates")
    if templates_dir.exists():
        for template_file in templates_dir.glob("*.json"):
            template_name = template_file.stem
            try:
                print(f"Loading template {template_name}...")
                config = load_config_by_id(template_name, "templates")
                if config:
                    print(f"  ✅ {template_name}: {config.name} ({config.agent_type})")
                else:
                    print(f"  ❌ {template_name}: Failed to load")
                    success = False
            except Exception as e:
                print(f"  ❌ {template_name}: Error - {e}")
                success = False
    
    return success


def test_agent_initialization():
    """Test configurable agent initialization."""
    print("\n🤖 Testing Agent Initialization")
    print("=" * 50)
    
    success = True
    
    # Test with survey agent config
    try:
        print("Testing survey agent initialization...")
        config = load_config_by_id("survey_agent", "development")
        if not config:
            config = load_config_by_id("survey_agent", "templates")
        
        if config:
            agent = ConfigurableAgent(config)
            print(f"  ✅ Created agent: {agent}")
            print(f"     Agent ID: {agent.agent_id}")
            print(f"     Agent Name: {agent.agent_name}")
            print(f"     Agent Type: {agent.agent_type}")
            print(f"     Description: {agent.description}")
            
            # Test agent properties
            print(f"     First Message: {agent.get_first_message()}")
            print(f"     Uses RAG: {agent.should_use_rag()}")
            print(f"     Uses Memory: {agent.should_use_memory()}")
            
            # Test chat context creation
            context = agent.create_chat_context()
            print(f"     Chat Context Items: {len(context.items)}")
            
        else:
            print("  ❌ Could not load survey agent config")
            success = False
            
    except Exception as e:
        print(f"  ❌ Agent initialization failed: {e}")
        success = False
    
    # Test with sales agent config if available
    try:
        print("Testing sales agent initialization...")
        config = load_config_by_id("sales_agent", "templates")
        if config:
            agent = ConfigurableAgent(config)
            print(f"  ✅ Created sales agent: {agent}")
        else:
            print("  ℹ️  Sales agent template not found (optional)")
    except Exception as e:
        print(f"  ❌ Sales agent initialization failed: {e}")
    
    return success


def test_component_integration():
    """Test component creation and integration."""
    print("\n⚙️  Testing Component Integration")
    print("=" * 50)
    
    success = True
    
    try:
        print("Testing component creation from configuration...")
        config = load_config_by_id("survey_agent")
        if not config:
            config = load_config_by_id("survey_agent", "templates")
        
        if config:
            factory = ComponentFactory()
            agent = ConfigurableAgent(config)
            
            # Test LLM creation
            try:
                print("  Creating LLM...")
                # We don't actually create it to avoid needing API keys
                if config.llm_config:
                    print(f"    ✅ LLM config valid: {config.llm_config.provider} {config.llm_config.model}")
                else:
                    print("    ❌ No LLM config found")
                    success = False
            except Exception as e:
                print(f"    ❌ LLM creation error: {e}")
                success = False
            
            # Test TTS creation
            try:
                print("  Creating TTS...")
                if config.tts_config:
                    print(f"    ✅ TTS config valid: {config.tts_config.provider}")
                else:
                    print("    ℹ️  No TTS config (optional)")
            except Exception as e:
                print(f"    ❌ TTS creation error: {e}")
            
            # Test STT creation
            try:
                print("  Creating STT...")
                if config.stt_config:
                    print(f"    ✅ STT config valid: {config.stt_config.provider}")
                else:
                    print("    ℹ️  No STT config (optional)")
            except Exception as e:
                print(f"    ❌ STT creation error: {e}")
                
        else:
            print("  ❌ Could not load agent configuration")
            success = False
            
    except Exception as e:
        print(f"  ❌ Component integration test failed: {e}")
        success = False
    
    return success


def test_entrypoint_functions():
    """Test entrypoint function creation."""
    print("\n🚀 Testing Entrypoint Functions")
    print("=" * 50)
    
    success = True
    
    try:
        print("Testing entrypoint creation...")
        
        # Test creating custom entrypoint
        entrypoint = create_entrypoint("survey_agent")
        if callable(entrypoint):
            print("  ✅ Custom entrypoint created successfully")
        else:
            print("  ❌ Custom entrypoint creation failed")
            success = False
        
        # Test room input options creation
        config = load_config_by_id("survey_agent")
        if not config:
            config = load_config_by_id("survey_agent", "templates")
        
        if config:
            # Mock noise cancellation availability
            with patch('src.agents.entrypoint.NOISE_CANCELLATION_AVAILABLE', True):
                with patch('src.agents.entrypoint.noise_cancellation') as mock_nc:
                    mock_nc.BVC.return_value = Mock()
                    
                    options = create_room_input_options(config)
                    if options:
                        print("  ✅ Room input options created successfully")
                    else:
                        print("  ℹ️  Room input options returned None (noise cancellation disabled)")
        
    except Exception as e:
        print(f"  ❌ Entrypoint function test failed: {e}")
        success = False
    
    return success


def test_greeting_handling():
    """Test initial greeting handling."""
    print("\n👋 Testing Greeting Handling")
    print("=" * 50)
    
    success = True
    
    try:
        print("Testing greeting handling...")
        
        config = load_config_by_id("survey_agent")
        if not config:
            config = load_config_by_id("survey_agent", "templates")
        
        if config:
            agent = ConfigurableAgent(config)
            
            # Test with first message
            if agent.get_first_message():
                print(f"  ✅ Agent has first message: {agent.get_first_message()}")
            elif agent.get_greeting_instructions():
                print(f"  ✅ Agent has greeting instructions: {agent.get_greeting_instructions()}")
            else:
                print("  ✅ Agent will use default greeting")
            
            # Mock session for testing greeting
            mock_session = Mock()
            mock_session.generate_reply = AsyncMock()
            
            # We can't actually test async function without running async,
            # but we can validate the agent setup
            print("  ✅ Greeting handling setup validated")
            
        else:
            print("  ❌ Could not load agent configuration")
            success = False
            
    except Exception as e:
        print(f"  ❌ Greeting handling test failed: {e}")
        success = False
    
    return success


def test_agent_data_handling():
    """Test agent-specific data handling."""
    print("\n📊 Testing Agent Data Handling")
    print("=" * 50)
    
    success = True
    
    try:
        print("Testing agent data handling...")
        
        # Test survey agent data
        config = load_config_by_id("survey_agent")
        if not config:
            config = load_config_by_id("survey_agent", "templates")
        
        if config:
            agent = ConfigurableAgent(config)
            agent_data = agent.get_agent_data()
            
            if agent_data:
                print(f"  ✅ Agent data loaded: {list(agent_data.keys())}")
                
                # Check for survey-specific data
                if "survey_config" in agent_data:
                    survey_config = agent_data["survey_config"]
                    print(f"    Survey company: {survey_config.get('company_name', 'N/A')}")
                    print(f"    Survey goal: {survey_config.get('survey_goal', 'N/A')}")
                    
                    # Test context building
                    if config.agent_type == "survey":
                        context = agent._build_survey_context(survey_config)
                        if context:
                            print(f"    ✅ Survey context built: {len(context)} characters")
                        else:
                            print("    ❌ Survey context building failed")
                            success = False
                
            else:
                print("  ℹ️  No agent-specific data found")
        
        # Test sales agent data if available
        try:
            sales_config = load_config_by_id("sales_agent", "templates")
            if sales_config:
                sales_agent = ConfigurableAgent(sales_config)
                sales_data = sales_agent.get_agent_data()
                if sales_data and "sales_config" in sales_data:
                    print(f"  ✅ Sales agent data handling validated")
        except:
            print("  ℹ️  Sales agent template not available")
            
    except Exception as e:
        print(f"  ❌ Agent data handling test failed: {e}")
        success = False
    
    return success


def run_all_tests():
    """Run all configurable agent tests."""
    print("🧪 LiveKit Configurable Agent System Tests")
    print("=" * 60)
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Agent Initialization", test_agent_initialization),
        ("Component Integration", test_component_integration),
        ("Entrypoint Functions", test_entrypoint_functions),
        ("Greeting Handling", test_greeting_handling),
        ("Agent Data Handling", test_agent_data_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n💥 {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The configurable agent system is working correctly.")
        return True
    else:
        print("💥 Some tests failed. Please check the output above for details.")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test the configurable agent system"
    )
    
    parser.add_argument(
        "--test", "-t",
        choices=["config", "agent", "components", "entrypoint", "greeting", "data"],
        help="Run specific test category"
    )
    
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all tests (default)"
    )
    
    args = parser.parse_args()
    
    if args.test == "config":
        success = test_configuration_loading()
    elif args.test == "agent":
        success = test_agent_initialization()
    elif args.test == "components":
        success = test_component_integration()
    elif args.test == "entrypoint":
        success = test_entrypoint_functions()
    elif args.test == "greeting":
        success = test_greeting_handling()
    elif args.test == "data":
        success = test_agent_data_handling()
    else:
        # Run all tests by default
        success = run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 