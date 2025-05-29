#!/usr/bin/env python3
"""
Script to create a dispatch with metadata for testing the survey agent in development.
"""

import os
import asyncio
import json
from dotenv import load_dotenv
from livekit import api

load_dotenv()

async def create_dispatch_with_metadata(
    user_name: str, 
    room_name: str = None,
    agent_name: str = "SurveyAgent",
    survey_type: str = None,
    survey_config: dict = None
):
    """
    Create a dispatch for the survey agent with user metadata.
    
    Args:
        user_name (str): The name of the user for the survey
        room_name (str, optional): Room name to use. If None, creates a new room.
        agent_name (str, optional): Name of the agent registered in LiveKit.
        survey_type (str, optional): Type of survey ("unacademy", etc.)
        survey_config (dict, optional): Full custom survey configuration
    """
    # Set up LiveKit API client
    livekit_api = api.LiveKitAPI(
        url=os.environ.get("LIVEKIT_URL"),
        api_key=os.environ.get("LIVEKIT_API_KEY"),
        api_secret=os.environ.get("LIVEKIT_API_SECRET")
    )
    
    # Create room name if not provided
    if room_name is None:
        room_name = f"survey-{user_name.replace(' ', '')}"
    
    # Create metadata
    metadata = {
        "customer_name": user_name
    }
    
    # Add survey type if provided
    if survey_type:
        metadata["survey_type"] = survey_type
        
    # Add custom survey config if provided
    if survey_config:
        metadata["survey"] = survey_config
    
    # Create a dispatch for the agent
    dispatch_req = api.CreateAgentDispatchRequest(
        agent_name=agent_name,  # Must match the agent_name in WorkerOptions / WorkerOptions.agent_name
        room=room_name,
        metadata=json.dumps(metadata)
    )
    
    try:
        # Use the agent_dispatch sub-client as per LiveKit API docs
        dispatch = await livekit_api.agent_dispatch.create_dispatch(dispatch_req)
        print(f"Created dispatch: {dispatch.id}")
        print(f"Room: {room_name}")
        print(f"Metadata: {json.dumps(metadata, indent=2)}")
        print(f"Agent will be available in room: {room_name}")
        print(f"You can join this room in the LiveKit Agents Playground")
        return dispatch
    except Exception as e:
        print(f"Error creating dispatch: {e}")
        raise
    finally:
        # Close the API client connection
        try:
            await livekit_api.aclose()
        except Exception:
            pass

def  create_sample_customer_satisfaction_survey():
    """Create a sample customer satisfaction survey configuration."""
    return {
        "survey_result_id": "survey-result-123",
        "name": "Hyundai Customer Satisfaction team",
        "goal": "customer satisfaction and loyalty measurement",
        "intro_text": "We'd like to get your feedback on our services. This will take about 3 minutes. May I proceed?",
        "closing_text": "Thank you for your valuable feedback! It helps us improve our services. Have a great day!",
        "first_question_id": "overall_satisfaction",
        "questions": [
            {
                "id": "overall_satisfaction",
                "text": "On a scale of 1 to 5, how satisfied are you with our service overall?",
                "type": "numeric_rating",
                "min_value": 1,
                "max_value": 5,
                "next_question_id": "recommend"
            },
            {
                "id": "recommend",
                "text": "Would you recommend our service to a friend or colleague?",
                "type": "yes_no",
                "next_question_id": "improvement_area",
                "conditional_next": {
                    "false": "why_not_recommend"
                }
            },
            {
                "id": "why_not_recommend",
                "text": "I understand. What could we do better to improve your experience?",
                "type": "free_text",
                "next_question_id": "improvement_area"
            },
            {
                "id": "improvement_area",
                "text": "Which area do you think needs the most improvement? You can press a number or just tell me.",
                "type": "multiple_choice",
                "options": {
                    "1": "Customer Service",
                    "2": "Product Quality", 
                    "3": "Pricing",
                    "4": "Delivery Speed",
                    "5": "Website or App Experience"
                },
                "next_question_id": "additional_comments"
            },
            {
                "id": "additional_comments",
                "text": "Any other comments or suggestions you'd like to share?",
                "type": "free_text",
                "next_question_id": None
            }
        ]
    }

def create_simple_nps_survey():
    """Create a simple Net Promoter Score survey."""
    return {
        "name": "NPS Survey",
        "intro_text": "We'd like to ask you one quick question about your experience. This will take less than a minute.",
        "closing_text": "Thank you for your feedback! We really appreciate your time.",
        "first_question_id": "nps_score",
        "questions": [
            {
                "id": "nps_score",
                "text": "On a scale of 0 to 10, how likely are you to recommend our service to a friend?",
                "type": "numeric_rating",
                "min_value": 0,
                "max_value": 10,
                "next_question_id": "nps_reason"
            },
            {
                "id": "nps_reason",
                "text": "Thank you. Could you tell me what's the main reason for your score?",
                "type": "free_text",
                "next_question_id": None
            }
        ]
    }

def create_survey():
    return {
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

async def main():
    """Main entry point for the script."""
    # Check environment variables
    required_vars = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        return
    
    print("Creating different survey dispatches...\n")
    
    # # Example 1: Default Unacademy survey (no survey config in metadata)
    # print("1. Creating dispatch with default Unacademy survey:")
    # await create_dispatch_with_metadata("Namish", "unacademy-survey")
    # print()
    
    # Example 2: Custom customer satisfaction survey
    print("2. Creating dispatch with custom customer satisfaction survey:")
    customer_survey = create_survey()
    await create_dispatch_with_metadata(
        "Namish", 
        "playground-Ytq9-suir",
        survey_config=customer_survey
    )
    print()
    
    # # Example 3: Simple NPS survey
    # print("3. Creating dispatch with simple NPS survey:")
    # nps_survey = create_simple_nps_survey()
    # await create_dispatch_with_metadata(
    #     "Jane Smith",
    #     "nps-survey", 
    #     survey_config=nps_survey
    # )
    # print()
    
    print("All dispatches created! You can join these rooms in the LiveKit Agents Playground to test different survey types.")

if __name__ == "__main__":
    asyncio.run(main()) 