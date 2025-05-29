# Call Utilities for LiveKit Survey Agent

This directory contains utilities for making outbound calls using LiveKit's SIP integration for survey campaigns.

## Files Overview

- **`make_call.py`** - Core outbound call utility with LiveKit API integration
- **`batch_calls.py`** - Batch processing for calling multiple customers from CSV
- **`test_outbound_call.py`** - Test script to verify call functionality
- **`dispatch_with_metadata.py`** - Advanced dispatch management
- **`join_room.py`** - Utility for joining existing LiveKit rooms

## Quick Start

### 1. Environment Setup

Create a `.env` file in your project root with:

```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# SIP Configuration
SIP_TRUNK_ID=your-sip-trunk-id
AGENT_NAME=survey-agent

# Optional: For testing
TEST_PHONE_NUMBER=+1234567890
```

### 2. Install Dependencies

```bash
pip install livekit livekit-agents python-dotenv
```

### 3. Test Your Setup

```bash
python call_utils/test_outbound_call.py +1234567890
```

## Usage Examples

### Making a Single Survey Call

```python
from call_utils.make_call import make_outbound_call

# Make a survey call with customer metadata
participant, room_name = await make_outbound_call(
    phone_number="+1234567890",
    customer_name="John Doe",
    survey_config={"survey_type": "satisfaction"},
    prep_goal="JEE",
    current_plan="Plus"
)

print(f"Call initiated in room: {room_name}")
```

### Making a Simple Call

```python
from call_utils.make_call import make_simple_call

# Make a basic call without survey metadata
participant = await make_simple_call(
    phone_number="+1234567890",
    participant_name="Test Caller"
)

print(f"Call SID: {participant.sip_call_id}")
```

### Batch Calling from CSV

```bash
python call_utils/batch_calls.py learners.csv --delay 300 --max-calls 10
```

CSV format:
```csv
phone_number,learner_name,time_to_call,prep_goal,current_plan
+1234567890,John Doe,09:30,JEE,Plus
+1987654321,Jane Smith,10:15,NEET,Iconic
```

### Using the OutboundCallManager Class

```python
from call_utils.make_call import OutboundCallManager

manager = OutboundCallManager()

try:
    # Create survey call with full control
    participant, room_name = await manager.create_survey_call(
        phone_number="+1234567890",
        customer_name="Alice Johnson",
        survey_config={
            "survey_type": "customer_satisfaction",
            "version": "2.0",
            "questions": [...]
        },
        customer_metadata={
            "prep_goal": "UPSC",
            "current_plan": "Free",
            "signup_date": "2024-01-15"
        }
    )
    
    print(f"Survey call created in room {room_name}")
    
finally:
    await manager.close()
```

## API Reference

### `make_outbound_call(phone_number, customer_name, survey_config=None, **kwargs)`

Creates an outbound call for survey purposes with full metadata support.

**Parameters:**
- `phone_number` (str): Phone number with country code (e.g., "+1234567890")
- `customer_name` (str): Name of the customer being called
- `survey_config` (dict, optional): Survey configuration data
- `**kwargs`: Additional customer metadata (prep_goal, current_plan, etc.)

**Returns:**
- `tuple[SIPParticipantInfo, str]`: Participant info and room name

### `make_simple_call(phone_number, room_name=None, participant_name=None)`

Creates a simple outbound call without survey-specific metadata.

**Parameters:**
- `phone_number` (str): Phone number with country code
- `room_name` (str, optional): Custom room name
- `participant_name` (str, optional): Custom participant name

**Returns:**
- `SIPParticipantInfo`: LiveKit SIP participant information

### `OutboundCallManager`

Class for managing outbound calls with advanced configuration.

**Methods:**
- `create_survey_call()`: Create a survey call with metadata
- `create_simple_call()`: Create a basic call
- `close()`: Close the LiveKit API connection

## Integration with Survey Agent

The outbound call utilities are designed to work seamlessly with your survey agent:

1. **Metadata Flow**: Customer data from CSV → Call metadata → Agent context
2. **Room Management**: Automatic room creation and cleanup
3. **Error Handling**: Robust error handling with logging
4. **Dispatch Integration**: Works with LiveKit's agent dispatch system

### Example Integration

```python
# In your survey agent entrypoint
async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    
    # Extract metadata from the outbound call
    metadata = json.loads(ctx.job.metadata) if ctx.job.metadata else {}
    
    customer_name = metadata.get("customer_name", "valued customer")
    prep_goal = metadata.get("prep_goal")
    current_plan = metadata.get("current_plan")
    
    # Use metadata to personalize the survey
    instructions = f"""
    You are speaking with {customer_name}.
    They are preparing for {prep_goal} and have a {current_plan} plan.
    Conduct the survey with this context in mind.
    """
    
    # Continue with agent setup...
```

## Error Handling

The utilities include comprehensive error handling:

- **Environment Validation**: Checks for required environment variables
- **Phone Number Validation**: Ensures proper format with country codes
- **API Error Handling**: Catches and logs LiveKit API errors
- **Graceful Failures**: Continues processing other calls if one fails

## Monitoring and Logging

All utilities include structured logging:

```python
import logging

# Configure logging level
logging.basicConfig(level=logging.INFO)

# The utilities will log:
# - Call initiation attempts
# - Success/failure status
# - Room names and participant IDs
# - Error details for troubleshooting
```

## Best Practices

1. **Rate Limiting**: Use appropriate delays between calls (default: 300 seconds)
2. **Error Handling**: Always wrap calls in try-catch blocks
3. **Resource Management**: Close OutboundCallManager instances properly
4. **Phone Validation**: Ensure phone numbers include country codes
5. **Environment Security**: Keep API keys secure in environment variables
6. **Testing**: Use the test script to verify setup before production use

## Troubleshooting

### Common Issues

1. **Missing SIP_TRUNK_ID**
   ```
   Solution: Get trunk ID with: lk sip outbound list
   ```

2. **Invalid Phone Number Format**
   ```
   Solution: Ensure format is +[country_code][number] (e.g., +1234567890)
   ```

3. **Agent Not Connecting**
   ```
   Solution: Verify agent is running with correct agent_name
   ```

4. **Call Fails Immediately**
   ```
   Solution: Check SIP trunk configuration and phone number validity
   ```

### Getting Help

- Check LiveKit documentation: https://docs.livekit.io/agents/
- Verify SIP trunk setup: https://docs.livekit.io/sip/
- Test with the provided test script first
- Enable debug logging for detailed error information

## License

This utility is part of the LiveKit Survey Agent project. 