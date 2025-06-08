"""
Simple Jinja-based instruction template system for LiveKit Configurable Agents.

This module provides a clean, template-driven approach for generating voice agent
system instructions following the ElevenLabs six building blocks methodology.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import jinja2

from universalagent.core.config import AgentConfig

logger = logging.getLogger(__name__)


class InstructionTemplate:
    """Simple Jinja-based instruction template generator."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """Initialize the instruction template.
        
        Args:
            template_dir: Optional custom template directory path
        """
        # Default to templates directory in core module
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        
        # Set up Jinja environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        logger.info(f"Initialized InstructionTemplate with template directory: {template_dir}")
    
    def generate_instructions(self, config: AgentConfig, 
                            additional_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate system instructions from agent configuration using Jinja template.
        
        Args:
            config: Agent configuration object
            additional_context: Optional additional context (e.g., tools)
            
        Returns:
            Generated system instructions string
        """
        try:
            # Load the base template
            template = self.env.get_template("base_instruction_template.jinja2")
            
            # Prepare template context
            context = self._prepare_template_context(config, additional_context)
            
            # Render the template
            instructions = template.render(**context)
            
            logger.info(f"Generated instructions for {config.name} ({len(instructions)} characters)")
            return instructions.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate instructions: {e}")
            # Fallback to basic instructions
            return self._generate_fallback_instructions(config)
    
    def _prepare_template_context(self, config: AgentConfig, 
                                additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare the context dictionary for template rendering.
        
        Args:
            config: Agent configuration
            additional_context: Optional additional context
            
        Returns:
            Context dictionary for template rendering
        """
        context = {
            # Basic agent information
            "user_instructions": config.system_instructions,
            "guardrails": config.guardrails,
            "context": config.initial_context,
            "tools": additional_context.get("available_tools", []) if additional_context else [],
        }
        
        # Add any additional context items
        if additional_context:
            for key, value in additional_context.items():
                if key not in context:  # Don't override existing keys
                    context[key] = value
        
        return context
    
    def _format_personality_traits(self, traits: Optional[Dict[str, Any]]) -> List[str]:
        """Format personality traits for template rendering.
        
        Args:
            traits: Personality traits dictionary
            
        Returns:
            List of formatted trait strings
        """
        if not traits:
            return []
        
        formatted_traits = []
        for trait, value in traits.items():
            if isinstance(value, bool) and value:
                formatted_traits.append(trait)
            elif isinstance(value, str) and value:
                formatted_traits.append(f"{trait} ({value})")
            elif value:  # Any other truthy value
                formatted_traits.append(str(trait))
        
        return formatted_traits
    
    def _generate_fallback_instructions(self, config: AgentConfig) -> str:
        """Generate basic fallback instructions if template rendering fails.
        
        Args:
            config: Agent configuration
            
        Returns:
            Basic instruction string
        """
        fallback = f"""You are {config.name or 'an AI assistant'}.

{config.system_instructions or 'Provide helpful, accurate assistance through natural conversation.'}

Use a natural, conversational tone with brief affirmations and clear speech patterns.
Adapt your communication style to the user's needs and maintain a professional demeanor.
If you encounter limitations, acknowledge them transparently and suggest alternatives."""

        logger.warning("Using fallback instructions due to template rendering failure")
        return fallback


def generate_system_instructions(config: AgentConfig, 
                               additional_context: Optional[Dict[str, Any]] = None,
                               template_dir: Optional[str] = None, 
                               runtime_metada: Optional[Dict[str, Any]] = None) -> str:
    """Generate system instructions for an agent configuration.
    
    Args:
        config: Agent configuration object
        additional_context: Optional additional context (tools, etc.)
        template_dir: Optional custom template directory
        
    Returns:
        Generated system instructions string
    """
    template = InstructionTemplate(template_dir)
    instructions = template.generate_instructions(config, additional_context)
    if runtime_metada:
        return render_instructions_with_data(instructions, runtime_metada)
    return instructions

#TODO: add this to the agent class if required or delete
def render_instructions_with_data(template_string: str, agent_data: Dict[str, Any]) -> str:
    """Render instruction template string with agent data placeholders.
    
    This allows users to provide instructions with placeholders that get filled
    from the agent_data field during runtime.
    
    Args:
        template_string: Instruction template with placeholders
        agent_data: Data dictionary for placeholder replacement
        
    Returns:
        Rendered instruction string
        
    Example:
        template = "You are calling for {{ company_name }} about {{ survey_topic }}."
        agent_data = {"company_name": "Acme Corp", "survey_topic": "customer satisfaction"}
        result = render_instructions_with_data(template, agent_data)
        # Returns: "You are calling for Acme Corp about customer satisfaction."
    """
    try:
        # Create a simple Jinja environment for string templates
        env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        template = env.from_string(template_string)
        return template.render(**agent_data).strip()
        
    except Exception as e:
        logger.warning(f"Failed to render template string with agent data: {e}")
        # Return original string if rendering fails
        return template_string 