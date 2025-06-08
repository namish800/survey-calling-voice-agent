"""
Configurable agent implementation for LiveKit.

This module provides the ConfigurableAgent class that creates LiveKit agents
from our configuration objects, integrating with the LiveKit AgentSession.
"""

import logging
from typing import Optional, Dict, Any

from livekit.agents import Agent
from livekit.agents import llm

from universalagent.core.config import AgentConfig
from universalagent.core.instruction_template import generate_system_instructions
from universalagent.components.factory import ComponentFactory, ComponentCreationError

logger = logging.getLogger(__name__)


#TODO prepare instructions for agent
#TODO add tools
class ConfigurableAgent(Agent):
    """A configurable LiveKit agent that loads behavior from configuration."""
    
    def __init__(self, config: AgentConfig, additional_context: Optional[Dict[str, Any]] = None):
        """Initialize the configurable agent.
        
        Args:
            config: Agent configuration object
            additional_context: Optional additional context (e.g., available tools)
        """
        self.config = config
        self.additional_context = additional_context or {}
        self.factory = ComponentFactory()
        
        # Generate comprehensive system instructions using the template
        instructions = generate_system_instructions(config, self.additional_context)
        
        # Initialize the base Agent with generated instructions
        super().__init__(instructions=instructions)
        
        logger.info(f"Initialized ConfigurableAgent: {config.name}")
        logger.info(f"Agent ID: {config.agent_id}")
        logger.info(f"Agent Type: {config.agent_type}")
        logger.info(f"Generated instructions: {len(instructions)} characters")
    
    async def on_enter(self) -> None:
        """Handle initial greeting for the agent."""
        # Get first message or greeting instructions
        first_message = self.get_first_message()
        greeting_instructions = self.get_greeting_instructions()
        
        if first_message:
            logger.info(f"Generating first message: {first_message}")
            await self.session.generate_reply(instructions=f"Say: {first_message}")
        elif greeting_instructions:
            logger.info(f"Generating greeting with instructions: {greeting_instructions}")
            await self.session.generate_reply(instructions=greeting_instructions)
        else:
            # Default greeting
            logger.info("Generating default greeting")
            await self.session.generate_reply(
                instructions="Greet the user warmly and offer your assistance."
            )

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"ConfigurableAgent(id={self.config.agent_id}, name={self.config.agent_name}, type={self.config.agent_type})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return (f"ConfigurableAgent(id='{self.config.agent_id}', name='{self.config.agent_name}', "
                f"type='{self.config.agent_type}', description='{self.config.description}')") 