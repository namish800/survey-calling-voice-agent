#!/usr/bin/env python3
"""
Utility for making outbound calls using LiveKit API for survey agents.

This module provides functions to create SIP participants and initiate
outbound calls with proper metadata for survey campaigns.
"""

import os
import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from livekit import api
from livekit.protocol.sip import CreateSIPParticipantRequest, SIPParticipantInfo

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OutboundCallManager:
    """Manager for handling outbound calls via LiveKit SIP."""
    
    def __init__(self):
        self.livekit_api = api.LiveKitAPI()
        self.sip_trunk_id = os.environ.get("SIP_TRUNK_ID")
        self.agent_name = os.environ.get("AGENT_NAME", "SurveyAgent")
        
        if not self.sip_trunk_id:
            raise ValueError("SIP_TRUNK_ID environment variable is required")
    
    async def create_survey_call(
        self,
        phone_number: str,
        customer_name: str,
        survey_config: Optional[Dict[str, Any]] = None,
        customer_metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[SIPParticipantInfo, str]:
        """
        Create an outbound call for a survey campaign.
        
        Args:
            phone_number: Phone number to call (with country code, e.g., +1234567890)
            customer_name: Name of the customer being called
            survey_config: Survey configuration data
            customer_metadata: Additional customer metadata (prep_goal, current_plan, etc.)
            
        Returns:
            Tuple of (SIP participant info, room name)
            
        Raises:
            ValueError: If required parameters are missing
            Exception: If the call creation fails
        """
        if not phone_number.startswith("+"):
            raise ValueError("Phone number must include country code (start with +)")
        
        # Generate unique room name
        timestamp = int(time.time())
        room_name = f"survey-{customer_name.replace(' ', '-').lower()}-{timestamp}"
        
        # Prepare metadata for the agent
        metadata = {
            "phone_number": phone_number,
            "customer_name": customer_name,
            "call_type": "survey",
            "timestamp": timestamp
        }

        
        # Add survey configuration if provided
        if survey_config:
            metadata["survey"] = survey_config['survey']
        
        # Add customer metadata if provided
        if customer_metadata:
            metadata.update(customer_metadata)
        
        print(f"Metadata: {metadata}")
        print(f"Room name: {room_name}")
        print(f"Agent name: {self.agent_name}")
        # Create dispatch first to ensure agent is ready
        dispatch_request = api.CreateAgentDispatchRequest(
            agent_name=self.agent_name, 
            room=room_name, 
            metadata=json.dumps(metadata)
        )
        try:
            # Create the dispatch
            logger.info(f"Creating dispatch for room {room_name}")
            dispatch = await self.livekit_api.agent_dispatch.create_dispatch(dispatch_request)
            logger.info(f"Dispatch created: {dispatch.id}")
            
            # Wait a moment for the agent to connect
            await asyncio.sleep(2)
            
            # Create SIP participant request

            sip_request = api.CreateSIPParticipantRequest(
                room_name=room_name,
                sip_trunk_id=self.sip_trunk_id,
                sip_call_to=phone_number,
                participant_identity=f"customer-{timestamp}",
                participant_name=customer_name,
                krisp_enabled=True,  # Enable noise cancellation
            )            
            # Create the SIP participant (this initiates the call)
            logger.info(f"Calling {customer_name} at {phone_number}")
            participant = await self.livekit_api.sip.create_sip_participant(sip_request)
            
            logger.info(f"Call initiated successfully: {participant}")
            return participant, room_name
            
        except Exception as e:
            logger.error(f"Failed to create call for {customer_name} at {phone_number}: {e}")
            raise
    
    async def create_simple_call(
        self,
        phone_number: str,
        room_name: Optional[str] = None,
        participant_name: Optional[str] = None
    ) -> SIPParticipantInfo:
        """
        Create a simple outbound call without survey-specific metadata.
        
        Args:
            phone_number: Phone number to call (with country code)
            room_name: Optional room name (will be generated if not provided)
            participant_name: Optional participant name
            
        Returns:
            SIP participant info
        """
        if not phone_number.startswith("+"):
            raise ValueError("Phone number must include country code (start with +)")
        
        if not room_name:
            timestamp = int(time.time())
            room_name = f"call-{timestamp}"
        
        if not participant_name:
            participant_name = "Caller"
        
        # Create SIP participant request
        sip_request = CreateSIPParticipantRequest(
            sip_trunk_id=self.sip_trunk_id,
            sip_call_to=phone_number,
            room_name=room_name,
            participant_identity=f"caller-{int(time.time())}",
            participant_name=participant_name,
            krisp_enabled=True,
        )
        
        try:
            logger.info(f"Calling {phone_number}")
            participant = await self.livekit_api.sip.create_sip_participant(sip_request)
            logger.info(f"Call created successfully: {participant}")
            return participant
            
        except Exception as e:
            logger.error(f"Failed to create call to {phone_number}: {e}")
            raise
    
    async def close(self):
        """Close the LiveKit API connection."""
        await self.livekit_api.aclose()

# Convenience functions for backward compatibility and ease of use

async def make_outbound_call(
    phone_number: str,
    customer_name: str,
    survey_config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> tuple[SIPParticipantInfo, str]:
    """
    Make an outbound call for survey purposes.
    
    Args:
        phone_number: Phone number to call
        customer_name: Name of the customer
        survey_config: Survey configuration
        **kwargs: Additional metadata
        
    Returns:
        Tuple of (participant info, room name)
    """
    manager = OutboundCallManager()
    try:
        return await manager.create_survey_call(
            phone_number=phone_number,
            customer_name=customer_name,
            survey_config=survey_config,
            customer_metadata=kwargs
        )
    finally:
        await manager.close()

async def make_simple_call(
    phone_number: str,
    room_name: Optional[str] = None,
    participant_name: Optional[str] = None
) -> SIPParticipantInfo:
    """
    Make a simple outbound call.
    
    Args:
        phone_number: Phone number to call
        room_name: Optional room name
        participant_name: Optional participant name
        
    Returns:
        SIP participant info
    """
    manager = OutboundCallManager()
    try:
        return await manager.create_simple_call(
            phone_number=phone_number,
            room_name=room_name,
            participant_name=participant_name
        )
    finally:
        await manager.close()

# Example usage and testing
async def test_call():
    """Test function to verify the outbound call functionality."""
    phone_number = os.environ.get("TEST_PHONE_NUMBER")
    user_name = os.environ.get("TEST_USER_NAME")
    if not phone_number:
        print("TEST_PHONE_NUMBER environment variable not set, skipping test")
        return
    
    print(f"Testing call to {phone_number}...")
    
    config = {
        "customer_name": "Asha",
        "phone_number": "+911234567890",
        "survey": {
            "company_name": "unacademy",
            "survey_name": "NPS Q2",
            "survey_goal": "Measure NPS",
            "intro_text": "Hello",
            "closing_text": "Good Bye",
            "first_question_id": "q1",
            "questions": [
                {
                    "id": "q1",
                    "text": "On a scale of 1-10, how likely are you to recommend us?"
                }
            ]
        }
    }
    # Test survey call
    participant, room_name = await make_outbound_call(
        phone_number=phone_number,
        customer_name=user_name,
        survey_config=config
    )
    
    print(f"Test call successful!")
    print(f"Participant: {participant}")
    print(f"Room: {room_name}")
        

if __name__ == "__main__":
    load_dotenv()
    # Run test if called directly
    asyncio.run(test_call())
