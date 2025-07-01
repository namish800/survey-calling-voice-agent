import logging

from livekit import api
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

call_management_tools = [
    ToolHolder(end_call, usage_instructions_llm="Use this tool when you want to end the call. You can specify a reason for ending the call (completed, busy, error, etc.)."),
]

