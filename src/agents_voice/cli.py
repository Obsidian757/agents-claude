"""Command line helpers for experimenting with the voice agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agent import VoiceAgent
from .settings import VoiceAgentSettings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a sample voice agent loop")
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Hello! How can I help you today?",
        help="Initial user text to bootstrap the conversation",
    )
    parser.add_argument(
        "--history-limit",
        type=int,
        help="Override the maximum number of messages retained in the history",
    )
    parser.add_argument(
        "--save-audio",
        type=Path,
        help="Optional path to store the generated speech as a .wav file",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = VoiceAgentSettings.from_env()
    if args.history_limit is not None:
        settings.history_limit = args.history_limit

    agent = VoiceAgent(settings)
    turn = agent.handle_text(args.prompt)

    print(turn.assistant_text)

    if args.save_audio and turn.audio_bytes:
        args.save_audio.write_bytes(turn.audio_bytes)
        print(f"Saved synthesized speech to {args.save_audio}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
