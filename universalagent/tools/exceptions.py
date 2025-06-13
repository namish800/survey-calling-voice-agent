"""
Custom exceptions for webhook tool templating system.
"""


class TemplateError(Exception):
    """Base exception for template-related errors."""
    pass


class TemplateValidationError(TemplateError):
    """Raised when template validation fails."""
    pass


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails."""
    pass


class WebhookToolError(Exception):
    """Base exception for webhook tool errors."""
    pass


class WebhookConfigError(WebhookToolError):
    """Raised when webhook tool configuration is invalid."""
    pass


class WebhookExecutionError(WebhookToolError):
    """Raised when webhook execution fails."""
    pass 