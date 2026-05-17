"""Backend voix Coqui XTTS v2 — voix beaucoup plus humaine, plus lent que Edge-TTS.

Génère un WAV puis convertit en MP3 via FFmpeg. Les timings mot-à-mot sont
estimés en distribuant la durée totale audio sur les mots de chaque phrase
(pondéré par la longueur des mots).
"""
import os
import re
import subprocess
from pathlib import Path

# Shim avant import TTS
from src import _coqui_shim  # noqa: F401

os.environ.setdefault("COQUI_TOS_AGREED", "1")

from src.config import (  # noqa: E402
    COQUI_LANGUAGE,
    COQUI_LENGTH_PENALTY,
    COQUI_REPETITION_PENALTY,
    COQUI_SPEAKER,
    COQUI_SPEAKER_WAV,
    COQUI_SPEED,
    COQUI_TEMPERATURE,
    COQUI_TOP_K,
    COQUI_TOP_P,
    FFMPEG,
)

_tts = None


def _get_tts():
    global _tts
    if _tts is None:
        from TTS.api import TTS
        print("   ⏳ Chargement modèle XTTS v2 (lent au 1er run)...")
        _tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    return _tts


SENTENCE_SPLIT = re.compile(r"(?<=[\.\!\?])\s+")
WORD_RE = re.compile(r"\S+")


def _split_sentences(text: str) -> list[str]:
    parts = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
    return parts


def _ffprobe_duration(audio_path: Path) -> float:
    p = Path(FFMPEG)
    ffprobe = str(p.with_name(p.name.replace("ffmpeg", "ffprobe", 1)))
    out = subprocess.check_output(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        text=True,
    )
    return float(out.strip())


def _wav_to_mp3(wav_path: Path, mp3_path: Path) -> None:
    cmd = [FFMPEG, "-y", "-i", str(wav_path),
           "-codec:a", "libmp3lame", "-q:a", "2", str(mp3_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion WAV→MP3 a échoué : {result.stderr[-500:]}")


def _distribute_word_timings(sentence: str, start: float, duration: float) -> list[dict]:
    words = WORD_RE.findall(sentence)
    if not words:
        return []
    weights = [max(1, len(re.sub(r"[^\wÀ-ÿ]", "", w))) for w in words]
    total = sum(weights)
    items: list[dict] = []
    cursor = start
    for w, weight in zip(words, weights):
        d = duration * (weight / total)
        items.append({"word": w, "start": cursor, "end": cursor + d})
        cursor += d
    return items


def synthesize(text: str, audio_path: Path) -> list[dict]:
    """Synthétise le texte en MP3 avec Coqui XTTS v2.

    Renvoie la liste des mots avec timings (estimés par distribution proportionnelle
    sur chaque phrase). Les pauses entre phrases reflètent le silence naturel généré.
    """
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    tts = _get_tts()

    # Découpage en phrases pour avoir des timings de phrase précis
    sentences = _split_sentences(text)
    if not sentences:
        sentences = [text.strip()]

    # On génère phrase par phrase puis on concatène (pour avoir les durées par phrase)
    work_dir = audio_path.parent / "coqui_chunks"
    work_dir.mkdir(parents=True, exist_ok=True)

    chunk_paths: list[Path] = []
    chunk_durations: list[float] = []

    # Voice cloning : si l'échantillon français existe, on clone cette voix.
    # Sinon, fallback sur le speaker intégré (accent anglo).
    use_clone = COQUI_SPEAKER_WAV.exists()
    speaker_kwargs = (
        {"speaker_wav": str(COQUI_SPEAKER_WAV)} if use_clone
        else {"speaker": COQUI_SPEAKER}
    )
    voix_label = "clone FR (reference_fr.wav)" if use_clone else COQUI_SPEAKER
    print(f"   🎤 Synthèse Coqui XTTS v2 [{voix_label}, {len(sentences)} phrases]...")

    for i, sent in enumerate(sentences):
        wav = work_dir / f"chunk_{i:03d}.wav"
        tts.tts_to_file(
            text=sent,
            language=COQUI_LANGUAGE,
            file_path=str(wav),
            temperature=COQUI_TEMPERATURE,
            repetition_penalty=COQUI_REPETITION_PENALTY,
            length_penalty=COQUI_LENGTH_PENALTY,
            top_k=COQUI_TOP_K,
            top_p=COQUI_TOP_P,
            speed=COQUI_SPEED,
            **speaker_kwargs,
        )
        dur = _ffprobe_duration(wav)
        chunk_paths.append(wav)
        chunk_durations.append(dur)
        print(f"     [{i+1}/{len(sentences)}] {dur:.1f}s · {sent[:50]}...")

    # Concatène les WAV en un seul MP3
    concat_list = work_dir / "concat.txt"
    concat_list.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in chunk_paths),
        encoding="utf-8",
    )

    final_wav = work_dir / "final.wav"
    cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
           "-c", "copy", str(final_wav)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg concat WAV a échoué : {result.stderr[-500:]}")

    _wav_to_mp3(final_wav, audio_path)

    # Construit les timings mot-à-mot
    word_items: list[dict] = []
    cursor = 0.0
    for sent, dur in zip(sentences, chunk_durations):
        word_items.extend(_distribute_word_timings(sent, cursor, dur))
        cursor += dur

    # Cleanup chunks (on garde le mp3 final)
    for p in chunk_paths + [final_wav, concat_list]:
        try:
            p.unlink()
        except Exception:
            pass

    return word_items
