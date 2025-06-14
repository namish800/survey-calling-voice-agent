import asyncio, inspect, functools
from typing import Callable, Optional, Awaitable, Any
from livekit.agents import RunContext
from universalagent.tools.tool_holder import ToolHolder


def fire_and_forget_tool_decorator(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    return_message: Optional[str] = None,
):
    """
    Decorator that converts an async function into a fire-and-forget ToolHolder.

    Usage:
        @fire_and_forget_tool_decorator(description="Log an event asynchronously")
        async def log_event(ctx: RunContext, event_type: str, note: str): ...
    """

    def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[str]]:
        async def _wrapper(*args, **kwargs) -> str:
            # launch the real coroutine in the background
            asyncio.create_task(fn(*args, **kwargs))
            return return_message or f"{fn.__name__} started in background"

        # make the wrapper indistinguishable from the original
        functools.update_wrapper(_wrapper, fn)
        _wrapper.__signature__ = inspect.signature(fn)  # type: ignore[attr-defined]
        return _wrapper

    return decorator

    return decorator
