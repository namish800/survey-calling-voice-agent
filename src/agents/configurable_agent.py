"""
Configurable agent implementation for LiveKit.

This module provides the ConfigurableAgent class that creates LiveKit agents
from our configuration objects, integrating with the LiveKit AgentSession.
"""

import logging
from typing import Optional, Dict, Any

from livekit.agents import Agent
from livekit.agents import llm

from ..core.config import AgentConfig
from ..components.factory import ComponentFactory, ComponentCreationError

logger = logging.getLogger(__name__)


#TODO prepare instructions for agent
#TODO add on_enter
#TODO add tools
class ConfigurableAgent(Agent):
    """A configurable LiveKit agent that loads behavior from configuration."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the configurable agent.
        
        Args:
            config: Agent configuration object
        """
        self.config = config
        self.factory = ComponentFactory()
        
        # Initialize the base Agent with instructions
        super().__init__(instructions=config.system_instructions)
        
        logger.info(f"Initialized ConfigurableAgent: {config.name}")
        logger.info(f"Agent ID: {config.agent_id}")
        logger.info(f"Agent Type: {config.agent_type}")
    
    async def on_enter(self) -> None:
        """Handle initial greeting for the agent.
        
        Args:
            session: AgentSession instance
            agent: ConfigurableAgent instance
        """
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
    
    @property
    def agent_id(self) -> str:
        """Get the agent ID."""
        return self.config.agent_id
    
    @property
    def agent_name(self) -> str:
        """Get the agent name."""
        return self.config.name
    
    @property
    def agent_type(self) -> str:
        """Get the agent type."""
        return self.config.agent_type
    
    @property
    def description(self) -> str:
        """Get the agent description."""
        return self.config.description
    
    def get_first_message(self) -> Optional[str]:
        """Get the first message the agent should say.
        
        Returns:
            First message string or None if not configured
        """
        return self.config.first_message
    
    def get_greeting_instructions(self) -> Optional[str]:
        """Get greeting instructions for the agent.
        
        Returns:
            Greeting instructions or None if not configured
        """
        return self.config.greeting_instructions
    
    def get_personality_traits(self) -> Dict[str, Any]:
        """Get the agent's personality traits.
        
        Returns:
            Dictionary of personality traits
        """
        return self.config.personality_traits
    
    def get_conversation_style(self) -> str:
        """Get the agent's conversation style.
        
        Returns:
            Conversation style string
        """
        return self.config.conversation_style
    
    def get_agent_data(self) -> Dict[str, Any]:
        """Get agent-specific data (e.g., survey questions, sales scripts).
        
        Returns:
            Dictionary of agent-specific data
        """
        return self.config.agent_data
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata.
        
        Returns:
            Dictionary of metadata
        """
        return self.config.metadata
    
    def should_use_rag(self) -> bool:
        """Check if RAG is enabled for this agent.
        
        Returns:
            True if RAG is enabled
        """
        return self.config.rag_config is not None and self.config.rag_config.enabled
    
    def should_use_memory(self) -> bool:
        """Check if memory is enabled for this agent.
        
        Returns:
            True if memory is enabled
        """
        return self.config.memory_config is not None and self.config.memory_config.enabled
    
    def get_max_conversation_duration(self) -> Optional[int]:
        """Get maximum conversation duration in seconds.
        
        Returns:
            Max duration in seconds or None if unlimited
        """
        return self.config.max_conversation_duration
    
    def get_silence_timeout(self) -> Optional[int]:
        """Get silence timeout in seconds.
        
        Returns:
            Silence timeout in seconds or None if not configured
        """
        return self.config.silence_timeout
    
    def should_handle_interruptions(self) -> bool:
        """Check if interruption handling is enabled.
        
        Returns:
            True if interruptions should be handled
        """
        return self.config.interruption_handling
    
    def get_noise_cancellation_type(self) -> str:
        """Get the noise cancellation type.
        
        Returns:
            Noise cancellation type string
        """
        return self.config.noise_cancellation
    
    def create_chat_context(self) -> llm.ChatContext:
        """Create initial chat context for the agent.
        
        Returns:
            Configured ChatContext with system instructions
        """
        context = llm.ChatContext()
        
        # Add system instructions - use add_message method
        if self.config.system_instructions:
            context.add_message(role="system", content=self.config.system_instructions)
        
        # Add personality context if available
        if self.config.personality_traits:
            personality_text = self._build_personality_prompt()
            context.add_message(role="system", content=personality_text)
        
        # Add agent-specific context
        agent_data = self.get_agent_data()
        if agent_data:
            agent_context = self._build_agent_context_prompt(agent_data)
            if agent_context:
                context.add_message(role="system", content=agent_context)
        
        return context
    
    def _build_personality_prompt(self) -> str:
        """Build personality prompt from traits.
        
        Returns:
            Formatted personality prompt
        """
        traits = self.config.personality_traits
        style = self.config.conversation_style
        
        prompt_parts = []
        
        if style:
            prompt_parts.append(f"Your conversation style is {style}.")
        
        if traits:
            trait_descriptions = []
            for trait, value in traits.items():
                if isinstance(value, bool) and value:
                    trait_descriptions.append(trait)
                elif isinstance(value, str):
                    trait_descriptions.append(f"{trait}: {value}")
            
            if trait_descriptions:
                prompt_parts.append(f"Your personality traits: {', '.join(trait_descriptions)}.")
        
        return " ".join(prompt_parts)
    
    def _build_agent_context_prompt(self, agent_data: Dict[str, Any]) -> Optional[str]:
        """Build agent-specific context prompt.
        
        Args:
            agent_data: Agent-specific data
            
        Returns:
            Formatted context prompt or None
        """
        if not agent_data:
            return None
        
        # Handle survey agent context
        if self.config.agent_type == "survey" and "survey_config" in agent_data:
            return self._build_survey_context(agent_data["survey_config"])
        
        # Handle sales agent context
        if self.config.agent_type == "sales" and "sales_config" in agent_data:
            return self._build_sales_context(agent_data["sales_config"])
        
        # Generic context for other agent types
        return f"Agent-specific data: {agent_data}"
    
    def _build_survey_context(self, survey_config: Dict[str, Any]) -> str:
        """Build survey-specific context.
        
        Args:
            survey_config: Survey configuration data
            
        Returns:
            Formatted survey context
        """
        context_parts = []
        
        if "company_name" in survey_config:
            context_parts.append(f"You are calling on behalf of {survey_config['company_name']}.")
        
        if "survey_goal" in survey_config:
            context_parts.append(f"Survey goal: {survey_config['survey_goal']}")
        
        if "intro_text" in survey_config:
            context_parts.append(f"Introduction: {survey_config['intro_text']}")
        
        if "questions" in survey_config and survey_config["questions"]:
            questions_text = "Survey questions: " + "; ".join([
                q.get("text", "") for q in survey_config["questions"] if q.get("text")
            ])
            context_parts.append(questions_text)
        
        return " ".join(context_parts)
    
    def _build_sales_context(self, sales_config: Dict[str, Any]) -> str:
        """Build sales-specific context.
        
        Args:
            sales_config: Sales configuration data
            
        Returns:
            Formatted sales context
        """
        context_parts = []
        
        if "company_name" in sales_config:
            context_parts.append(f"You represent {sales_config['company_name']}.")
        
        if "product_name" in sales_config:
            context_parts.append(f"You're promoting {sales_config['product_name']}.")
        
        if "value_proposition" in sales_config:
            context_parts.append(f"Value proposition: {sales_config['value_proposition']}")
        
        if "qualification_criteria" in sales_config:
            criteria = sales_config["qualification_criteria"]
            criteria_text = "Qualification criteria: " + "; ".join([
                f"{k}: {v}" for k, v in criteria.items() if v
            ])
            context_parts.append(criteria_text)
        
        return " ".join(context_parts)
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"ConfigurableAgent(id={self.agent_id}, name={self.agent_name}, type={self.agent_type})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return (f"ConfigurableAgent(id='{self.agent_id}', name='{self.agent_name}', "
                f"type='{self.agent_type}', description='{self.description}')") 