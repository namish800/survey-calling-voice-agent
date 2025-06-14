import json
import logging
from typing import Dict, List, Optional
from core.config import MemoryConfig
from livekit.agents import get_job_context, RunContext
from livekit.agents import ChatItem
from mem0 import AsyncMemoryClient
from tools.decorators import fire_and_forget_tool_decorator
from tools.tool_holder import FireAndForgetToolHolder, ToolHolder


logger = logging.getLogger(__name__)


class MemoryManagementTool:
    def __init__(
        self,
        memory_config: MemoryConfig,
        memory_manager: AsyncMemoryClient,
        user_id: str,
        agent_id: str,
    ):
        self.memory_config = memory_config
        self.memory_manager = memory_manager
        self.user_id = user_id
        self.agent_id = agent_id

    async def save_memory_from_messages(self, messages: List[ChatItem]):
        """Save the memory from the messages.
        This will save the memory from the messages.
        """
        messages_to_save = []
        for message in messages:
            messages_to_save.append({"role": message.role, "content": message.text_content})
        await self.memory_manager.add(
            messages_to_save, user_id=self.user_id, agent_id=self.agent_id
        )

    async def store_important_info(self, info: str, category: str):
        """Store important information about the user's call.
        This information should be valid for the task at hand. These memories will be used by you in the future.
        Also, other agents will use this information to help them with their tasks.
        And Companies will use this information to understand their customers better.

        Args:
            info: The important information to store
            category: The category of information (e.g., 'travel_planning', 'preferences', 'requirements')
        """
        try:
            customer_id = self.user_id

            if not customer_id:
                logger.error("No customer_id available in context.userdata for storing information")
                return "I had trouble storing that information - no user has been identified for this call."

            if not self.memory_manager:
                logger.error("Memory manager (mem0) not found in context.userdata")
                return "My memory system is currently unavailable. Please try again later."

            logger.info(f"Storing important information for user {customer_id}: {info}")

            # Format the memory data according to Mem0's API requirements
            messages = [{"role": "assistant", "content": info}]

            logger.debug(f"Attempting to store memory with data: {messages}")
            result = await self.memory_manager.add(
                messages,
                user_id=customer_id,
            )
            logger.debug(f"Memory storage result: {result}")

            return f"Stored important information about {category}"
        except Exception as e:
            logger.error(f"Error storing important information for user {self.user_id}: {str(e)}")
            logger.error(f"Full error details: {e.__dict__ if hasattr(e, '__dict__') else str(e)}")

    async def get_memory(self, query: str):
        """Get the memory for the user.
        This will return a list of memories that you can use to personalize your responses.
        Args:
            query: The query to search for in the memory
        """
        try:
            filters = {"AND": [{"user_id": self.user_id}]}
            memories = await self.memory_manager.search(
                query=query, limit=self.memory_config.max_history, filters=filters, version="v2"
            )

            memory_prompt = f"Here are the memories for the user {self.user_id} related to the query {query}: \n"
            memory_string = memory_prompt + "\n".join([memory["memory"] for memory in memories])
            return memory_string
        except Exception as e:
            logger.error(f"Error getting memory for user {self.user_id}: {str(e)}")
            return "I had trouble retrieving that information. Please try again later."

    def get_memory_management_tools(self) -> List[ToolHolder]:
        async def get_memory(context: RunContext, query: str):
            """Get the memory for the user.
            This will return a list of memories that you can use to personalize your responses.
            Args:
                query: The query to search for in the memory
            """
            return await self.get_memory(query)

        @fire_and_forget_tool_decorator()
        async def store_important_info(context: RunContext, info: str, category: str):
            """Store important information about the user's call.
            This information should be valid for the task at hand. These memories will be used by you in the future.
            Also, other agents will use this information to help them with their tasks.
            And Companies will use this information to understand their customers better.

            Args:
                info    : The important information to store
                category: The category of information (e.g., 'travel_planning', 'preferences', 'requirements')
            """
            return await self.store_important_info(info, category)

        return [ToolHolder(get_memory), ToolHolder(store_important_info)]
