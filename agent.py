import datetime
import os
import logging
import aiohttp
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, Callable, TypeVar, Generic, Literal, cast
from enum import Enum
import time
import json

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, RunContext, function_tool
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import elevenlabs
from livekit import api
from livekit.agents import BackgroundAudioPlayer, AudioConfig, BuiltinAudioClip

from instructions import survey_agent_instructions_v2

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()


@dataclass
class SurveyConfig:
    name: str
    goal: str
    intro_text: str
    closing_text: str
    questions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    first_question_id: Optional[str] = None
    survey_config_id: Optional[str] = None  # Supabase ID
    
    def add_question(self, question: Dict[str, Any]) -> None:
        self.questions[question['question_id']] = question
        if self.first_question_id is None:
            self.first_question_id = question['question_id']
    
    # def get_next_question_id(self, current_id: str, answer: Any) -> Optional[str]:
    #     if current_id not in self.questions:
    #         return None
            
    #     question = self.questions[current_id]
        
    #     # Check for conditional next question based on answer
    #     if question.conditional_next and answer in question.conditional_next:
    #         return question.conditional_next[answer]
            
    #     # Otherwise return the default next question
    #     return question.next_question_id
    
    def get_questions_as_text(self) -> str:
        """Generate a formatted text representation of all questions for instructions."""
        questions_text = ""
        for question in self.questions.values():
            questions_text += f"Question ID: {question['question_id']}\n"
            questions_text += f"Question: {question['text']}\n"
            
            if question['type'] == "rating":
                questions_text += f"Type: Rating scale from {question['min_value']} to {question['max_value']}\n"
            elif question['type'] == "multiple_choice" and question.get('options'):
                questions_text += "Type: Multiple choice\n"
                questions_text += "Options:\n"
                # Parse the options from JSON string if needed
                options = question['options']
                if isinstance(options, str):
                    import json
                    try:
                        options = json.loads(options)
                    except json.JSONDecodeError:
                        options = {}
                for key, value in options.items():
                    questions_text += f"- {key}: {value}\n"
            else:
                questions_text += f"Type: {question['type']}\n"
                
            questions_text += "\n"
        
        return questions_text

@dataclass
class SurveyData:
    survey_config: SurveyConfig
    learner_name: Optional[str] = None
    call_log_id: Optional[str] = None
    phone_number: Optional[str] = None
    current_question_id: Optional[str] = None
    answers: Dict[str, Any] = field(default_factory=dict)
    is_busy: bool = False
    wants_callback: bool = False
    call_start_time: Optional[float] = None
    call_end_time: Optional[float] = None
    comments: Optional[str] = None
    
    def __post_init__(self):
        if self.current_question_id is None:
            self.current_question_id = self.survey_config.first_question_id


