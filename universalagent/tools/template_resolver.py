"""
Jinja2-based template resolver for webhook tools.

Handles templating with three namespaces:
- const: Constants from tool configuration
- ctx: Runtime context data
- arg: LLM-supplied arguments
"""

import re
import logging
from typing import Any, Dict, Set
import jinja2
from jinja2 import Environment, BaseLoader, meta

from .exceptions import TemplateValidationError, TemplateRenderError

logger = logging.getLogger(__name__)

# Regex to find all {{namespace.key}} patterns
PLACEHOLDER_PATTERN = re.compile(r'\{\{\s*(\w+)\.(\w+)\s*\}\}')

# Security: fields to mask in logs
SENSITIVE_FIELDS = {'token', 'secret', 'key', 'password', 'auth', 'api_key', 'access_token'}


class TemplateResolver:
    """Resolves Jinja2 templates with namespace support."""
    
    def __init__(self):
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=False,  # We're not rendering HTML
            undefined=jinja2.StrictUndefined  # Fail on undefined variables
        )
    
    def validate_template(self, template: str, allowed_namespaces: Set[str]) -> None:
        """Validate that template only uses allowed namespaces.
        
        Args:
            template: Template string to validate
            allowed_namespaces: Set of allowed namespace names
            
        Raises:
            TemplateValidationError: If template uses invalid namespaces
        """
        if not isinstance(template, str):
            return  # Skip validation for non-string templates
            
        placeholders = PLACEHOLDER_PATTERN.findall(template)
        
        for namespace, key in placeholders:
            if namespace not in allowed_namespaces:
                raise TemplateValidationError(
                    f"Invalid namespace '{namespace}' in template. "
                    f"Allowed namespaces: {sorted(allowed_namespaces)}"
                )
    
    def extract_namespaces(self, template: str) -> Dict[str, Set[str]]:
        """Extract all namespaces and their keys from a template.
        
        Args:
            template: Template string to analyze
            
        Returns:
            Dict mapping namespace names to sets of keys used
        """
        if not isinstance(template, str):
            return {}
            
        namespaces = {}
        placeholders = PLACEHOLDER_PATTERN.findall(template)
        
        for namespace, key in placeholders:
            if namespace not in namespaces:
                namespaces[namespace] = set()
            namespaces[namespace].add(key)
            
        return namespaces
    
    def render_template(self, template: str, const: Dict[str, Any], 
                       ctx: Dict[str, Any], arg: Dict[str, Any]) -> str:
        """Render a template with the three namespaces.
        
        Args:
            template: Template string to render
            const: Constants namespace
            ctx: Context namespace  
            arg: Arguments namespace
            
        Returns:
            Rendered template string
            
        Raises:
            TemplateRenderError: If rendering fails
        """
        if not isinstance(template, str):
            return template  # Return non-strings as-is
            
        try:
            jinja_template = self.env.from_string(template)
            
            # Prepare template context
            template_context = {
                'const': const or {},
                'ctx': ctx or {},
                'arg': arg or {}
            }
            
            result = jinja_template.render(**template_context)
            
            # Log the rendering (with sensitive data masked)
            self._log_template_render(template, template_context, result)
            
            return result
            
        except jinja2.TemplateError as e:
            raise TemplateRenderError(f"Failed to render template: {e}")
        except Exception as e:
            raise TemplateRenderError(f"Unexpected error rendering template: {e}")
    
    def render_dict(self, data: Dict[str, Any], const: Dict[str, Any],
                   ctx: Dict[str, Any], arg: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively render all string values in a dictionary.
        
        Args:
            data: Dictionary to render
            const: Constants namespace
            ctx: Context namespace
            arg: Arguments namespace
            
        Returns:
            Dictionary with rendered string values
        """
        if not isinstance(data, dict):
            return data
            
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.render_template(value, const, ctx, arg)
            elif isinstance(value, dict):
                result[key] = self.render_dict(value, const, ctx, arg)
            elif isinstance(value, list):
                result[key] = [
                    self.render_template(item, const, ctx, arg) if isinstance(item, str)
                    else self.render_dict(item, const, ctx, arg) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    
    def _log_template_render(self, template: str, context: Dict[str, Any], result: str) -> None:
        """Log template rendering with sensitive data masked."""
        # Mask sensitive data in context
        masked_context = self._mask_sensitive_data(context)
        
        logger.debug(
            f"Template rendered: '{template}' -> '{result}' "
            f"(context: {masked_context})"
        )
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """Recursively mask sensitive data in logs."""
        if isinstance(data, dict):
            return {
                key: "***MASKED***" if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS)
                else self._mask_sensitive_data(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data


def validate_no_overlap(const_keys: Set[str], ctx_keys: Set[str], 
                       llm_var_names: Set[str]) -> None:
    """Validate that there's no overlap between namespace keys.
    
    Args:
        const_keys: Keys used in const namespace
        ctx_keys: Keys used in ctx namespace  
        llm_var_names: Names of LLM variables
        
    Raises:
        TemplateValidationError: If there's overlap between namespaces
    """
    # Check const vs ctx overlap
    const_ctx_overlap = const_keys & ctx_keys
    if const_ctx_overlap:
        raise TemplateValidationError(
            f"Overlap between const and ctx namespaces: {sorted(const_ctx_overlap)}"
        )
    
    # Check const vs llm_vars overlap
    const_llm_overlap = const_keys & llm_var_names
    if const_llm_overlap:
        raise TemplateValidationError(
            f"Overlap between const and llm_vars: {sorted(const_llm_overlap)}"
        )
    
    # Check ctx vs llm_vars overlap  
    ctx_llm_overlap = ctx_keys & llm_var_names
    if ctx_llm_overlap:
        raise TemplateValidationError(
            f"Overlap between ctx and llm_vars: {sorted(ctx_llm_overlap)}"
        ) 