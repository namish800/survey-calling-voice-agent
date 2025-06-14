# universalagent/transcripts/formatters.py
"""
Transcript formatters.

This module provides formatters to convert transcripts into
readable formats like markdown and HTML.
"""

from typing import Dict, Any, List, Optional
from universalagent.transcripts.models import Transcript, TranscriptMessage


class MarkdownFormatter:
    """Formats transcripts as Markdown text."""

    def format(self, transcript: Transcript) -> str:
        """Format a transcript as Markdown.

        Args:
            transcript: The transcript to format

        Returns:
            Formatted Markdown string
        """
        metadata = transcript.metadata

        # Start building the markdown
        markdown_lines = [
            f"# Call Transcript",
            f"",
            f"**Call ID:** {metadata.call_id}",
            f"**Agent:** {metadata.agent_name}",
        ]

        # Add customer details if available
        if metadata.customer_name:
            markdown_lines.append(f"**Customer:** {metadata.customer_name}")

        if metadata.phone_number:
            markdown_lines.append(f"**Phone:** {metadata.phone_number}")

        # Add timestamps
        if metadata.start_time:
            markdown_lines.append(f"**Start Time:** {metadata.start_time.isoformat()}")

        if metadata.end_time:
            markdown_lines.append(f"**End Time:** {metadata.end_time.isoformat()}")

        if metadata.duration_seconds is not None:
            minutes, seconds = divmod(metadata.duration_seconds, 60)
            markdown_lines.append(f"**Duration:** {minutes}m {seconds}s")

        # Add context if available
        if metadata.context:
            markdown_lines.extend(["", "## Context", ""])
            for key, value in metadata.context.items():
                markdown_lines.append(f"**{key}:** {value}")

        # Add the conversation
        markdown_lines.extend(["", "## Conversation", ""])

        for message in transcript.messages:
            # Format based on role
            if message.role == "assistant":
                speaker = f"**{metadata.agent_name}:**"
            elif message.role == "user":
                speaker = f"**{metadata.customer_name or 'Customer'}:**"
            else:
                speaker = f"**{message.role.title()}:**"

            # Add interrupted indicator if applicable
            interrupted_indicator = " *(interrupted)*" if message.interrupted else ""

            markdown_lines.append(f"{speaker} {message.content}{interrupted_indicator}")
            markdown_lines.append("")

        # Add stats
        markdown_lines.extend(
            [
                "---",
                "",
                "## Call Statistics",
                "",
                f"- **Total Messages:** {len(transcript.messages)}",
                f"- **Customer Messages:** {sum(1 for m in transcript.messages if m.role == 'user')}",
                f"- **Agent Messages:** {sum(1 for m in transcript.messages if m.role == 'assistant')}",
                f"- **Interruptions:** {sum(1 for m in transcript.messages if m.interrupted)}",
            ]
        )

        return "\n".join(markdown_lines)


class HTMLFormatter:
    """Formats transcripts as HTML."""

    def format(self, transcript: Transcript) -> str:
        """Format a transcript as HTML.

        Args:
            transcript: The transcript to format

        Returns:
            Formatted HTML string
        """
        metadata = transcript.metadata

        # Basic HTML structure
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>Transcript: {metadata.call_id}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1 { color: #333; }",
            ".metadata { background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }",
            ".conversation { margin-bottom: 20px; }",
            ".message { margin-bottom: 10px; padding: 8px; border-radius: 5px; }",
            ".assistant { background: #e6f7ff; border-left: 4px solid #1890ff; }",
            ".user { background: #f6ffed; border-left: 4px solid #52c41a; }",
            ".system { background: #fff7e6; border-left: 4px solid #faad14; }",
            ".function { background: #f9f0ff; border-left: 4px solid #722ed1; }",
            ".interrupted { font-style: italic; color: #f5222d; }",
            ".stats { background: #f5f5f5; padding: 15px; border-radius: 5px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>Call Transcript</h1>",
            "<div class='metadata'>",
            f"<p><strong>Call ID:</strong> {metadata.call_id}</p>",
            f"<p><strong>Agent:</strong> {metadata.agent_name}</p>",
        ]

        # Add customer details if available
        if metadata.customer_name:
            html.append(f"<p><strong>Customer:</strong> {metadata.customer_name}</p>")

        if metadata.phone_number:
            html.append(f"<p><strong>Phone:</strong> {metadata.phone_number}</p>")

        # Add timestamps
        if metadata.start_time:
            html.append(f"<p><strong>Start Time:</strong> {metadata.start_time.isoformat()}</p>")

        if metadata.end_time:
            html.append(f"<p><strong>End Time:</strong> {metadata.end_time.isoformat()}</p>")

        if metadata.duration_seconds is not None:
            minutes, seconds = divmod(metadata.duration_seconds, 60)
            html.append(f"<p><strong>Duration:</strong> {minutes}m {seconds}s</p>")

        html.append("</div>")

        # Add context if available
        if metadata.context:
            html.append("<h2>Context</h2>")
            html.append("<div class='metadata'>")
            for key, value in metadata.context.items():
                html.append(f"<p><strong>{key}:</strong> {value}</p>")
            html.append("</div>")

        # Add the conversation
        html.append("<h2>Conversation</h2>")
        html.append("<div class='conversation'>")

        for message in transcript.messages:
            # Determine CSS class based on role
            css_class = message.role

            # Get speaker name
            if message.role == "assistant":
                speaker = metadata.agent_name
            elif message.role == "user":
                speaker = metadata.customer_name or "Customer"
            else:
                speaker = message.role.title()

            # Add message
            html.append(f"<div class='message {css_class}'>")
            html.append(f"<p><strong>{speaker}:</strong> {message.content}")

            # Add interrupted indicator if applicable
            if message.interrupted:
                html.append("<span class='interrupted'> (interrupted)</span>")

            html.append("</p>")
            html.append("</div>")

        html.append("</div>")

        # Add stats
        html.append("<h2>Call Statistics</h2>")
        html.append("<div class='stats'>")
        html.append("<ul>")
        html.append(f"<li><strong>Total Messages:</strong> {len(transcript.messages)}</li>")
        html.append(
            f"<li><strong>Customer Messages:</strong> {sum(1 for m in transcript.messages if m.role == 'user')}</li>"
        )
        html.append(
            f"<li><strong>Agent Messages:</strong> {sum(1 for m in transcript.messages if m.role == 'assistant')}</li>"
        )
        html.append(
            f"<li><strong>Interruptions:</strong> {sum(1 for m in transcript.messages if m.interrupted)}</li>"
        )
        html.append("</ul>")
        html.append("</div>")

        # Close HTML
        html.extend(["</body>", "</html>"])

        return "\n".join(html)