class WebhookClient:
    """Client for submitting survey data to webhook endpoint."""
    
    def __init__(self, webhook_url: str = "https://primary-production-4c903.up.railway.app/webhook/4365d18d-07d1-4712-a9a1-dc578c1fe945"):
        self.webhook_url = webhook_url
    
    async def submit_survey_data(self, survey_data: Dict[str, Any]) -> bool:
        """Submit survey data to webhook endpoint.
        
        Args:
            survey_data: Dictionary containing survey response data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    headers={'Content-Type': 'application/json'},
                    json=survey_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully submitted survey data to webhook. Status: {response.status}")
                        return True
                    else:
                        logger.error(f"Failed to submit survey data. Status: {response.status}, Response: {await response.text()}")
                        return False
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error submitting survey data: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error submitting survey data: {e}")
            return False

    async def submit_transcript_data(self, transcript_data: Dict[str, Any]) -> bool:
        """Submit transcript data to webhook endpoint.
        
        Args:
            transcript_data: Dictionary containing transcript data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    headers={'Content-Type': 'application/json'},
                    json=transcript_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully submitted transcript data to webhook. Status: {response.status}")
                        return True
                    else:
                        logger.error(f"Failed to submit transcript data. Status: {response.status}, Response: {await response.text()}")
                        return False
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error submitting transcript data: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error submitting transcript data: {e}")
            return False

    def format_transcript_to_markdown(self, transcript_history: Dict[str, Any], survey_config: SurveyConfig, customer_name: str, call_log_id: str) -> str:
        """Format transcript history into a readable markdown format.
        
        Args:
            transcript_history: The session history dictionary
            survey_config: Survey configuration object
            customer_name: Name of the customer
            call_log_id: Call log ID for reference
            
        Returns:
            str: Formatted markdown transcript
        """
        # Get current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Start building the markdown
        markdown_lines = [
            f"# Survey Call Transcript",
            f"",
            f"**Date:** {timestamp}",
            f"**Customer:** {customer_name}",
            f"**Call Log ID:** {call_log_id}",
            f"**Survey:** {survey_config.name}",
            f"**Goal:** {survey_config.goal}",
            f"",
            f"---",
            f"",
            f"## Conversation",
            f""
        ]
        
        # Process the transcript items
        if 'items' in transcript_history:
            for item in transcript_history['items']:
                if item.get('type') == 'message':
                    role = item.get('role', 'unknown')
                    content_list = item.get('content', [])
                    interrupted = item.get('interrupted', False)
                    
                    # Join content if it's a list
                    content = ' '.join(content_list) if isinstance(content_list, list) else str(content_list)
                    
                    # Skip empty content
                    if not content.strip():
                        continue
                    
                    # Format based on role
                    if role == 'assistant':
                        speaker = "**Agent:**"
                    elif role == 'user':
                        speaker = f"**{customer_name}:**"
                    else:
                        speaker = f"**{role.title()}:**"
                    
                    # Add interrupted indicator if applicable
                    interrupted_indicator = " *(interrupted)*" if interrupted else ""
                    
                    markdown_lines.append(f"{speaker} {content}{interrupted_indicator}")
                    markdown_lines.append("")
        
        # Add summary section
        markdown_lines.extend([
            "---",
            "",
            "## Call Summary",
            "",
            f"- **Survey Name:** {survey_config.name}",
            f"- **Survey Goal:** {survey_config.goal}",
            f"- **Total Messages:** {len([item for item in transcript_history.get('items', []) if item.get('type') == 'message' and item.get('content')])}"
        ])
        
        return '\n'.join(markdown_lines)

