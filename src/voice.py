"""Synthèse vocale avec dispatch entre Edge-TTS et Coqui XTTS v2.

TTS_PROVIDER=edge   → Edge-TTS (rapide, synthétique, défaut)
TTS_PROVIDER=coqui  → Coqui XTTS v2 (lent CPU, voix humaine)

API publique :
- assemble_narration(scenes_narrations) : joint avec ponctuation/sauts pour pauses TTS
- synthesize(text, audio_path) : génère le MP3 et renvoie les timings mot-à-mot
"""
import asyncio
import re
from pathlib import Path

from src.config import TTS_PROVIDER, VOICE, VOICE_RATE


def _split_words(sentence: str) -> list[str]:
    return [w for w in re.findall(r"\S+", sentence.strip()) if w]


def _distribute_word_timings(sentence: str, sent_start: float, sent_duration: float) -> list[dict]:
    words = _split_words(sentence)
    if not words:
        return []
    weights = [max(1, len(re.sub(r"[^\wÀ-ÿ]", "", w))) for w in words]
    total = sum(weights)
    items: list[dict] = []
    cursor = sent_start
    for w, weight in zip(words, weights):
        d = sent_duration * (weight / total)
        items.append({"word": w, "start": cursor, "end": cursor + d})
        cursor += d
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
    return "\n\n".join(cleaned)


# --- Edge-TTS ---

async def _edge_synthesize(text: str, audio_path: Path) -> list[dict]:
    import edge_tts
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
                start = chunk["offset"] / 1e7
                dur = chunk["duration"] / 1e7
                word_items.append({"word": chunk["text"], "start": start, "end": start + dur})
    return word_items


def _synthesize_edge(text: str, audio_path: Path) -> list[dict]:
    return asyncio.run(_edge_synthesize(text, audio_path))


# --- Dispatch ---

def synthesize(text: str, audio_path: Path) -> list[dict]:
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    if TTS_PROVIDER == "coqui":
        try:
            from src.voice_coqui import synthesize as coqui_synthesize
            return coqui_synthesize(text, audio_path)
        except Exception as e:
            print(f"   ⚠️  Coqui a échoué ({str(e)[:120]}) — fallback Edge-TTS")
            return _synthesize_edge(text, audio_path)
    return _synthesize_edge(text, audio_path)
