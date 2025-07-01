"""
Built-in call management tools for configurable agents.

These tools handle basic call flow operations like ending calls,
handling busy responses, and scheduling callbacks.
"""

import logging
from typing import Dict, List
from universalagent.tools.call_management.tools import call_management_tools
from universalagent.tools.time_management.tools import time_management_tools
from universalagent.tools.tool_holder import ToolHolder

logger = logging.getLogger(__name__)


# Registry of all built-in tools
BUILT_IN_TOOLS: Dict[str, List[ToolHolder]] = {
    "call_management": call_management_tools,
    "time_management": time_management_tools,
}
