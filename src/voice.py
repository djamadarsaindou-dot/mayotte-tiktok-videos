"""Synthèse vocale via Edge-TTS (Microsoft) — gratuit et illimité."""
import asyncio
from pathlib import Path

import edge_tts

from src.config import VOICE, VOICE_RATE


async def _synthesize(text: str, audio_path: Path, srt_path: Path) -> None:
    communicate = edge_tts.Communicate(text=text, voice=VOICE, rate=VOICE_RATE)
    submaker = edge_tts.SubMaker()
    with audio_path.open("wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
    srt_path.write_text(submaker.get_srt(), encoding="utf-8")


def synthesize(text: str, audio_path: Path, srt_path: Path) -> None:
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synthesize(text, audio_path, srt_path))
