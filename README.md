# agents-voice — 12th House AI
![Banner](../BRAND/banner.png)

## Overview
Starter toolkit for building a voice-forward agent on top of OpenAI's
Responses and Audio APIs. The package provides:

- Environment-driven configuration
- A reusable `VoiceAgent` conversation loop
- Command line utilities for quick experimentation
- Test coverage that demonstrates how to mock the LLM layer

## Setup
1. Create and fill a `.env` file:
   ```bash
   cp .env.example .env
   # edit .env to include your OpenAI key and optional overrides
   ```
2. Install dependencies (optionally with extra audio features):
   ```bash
   pip install -e .
   # or pip install -e .[audio] for microphone playback/recording
   ```

## Usage
### Environment variables
| Variable | Description | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | Required key used for all OpenAI requests | — |
| `AGENT_VOICE_RESPONSE_MODEL` | Model used for responses and TTS | `gpt-4o-mini` |
| `AGENT_VOICE_TRANSCRIPTION_MODEL` | Model used for speech-to-text | `gpt-4o-mini-transcribe` |
| `AGENT_VOICE_VOICE` | Name of the voice for synthesis | `verse` |
| `AGENT_VOICE_HISTORY_LIMIT` | Maximum stored conversation turns | `6` |

### Python
```python
from agents_voice import VoiceAgent, VoiceAgentSettings

settings = VoiceAgentSettings.from_env()
agent = VoiceAgent(settings)
turn = agent.handle_text("Tell me a short bedtime story")
print(turn.assistant_text)
```

### CLI
```bash
python -m agents_voice.cli "Summarize the meeting notes"
# optionally save speech to disk
python -m agents_voice.cli "Summarize the meeting" --save-audio reply.wav
```

## Development
- Run tests with `pytest`
- Use the dummy client in `tests/test_agent.py` as a template when mocking
  the OpenAI client for integration tests

## Roadmap
- Add microphone capture helpers
- Provide streaming/Realtime API integration
- Package launch scripts for different operating systems
