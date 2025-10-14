from __future__ import annotations

from dataclasses import dataclass

import pytest

from agents_voice.agent import VoiceAgent, VoiceAgentTurn
from agents_voice.settings import VoiceAgentSettings


@dataclass
class _DummyClient:
    """Simple fake client for unit tests."""

    transcript: str | None = None

    def respond(self, *, prompt: str, history):
        return f"Echo: {prompt} ({len(list(history))} messages)"

    def synthesize(self, *, text: str, voice: str) -> bytes:
        return f"{voice}:{text}".encode()

    def transcribe(self, *, audio: bytes, mime_type: str) -> str:
        self.transcript = audio.decode()
        return self.transcript


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    return VoiceAgentSettings.from_env()


def test_handle_text_tracks_history(settings):
    agent = VoiceAgent(settings=settings, client=_DummyClient())

    turn1 = agent.handle_text("Hello")
    assert isinstance(turn1, VoiceAgentTurn)
    assert turn1.assistant_text.startswith("Echo: Hello")
    assert agent.history[-1]["role"] == "assistant"

    turn2 = agent.handle_text("How are you?")
    assert "How are you" in turn2.assistant_text
    assert len(agent.history) == 4


def test_handle_audio_transcribes_before_responding(settings):
    client = _DummyClient()
    agent = VoiceAgent(settings=settings, client=client)

    turn = agent.handle_audio(b"Say hi")
    assert turn.user_text == "Say hi"
    assert client.transcript == "Say hi"


def test_handle_text_rejects_empty_input(settings):
    agent = VoiceAgent(settings=settings, client=_DummyClient())

    with pytest.raises(ValueError):
        agent.handle_text("   ")
