"""Configuration helpers for the voice agent."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional


@dataclass(slots=True)
class VoiceAgentSettings:
    """Configuration values required by :class:`~agents_voice.agent.VoiceAgent`."""

    openai_api_key: str
    transcription_model: str = "gpt-4o-mini-transcribe"
    response_model: str = "gpt-4o-mini"
    voice: str = "verse"
    history_limit: int = 6

    @classmethod
    def from_env(cls, prefix: str = "AGENT_VOICE") -> "VoiceAgentSettings":
        """Create settings from environment variables.

        Parameters
        ----------
        prefix:
            Optional prefix to allow multiple agents to co-exist. The method
            expects the following variables to be present::

                OPENAI_API_KEY
                <prefix>_TRANSCRIPTION_MODEL (optional)
                <prefix>_RESPONSE_MODEL (optional)
                <prefix>_VOICE (optional)
                <prefix>_HISTORY_LIMIT (optional)
        """

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required but was not found in the environment"
            )

        def _get(name: str, default: Optional[str] = None) -> Optional[str]:
            return os.getenv(f"{prefix}_{name}", default)

        history_limit_str = _get("HISTORY_LIMIT")
        history_limit = int(history_limit_str) if history_limit_str else 6

        return cls(
            openai_api_key=api_key,
            transcription_model=_get("TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"),
            response_model=_get("RESPONSE_MODEL", "gpt-4o-mini"),
            voice=_get("VOICE", "verse"),
            history_limit=history_limit,
        )


__all__ = ["VoiceAgentSettings"]
