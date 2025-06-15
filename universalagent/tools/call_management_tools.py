"""
Built-in call management tools for configurable agents.

These tools handle basic call flow operations like ending calls,
handling busy responses, and scheduling callbacks.
"""

import logging
from typing import Optional, Dict, Any

from livekit.agents import function_tool
from livekit import rtc, api
from livekit.agents import get_job_context, RunContext

from universalagent.tools.tool_holder import ToolHolder

logger = logging.getLogger(__name__)


async def end_call(ctx: RunContext, reason: str = "completed") -> str:
    """
    End the current call gracefully.

    Args:
        reason: Reason for ending the call (completed, busy, error, etc.)

    Returns:
        Confirmation message
    """
    logger.info(f"Ending call with reason: {reason}")

    current_speech = ctx.session.current_speech
    if current_speech:
        logger.info("Waiting for current speech to playout")
        await current_speech.wait_for_playout()

    job_ctx = get_job_context()

    try:
        await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))
    except Exception as e:
        logger.error(f"Error ending call: {e}")
        await job_ctx.room.disconnect()


# Registry of all built-in tools
BUILT_IN_TOOLS = {
    "end_call": ToolHolder(end_call),
}
