"""
Webhook tool builder for dynamic API templating.

Converts ToolConfig objects with webhook type into executable ToolHolder instances
that support Jinja2 templating with const/ctx/arg namespaces.
"""

import json
import logging
import asyncio
from typing import Any, Dict, Set
import httpx

from livekit.agents import RunContext, function_tool

from universalagent.core.config import ToolConfig, ApiSpec, LLMVar, ToolType
from universalagent.tools.tool_holder import ToolHolder
from .template_resolver import TemplateResolver, validate_no_overlap
from .exceptions import (
    WebhookConfigError, 
    WebhookExecutionError, 
    TemplateValidationError,
    TemplateRenderError
)

logger = logging.getLogger(__name__)


class WebhookToolBuilder:
    """Builds executable webhook tools from configuration."""
    
    def __init__(self):
        self.resolver = TemplateResolver()
    
    def build_webhook_tool(self, config: ToolConfig) -> ToolHolder:
        """Build a ToolHolder from a webhook ToolConfig.
        
        Args:
            config: ToolConfig with type=WEBHOOK
            
        Returns:
            ToolHolder that can be used by LiveKit agents
            
        Raises:
            WebhookConfigError: If configuration is invalid
        """
        if config.type not in (ToolType.WEBHOOK, ToolType.WEBHOOK.value):
            raise WebhookConfigError(f"Tool {config.name} is not a webhook tool")
        
        if not config.api_spec:
            raise WebhookConfigError(f"Webhook tool {config.name} missing api_spec")
        
        # Validate configuration at build time
        self._validate_config(config)
        
        # Create the async function that will be called by the LLM
        async def webhook_function(ctx: RunContext, **kwargs) -> Any:
            return await self._execute_webhook(config, ctx, kwargs)
        
        # Generate description with parameter info
        description = self._generate_description_with_params(config)
        
        return ToolHolder(
            webhook_function,
            name=config.name,
            description=description,
            usage_instructions_llm=self._generate_usage_instructions(config)
        )
    
    def _validate_config(self, config: ToolConfig) -> None:
        """Validate webhook tool configuration.
        
        Args:
            config: ToolConfig to validate
            
        Raises:
            WebhookConfigError: If configuration is invalid
        """
        spec = config.api_spec
        
        # Validate URL
        if not spec.url:
            raise WebhookConfigError(f"Tool {config.name}: URL is required")
        
        # Validate method
        if spec.method.upper() not in {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'}:
            raise WebhookConfigError(f"Tool {config.name}: Invalid HTTP method {spec.method}")
        
        # Extract all template namespaces used
        all_templates = [spec.url]
        all_templates.extend(spec.headers.values())
        all_templates.extend(spec.query.values())
        if isinstance(spec.body, str):
            all_templates.append(spec.body)
        elif isinstance(spec.body, dict):
            all_templates.extend(self._extract_dict_strings(spec.body))
        
        # Validate templates use only allowed namespaces
        allowed_namespaces = {'const', 'ctx', 'arg'}
        for template in all_templates:
            if isinstance(template, str):
                try:
                    self.resolver.validate_template(template, allowed_namespaces)
                except TemplateValidationError as e:
                    raise WebhookConfigError(f"Tool {config.name}: {e}")
        
        # Extract namespace usage for overlap validation
        const_keys = set(config.consts.keys()) if config.consts else set()
        ctx_keys = set()  # Will be determined at runtime
        llm_var_names = {var.name for var in spec.llm_vars}
        
        # For now, just validate const vs llm_vars overlap
        const_llm_overlap = const_keys & llm_var_names
        if const_llm_overlap:
            raise WebhookConfigError(
                f"Tool {config.name}: Overlap between consts and llm_vars: {sorted(const_llm_overlap)}"
            )
    
    def _extract_dict_strings(self, data: Any) -> list[str]:
        """Recursively extract all string values from a dictionary."""
        strings = []
        if isinstance(data, dict):
            for value in data.values():
                strings.extend(self._extract_dict_strings(value))
        elif isinstance(data, list):
            for item in data:
                strings.extend(self._extract_dict_strings(item))
        elif isinstance(data, str):
            strings.append(data)
        return strings
    
    def _generate_usage_instructions(self, config: ToolConfig) -> str:
        """Generate usage instructions for the LLM.
        
        Args:
            config: ToolConfig
            
        Returns:
            Usage instructions string
        """
        spec = config.api_spec
        instructions = [
            f"Use this tool to call {spec.method} {spec.url}."
        ]
        
        if spec.llm_vars:
            instructions.append("Required parameters:")
            for var in spec.llm_vars:
                req_str = "required" if var.required else "optional"
                instructions.append(f"  - {var.name} ({req_str}): {var.description}")
        
        return "\n".join(instructions)
    
    async def _execute_webhook(self, config: ToolConfig, ctx: RunContext, 
                              llm_args: Dict[str, Any]) -> Any:
        """Execute the webhook with templated parameters.
        
        Args:
            config: ToolConfig for the webhook
            ctx: LiveKit RunContext
            llm_args: Arguments provided by the LLM
            
        Returns:
            Response from the webhook
            
        Raises:
            WebhookExecutionError: If execution fails
        """
        spec = config.api_spec
        
        try:
            # Prepare template contexts
            const_ctx = config.consts or {}
            runtime_ctx = self._build_runtime_context(ctx)
            arg_ctx = llm_args
            
            # Render all template fields
            url = self.resolver.render_template(spec.url, const_ctx, runtime_ctx, arg_ctx)
            headers = self.resolver.render_dict(spec.headers, const_ctx, runtime_ctx, arg_ctx)
            query = self.resolver.render_dict(spec.query, const_ctx, runtime_ctx, arg_ctx)
            
            # Handle body rendering
            body = None
            if spec.body is not None:
                if isinstance(spec.body, str):
                    body = self.resolver.render_template(spec.body, const_ctx, runtime_ctx, arg_ctx)
                    # Try to parse as JSON if it looks like JSON
                    if body.strip().startswith(('{', '[')):
                        try:
                            body = json.loads(body)
                        except json.JSONDecodeError:
                            pass  # Keep as string
                else:
                    body = self.resolver.render_dict(spec.body, const_ctx, runtime_ctx, arg_ctx)
            
            # Log the request (with sensitive data masked)
            logger.info(f"Executing webhook {config.name}: {spec.method} {url}")
            logger.debug(f"Headers: {self.resolver._mask_sensitive_data(headers)}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Body: {self.resolver._mask_sensitive_data(body)}")
            
            # Execute HTTP request
            timeout = 30  # TODO: Make configurable
            async with httpx.AsyncClient(timeout=timeout) as client:
                if spec.method.upper() == 'GET':
                    response = await client.get(url, headers=headers, params=query)
                else:
                    response = await client.request(
                        spec.method.upper(),
                        url,
                        headers=headers,
                        params=query,
                        json=body if isinstance(body, (dict, list)) else None,
                        content=body if isinstance(body, str) else None
                    )
            
            # Handle response
            response.raise_for_status()
            
            # Try to parse as JSON, fall back to text
            try:
                result = response.json()
                logger.info(f"Webhook {config.name} succeeded with JSON response")
                return result
            except (json.JSONDecodeError, ValueError):
                result = response.text
                logger.info(f"Webhook {config.name} succeeded with text response")
                return result
                
        except TemplateRenderError as e:
            error_msg = f"Template rendering failed: {e}"
            logger.error(f"Webhook {config.name} failed: {error_msg}")
            return {"error": error_msg}
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Webhook {config.name} failed: {error_msg}")
            return {"error": error_msg}
            
        except httpx.RequestError as e:
            error_msg = f"Request failed: {e}"
            logger.error(f"Webhook {config.name} failed: {error_msg}")
            return {"error": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(f"Webhook {config.name} failed: {error_msg}")
            return {"error": error_msg}
    
    def _build_runtime_context(self, ctx: RunContext) -> Dict[str, Any]:
        """Build runtime context from RunContext.
        
        Args:
            ctx: LiveKit RunContext
            
        Returns:
            Dictionary of context values
        """
        runtime_ctx = {}
        
        # Add userdata if available
        if hasattr(ctx, 'userdata') and ctx.userdata:
            runtime_ctx.update(ctx.userdata)
        
        # Add session data if available
        if hasattr(ctx, 'session') and ctx.session and hasattr(ctx.session, 'userdata'):
            runtime_ctx.update(ctx.session.userdata or {})
        
        return runtime_ctx

    def _generate_description_with_params(self, config: ToolConfig) -> str:
        """Generate a description of the webhook tool including parameter information.
        
        Args:
            config: ToolConfig
            
        Returns:
            Description string
        """
        spec = config.api_spec
        description = f"Call {spec.method} {spec.url}"
        
        if spec.llm_vars:
            description += f" with parameters: {', '.join(var.name for var in spec.llm_vars)}"
        
        return description


# Global instance
_builder = WebhookToolBuilder()


def build_webhook_tool(config: ToolConfig) -> ToolHolder:
    """Build a webhook tool from configuration.
    
    Args:
        config: ToolConfig with type=WEBHOOK
        
    Returns:
        ToolHolder that can be used by LiveKit agents
    """
    return _builder.build_webhook_tool(config) 