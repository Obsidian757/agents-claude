from __future__ import annotations

import pytest

from agents_voice.settings import VoiceAgentSettings


def test_from_env_requires_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        VoiceAgentSettings.from_env()


def test_from_env_uses_prefix(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "abc")
    monkeypatch.setenv("AGENT_VOICE_RESPONSE_MODEL", "gpt-test")
    monkeypatch.setenv("AGENT_VOICE_TRANSCRIPTION_MODEL", "gpt-transcribe")
    monkeypatch.setenv("AGENT_VOICE_VOICE", "alloy")
    monkeypatch.setenv("AGENT_VOICE_HISTORY_LIMIT", "12")

    settings = VoiceAgentSettings.from_env()
    assert settings.response_model == "gpt-test"
    assert settings.transcription_model == "gpt-transcribe"
    assert settings.voice == "alloy"
    assert settings.history_limit == 12


def test_from_env_custom_prefix(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "abc")
    monkeypatch.setenv("CUSTOM_RESPONSE_MODEL", "model")

    settings = VoiceAgentSettings.from_env(prefix="CUSTOM")
    assert settings.response_model == "model"
