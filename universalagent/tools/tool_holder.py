from typing import Callable, Optional, Any, Awaitable
import asyncio
import logging
from livekit.agents import function_tool, RunContext


logger = logging.getLogger(__name__)


class ToolHolder:
    def __init__(self, fnc: Callable, 
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 usage_instructions_llm: str = ""):
        self.fnc = fnc
        if name is None:
            self.name = fnc.__name__
        else:
            self.name = name
        if description is None:
            self.description = fnc.__doc__
        else:
            self.description = description

        self._usage_instructions_llm = usage_instructions_llm


    @property
    def livekit_tool(self):
        return function_tool(
            self.fnc,
            name=self.name,
            description=self.description,
        )

    @property
    def usage_instructions_llm(self):
        return self._usage_instructions_llm


class FireAndForgetToolHolder(ToolHolder):
    """A tool holder that executes the function in the background without waiting for it to complete.
    
    This is useful for tools that don't need to return a result immediately, like logging, analytics,
    or any operation that can run asynchronously without blocking the main execution flow.
    """
    
    def __init__(self, fnc: Callable[..., Awaitable[Any]], 
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 usage_instructions_llm: str = ""):
        """Initialize a fire-and-forget tool holder.
        
        Args:
            fnc: An async function to execute without waiting for completion
            name: Optional name for the tool (defaults to function name)
            description: Optional description (defaults to function docstring)
            usage_instructions_llm: Optional usage instructions for the LLM
        """
        # Create a wrapper function that runs the original function in the background
        async def fire_and_forget_wrapper(ctx: RunContext, *args, **kwargs) -> str:
            # Start the task but don't await it
            asyncio.create_task(self._execute_and_log(fnc, ctx, *args, **kwargs))
            # Return immediately
            return f"Operation {name or fnc.__name__} started in the background"
        
        # Store the original function for reference
        self.original_fnc = fnc
        
        # Pass the wrapper to the parent class
        super().__init__(
            fire_and_forget_wrapper, 
            name=name, 
            description=description, 
            usage_instructions_llm=usage_instructions_llm
        )
    
    async def _execute_and_log(self, fnc: Callable, ctx: RunContext, *args, **kwargs) -> None:
        """Execute the function and log any errors."""
        try:
            await fnc(ctx, *args, **kwargs)
            logger.info(f"Background task {self.name} completed successfully")
        except Exception as e:
            logger.error(f"Error in background task {self.name}: {e}")