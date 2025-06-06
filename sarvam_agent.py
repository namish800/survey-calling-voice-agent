from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import elevenlabs
from livekit.agents import AgentSession, Agent, RoomInputOptions, RunContext, function_tool


from runner import retrieve_chunk

load_dotenv()
from livekit.agents import ChatContext, ChatMessage



class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="Your goal is learn about the user's work and sell them Sarvam's new offering. your name is Nancy and you are a sales agent")

    # async def on_user_turn_completed(
    #     self, turn_ctx: ChatContext, new_message: ChatMessage,
    # ) -> None:
    #     # RAG function definition omitted for brevity
    #     rag_content = await retrieve_chunk(new_message.text_content)
    #     turn_ctx.add_message(
    #         role="assistant", 
    #         content=f"Additional information relevant to the user's next message: {rag_content}"
    #     )

    @function_tool()
    async def search_knowledge_center(self,
    context: RunContext,
    query: str) -> None:
        """Search the knowledge center for information relevant to the user's query."""
        rag_content = await retrieve_chunk(query)
        return rag_content



async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        stt=elevenlabs.STT(language_code="en"),
        llm=openai.LLM(model="gpt-4.1"),
        tts=elevenlabs.TTS(voice_id="MzqUf1HbJ8UmQ0wUsx2p", model="eleven_flash_v2_5"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )


    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )
    

    await ctx.connect()

    await session.generate_reply(
        instructions="Greet the user and introduce yourself."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, agent_name="sarvam_agent"))