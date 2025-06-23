# Vaani – Universal Agent for LiveKit Voice AI

## Intorduction

Vaani is a **configuration-driven voice-AI framework** built on top of the [LiveKit Agents](https://github.com/livekit/agents) SDK.  
Instead of hard-coding every interaction, you describe how your agent should behave in a single JSON file. Vaani loads that file, connects the dots (LLM, TTS, STT, VAD, RAG, tools, memory, etc.) and spins up a fully-working, production-ready voice agent.

## Features

* **Zero-code configuration** – change behaviour by editing JSON, no redeploys needed.  
* **Pluggable providers** – OpenAI, Deepgram, ElevenLabs, Sarvam, Pinecone & more.  
* **Built-in tool system** – extend the agent with Python async functions, exposed to the LLM.  
* **Realtime turn detection** – Silero VAD + optional LiveKit EOU model.  
* **RAG ready** – drop-in Pinecone + LlamaIndex retrieval pipeline.  
* **Conversation memory** – opt-in long-term memory backed by [Mem0](https://github.com/mem0-ai/mem0).  
* **Streamlit config builder** – point-and-click wizard to generate valid configs.  
* **Works everywhere** – macOS, Linux, Windows, Cloud, Docker.

## Requirements

* Python ≥ 3.9  
* A LiveKit Cloud project **or** self-hosted LiveKit server
* Livekit API keys  
* API keys for the providers you plan to use (OpenAI, Deepgram, Pinecone, …)  
* (Optional) `ffmpeg` installed locally for audio transcoding

## Setup

```bash
# 1. clone & cd
$ git clone https://github.com/your-org/vaani.git
$ cd vaani

# 2. create & activate venv
$ python -m venv .venv
$ source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. install in editable mode (+ extras)
$ pip install -e .[dev]

# 4. copy env template & add your keys
$ cp .env.example .env
```

Download the files
```bash
python main.py download-files
```

Run the default assistant in **dev** mode:

```bash
$ python main.py dev
```

The agent registers with LiveKit under the ID defined in `main.py` and is ready to accept calls.

## explain Agent configuration

Each agent is described by a single JSON conforming to `universalagent.core.AgentConfig`.  
Below is a minimal but complete example:

```json
{
  "agent_id": "demo_assistant",
  "name": "Demo Assistant",
  "description": "General purpose helper",

  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.7
  },

  "tts_config": { "provider": "deepgram" },
  "stt_config": { "provider": "deepgram", "language": "en" },

  "max_conversation_duration": 900,
  "silence_timeout": 15,
  "tools": ["end_call"],

  "rag_config": { "enabled": false },
  "memory_config": { "enabled": false }
}
```

Key sections:

| Section | Purpose |
|---------|---------|
| `agent_id` | Unique dispatch key used by LiveKit |
| `llm_config` / `tts_config` / `stt_config` | Chooses providers & models |
| `rag_config` | Toggles knowledge-retrieval pipeline |
| `memory_config` | Enables per-user memory & sets limits |
| `tools` | List of tool *names* exposed to the LLM |
| `max_conversation_duration` | Auto-hangup after N seconds |
| `silence_timeout` | Prompt the user after N seconds of silence |

Environment variables (see `.env.example`) hold the API keys so you can share config JSON without secrets.

## Default tools

The framework ships with a small but useful set of always-available tools:

| Tool | Description |
|------|-------------|
| `end_call` | Gracefully terminates the current LiveKit room & cleans up |

You can add your own by wrapping an `async def` with `ToolHolder`.

## RAG tools when rag enabled

When `rag_config.enabled == true` Vaani automatically registers **`search_knowledge_base`** powered by `LlamaIndexPineconeRagTool`. Just drop in your namepsace

Usage (inside the LLM):
```
#tool search_knowledge_base("what is the refund policy?")
```
The tool returns relevant chunks which are then weaved into the assistant response.

## Memory tools when memory enabled

Enabling `memory_config.enabled` adds two tools:

| Tool | Mode | Purpose |
|------|------|---------|
| `get_memory` | sync | Retrieve previous memories relevant to a query |
| `store_important_info` | fire-and-forget | Persist information the user reveals during the call |

When memory is enabled, at the end of the call the transcription is used to create both agent and user memories.
Memories are stored in Mem0 and automatically summarised when they exceed `summarize_threshold`.

## Example configs

* `example/configs/default.json` – simple assistant  
* `example/configs/clinic_receptionist.json` – appointment scheduling agent  
* `example/configs/survey_agent.json` – multi-question NPS survey with `record_answer` tool

Copy one of these, tweak, then launch with:
Start and Register the worker with livekit server
```bash
python main.py dev
```

Dispatch the agent:
```bash
lk dispatch create \
  --agent-name base_agent \ # This should match the agent name in worker options
  --metadata '{
    "agent_id": "clinic_receptionist",
    "call_id": "xyz-call-id",
    "customer_name": "",
    "customer_id": "xyz-cust-id", # this will be used to create memories about the caller
    "phone_number": "",
    }'
```

## configbuilder

A Streamlit app that lets non-developers design agents via a 4-step wizard, complete with real-time validation and provider auto-detection.

```bash
$ cd configbuilder/streamlit
$ pip install -r requirements.txt
$ streamlit run agent_config_builder.py
```

The generated JSON can be saved directly into the `example/configs` folder.

## Contrubuting

Pull requests are welcome! Please:
1. Fork & create a branch (`feature/my-feature`)
2. Submit the PR and fill in the template

## License

This project is released under the **MIT License** – see [`LICENSE`](LICENSE) for details.

## Support

* **Issues** – bug reports & feature requests on GitHub  
* **Discussions** – ask „how do I…?“ in the GitHub Discussions tab  
* **LiveKit Slack** – #voice-ai-agents channel for real-time help

## Related projects

* [LiveKit](https://github.com/livekit/livekit) – realtime audio/video infra  
* [LiveKit Agents](https://github.com/livekit/agents) – official agents SDK  
* [Mem0](https://github.com/mem0-ai/mem0) – vector-based memory store  
* [LlamaIndex](https://github.com/llama-index-research/llama_index) – data framework for RAG  
* [Pinecone](https://www.pinecone.io/) – vector database powering the RAG example  

## Future steps

The roadmap for Vaani includes several significant capabilities that are already under active development:

1. **Custom tools via OpenAPI / JSON Schema**  
   Allow tool authors to describe functions with a full *API spec*. The spec is surfaced to the LLM so it can reason about parameters, response shapes & error codes automatically—no manual prompt engineering required.

2. **Remote configuration server**  
   Allow the worker to fetch the agent config from a remote server using `agent_id` instead of searching in local files.

3. **MCP integration**  
   Add support for MCP which allows users to connect their tools following Model context protocol.

4. **Context enrichment from memory**  
   When `memory_config.enabled` is `true`, the start-up pipeline will query Mem0 for the caller's recent memories and automatically prepend them to the agent's *initial context* so the LLM starts the conversation fully informed.

Feel free to open discussions or issues if you'd like to shape any of these features.
