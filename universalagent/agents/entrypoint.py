"""
Entrypoint functions for configurable LiveKit agents.

This module provides functions to create and start configurable agents
from configuration, integrating with LiveKit's JobContext and AgentSession.
"""

import asyncio
import os
import json
import logging
from typing import List, Optional, Dict, Any, Callable

from events.event_sender import EventSender
from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions, JobContext
from livekit.agents import BackgroundAudioPlayer, AudioConfig, BuiltinAudioClip
from livekit.agents import metrics, MetricsCollectedEvent
from livekit.agents import JobProcess


# Import optional noise cancellation
from livekit.plugins import noise_cancellation, silero
from tools.memory.memory_management_tools import MemoryManagementTool
from transcripts.models import TranscriptMetadata

from universalagent.core.config import AgentConfig
from universalagent.core.config_loader import load_config_hybrid
from universalagent.components.factory import ComponentFactory, ComponentCreationError
from universalagent.agents.configurable_agent import ConfigurableAgent
from universalagent.tools.call_management_tools import BUILT_IN_TOOLS
from universalagent.tools.knowledge.rag_tool import LlamaIndexPineconeRagTool, RAGToolConfig
from universalagent.tools.tool_holder import ToolHolder
from universalagent.agents.metadata import CallMetadata

from mem0 import AsyncMemoryClient

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
    
    # Parse metadata using the DTO
    meta = CallMetadata.from_json(ctx.job.metadata)
    logger.info(f"Parsed metadata: {meta}")
    
    # Load configuration
    config = await load_config_hybrid(meta.agent_id, meta.raw)
    
    if not config:
        logger.error(f"Failed to load configuration for agent: {meta.agent_id}")
        raise Exception(f"Failed to load configuration for agent: {meta.agent_id}")
    
    logger.info(f"Loaded configuration for agent: {config.name}")

    # Create and start the agent session
    await start_agent_session(ctx, config, meta)

# TODO: setup context for agent(shared state)
# TODO: Need to utilize prewarm func
async def start_agent_session(ctx: JobContext, config: AgentConfig, meta: CallMetadata) -> None:
    """Start an agent session with the given configuration.
    
    Args:
        ctx: LiveKit JobContext
        config: Agent configuration
    """ 
    try:


        transcript_metadata = TranscriptMetadata(
            call_id=meta.call_id,
            agent_id=meta.agent_id,
            agent_name=config.name,
            customer_name=meta.customer_name,
            phone_number=meta.phone_number,
        )
        usage_collector = metrics.UsageCollector()

        memory_tool = None
        if config.memory_config and config.memory_config.enabled:
            logger.info(f"Initializing memory management tool for customer: {meta.customer_id}")
            memory_tool = MemoryManagementTool(
                memory_config=config.memory_config,
                memory_manager=ctx.proc.userdata["memory_manager"],
                user_id=meta.customer_id,
                agent_id=meta.agent_id
            )

            async def memory_manager_shutdown_callback():
                messages = session.history.items
                await memory_tool.save_memory_from_messages(messages)
                logger.info(f"Saved memory from messages")

            ctx.add_shutdown_callback(memory_manager_shutdown_callback)

        async def event_sender_shutdown_callback():
            event_sender = EventSender(
                transcript_webhook_url=os.getenv("COMPLETION_WEBHOOK_URL"),
                metrics_webhook_url=os.getenv("COMPLETION_WEBHOOK_URL"),
            )
            await event_sender.send_transcript(session, transcript_metadata)
            summary = usage_collector.get_summary()
            await event_sender.send_metrics(summary, meta.to_dict())
            await event_sender.aclose()

        ctx.add_shutdown_callback(event_sender_shutdown_callback)

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
        
        # Initialize tools
        tools = initialize_tools(ctx, config, meta, memory_tool)

        # Connect to the room
        await ctx.connect()

        # Create configurable agent
        agent = ConfigurableAgent(config, runtime_metadata=meta.agent_data, tools=tools)
        logger.info(f"Created agent: {agent}")
        
        session_userdata = {
            "customer_id": meta.customer_id,
            "memory_manager": ctx.proc.userdata.get("memory_manager")
        }

        # Create AgentSession
        session = AgentSession(
            stt=stt,
            llm=llm,
            tts=tts,
            vad=ctx.proc.userdata["vad"],
            turn_detection=turn_detection,
            userdata=session_userdata
        )
        
        # Create room input options with noise cancellation
        room_input_options = create_room_input_options(config)
        
        logger.info("Waiting for participant to connect...")
        participant = await ctx.wait_for_participant()
        logger.info(f"Participant connected: {participant.identity}")

        # Start the session
        await session.start(
            room=ctx.room,
            agent=agent,
            room_input_options=room_input_options,
        )

        @session.on("metrics_collected")
        def _on_metrics_collected(ev: MetricsCollectedEvent):
            usage_collector.collect(ev.metrics)

        logger.info("Agent session started successfully")
        
            # Start background audio for better UX
        background_audio = BackgroundAudioPlayer(
            thinking_sound=[
                AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.8),
                AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING2, volume=0.7),
            ],
        )

        # TODO: THis causes delay in shutdown in the callback.
        # try:
        #     await background_audio.start(room=ctx.room, agent_session=session)
        # except Exception as e:
        #     logger.error(f"Error starting background audio: {e}")
        #     # Continue without background audio if it fails
        #     background_audio = None

        # # Add cleanup for background audio
        # async def background_audio_shutdown_callback():
        #     if background_audio:
        #         await background_audio.aclose()

        # ctx.add_shutdown_callback(background_audio_shutdown_callback)
        
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

#TODO: better way of loading environment variables
def initialize_tools(ctx: JobContext, config: AgentConfig, meta: CallMetadata, memory_tool: MemoryManagementTool) -> List[ToolHolder]:
    """Initialize tools based on configuration."""
    tools = []
    # Add built-in tools
    tools.extend(list(BUILT_IN_TOOLS.values()))

    # Add RAG tool
    if config.rag_config and config.rag_config.enabled:
        logger.info(f"Initializing RAG tool")
        rag_tool_config = RAGToolConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            pinecone_api_key=os.getenv("PINECONE_API_KEY"),
            index_name=os.getenv("PINECONE_INDEX_NAME"),
            namespace=config.rag_config.namespace,
            embedding_model=os.getenv("EMBEDDING_MODEL"),
            similarity_top_k=int(os.getenv("SIMILARITY_TOP_K", 3)),
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", 0.7)),
        )
        rag_tool = LlamaIndexPineconeRagTool(rag_tool_config)
        tools.append(rag_tool.get_rag_tool())
    
    if config.memory_config and config.memory_config.enabled and memory_tool is not None:
        logger.info(f"Initializing memory management tool for customer: {meta.customer_id}")
        tools.extend(memory_tool.get_memory_management_tools())

    return tools

def prewarm_fnc(proc: JobProcess):
    # load silero weights and store to process userdata
    proc.userdata["vad"] = silero.VAD.load()

    # initialize mem0 client
    mem0 = AsyncMemoryClient()
    proc.userdata['memory_manager'] = mem0

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
        prewarm_fnc=prewarm_fnc,
    )