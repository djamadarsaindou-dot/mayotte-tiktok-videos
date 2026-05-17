"""Mastering audio de la voix off via FFmpeg.

Transforme une voix TTS « brute » en voix « radio » : présente, claire, sans
grondement ni boue, à un volume normalisé pour les plateformes sociales.

Chaîne :
- highpass 80 Hz       : enlève le grondement / souffle basse fréquence
- afftdn               : débruitage léger (artefacts TTS)
- EQ -2 dB @ 300 Hz    : enlève la « boue » des bas-médiums
- EQ +3 dB @ 3 kHz     : présence / clarté de la voix
- acompressor          : compression douce → voix dense et constante
- loudnorm -14 LUFS    : volume normalisé (cible réseaux sociaux)
"""
import subprocess
from pathlib import Path

from src.config import FFMPEG

# Chaîne de filtres pour la voix finale (mixée dans la vidéo)
VOICE_MASTER_CHAIN = (
    "highpass=f=80,"
    "afftdn=nr=12:nf=-25,"
    "equalizer=f=300:t=q:w=1.4:g=-2,"
    "equalizer=f=3000:t=q:w=1.6:g=3,"
    "acompressor=threshold=-20dB:ratio=3:attack=10:release=150,"
    "loudnorm=I=-14:TP=-1.5:LRA=11"
)

# Chaîne plus douce pour nettoyer un échantillon de référence (voice cloning) :
# on débruite et on normalise, mais sans compresser (XTTS préfère un timbre naturel).
SAMPLE_CLEAN_CHAIN = (
    "highpass=f=75,"
    "afftdn=nr=10:nf=-25,"
    "loudnorm=I=-18:TP=-2:LRA=11"
)


def _run(cmd: list[str], label: str) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-800:])
        raise RuntimeError(f"FFmpeg {label} a échoué (code {result.returncode})")


def master_voice(audio_path: Path) -> Path:
    """Masterise la voix en place (remplace le fichier par sa version masterisée)."""
    tmp = audio_path.with_name(audio_path.stem + "_master" + audio_path.suffix)
    cmd = [
        FFMPEG, "-y", "-i", str(audio_path),
        "-af", VOICE_MASTER_CHAIN,
        "-codec:a", "libmp3lame", "-q:a", "2",
        str(tmp),
    ]
    _run(cmd, "mastering voix")
    tmp.replace(audio_path)
    return audio_path


def clean_sample(input_path: Path, output_path: Path) -> Path:
    """Nettoie un échantillon de voix de référence (pour le voice cloning)."""
    cmd = [
        FFMPEG, "-y", "-i", str(input_path),
        "-af", SAMPLE_CLEAN_CHAIN,
        "-ar", "22050", "-ac", "1",  # mono 22 kHz : format attendu par XTTS
        str(output_path),
    ]
    _run(cmd, "nettoyage échantillon")
    return output_path
