# universalagent/transcripts/models.py
"""
Data models for transcript management.

This module defines the data structures used for transcript collection,
formatting, and transmission to webhook endpoints.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import json


class MessageRole(str, Enum):
    """Roles in conversation messages."""

    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"
    FUNCTION = "function"


@dataclass
class TranscriptMessage:
    """Represents a single message in a transcript."""

    role: str
    content: Union[str, List[str]]
    interrupted: bool = False
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Convert content to string if it's a list."""
        if isinstance(self.content, list):
            self.content = " ".join(self.content)

        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "interrupted": self.interrupted,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class TranscriptMetadata:
    """Metadata about a transcript."""

    call_id: str
    agent_id: str
    agent_name: str
    customer_name: Optional[str] = None
    customer_id: Optional[str] = None
    phone_number: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set start time if not provided."""
        if self.start_time is None:
            self.start_time = datetime.now()

    def set_end_time(self, end_time: Optional[datetime] = None) -> None:
        """Set end time and calculate duration."""
        self.end_time = end_time or datetime.now()
        if self.start_time:
            self.duration_seconds = int((self.end_time - self.start_time).total_seconds())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "call_id": self.call_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "customer_name": self.customer_name,
            "customer_id": self.customer_id,
            "phone_number": self.phone_number,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "context": self.context,
        }


@dataclass
class Transcript:
    """Complete transcript data."""

    metadata: TranscriptMetadata
    messages: List[TranscriptMessage] = field(default_factory=list)
    raw_history: Optional[Dict[str, Any]] = None

    def add_messages(self, messages: List[TranscriptMessage]) -> None:
        """Add a message to the transcript."""
        self.messages.extend(messages)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "messages": [msg.to_dict() for msg in self.messages],
            "raw_history": self.raw_history,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_livekit_history(
        cls, history: Dict[str, Any], metadata: TranscriptMetadata
    ) -> "Transcript":
        """Create a Transcript from LiveKit session history."""
        transcript = cls(metadata=metadata, raw_history=history)

        if "items" in history:
            for item in history["items"]:
                if item.get("type") == "message":
                    role = item.get("role", "unknown")
                    content = item.get("content", [])
                    interrupted = item.get("interrupted", False)

                    # Create a TranscriptMessage from the history item
                    message = TranscriptMessage(role=role, content=content, interrupted=interrupted)
                    transcript.add_message(message)

        return transcript


@dataclass
class TranscriptWebhookPayload:
    """Payload for webhook transmission."""

    transcript: Transcript
    event_type: str = "transcript.complete"
    event_id: str = field(default_factory=lambda: f"evt_{int(datetime.now().timestamp())}")
    timestamp: datetime = field(default_factory=datetime.now)
    formatted_transcript: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "transcript": self.transcript.to_dict(),
            "formatted_transcript": self.formatted_transcript,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
