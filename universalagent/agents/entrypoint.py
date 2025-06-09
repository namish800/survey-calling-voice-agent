"""
Entrypoint functions for configurable LiveKit agents.

This module provides functions to create and start configurable agents
from configuration, integrating with LiveKit's JobContext and AgentSession.
"""

import json
import logging
from typing import Optional, Dict, Any, Callable

from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions, JobContext
from livekit.agents import BackgroundAudioPlayer, AudioConfig, BuiltinAudioClip

# Import optional noise cancellation
from livekit.plugins import noise_cancellation

from universalagent.core.config import AgentConfig
from universalagent.core.config_loader import load_config_hybrid
from universalagent.components.factory import ComponentFactory, ComponentCreationError
from universalagent.agents.configurable_agent import ConfigurableAgent
from universalagent.tools.call_management_tools import BUILT_IN_TOOLS

logger = logging.getLogger(__name__)


async def configurable_agent_entrypoint(ctx: JobContext) -> None:
    """Universal entrypoint for configurable agents.
    
    This entrypoint can be used for any configurable agent. It loads the
    configuration based on metadata and creates the appropriate agent.
    
    Args:
        ctx: LiveKit JobContext containing room and metadata
    """
    logger.info(f"Starting configurable agent entrypoint")
    logger.info(f"Room: {ctx.room.name}")
    logger.info(f"Metadata: {ctx.job.metadata}")
    
    # Connect to the room
    await ctx.connect()
    metadata = json.loads(ctx.job.metadata) if ctx.job.metadata else {}
    # Load configuration
    agent_id = metadata.get("agent_id", "default")
    agent_data = metadata.get("agent_data", None)

    config = await load_config_hybrid(agent_id, metadata)
    
    if not config:
        logger.error(f"Failed to load configuration for agent: {agent_id}")
        raise Exception(f"Failed to load configuration for agent: {agent_id}")
    
    logger.info(f"Loaded configuration for agent: {config.name}")
    
    # Create and start the agent session
    await start_agent_session(ctx, config, agent_data)

# TODO: Add shutdown hook for saving call data
# TODO: Interface for metadata eg. to replace placeholders in instructions
# TODO: Fetch data from webhook for agent config -- event interface for agent init and fetch data required by agent from webhook
# TODO: setup context for agent(shared state)
async def start_agent_session(ctx: JobContext, config: AgentConfig, agent_data: Optional[Dict[str, Any]] = None) -> None:
    """Start an agent session with the given configuration.
    
    Args:
        ctx: LiveKit JobContext
        config: Agent configuration
    """
    try:
        # Create component factory
        factory = ComponentFactory()
        
        # Create LLM
        llm = factory.create_llm(config.llm_config)
        logger.info(f"Created LLM: {config.llm_config.provider} {config.llm_config.model}")
        
        # Create TTS (optional)
        tts = None
        if config.tts_config:
            tts = factory.create_tts(config.tts_config)
            logger.info(f"Created TTS: {config.tts_config.provider}")
        
        # Create STT (optional)
        stt = None
        if config.stt_config:
            stt = factory.create_stt(config.stt_config)
            logger.info(f"Created STT: {config.stt_config.provider}")
        
        # Create VAD
        vad = factory.create_vad(config.vad_config)
        logger.info("Created VAD")
        
        # Create turn detection
        turn_detection = factory.create_turn_detection(config.turn_detection_config)
        logger.info("Created turn detection")
        
        tools = list(BUILT_IN_TOOLS.values())
        # Create configurable agent
        agent = ConfigurableAgent(config, runtime_metadata=agent_data, tools=tools)
        logger.info(f"Created agent: {agent}")
        
        # Create AgentSession
        session = AgentSession(
            stt=stt,
            llm=llm,
            tts=tts,
            vad=vad,
            turn_detection=turn_detection,
        )
        
        # Create room input options with noise cancellation
        room_input_options = create_room_input_options(config)
        
        # Start the session
        await session.start(
            room=ctx.room,
            agent=agent,
            room_input_options=room_input_options,
        )
        
        logger.info("Agent session started successfully")
        
            # Start background audio for better UX
        background_audio = BackgroundAudioPlayer(
            thinking_sound=[
                AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.8),
                AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING2, volume=0.7),
            ],
        )

        try:
            await background_audio.start(room=ctx.room, agent_session=session)
        except Exception as e:
            logger.error(f"Error starting background audio: {e}")
            # Continue without background audio if it fails
            background_audio = None

        # Add cleanup for background audio
        ctx.add_shutdown_callback(lambda: background_audio.aclose() if background_audio else None)
        
    except ComponentCreationError as e:
        logger.error(f"Failed to create agent components: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to start agent session: {e}")
        raise


def create_room_input_options(config: AgentConfig) -> Optional[RoomInputOptions]:
    """Create RoomInputOptions based on configuration.
    
    Args:
        config: Agent configuration
        
    Returns:
        RoomInputOptions with noise cancellation or None
    """
    
    # Access noise cancellation directly from config property
    noise_cancellation_type = config.noise_cancellation
    
    try:
        if noise_cancellation_type == "BVC":
            return RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            )
        elif noise_cancellation_type == "BVCTelephony":
            return RoomInputOptions(
                noise_cancellation=noise_cancellation.BVCTelephony(),
            )
        else:
            logger.info(f"No noise cancellation configured: {noise_cancellation_type}")
            return None
            
    except Exception as e:
        logger.warning(f"Failed to create noise cancellation: {e}")
        return None


def create_worker_options(entrypoint_func: Optional[Callable] = None) -> agents.WorkerOptions:
    """Create WorkerOptions for running the configurable agent.
    
    Args:
        entrypoint_func: Custom entrypoint function (defaults to configurable_agent_entrypoint)
        
    Returns:
        WorkerOptions configured for the agent
    """
    entrypoint = entrypoint_func or configurable_agent_entrypoint
    
    return agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="base_agent",
        # Additional worker options can be added here
    )