class SurveyAgent(Agent):
    def __init__(self, survey_config: SurveyConfig, customer_name: str, webhook_client: WebhookClient) -> None:
        # Generate instructions with the survey questions
        questions_text = survey_config.get_questions_as_text()
        
        instructions = survey_agent_instructions_v2.format(
            company_name=survey_config.name,
            customer_name=customer_name,
            survey_goal=survey_config.goal,
            closing_text=survey_config.closing_text,
            questions_text=questions_text,
            first_question_id=survey_config.first_question_id
        )
        logger.info(f"####################instructions: {instructions}")
        super().__init__(instructions=instructions)
        # Initialize webhook client
        self.webhook_client = webhook_client

    @function_tool()
    async def handle_is_busy(self, context: RunContext[SurveyData], is_busy: bool = False, comments: Optional[str] = None) -> None:
        """Call this when the person indicates they're busy.
        
        Args:
            is_busy: Whether the person is busy and prefers a callback.
            comments: Optional additional comments about the busy status.
        """
        if is_busy:
            context.userdata.is_busy = True
            context.userdata.wants_callback = True
            context.userdata.comments = comments

        return "customer is busy, asking for a better time to call back"

    @function_tool()
    async def record_answer(self, context: RunContext[SurveyData], question_id: str, answer: Union[bool, int, str], comments: Optional[str] = None) -> str:
        """Call this to record an answer to a specific question.
        
        Args:
            question_id: The ID of the question being answered
            answer: The answer to the question (boolean for yes/no, int for ratings, string for text/multiple choice)
            comments: Optional additional comments about the answer.
            
        Returns:
            Information about what question to ask next, or if the survey is complete.
        """
        # Store the answer and comments locally
        context.userdata.answers[question_id] = {"answer": answer}
        if comments:
            context.userdata.answers[question_id]["comments"] = comments
        
        # Update current question
        context.userdata.current_question_id = question_id
        
        # Get the next question
        config = context.userdata.survey_config
        
        # Get all question IDs in order
        question_ids = list(config.questions.keys())
        try:
            current_index = question_ids.index(question_id)
            if current_index + 1 < len(question_ids):
                # Move to next question
                next_id = question_ids[current_index + 1]
                context.userdata.current_question_id = next_id
                next_question = config.questions[next_id]
                return f"Answer recorded. Next question ID: {next_id}. Ask: {next_question['text']}"
            else:
                # Survey is complete
                return "Survey complete. Finishing the survey and ending call."
        except ValueError:
            # Question ID not found, survey complete
            return "Survey complete. Finishing the survey and ending call."

    @function_tool()
    async def finish_survey(self, context: RunContext[SurveyData], comments: Optional[str] = None) -> None:
        """Call this to save the current state of the survey data. Call this before ending the call always."""
        
        context.userdata.call_end_time = time.time()
        print(f"####################comments: {comments}")
        # if comments is not None:
        #     context.userdata.comments += f"\n\n{comments}"

        # call webhook to save survey data
        await self.save_survey_data(context)

        return "Survey data saved. Ending call."
        

    async def save_survey_data(self, context: RunContext[SurveyData]) -> None:
        """Call this to save the survey data to local storage as backup. call webhook to save survey data"""
        
        # Calculate call duration
        duration_s = 0
        if context.userdata.call_start_time and context.userdata.call_end_time:
            duration_s = int(context.userdata.call_end_time - context.userdata.call_start_time)
        
        # Determine call status [Completed, No Answer, Busy, Refused, Voicemail, Pending]
        call_status = "Completed"
        if context.userdata.is_busy:
            call_status = "Busy"
        elif not context.userdata.answers:
            call_status = "Refused"
        
        # Format data for webhook API
        webhook_data = {
            "duration_s": duration_s,
            "survey_name": context.userdata.survey_config.name,
            "survey_goal": context.userdata.survey_config.goal,
            "learner_name": context.userdata.learner_name,
            "call_log_id": context.userdata.call_log_id,
            "phone_number": context.userdata.phone_number,
            "is_busy": context.userdata.is_busy,
            "wants_callback": context.userdata.wants_callback,
            "call_status": call_status,
            "answers": context.userdata.answers,
            "notes": context.userdata.comments
        }
        
        # Submit to webhook
        webhook_success = await self.webhook_client.submit_survey_data(webhook_data)
        
        if webhook_success:
            logger.info("Survey data successfully submitted to webhook")
        else:
            logger.error("Failed to submit survey data to webhook, saving locally as backup")
        
    @function_tool()
    async def end_call(self, context: RunContext[SurveyData]) -> None:
        """Call this to end the call."""
        from livekit import rtc, api
        from livekit.agents import get_job_context
        
        job_ctx = get_job_context()
        
        try:
            await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))
        except Exception as e:
            logger.error(f"Error ending call: {e}")
            await job_ctx.room.disconnect()

async def get_survey_config_from_metadata(metadata: Dict[str, Any]) -> Optional[SurveyConfig]:
    """Load survey configuration from metadata or Supabase."""
    try:
        # Check if there's a full survey config in metadata
        survey_config_data = metadata.get("survey")
        if survey_config_data:
            # Parse custom survey config from metadata
            config = SurveyConfig(
                name=survey_config_data.get("company_name"),
                goal=survey_config_data.get("survey_goal"),
                intro_text=survey_config_data.get("intro_text"),
                closing_text=survey_config_data.get("closing_text"),
                first_question_id=survey_config_data.get("first_question_id"),
            )

            questions = survey_config_data.get("questions")
            for question in questions:
                config.add_question(question)
            
            # Set first question if not specified
            if config.first_question_id is None and config.questions:
                config.first_question_id = list(config.questions.keys())[0]
            
            logger.info(f"Successfully loaded custom survey config from metadata: {config.name} with {len(config.questions)} questions")
            return config
            
    except Exception as e:
        logger.error(f"Error loading survey config from metadata: {e}")
    
    return None

