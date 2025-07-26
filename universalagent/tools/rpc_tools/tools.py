from livekit.agents import get_job_context, RunContext
from universalagent.tools.tool_holder import ToolHolder
import json
import logging

logger = logging.getLogger(__name__)


async def present_url(ctx: RunContext, title: str, url: str, description: str = "") -> str:
    """Present a URL to the user via RPC call to the frontend.
    
    Args:
        title: Title for the URL presentation
        url: The URL to present
        description: Optional description of the URL
        
    Returns:
        Confirmation message
    """
    try:
        # Get the job context to access room
        job_ctx = get_job_context()
        
        # Get the participant identity
        participants = list(job_ctx.room.remote_participants.values())
        if not participants:
            logger.warning("No participants found to send URL to")
            return "No participants found to send URL to"
            
        participant_identity = participants[0].identity
        
        # Perform the RPC call
        response = await job_ctx.room.local_participant.perform_rpc(
            destination_identity=participant_identity,
            method="showUrl",
            payload=json.dumps({
                "title": title,
                "url": url,
                "description": description
            }),
            response_timeout=10.0,
        )
        
        logger.info(f"Successfully sent URL to frontend: {title} - {url}")
        return f"URL '{title}' presented to user successfully"
        
    except Exception as e:
        logger.error(f"Failed to present URL via RPC: {e}")
        return f"Failed to present URL: {str(e)}"

async def send_rpc_to_frontend(ctx: RunContext, method: str, payload_data: str) -> str:
    """Send a generic RPC call to the frontend.
    
    Args:
        method: The RPC method name to call on the frontend
        payload_data: JSON string payload to send
        
    Returns:
        Confirmation message or response from frontend
    """
    try:
        # Get the job context to access room
        job_ctx = get_job_context()
        
        # Get the participant identity
        participants = list(job_ctx.room.remote_participants.values())
        if not participants:
            logger.warning("No participants found to send RPC to")
            return "No participants found to send RPC to"
            
        participant_identity = participants[0].identity
        
        # Perform the RPC call
        response = await job_ctx.room.local_participant.perform_rpc(
            destination_identity=participant_identity,
            method=method,
            payload=payload_data,
            response_timeout=10.0,
        )
        
        logger.info(f"Successfully sent RPC '{method}' to frontend")
        if response:
            return f"RPC '{method}' sent successfully. Response: {response}"
        else:
            return f"RPC '{method}' sent successfully"
        
    except Exception as e:
        logger.error(f"Failed to send RPC '{method}' to frontend: {e}")
        return f"Failed to send RPC '{method}': {str(e)}"

generic_rpc_tool = ToolHolder(
    send_rpc_to_frontend,
    usage_instructions_llm="Use this tool to send custom RPC calls to the frontend. Specify the method name and provide a JSON string as payload. This is for advanced frontend interactions beyond URL presentation."
)

description="""Present data to the user via RPC call to the frontend.
    
    Args:
        title: Title for the URL presentation
        data: The message to present
        description: Optional description.
        
    Returns:
        Confirmation message

    eg. If user needs to login to a website, you can use this tool to present the login page to the user.
"""

present_url_tool = ToolHolder(
    present_url,
    name="present_data",
    description=description
)


