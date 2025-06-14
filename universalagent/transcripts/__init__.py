# universalagent/transcripts/__init__.py
"""
Transcript management package.

This package provides functionality for collecting, formatting, and
transmitting conversation transcripts to webhook endpoints.
"""

from universalagent.transcripts.models import (
    Transcript,
    TranscriptMetadata,
    TranscriptMessage,
    TranscriptWebhookPayload,
)
from universalagent.transcripts.formatters import MarkdownFormatter, HTMLFormatter

__all__ = [
    "Transcript",
    "TranscriptMetadata",
    "TranscriptMessage",
    "TranscriptWebhookPayload",
    "MarkdownFormatter",
    "HTMLFormatter",
]
