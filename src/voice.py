"""Synthèse vocale via Edge-TTS.

Edge-TTS v7+ ne renvoie plus de WordBoundary, seulement des SentenceBoundary.
On reconstruit les timings mot-à-mot en distribuant proportionnellement
la durée de chaque phrase sur ses mots (pondéré par la longueur des mots).
"""
import asyncio
import re
from pathlib import Path

import edge_tts

from src.config import VOICE, VOICE_RATE


def _split_words(sentence: str) -> list[str]:
    """Découpe une phrase en mots, ponctuation collée au mot précédent."""
    words = re.findall(r"\S+", sentence.strip())
    return [w for w in words if w]


def _distribute_word_timings(
    sentence: str, sent_start: float, sent_duration: float
) -> list[dict]:
    """Pour une phrase, renvoie une liste de mots avec start/end estimés.

    Pondère par la longueur du mot pour que les longs mots aient plus de temps.
    """
    words = _split_words(sentence)
    if not words:
        return []

    weights = [max(1, len(re.sub(r"[^\wÀ-ÿ]", "", w))) for w in words]
    total_w = sum(weights)
    if total_w == 0:
        return []

    items: list[dict] = []
    cursor = sent_start
    for w, weight in zip(words, weights):
        dur = sent_duration * (weight / total_w)
        items.append({"word": w, "start": cursor, "end": cursor + dur})
        cursor += dur
    return items


def assemble_narration(scenes_narrations: list[str]) -> str:
    """Joint les phrases avec ponctuation forte + saut de ligne pour pauses TTS."""
    cleaned: list[str] = []
    for n in scenes_narrations:
        n = n.strip()
        if not n:
            continue
        if n[-1] not in ".!?":
            n += "."
        cleaned.append(n)
    # Double newline = pause naturelle plus longue dans Edge-TTS
    return "\n\n".join(cleaned)


async def _synthesize(text: str, audio_path: Path) -> list[dict]:
    communicate = edge_tts.Communicate(text=text, voice=VOICE, rate=VOICE_RATE)
    word_items: list[dict] = []
    with audio_path.open("wb") as f:
        async for chunk in communicate.stream():
            t = chunk["type"]
            if t == "audio":
                f.write(chunk["data"])
            elif t == "SentenceBoundary":
                start = chunk["offset"] / 1e7
                dur = chunk["duration"] / 1e7
                word_items.extend(_distribute_word_timings(chunk["text"], start, dur))
            elif t == "WordBoundary":
                # cas rare où WordBoundary marche encore
                start = chunk["offset"] / 1e7
                dur = chunk["duration"] / 1e7
                word_items.append({
                    "word": chunk["text"], "start": start, "end": start + dur
                })
    return word_items


def synthesize(text: str, audio_path: Path) -> list[dict]:
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    return asyncio.run(_synthesize(text, audio_path))
