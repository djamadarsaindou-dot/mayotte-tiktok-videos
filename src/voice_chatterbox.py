"""Backend voix Chatterbox Multilingual (Resemble AI) — choisi à l'oreille
par l'utilisateur le 2026-07-03 (échantillon « expressif » : exaggeration 0.8).

Clone la même voix de référence que XTTS (COQUI_SPEAKER_WAV) mais avec une
prosodie plus expressive. GPU requis en pratique (RTF ~0.84 sur RTX 5060,
~3.5 Go VRAM). Sortie filigranée de façon inaudible (resemble-perth, défaut).

Même contrat que voice_coqui.synthesize : MP3 + timings mot-à-mot (estimés
puis raffinés par l'alignement Whisper de src/word_align.py).
"""
import os
import subprocess
import wave
from pathlib import Path

import numpy as np

# La barre « Sampling » de chatterbox noierait les logs du cron
os.environ.setdefault("TQDM_DISABLE", "1")

from src.config import (
    COQUI_LANGUAGE,
    COQUI_SPEAKER_WAV,
    FFMPEG,
)

# Réglages du rendu « expressif » validé à l'écoute (test_G_chatterbox_expressif)
CHATTERBOX_EXAGGERATION = float(os.getenv("CHATTERBOX_EXAGGERATION", "0.8"))
CHATTERBOX_CFG_WEIGHT = float(os.getenv("CHATTERBOX_CFG_WEIGHT", "0.4"))
CHATTERBOX_TEMPERATURE = float(os.getenv("CHATTERBOX_TEMPERATURE", "0.8"))

_model = None


def _get_model():
    global _model
    if _model is None:
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"   ⏳ Chargement modèle Chatterbox multilingue sur {device} "
              "(3 Go, lent au 1er run)...")
        _model = ChatterboxMultilingualTTS.from_pretrained(device=device)
    return _model


def _save_wav(path: Path, tensor, sample_rate: int) -> None:
    """Sauvegarde via le module wave stdlib (torchaudio/torchcodec cassés ici)."""
    arr = tensor.squeeze().detach().cpu().numpy()
    arr = np.clip(arr, -1.0, 1.0)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes((arr * 32767.0).astype(np.int16).tobytes())


def synthesize(text: str, audio_path: Path) -> list[dict]:
    """Synthétise le texte en MP3 avec Chatterbox. Renvoie les timings mot-à-mot."""
    # Réutilise le découpage/sanitisation et les utilitaires éprouvés de Coqui
    from src.voice_coqui import (
        _distribute_word_timings,
        _ffprobe_duration,
        _split_sentences,
        _wav_to_mp3,
    )

    audio_path.parent.mkdir(parents=True, exist_ok=True)
    if not COQUI_SPEAKER_WAV.exists():
        raise FileNotFoundError(
            f"Échantillon de clonage absent : {COQUI_SPEAKER_WAV}")

    model = _get_model()

    sentences = _split_sentences(text)
    if not sentences:
        sentences = [text.strip()]

    work_dir = audio_path.parent / "chatterbox_chunks"
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"   🎤 Synthèse Chatterbox [clone FR ({COQUI_SPEAKER_WAV.name}), "
          f"exaggeration={CHATTERBOX_EXAGGERATION}, {len(sentences)} phrases]...")

    chunk_paths: list[Path] = []
    chunk_durations: list[float] = []
    for i, sent in enumerate(sentences):
        wav_tensor = model.generate(
            sent,
            language_id=COQUI_LANGUAGE,
            audio_prompt_path=str(COQUI_SPEAKER_WAV),
            exaggeration=CHATTERBOX_EXAGGERATION,
            cfg_weight=CHATTERBOX_CFG_WEIGHT,
            temperature=CHATTERBOX_TEMPERATURE,
        )
        wav = work_dir / f"chunk_{i:03d}.wav"
        _save_wav(wav, wav_tensor, model.sr)
        dur = _ffprobe_duration(wav)
        chunk_paths.append(wav)
        chunk_durations.append(dur)
        print(f"     [{i+1}/{len(sentences)}] {dur:.1f}s · {sent[:50]}...")

    concat_list = work_dir / "concat.txt"
    concat_list.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in chunk_paths),
        encoding="utf-8",
    )
    final_wav = work_dir / "final.wav"
    result = subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-c", "copy", str(final_wav)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg concat WAV a échoué : {result.stderr[-500:]}")
    _wav_to_mp3(final_wav, audio_path)

    word_items: list[dict] = []
    cursor = 0.0
    for sent, dur in zip(sentences, chunk_durations):
        word_items.extend(_distribute_word_timings(sent, cursor, dur))
        cursor += dur

    for p in chunk_paths + [final_wav, concat_list]:
        try:
            p.unlink()
        except Exception:
            pass

    # Alignement Whisper : timings réels (±20-100 ms). Jamais bloquant.
    try:
        from src.word_align import align_words
        word_items = align_words(audio_path, " ".join(sentences), word_items)
    except Exception as e:
        print(f"   ⚠️  Alignement Whisper indisponible ({str(e)[:80]}) — timings estimés")

    return word_items
