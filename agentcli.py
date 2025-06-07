#!/usr/bin/env python3
"""
Sample configurable agent runner.

This script demonstrates how to run configurable LiveKit agents using
our configuration system. It can be used to run any configured agent.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.entrypoint import run_configurable_agent, run_universal_agent
from src.core.config_loader import load_config_by_id, list_available_configs
from src.core.config import AgentConfig


def setup_logging(level: str = "INFO"):
    """Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )


def list_agents():
    """List all available agent configurations."""
    print("\n📋 Available Agent Configurations:")
    print("=" * 50)
    
    environments = ["development", "staging", "production"]
    
    for env in environments:
        try:
            configs = list_available_configs(env)
            if configs:
                print(f"\n{env.upper()}:")
                for config_name in configs:
                    # Try to load config to show details
                    try:
                        config = load_config_by_id(config_name, env)
                        if config:
                            print(f"  - {config_name:15} | {config.name} ({config.agent_type})")
                        else:
                            print(f"  - {config_name:15} | Failed to load")
                    except Exception as e:
                        print(f"  - {config_name:15} | Error: {e}")
        except Exception as e:
            print(f"\n{env.upper()}: Error listing configs - {e}")
    
    # List templates
    print(f"\nTEMPLATES:")
    templates_dir = Path("configs/templates")
    if templates_dir.exists():
        for template_file in templates_dir.glob("*.json"):
            template_name = template_file.stem
            try:
                config = load_config_by_id(template_name, "templates")
                if config:
                    print(f"  - {template_name:15} | {config.name} ({config.agent_type})")
            except:
                print(f"  - {template_name:15} | Template")


def validate_agent_config(agent_id: str, environment: str = "development") -> bool:
    """Validate an agent configuration.
    
    Args:
        agent_id: Agent ID to validate
        environment: Environment to load from
        
    Returns:
        True if valid, False otherwise
    """
    try:
        config = load_config_by_id(agent_id, environment)
        if not config:
            print(f"❌ Failed to load configuration for agent: {agent_id}")
            return False
        
        print(f"✅ Configuration loaded: {config.name}")
        print(f"   Agent ID: {config.agent_id}")
        print(f"   Agent Type: {config.agent_type}")
        print(f"   Description: {config.description}")
        
        # Validate configuration
        issues = config.validate()
        if issues:
            print(f"⚠️  Configuration issues:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print(f"✅ Configuration is valid")
            return True
            
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Run configurable LiveKit agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run survey agent
  python agent.py --agent survey_agent

  # Run with specific environment
  python agent.py --agent survey_agent --env production

  # Run universal agent (loads config from job metadata)
  python agent.py --universal

  # List available agents
  python agent.py --list

  # Validate agent configuration
  python agent.py --validate survey_agent

  # Run with debug logging
  python agent.py --agent survey_agent --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "--agent", "-a",
        help="Agent ID to run (e.g., survey_agent, sales_agent)"
    )
    
    parser.add_argument(
        "--env", "-e",
        default="development",
        help="Environment to load configuration from (default: development)"
    )
    
    parser.add_argument(
        "--universal", "-u",
        action="store_true",
        help="Run universal agent (loads config from job metadata)"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available agent configurations"
    )
    
    parser.add_argument(
        "--validate", "-v",
        help="Validate agent configuration without running"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    print("🚀 LiveKit Configurable Agent Runner")
    print("=" * 60)
    
    # Handle list command
    if args.list:
        list_agents()
        return
    
    # Handle validate command
    if args.validate:
        is_valid = validate_agent_config(args.validate, args.env)
        sys.exit(0 if is_valid else 1)
    
    # Handle universal agent
    if args.universal:
        print("🌐 Starting universal configurable agent...")
        print("Agent will load configuration from job metadata")
        run_universal_agent()
        return
    
    # Handle specific agent
    if args.agent:
        print(f"🤖 Starting configurable agent: {args.agent}")
        print(f"Environment: {args.env}")
        
        # Validate configuration first
        if not validate_agent_config(args.agent, args.env):
            print(f"❌ Configuration validation failed for {args.agent}")
            sys.exit(1)
        
        print(f"🚀 Starting agent session...")
        run_configurable_agent(args.agent)
        return
    
    # No specific command provided
    print("❌ Please specify an agent to run or use --list to see available agents")
    print("Use --help for more information")
    sys.exit(1)


if __name__ == "__main__":
    main() 