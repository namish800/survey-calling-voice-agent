import asyncio
import logging
from livekit.agents import AgentSession, UserStateChangedEvent, AgentStateChangedEvent

logger = logging.getLogger(__name__)

class SilenceTimeoutHandler:
    def __init__(self, session: AgentSession, timeout_seconds: int = 10):
        self.session = session
        self.timeout_seconds = timeout_seconds
        self.silence_timer = None
        self.is_user_silent = False
        
        # Register for user state change events
        self.session.on("user_state_changed", self.handle_user_state_changed)
        self.session.on("agent_state_changed", self.handle_agent_state_changed)
    
    def handle_agent_state_changed(self, ev: AgentStateChangedEvent):
        logger.info(f"Agent state changed from {ev.old_state} to {ev.new_state}")
    
    def handle_user_state_changed(self, ev: UserStateChangedEvent):
        logger.info(f"User state changed from {ev.old_state} to {ev.new_state}")
        if ev.new_state == "away":
            # User stopped speaking, start silence timer
            logger.info("User is away, starting silence timer")
            self.is_user_silent = True
            self.start_silence_timer()
        else:
            # User is either listening or speaking, cancel any running timer
            logger.info("User is listening or speaking, canceling silence timer")
            self.is_user_silent = False
            self.cancel_silence_timer()
    
    def start_silence_timer(self):
        # Cancel any existing timer
        self.cancel_silence_timer()
        
        # Create a new timer
        self.silence_timer = asyncio.create_task(self._silence_timeout())
    
    def cancel_silence_timer(self):
        if self.silence_timer and not self.silence_timer.done():
            self.silence_timer.cancel()
            self.silence_timer = None
    
    async def _silence_timeout(self):
        try:
            # Wait for the specified timeout period
            await asyncio.sleep(self.timeout_seconds)
            
            # If we're still silent after the timeout, prompt the user
            if self.is_user_silent:
                logger.info(f"Silence detected for {self.timeout_seconds} seconds, prompting user")
                await self.prompt_user()
        except asyncio.CancelledError:
            # Timer was cancelled, silence ended before timeout
            pass
        except Exception as e:
            logger.error(f"Error in silence timeout handler: {e}")
    
    async def prompt_user(self):
        """Prompt the user after detecting silence"""
        try:
            # Check if the agent is speaking first
            if self.session.agent_state == "speaking":
                logger.info("Agent is speaking, not sending silence prompt")
                return
                
            # Send a gentle prompt to encourage the user to speak
            await self.session.generate_reply(
                instructions="Ask if the user is still there"
            )
        except Exception as e:
            logger.error(f"Error prompting user after silence: {e}")