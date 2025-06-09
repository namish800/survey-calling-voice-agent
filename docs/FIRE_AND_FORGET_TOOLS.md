# Fire-and-Forget Tools Guide

## Overview

Fire-and-forget tools are special tools that run asynchronously in the background without blocking the main conversation flow. These are particularly useful for operations that:

- Don't need to return a result immediately
- Should not interrupt the user experience
- Perform actions that can happen concurrently
- Take a long time to complete

Examples include logging interactions, sending analytics data, calling external APIs, or performing background database operations.

## How They Work

The `FireAndForgetToolHolder` class wraps an async function and executes it in a background task without awaiting its completion. This means:

1. The tool is called like a normal tool
2. The tool immediately returns a confirmation message
3. The actual work happens in the background
4. Errors are logged but don't affect the main conversation

## Creating Fire-and-Forget Tools

### 1. Define Your Async Function

```python
import asyncio
import logging
from livekit.agents import RunContext

logger = logging.getLogger(__name__)

async def log_event(ctx: RunContext, event_type: str, details: str = "") -> None:
    """Log an event to the analytics system."""
    try:
        # Your logging logic here
        logger.info(f"Logging event: {event_type} - {details}")
        
        # Simulate some processing time
        await asyncio.sleep(2)
        
        # Actual work happens here
        # ... database call, API call, file writing, etc.
        
        logger.info(f"Event logged successfully: {event_type}")
    except Exception as e:
        logger.error(f"Failed to log event: {e}")
```

### 2. Create a FireAndForgetToolHolder

```python
from universalagent.tools.tool_holder import FireAndForgetToolHolder

# Create the fire-and-forget tool
log_event_tool = FireAndForgetToolHolder(
    log_event,
    name="log_event",
    description="Log an event to the analytics system without blocking the conversation"
)
```

### 3. Register the Tool

Either add it to your tools registry or expose it via a function:

```python
def get_async_tools():
    """Return a list of fire-and-forget tools."""
    return [log_event_tool]
```

## Configuration

Enable fire-and-forget tools in your agent configuration:

```json
{
  "agent_id": "my_agent",
  "name": "My Agent",
  "system_instructions": "You are a helpful assistant...",
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o-mini"
  },
  "tools": ["end_call", "log_event"],
  "async_tools_enabled": true
}
```

## Sample Implementation

The `universalagent/tools/example_async_tool.py` file provides a complete example with:

1. `log_user_interaction`: Logs interaction data to a file
2. `trigger_external_api`: Calls an external API without blocking

To use these examples:

```python
# In your agent code
from universalagent.tools.example_async_tool import get_async_tools

# Get all async tools
async_tools = get_async_tools()

# Add them to your agent's tools
agent_tools.extend(async_tools)
```

## Best Practices

1. **Error Handling**: Always include try/except blocks in your async functions
2. **Logging**: Log the start and completion of background tasks
3. **Status Updates**: Consider implementing a separate tool to check the status of background operations
4. **Resource Management**: Be mindful of how many background tasks you create
5. **Use Cases**: Only use for operations that don't affect the immediate conversation

## When to Use

✅ **Good Use Cases**:
- Analytics and logging
- Notifications to external systems
- Asynchronous database updates
- Report generation
- File uploads/downloads
- Email/SMS sending

❌ **Poor Use Cases**:
- Data needed for the current conversation
- Operations that affect the conversation flow
- Critical system operations where failures must be handled

## Example: Sample Agent Configuration

See the provided example configuration at `configs/development/async_tools_example.json`.

## Troubleshooting

If your fire-and-forget tools are not being registered:

1. Check that `async_tools_enabled` is set to `true` in your agent config
2. Ensure your tool names are correctly listed in the `tools` array
3. Check logs for any import errors
4. Verify your async functions have proper error handling

## Advanced: Custom Task Management

For more advanced use cases, you can implement a task management system:

```python
class BackgroundTaskManager:
    """Manages background tasks for fire-and-forget operations."""
    
    _tasks = {}
    
    @classmethod
    def create_task(cls, task_id: str, coro):
        """Create and track a background task."""
        cls._tasks[task_id] = asyncio.create_task(coro)
        return task_id
    
    @classmethod
    def get_task_status(cls, task_id: str) -> str:
        """Get the status of a background task."""
        if task_id not in cls._tasks:
            return "not_found"
        
        task = cls._tasks[task_id]
        if task.done():
            return "completed" if not task.exception() else "failed"
        return "running"
```

This allows for more sophisticated task tracking and management. 