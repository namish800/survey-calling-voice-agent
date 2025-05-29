#!/usr/bin/env python3
"""
Dispatch script for triggering voice survey calls with Supabase integration.
This script demonstrates how to:
1. Load survey configs from Supabase
2. Pass learner metadata
3. Trigger LiveKit agent dispatch
"""

import asyncio
import json
import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

# LiveKit configuration
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

async def dispatch_survey_call(
    phone_number: str,
    customer_name: str,
    survey_name: str = "Unacademy Learning Experience Survey",
    learner_metadata: dict = None
):
    """
    Dispatch a survey call with Supabase integration.
    
    Args:
        phone_number: Phone number to call
        customer_name: Name of the customer
        survey_name: Name of survey config in Supabase (optional)
        learner_metadata: Additional metadata about the learner
    """
    
    # Prepare metadata for the agent
    metadata = {
        "phone_number": phone_number,
        "customer_name": customer_name,
        "name": customer_name,  # Alternative field name
        "survey_name": survey_name,  # This will trigger Supabase lookup
        "learner_metadata": learner_metadata or {}
    }
    
    # Create room name
    room_name = f"survey-{phone_number.replace('+', '').replace('-', '')}-{int(asyncio.get_event_loop().time())}"
    
    print(f"🚀 Dispatching survey call...")
    print(f"   Phone: {phone_number}")
    print(f"   Customer: {customer_name}")
    print(f"   Survey: {survey_name}")
    print(f"   Room: {room_name}")
    
    try:
        # Initialize LiveKit API
        lkapi = api.LiveKitAPI(
            url=LIVEKIT_URL,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET
        )
        
        # Create agent dispatch
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="SurveyAgent",
                room=room_name,
                metadata=json.dumps(metadata)
            )
        )
        
        print(f"✅ Dispatch created successfully!")
        print(f"   Dispatch ID: {dispatch.id}")
        print(f"   Room: {dispatch.room}")
        print(f"   Agent: {dispatch.agent_name}")
        
        await lkapi.aclose()
        return dispatch
        
    except Exception as e:
        print(f"❌ Error creating dispatch: {e}")
        return None

async def dispatch_multiple_calls():
    """Example of dispatching multiple survey calls."""
    
    # Sample learners to call
    learners = [
        {
            "phone_number": "+1234567890",
            "customer_name": "Rahul Sharma",
            "learner_metadata": {
                "goal": "JEE",
                "subscription_type": "Plus",
                "join_date": "2024-01-15",
                "last_active": "2024-05-20"
            }
        },
        {
            "phone_number": "+1234567891",
            "customer_name": "Priya Patel",
            "learner_metadata": {
                "goal": "NEET",
                "subscription_type": "Pro",
                "join_date": "2024-02-20",
                "last_active": "2024-05-22"
            }
        },
        {
            "phone_number": "+1234567892",
            "customer_name": "Amit Kumar",
            "learner_metadata": {
                "goal": "UPSC",
                "subscription_type": "Plus",
                "join_date": "2024-03-10",
                "last_active": "2024-05-18"
            }
        }
    ]
    
    print(f"📞 Dispatching {len(learners)} survey calls...\n")
    
    dispatches = []
    for i, learner in enumerate(learners):
        print(f"Call {i+1}/{len(learners)}:")
        
        dispatch = await dispatch_survey_call(
            phone_number=learner["phone_number"],
            customer_name=learner["customer_name"],
            survey_name="Unacademy Learning Experience Survey",
            learner_metadata=learner["learner_metadata"]
        )
        
        if dispatch:
            dispatches.append(dispatch)
        
        print()  # Empty line for readability
        
        # Add delay between calls to avoid overwhelming the system
        if i < len(learners) - 1:
            print("⏳ Waiting 5 seconds before next call...")
            await asyncio.sleep(5)
    
    print(f"🎉 Completed dispatching {len(dispatches)} calls successfully!")
    return dispatches

async def dispatch_with_custom_survey():
    """Example of dispatching with a custom survey config in metadata."""
    
    # Custom survey configuration
    custom_survey_config = {
        "name": "Quick Feedback Survey",
        "goal": "quick feedback collection",
        "intro_text": "We'd like to get your quick feedback. This will only take 2 minutes.",
        "closing_text": "Thank you for your feedback!",
        "questions": [
            {
                "id": "satisfaction",
                "text": "How satisfied are you with our service on a scale of 1 to 5?",
                "type": "numeric_rating",
                "min_value": 1,
                "max_value": 5,
                "required": True
            },
            {
                "id": "recommendation",
                "text": "Would you recommend us to a friend?",
                "type": "yes_no",
                "required": True
            },
            {
                "id": "comments",
                "text": "Any additional comments?",
                "type": "free_text",
                "required": False
            }
        ]
    }
    
    metadata = {
        "phone_number": "+1234567999",
        "customer_name": "Test User",
        "survey_config": custom_survey_config,  # Custom survey instead of Supabase lookup
        "learner_metadata": {
            "source": "custom_survey_test",
            "priority": "high"
        }
    }
    
    room_name = f"custom-survey-{int(asyncio.get_event_loop().time())}"
    
    print("🔧 Dispatching call with custom survey config...")
    print(f"   Survey: {custom_survey_config['name']}")
    print(f"   Questions: {len(custom_survey_config['questions'])}")
    
    try:
        lkapi = api.LiveKitAPI(
            url=LIVEKIT_URL,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET
        )
        
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="SurveyAgent",
                room=room_name,
                metadata=json.dumps(metadata)
            )
        )
        
        print(f"✅ Custom survey dispatch created: {dispatch.id}")
        
        await lkapi.aclose()
        return dispatch
        
    except Exception as e:
        print(f"❌ Error creating custom survey dispatch: {e}")
        return None

async def main():
    """Main function to demonstrate different dispatch scenarios."""
    
    print("🎯 LiveKit Voice Survey Agent - Supabase Integration Demo\n")
    
    # Check environment variables
    if not all([LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL]):
        print("❌ Missing LiveKit environment variables!")
        print("Please set LIVEKIT_API_KEY, LIVEKIT_API_SECRET, and LIVEKIT_URL")
        return
    
    print("Choose an option:")
    print("1. Single call with Supabase survey config")
    print("2. Multiple calls with Supabase survey config")
    print("3. Single call with custom survey config")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        phone = input("Enter phone number (e.g., +1234567890): ").strip()
        name = input("Enter customer name: ").strip()
        
        await dispatch_survey_call(
            phone_number=phone,
            customer_name=name,
            survey_name="Unacademy Learning Experience Survey",
            learner_metadata={"source": "manual_dispatch"}
        )
        
    elif choice == "2":
        await dispatch_multiple_calls()
        
    elif choice == "3":
        await dispatch_with_custom_survey()
        
    elif choice == "4":
        print("👋 Goodbye!")
        return
        
    else:
        print("❌ Invalid choice!")

if __name__ == "__main__":
    asyncio.run(main()) 