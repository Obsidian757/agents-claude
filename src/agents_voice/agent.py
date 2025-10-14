"""High level abstractions for building a voice-forward agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Protocol

from .settings import VoiceAgentSettings

try:  # pragma: no cover - optional dependency
    from openai import OpenAI
except Exception:  # pragma: no cover - import guard for environments without openai
    OpenAI = None  # type: ignore


class SupportsLLMResponse(Protocol):
    """Protocol describing the minimal LLM client interface."""

    def respond(self, *, prompt: str, history: Iterable[dict[str, str]]) -> str:
        ...

    def synthesize(self, *, text: str, voice: str) -> bytes:
        ...

    def transcribe(self, *, audio: bytes, mime_type: str) -> str:
        ...


@dataclass(slots=True)
class VoiceAgentTurn:
    """Container describing a single interaction with the agent."""

    user_text: str
    assistant_text: str
    audio_bytes: bytes | None = None


@dataclass
class VoiceAgent:
    """Drive a conversational loop with text and audio modalities."""

    settings: VoiceAgentSettings
    client: SupportsLLMResponse | None = None
    _history: List[dict[str, str]] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.client is None:
            self.client = self._default_client()

    # ------------------------------------------------------------------
    def _default_client(self) -> SupportsLLMResponse:
        if OpenAI is None:  # pragma: no cover - executed only without dependency
            raise RuntimeError(
                "openai package is required for the default client but is not installed"
            )
        return _OpenAIClient(self.settings)

    # ------------------------------------------------------------------
    def handle_text(self, user_text: str) -> VoiceAgentTurn:
        """Add a text turn and request an assistant reply."""

        user_text = user_text.strip()
        if not user_text:
            raise ValueError("user_text cannot be empty")

        self._history.append({"role": "user", "content": user_text})
        response_text = self.client.respond(prompt=user_text, history=self._history)
        self._history.append({"role": "assistant", "content": response_text})

        audio_bytes = None
        try:
            audio_bytes = self.client.synthesize(
                text=response_text, voice=self.settings.voice
            )
        except NotImplementedError:
            audio_bytes = None

        return VoiceAgentTurn(
            user_text=user_text, assistant_text=response_text, audio_bytes=audio_bytes
        )

    # ------------------------------------------------------------------
    def handle_audio(self, audio: bytes, *, mime_type: str = "audio/wav") -> VoiceAgentTurn:
        """Process raw audio bytes by transcribing before responding."""

        user_text = self.client.transcribe(audio=audio, mime_type=mime_type)
        return self.handle_text(user_text)

    # ------------------------------------------------------------------
    @property
    def history(self) -> List[dict[str, str]]:
        """Return a shallow copy of the current conversation history."""

        return list(self._history)


class _OpenAIClient:
    """Minimal wrapper around ``openai`` covering the features we use."""

    def __init__(self, settings: VoiceAgentSettings) -> None:
        if OpenAI is None:  # pragma: no cover - import guard
            raise RuntimeError("openai package is required to use _OpenAIClient")

        self._settings = settings
        self._client = OpenAI(api_key=settings.openai_api_key)

    def respond(self, *, prompt: str, history: Iterable[dict[str, str]]) -> str:
        messages = [dict(item) for item in history]
        if not messages or messages[-1]["content"] != prompt:
            messages.append({"role": "user", "content": prompt})

        response = self._client.responses.create(
            model=self._settings.response_model,
            input=[
                {
                    "role": item["role"],
                    "content": [
                        {
                            "type": "input_text",
                            "text": item["content"],
                        }
                    ],
                }
                for item in messages
            ],
        )
        content = response.output[0].content[0].text
        return content

    def synthesize(self, *, text: str, voice: str) -> bytes:
        audio = self._client.audio.speech.create(
            model=self._settings.response_model,
            voice=voice,
            input=text,
        )
        return audio.read()

    def transcribe(self, *, audio: bytes, mime_type: str) -> str:
        transcription = self._client.audio.transcriptions.create(
            model=self._settings.transcription_model,
            file=("input", audio, mime_type),
        )
        return transcription.text


__all__ = ["VoiceAgent", "VoiceAgentTurn"]
