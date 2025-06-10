# universalagent/transcripts/manager.py
"""
Transcript management system.

This module provides functionality for collecting, formatting, and
transmitting conversation transcripts to webhook endpoints.
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Union
from pathlib import Path
import aiohttp
import aiofiles

from livekit.agents import AgentSession, JobContext

from universalagent.transcripts.models import (
    Transcript, TranscriptMetadata, TranscriptMessage, TranscriptWebhookPayload
)
from universalagent.transcripts.formatters import MarkdownFormatter, HTMLFormatter

logger = logging.getLogger(__name__)


class TranscriptManager:
    """Manages transcript collection, storage, and transmission."""
    
    def __init__(
        self, 
        webhook_url: Optional[str] = None,
        webhook_headers: Optional[Dict[str, str]] = None,
        formatter: Optional[Callable[[Transcript], str]] = None
    ):
        """Initialize the transcript manager.
        
        Args:
            webhook_url: URL to send transcripts to (optional)
            webhook_headers: Custom headers for webhook requests
            formatter: Custom formatter function for transcripts
        """
        if not webhook_url:
            raise ValueError("webhook_url is required")
        
        self.webhook_url = webhook_url
        self.webhook_headers = webhook_headers or {'Content-Type': 'application/json'}
        self.formatter = formatter or MarkdownFormatter().format
        
        # Active transcripts by call ID
        self.active_transcripts: Dict[str, Transcript] = {}
    
    def register_transcript(self, ctx: JobContext, metadata: TranscriptMetadata) -> None:
        """Register this manager with a JobContext to handle shutdown.
        
        Args:
            ctx: LiveKit JobContext
            metadata: Transcript metadata
        """
        # Create initial transcript
        transcript = Transcript(metadata=metadata)
        self.active_transcripts[metadata.call_id] = transcript
        
        logger.info(f"Registered transcript manager for call {metadata.call_id}")
    
    async def handle_shutdown(self, call_id: str, messages: List[TranscriptMessage]) -> None:
        """Handle call shutdown, save transcript and send to webhook.
        
        Args:
            call_id: Call ID to process
        """
        if call_id not in self.active_transcripts:
            logger.warning(f"No active transcript found for call {call_id}")
            return
            
        transcript = self.active_transcripts[call_id]
        
        # Update end time and duration
        transcript.metadata.set_end_time()
        transcript.add_messages(messages)
        
        # Send to webhook if configured
        await self.send_to_webhook(call_id)
            
        # Remove from active transcripts
        del self.active_transcripts[call_id]
        logger.info(f"Processed shutdown for call {call_id}")
    
    async def send_to_webhook(self, call_id: str) -> bool:
        """Send transcript to webhook endpoint.
        
        Args:
            call_id: Call ID to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            logger.warning("No webhook URL configured")
            return False
            
        if call_id not in self.active_transcripts:
            logger.warning(f"No active transcript found for call {call_id}")
            return False
            
        transcript = self.active_transcripts[call_id]
        
        # Format transcript for readability
        formatted_transcript = self.formatter(transcript)
        
        # Create webhook payload
        payload = TranscriptWebhookPayload(
            transcript=transcript,
            formatted_transcript=formatted_transcript
        )
        print(payload.to_dict())
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    headers=self.webhook_headers,
                    json=payload.to_dict(),
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully sent transcript to webhook for call {call_id}")
                        return True
                    else:
                        logger.error(f"Failed to send transcript. Status: {response.status}, Response: {await response.text()}")
                        return False
        except aiohttp.ClientError as e:
            logger.error(f"Network error sending transcript: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending transcript: {e}")
            return False
    
    def get_transcript(self, call_id: str) -> Optional[Transcript]:
        """Get a transcript by call ID.
        
        Args:
            call_id: Call ID to retrieve
            
        Returns:
            Transcript or None if not found
        """
        return self.active_transcripts.get(call_id)