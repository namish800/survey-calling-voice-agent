"""
Tests for webhook tool functionality.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock

from universalagent.core.config import AgentConfig, ToolConfig, ApiSpec, LLMVar, ToolType
from universalagent.tools.webhook_tool_builder import build_webhook_tool
from universalagent.tools.exceptions import WebhookConfigError


class TestWebhookToolBuilder:
    """Test webhook tool builder functionality."""
    
    def test_build_simple_webhook_tool(self):
        """Test building a simple webhook tool."""
        tool_config = ToolConfig(
            id="test-tool",
            name="testTool",
            description="A test webhook tool",
            type=ToolType.WEBHOOK,
            api_spec=ApiSpec(
                url="https://httpbin.org/get",
                method="GET",
                llm_vars=[
                    LLMVar(
                        name="query",
                        description="Search query",
                        schema={"type": "string"},
                        required=True
                    )
                ]
            )
        )
        
        tool_holder = build_webhook_tool(tool_config)
        
        assert tool_holder.name == "testTool"
        assert "test webhook tool" in tool_holder.description.lower()
    
    def test_build_webhook_tool_with_templates(self):
        """Test building a webhook tool with template placeholders."""
        tool_config = ToolConfig(
            id="booking-tool",
            name="bookAppointment",
            description="Book an appointment",
            type=ToolType.WEBHOOK,
            consts={"api_key": "test123"},
            api_spec=ApiSpec(
                url="https://httpbin.org/post",
                method="POST",
                headers={"Authorization": "Bearer {{const.api_key}}"},
                body={
                    "customer_id": "{{ctx.customer_id}}",
                    "time": "{{arg.appointment_time}}"
                },
                llm_vars=[
                    LLMVar(
                        name="appointment_time",
                        description="Appointment time",
                        schema={"type": "string"},
                        required=True
                    )
                ]
            )
        )
        
        tool_holder = build_webhook_tool(tool_config)
        
        assert tool_holder.name == "bookAppointment"
    
    def test_invalid_webhook_config_missing_api_spec(self):
        """Test that missing api_spec raises error."""
        tool_config = ToolConfig(
            id="invalid-tool",
            name="invalidTool",
            type=ToolType.WEBHOOK
        )
        
        with pytest.raises(WebhookConfigError, match="missing api_spec"):
            build_webhook_tool(tool_config)
    
    def test_invalid_webhook_config_wrong_type(self):
        """Test that non-webhook type raises error."""
        tool_config = ToolConfig(
            id="invalid-tool",
            name="invalidTool",
            type=ToolType.DEFAULT,
            api_spec=ApiSpec(url="https://example.com")
        )
        
        with pytest.raises(WebhookConfigError, match="not a webhook tool"):
            build_webhook_tool(tool_config)
    
    def test_invalid_http_method(self):
        """Test that invalid HTTP method raises error."""
        tool_config = ToolConfig(
            id="invalid-tool",
            name="invalidTool",
            type=ToolType.WEBHOOK,
            api_spec=ApiSpec(
                url="https://httpbin.org/get",
                method="INVALID"
            )
        )
        
        with pytest.raises(WebhookConfigError, match="Invalid HTTP method"):
            build_webhook_tool(tool_config)
    
    def test_const_llm_var_overlap(self):
        """Test that overlap between consts and llm_vars raises error."""
        tool_config = ToolConfig(
            id="overlap-tool",
            name="overlapTool",
            type=ToolType.WEBHOOK,
            consts={"query": "test"},
            api_spec=ApiSpec(
                url="https://httpbin.org/get",
                llm_vars=[
                    LLMVar(
                        name="query",  # Same name as in consts
                        description="Search query",
                        schema={"type": "string"},
                        required=True
                    )
                ]
            )
        )
        
        with pytest.raises(WebhookConfigError, match="Overlap between consts and llm_vars"):
            build_webhook_tool(tool_config)


class TestAgentConfigParsing:
    """Test that AgentConfig can parse webhook tool configurations."""
    
    def test_parse_webhook_tool_config(self):
        """Test parsing a complete webhook tool configuration."""
        config_data = {
            "agent_id": "test-agent",
            "name": "Test Agent",
            "description": "A test agent",
            "llm_config": {
                "provider": "openai",
                "model": "gpt-4"
            },
            "tools": [
                {
                    "id": "book-slot",
                    "name": "bookClinicSlot",
                    "description": "Books an appointment",
                    "type": "webhook",
                    "enabled": True,
                    "consts": {"api_key": "TEST123"},
                    "api_spec": {
                        "url": "https://httpbin.org/post",
                        "method": "POST",
                        "headers": {
                            "Authorization": "Bearer {{const.api_key}}"
                        },
                        "body": {
                            "time": "{{arg.desired_time}}",
                            "note": "{{arg.note}}"
                        },
                        "llm_vars": [
                            {
                                "name": "desired_time",
                                "description": "Preferred appointment time",
                                "schema": {"type": "string"},
                                "required": True
                            },
                            {
                                "name": "note",
                                "description": "Note for doctor",
                                "schema": {"type": "string", "maxLength": 120},
                                "required": True
                            }
                        ]
                    },
                    "wait_for_result": True
                }
            ]
        }
        
        config = AgentConfig.from_dict(config_data)
        
        assert len(config.tools) == 1
        tool = config.tools[0]
        assert tool.name == "bookClinicSlot"
        assert tool.type == ToolType.WEBHOOK
        assert tool.consts == {"api_key": "TEST123"}
        assert tool.api_spec is not None
        assert len(tool.api_spec.llm_vars) == 2
        assert tool.api_spec.llm_vars[0].name == "desired_time"
        assert tool.api_spec.llm_vars[1].name == "note"
        assert tool.wait_for_result is True


@pytest.mark.asyncio
class TestWebhookExecution:
    """Test webhook execution with mocked HTTP calls."""
    
    async def test_webhook_execution_success(self, monkeypatch):
        """Test successful webhook execution."""
        # Mock httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "id": "123"}
        mock_response.raise_for_status.return_value = None
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.request.return_value = mock_response
        
        # Patch httpx.AsyncClient
        import universalagent.tools.webhook_tool_builder
        monkeypatch.setattr(universalagent.tools.webhook_tool_builder, "httpx", MagicMock())
        universalagent.tools.webhook_tool_builder.httpx.AsyncClient.return_value = mock_client
        
        # Create tool
        tool_config = ToolConfig(
            id="test-tool",
            name="testTool",
            type=ToolType.WEBHOOK,
            consts={"api_key": "test123"},
            api_spec=ApiSpec(
                url="https://httpbin.org/post",
                method="POST",
                headers={"Authorization": "Bearer {{const.api_key}}"},
                body={"message": "{{arg.message}}"},
                llm_vars=[
                    LLMVar(
                        name="message",
                        description="Message to send",
                        schema={"type": "string"},
                        required=True
                    )
                ]
            )
        )
        
        tool_holder = build_webhook_tool(tool_config)
        
        # Mock RunContext
        mock_ctx = MagicMock()
        mock_ctx.userdata = {"customer_id": "cust123"}
        
        # Execute the tool
        result = await tool_holder.fnc(mock_ctx, message="Hello World")
        
        assert result == {"success": True, "id": "123"}
        
        # Verify the HTTP call was made correctly
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        
        assert call_args[0][0] == "POST"  # method
        assert call_args[0][1] == "https://httpbin.org/post"  # url
        assert call_args[1]["headers"]["Authorization"] == "Bearer test123"
        assert call_args[1]["json"]["message"] == "Hello World" 