# universalagent/events/event_sender.py
"""
Simple event sender for transcript and metrics data.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from livekit.agents import JobContext, AgentSession
from livekit.agents.metrics.usage_collector import UsageSummary
from transcripts.formatters import MarkdownFormatter
from transcripts.models import Transcript, TranscriptMessage, TranscriptMetadata, TranscriptWebhookPayload

from universalagent.events.webhook_client import WebhookClient

logger = logging.getLogger(__name__)

class EventSender:
    """Sends transcript and metrics events to webhook endpoints."""
    
    def __init__(
        self, 
        transcript_webhook_url: Optional[str] = None,
        metrics_webhook_url: Optional[str] = None
    ):
        """Initialize event sender.
        
        Args:
            transcript_webhook_url: URL for transcript webhooks
            metrics_webhook_url: URL for metrics webhooks
        """
        self.transcript_client = None
        if transcript_webhook_url:
            self.transcript_client = WebhookClient(transcript_webhook_url)
            
        self.metrics_client = None
        if metrics_webhook_url:
            self.metrics_client = WebhookClient(metrics_webhook_url)

        self.transcript_formatter = MarkdownFormatter().format
        
    
    async def send_transcript(self, session: AgentSession, transcript_metadata: TranscriptMetadata) -> bool:
        """Send transcript data from a LiveKit session.
        
        Args:
            session: LiveKit agent session
            transcript_metadata: TranscriptMetadata object
            
        Returns:    
            True if successful, False otherwise
        """
        if not self.transcript_client:
            logger.info("No transcript webhook configured")
            return False
        
        try:
            # Get transcript history from session
            transcript_messages: List[TranscriptMessage] = [TranscriptMessage(role=item.role,
                                                                            content=' '.join(item.content) if isinstance(item.content, list) else str(item.content),
                                                                            interrupted=item.interrupted)
                                                                            for item in session.history.items]
            
            transcript: Transcript = Transcript(
                metadata=transcript_metadata,
                messages=transcript_messages,
            )

            transcript.metadata.set_end_time()

            formatted_transcript = self.transcript_formatter(transcript)

            # Create payload with metadata and transcript
            payload = TranscriptWebhookPayload(
                transcript=transcript,
                formatted_transcript=formatted_transcript
            )
            # Send to webhook
            return await self.transcript_client.send_payload(payload.to_dict())
            
        except Exception as e:
            logger.error(f"Error sending transcript: {e}")
            return False
    
    async def send_metrics(self, usage: UsageSummary, metadata: Dict[str, Any]) -> bool:
        """Send metrics data from LiveKit UsageSummary.
        
        Args:
            usage: LiveKit UsageSummary object
            metadata: Additional metadata for the metrics
            
        Returns:
            True if successful, False otherwise
        """
        if not self.metrics_client:
            logger.info("No metrics webhook configured")
            return False
        
        try:
            # Create payload with metadata and metrics
            payload = {
                "event_type": "metrics",
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata,
                "metrics": {
                    "llm_prompt_tokens": usage.llm_prompt_tokens,
                    "llm_prompt_cached_tokens": usage.llm_prompt_cached_tokens,
                    "llm_completion_tokens": usage.llm_completion_tokens,
                    "tts_characters_count": usage.tts_characters_count,
                    "stt_audio_duration": usage.stt_audio_duration
                }
            }
            
            # Send to webhook
            return await self.metrics_client.send_payload(payload)
            
        except Exception as e:
            logger.error(f"Error sending metrics: {e}")
            return False

    async def aclose(self):
        if self.transcript_client:
            await self.transcript_client.aclose()
        if self.metrics_client:
            await self.metrics_client.aclose()