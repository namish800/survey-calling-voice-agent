# LiveKit Voice Survey Agent with Supabase Integration

A sophisticated voice agent built with LiveKit v1.0 for conducting automated surveys over phone calls. The agent now integrates with Supabase for dynamic survey configuration, learner management, and response storage.

## 🚀 Features

### Core Capabilities
- **Voice-based surveys** with natural conversation flow
- **Dynamic survey configuration** from Supabase database or metadata
- **Learner management** with automatic creation and tracking
- **Real-time response storage** in Supabase
- **Call logging and analytics** with comprehensive tracking
- **Flexible question types**: Yes/No, Numeric Rating, Multiple Choice, Free Text
- **Conditional branching** based on responses
- **Error handling** for busy users, callbacks, and opt-out requests

### Supabase Integration
- **Survey configurations** stored and retrieved from database
- **Learner profiles** with metadata and call history
- **Call logs** with status tracking and duration
- **Survey responses** with detailed analytics
- **Real-time analytics** views for reporting
- **Fallback support** for metadata-based configurations

### Natural Conversation Features
- **Empathetic responses** based on rating ranges
- **Smooth transitions** between questions
- **Error recovery** with clarification requests
- **Interruption handling** and context maintenance
- **Professional yet warm** tone throughout

## 🏗️ Architecture

### Database Schema (Supabase)
- **`survey_configs`** - Survey configurations as JSON
- **`learners`** - Contact information and metadata
- **`call_logs`** - Call attempts and outcomes
- **`survey_responses`** - Individual question responses
- **`survey_analytics`** - Aggregated statistics view
- **`learner_call_history`** - Complete call history view

### Agent Components
- **SurveyAgent** - Main agent class with conversation logic
- **SupabaseManager** - Database operations handler
- **Question/SurveyConfig** - Data models for survey structure
- **Function tools** - Record answers, handle callbacks, manage flow

## 📋 Prerequisites

- Python 3.8+
- LiveKit Cloud account or self-hosted instance
- Supabase project (provided: `voice-survey-platform`)
- SIP trunk provider (Twilio, Telnyx, etc.)
- API keys for:
  - LiveKit
  - OpenAI (for LLM)
  - ElevenLabs (for TTS/STT)
  - Supabase

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd livekit-voice-agents
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env_template.txt .env
   # Edit .env with your API keys
   ```

4. **Test Supabase integration**
   ```bash
   python test_supabase_integration.py
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# LiveKit Configuration
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=wss://your-project.livekit.cloud

# AI Provider Keys
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Supabase Configuration (pre-configured)
SUPABASE_URL=https://oeudjqbyynefajbrtqlu.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# SIP Configuration
SIP_TRUNK_ID=your_sip_trunk_id
```

### Survey Configuration Options

#### Option 1: Supabase Database (Recommended)
Store survey configurations in the `survey_configs` table:

```json
{
  "survey_name": "Customer Satisfaction Survey",
  "description": "Collect customer feedback",
  "questions": [
    {
      "id": "satisfaction",
      "text": "How satisfied are you with our service?",
      "type": "numeric_rating",
      "min_value": 1,
      "max_value": 5,
      "required": true
    }
  ]
}
```

#### Option 2: Metadata Configuration
Pass survey config directly in dispatch metadata:

```python
metadata = {
    "phone_number": "+1234567890",
    "customer_name": "John Doe",
    "survey_config": {
        "name": "Quick Survey",
        "questions": [...]
    }
}
```

#### Option 3: Survey Name Lookup
Reference existing survey by name:

```python
metadata = {
    "phone_number": "+1234567890",
    "customer_name": "John Doe",
    "survey_name": "Unacademy Learning Experience Survey"
}
```

## 🚀 Usage

### 1. Start the Agent

```bash
python survey_agent.py dev
```

### 2. Dispatch Survey Calls

#### Using the Dispatch Script
```bash
python dispatch_with_supabase.py
```

#### Using LiveKit CLI
```bash
lk dispatch create \
  --new-room \
  --agent-name SurveyAgent \
  --metadata '{"phone_number": "+1234567890", "customer_name": "John Doe", "survey_name": "Unacademy Learning Experience Survey"}'