async def entrypoint(ctx: agents.JobContext):
    """Main entrypoint for outbound survey calls."""
    
    # Track call start time for duration calculation
    call_start_time = time.time() 
    # Create webhook client instance for transcript submission
    webhook_client = WebhookClient()

    async def save_transcript():
        print("Saving conversation")
        
        try:
            # Get the transcript history
            transcript_history = session.history.to_dict()
            print("Raw transcript history:", transcript_history)
            

            
            # Format transcript to markdown
            markdown_transcript = webhook_client.format_transcript_to_markdown(
                transcript_history=transcript_history,
                survey_config=survey_config,
                customer_name=customer_name,
                call_log_id=call_log_id
            )
            
            print("Formatted markdown transcript:")
            print(markdown_transcript)
            
            # Prepare transcript data for webhook
            transcript_data = {
                "type": "transcript",
                "call_log_id": call_log_id,
                "customer_name": customer_name,
                "survey_name": survey_config.name,
                "timestamp": datetime.datetime.now().isoformat(),
                "markdown_transcript": markdown_transcript,
                "raw_transcript": transcript_history
            }
            
            # Submit transcript to webhook
            transcript_success = await webhook_client.submit_transcript_data(transcript_data)
            
            if transcript_success:
                logger.info("Transcript successfully submitted to webhook")
            else:
                logger.error("Failed to submit transcript to webhook")
                
        except Exception as e:
            logger.error(f"Error processing transcript: {e}")
            print(f"Error processing transcript: {e}")

    ctx.add_shutdown_callback(save_transcript)   

    # Parse metadata for customer info and survey config
    try:
        metadata = json.loads(ctx.job.metadata) if ctx.job.metadata else {}
        logger.info(f"Received metadata: {metadata}")
        
        customer_name = metadata.get("customer_name")
        phone_number = metadata.get("phone_number")
        call_log_id = metadata.get("call_log_id")
        
        # Try to get survey config from metadata
        survey_config = await get_survey_config_from_metadata(metadata)
        if survey_config is None:
            logger.info("No survey config found in metadata")
            raise ValueError("No survey config found in metadata")
        else:
            logger.info(f"Using survey config: {survey_config.name}")
            
    except (json.JSONDecodeError, AttributeError) as e:
        # Fallback for development when no metadata is provided
        logger.error(f"Error parsing metadata: {e}")
        raise e
    
    # Set up userdata with survey config and Supabase IDs
    userdata = SurveyData(
        survey_config=survey_config,
        learner_name=customer_name,
        call_log_id=call_log_id,
        phone_number=phone_number,
        call_start_time=call_start_time
    )
    
    logger.info(f"Connecting to room {ctx.room.name} for {customer_name} at {phone_number}")
    logger.info(f"Call Log ID: {call_log_id}")
    
    # Connect to the room first
    await ctx.connect()
    
    # For outbound calls, wait for the SIP participant to connect
    logger.info("Waiting for SIP participant to connect...")
    participant = await ctx.wait_for_participant()
    logger.info(f"SIP participant connected: {participant.identity}")
    
    # Create and start the agent session
    session = AgentSession[SurveyData](
        stt=elevenlabs.STT(language_code="en"),
        llm=openai.LLM(model="gpt-4.1"),
        tts=elevenlabs.TTS(voice_id="MzqUf1HbJ8UmQ0wUsx2p", model="eleven_flash_v2_5"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        userdata=userdata
    )

    await session.start(
        room=ctx.room,
        agent=SurveyAgent(survey_config, customer_name, webhook_client),
        room_input_options=RoomInputOptions(
            # Enhanced noise cancellation for call quality
            noise_cancellation=noise_cancellation.BVCTelephony(), 
        ),
    )

    # Start background audio for better UX
    background_audio = BackgroundAudioPlayer(
        thinking_sound=[
            AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.8),
            AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING2, volume=0.7),
        ],
    )
    await background_audio.start(room=ctx.room, agent_session=session)
    
    logger.info(f"Survey agent started for {customer_name}")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="SurveyAgent"
    )) 