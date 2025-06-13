#!/usr/bin/env python3
"""
Configuration validation script.

This script validates all configuration files in the configs directory
and reports any issues found.
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from universalagent.core.config_loader import HybridConfigurationLoader, ConfigurationLoader


def validate_environment_configs(environment: str) -> bool:
    """Validate all configurations in a specific environment.
    
    Args:
        environment: Environment name to validate
        
    Returns:
        True if all configurations are valid, False otherwise
    """
    print(f"\n🔍 Validating configurations for environment: {environment}")
    
    loader = HybridConfigurationLoader()
    results = loader.validate_all_configs(environment)
    
    all_valid = True
    total_configs = len(results)
    valid_configs = 0
    
    for config_name, issues in results.items():
        if not issues:
            print(f"✅ {config_name}: VALID")
            valid_configs += 1
        else:
            print(f"❌ {config_name}: INVALID")
            for issue in issues:
                print(f"   - {issue}")
            all_valid = False
    
    print(f"\n📊 Summary: {valid_configs}/{total_configs} configurations are valid")
    return all_valid


def validate_specific_config(file_path: str) -> bool:
    """Validate a specific configuration file.
    
    Args:
        file_path: Path to the configuration file
        
    Returns:
        True if valid, False otherwise
    """
    print(f"\n🔍 Validating configuration file: {file_path}")
    
    loader = ConfigurationLoader()
    issues = loader.validate_config_file(file_path)
    
    if not issues:
        print("✅ Configuration is VALID")
        return True
    else:
        print("❌ Configuration is INVALID")
        for issue in issues:
            print(f"   - {issue}")
        return False


def validate_templates() -> bool:
    """Validate all template configurations.
    
    Returns:
        True if all templates are valid, False otherwise
    """
    print(f"\n🔍 Validating configuration templates")
    
    templates_dir = Path("configs/templates")
    if not templates_dir.exists():
        print("❌ Templates directory not found")
        return False
    
    template_files = list(templates_dir.glob("*.json"))
    
    if not template_files:
        print("⚠️  No template files found")
        return True
    
    loader = ConfigurationLoader()
    all_valid = True
    valid_count = 0
    
    for template_file in template_files:
        issues = loader.validate_config_file(str(template_file))
        
        if not issues:
            print(f"✅ {template_file.name}: VALID")
            valid_count += 1
        else:
            print(f"❌ {template_file.name}: INVALID")
            for issue in issues:
                print(f"   - {issue}")
            all_valid = False
    
    print(f"\n📊 Template Summary: {valid_count}/{len(template_files)} templates are valid")
    return all_valid


def list_available_configs():
    """List all available configurations."""
    print("\n📋 Available Configurations:")
    
    loader = ConfigurationLoader()
    
    # List by environment
    environments = ["development", "staging", "production"]
    
    for env in environments:
        configs = loader.list_available_configs(env)
        if configs:
            print(f"\n{env.upper()}:")
            for config in configs:
                print(f"  - {config}")
        else:
            print(f"\n{env.upper()}: No configurations found")
    
    # List templates
    templates_dir = Path("configs/templates")
    if templates_dir.exists():
        template_files = [f.stem for f in templates_dir.glob("*.json")]
        if template_files:
            print(f"\nTEMPLATES:")
            for template in template_files:
                print(f"  - {template}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Validate LiveKit configurable agent configurations"
    )
    
    parser.add_argument(
        "--environment", "-e",
        help="Validate specific environment (development, staging, production)"
    )
    
    parser.add_argument(
        "--file", "-f",
        help="Validate specific configuration file"
    )
    
    parser.add_argument(
        "--templates", "-t",
        action="store_true",
        help="Validate template configurations"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available configurations"
    )
    
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Validate all environments and templates"
    )
    
    args = parser.parse_args()
    
    print("🚀 LiveKit Configurable Agents - Configuration Validator")
    print("=" * 60)
    
    success = True
    
    if args.list:
        list_available_configs()
        return
    
    if args.file:
        success = validate_specific_config(args.file)
    
    elif args.templates:
        success = validate_templates()
    
    elif args.environment:
        success = validate_environment_configs(args.environment)
    
    elif args.all:
        # Validate all environments
        environments = ["development", "staging", "production"]
        for env in environments:
            env_success = validate_environment_configs(env)
            success = success and env_success
        
        # Validate templates
        template_success = validate_templates()
        success = success and template_success
    
    else:
        # Default: validate development environment
        success = validate_environment_configs("development")
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All validations passed!")
        sys.exit(0)
    else:
        print("💥 Some validations failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 