```

#### Using Python API
```python
import asyncio
from dispatch_with_supabase import dispatch_survey_call

await dispatch_survey_call(
    phone_number="+1234567890",
    customer_name="John Doe",
    survey_name="Unacademy Learning Experience Survey",
    learner_metadata={"goal": "JEE", "subscription": "Plus"}
)
```

### 3. Monitor Results

#### View Call Logs
```sql
SELECT * FROM learner_call_history 
WHERE phone_number = '+1234567890' 
ORDER BY started_at DESC;
```

#### View Survey Analytics
```sql
SELECT * FROM survey_analytics;
```

#### Export Responses
```sql
SELECT 
    l.name,
    l.phone_number,
    sr.question_id,
    sr.question_text,
    sr.answer_value,
    sr.answered_at
FROM survey_responses sr
JOIN learners l ON sr.learner_id = l.id
WHERE sr.survey_config_id = 'your-survey-id'
ORDER BY sr.answered_at;
```

## 📊 Analytics and Reporting

### Built-in Views

1. **Survey Analytics** (`survey_analytics`)
   - Total calls per survey
   - Completion rates
   - Average call duration
   - Response counts

2. **Learner Call History** (`learner_call_history`)
   - Complete call timeline
   - Response counts per learner
   - Call outcomes and durations

### Custom Queries

```sql
-- Response distribution for rating questions
SELECT 
    question_id,
    answer_value,
    COUNT(*) as response_count
FROM survey_responses 
WHERE answer_type = 'numeric_rating'
GROUP BY question_id, answer_value
ORDER BY question_id, answer_value;

-- Daily call volume
SELECT 
    DATE(started_at) as call_date,
    COUNT(*) as total_calls,
    COUNT(CASE WHEN call_status = 'completed' THEN 1 END) as completed_calls
FROM call_logs 
GROUP BY DATE(started_at)
ORDER BY call_date DESC;
```

## 🔄 n8n Workflow Integration

The Supabase database is designed to work seamlessly with n8n workflows:

### Trigger Survey Calls
```javascript
// n8n HTTP Request Node
{
  "method": "POST",
  "url": "your-agent-endpoint/dispatch",
  "body": {
    "phone_number": "{{$json.phone}}",
    "customer_name": "{{$json.name}}",
    "survey_name": "Customer Satisfaction Survey",
    "learner_metadata": {
      "source": "n8n_workflow",
      "campaign_id": "{{$json.campaign_id}}"
    }
  }
}
```

### Monitor Call Status
```sql
-- n8n Supabase Node Query
SELECT call_status, ended_at 
FROM call_logs 
WHERE id = '{{$json.call_log_id}}';
```

### Process Responses
```sql
-- n8n Supabase Node Query
SELECT * FROM survey_responses 
WHERE call_log_id = '{{$json.call_log_id}}';
```

## 🧪 Testing

### Test Supabase Integration
```bash
python test_supabase_integration.py
```

### Test Survey Dispatch
```bash
python dispatch_with_supabase.py
```

### Manual Testing
1. Start the agent: `python survey_agent.py dev`
2. Use dispatch script to trigger a test call
3. Check Supabase tables for stored data
4. Review call logs and responses

## 📁 Project Structure

```
livekit-voice-agents/
├── survey_agent.py              # Main agent with Supabase integration
├── instructions.py              # Agent conversation instructions
├── dispatch_with_supabase.py    # Dispatch script with examples
├── test_supabase_integration.py # Supabase integration tests
├── requirements.txt             # Python dependencies
├── env_template.txt            # Environment variables template
├── supabase_config.md          # Supabase setup documentation
├── types/
│   └── supabase.ts            # TypeScript types for database
├── transcripts/               # Call transcripts (auto-generated)
└── README.md                  # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the [Supabase configuration](supabase_config.md)
2. Run the test script to verify setup
3. Review LiveKit agent logs
4. Check Supabase database for data consistency

## 🔮 Roadmap

- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Voice sentiment analysis
- [ ] Real-time call monitoring
- [ ] Automated callback scheduling
- [ ] Integration with CRM systems
- [ ] Advanced branching logic
- [ ] A/B testing for survey variations 