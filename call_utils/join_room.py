#!/usr/bin/env python3
"""
Simple script to join a LiveKit room as a participant to test the survey agent.
"""

import asyncio
import os
from dotenv import load_dotenv
from livekit import rtc, api

load_dotenv()

async def join_room_as_participant(room_name: str, participant_name: str = "Test User"):
    """
    Join a LiveKit room as a participant to interact with the survey agent.
    
    Args:
        room_name (str): Name of the room to join
        participant_name (str): Name to use as participant
    """
    # Create access token for the participant
    livekit_api = api.LiveKitAPI(
        url=os.environ.get("LIVEKIT_URL"),
        api_key=os.environ.get("LIVEKIT_API_KEY"),
        api_secret=os.environ.get("LIVEKIT_API_SECRET")
    )
    
    try:
        # Create access token
        token = api.AccessToken(
            api_key=os.environ.get("LIVEKIT_API_KEY"),
            api_secret=os.environ.get("LIVEKIT_API_SECRET")
        )
        token = token.with_identity(participant_name).with_name(participant_name)
        token = token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        ))
        
        print(f"Joining room: {room_name}")
        print(f"Participant: {participant_name}")
        print(f"LiveKit URL: {os.environ.get('LIVEKIT_URL')}")
        print("\nConnecting to room...")
        
        # Connect to the room
        room = rtc.Room()
        
        @room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            print(f"Participant connected: {participant.identity} ({participant.name})")
            
        @room.on("participant_disconnected") 
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            print(f"Participant disconnected: {participant.identity}")
            
        @room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            print(f"Track subscribed: {track.kind} from {participant.identity}")
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                print("Audio track received from agent!")
                
        @room.on("data_received")
        def on_data_received(data: bytes, participant: rtc.RemoteParticipant):
            message = data.decode('utf-8')
            print(f"Data from {participant.identity}: {message}")
            
        @room.on("disconnected")
        def on_disconnected():
            print("Disconnected from room")
            
        # Connect to room
        await room.connect(
            url=os.environ.get("LIVEKIT_URL"),
            token=token.to_jwt()
        )
        
        print(f"Connected to room: {room.name}")
        print(f"Local participant: {room.local_participant.identity}")
        
        # List existing participants
        print(f"Room participants: {len(room.remote_participants)}")
        for participant in room.remote_participants.values():
            print(f"  - {participant.identity} ({participant.name})")
            
        # Enable microphone for voice interaction
        print("\nEnabling microphone...")
        try:
            # Create audio source and track
            source = rtc.AudioSource(sample_rate=48000, num_channels=1)
            track = rtc.LocalAudioTrack.create_audio_track("microphone", source)
            options = rtc.TrackPublishOptions()
            options.source = rtc.TrackSource.SOURCE_MICROPHONE
            
            publication = await room.local_participant.publish_track(track, options)
            print("Microphone enabled! You can now speak to the survey agent.")
            
        except Exception as e:
            print(f"Could not enable microphone: {e}")
            print("You can still listen to the agent, but voice interaction won't work.")
            
        print("\n" + "="*60)
        print("READY TO TEST SURVEY AGENT!")
        print("="*60)
        print("- The survey agent should start speaking shortly")
        print("- Speak clearly into your microphone to respond")
        print("- Press Ctrl+C to exit")
        print("="*60)
        
        # Keep the connection alive
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nDisconnecting...")
            
    except Exception as e:
        print(f"Error joining room: {e}")
        raise
    finally:
        try:
            await room.disconnect()
            await livekit_api.aclose()
        except:
            pass

async def main():
    """Main entry point for the script."""
    # Check environment variables
    required_vars = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        return
    
    # You can customize these
    room_name = "customer-satisfaction"  # Change this to match your dispatch room
    participant_name = "John Doe"  # This should match the user_name in your dispatch metadata
    
    print(f"Attempting to join room: {room_name}")
    print(f"As participant: {participant_name}")
    print("\nMake sure:")
    print("1. Your survey agent is running (python survey_agent.py dev)")
    print("2. You've created a dispatch for this room")
    print("3. The room name matches your dispatch\n")
    
    await join_room_as_participant(room_name, participant_name)

if __name__ == "__main__":
    asyncio.run(main()) 