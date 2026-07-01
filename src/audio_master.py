"""Mastering audio de la voix off via FFmpeg.

Transforme une voix TTS « brute » (XTTS v2, ~24 kHz, sibilantes dures + un peu
de souffle) en voix « radio » : présente, claire, sans grondement ni boue.

Chaîne (audit + recherche juillet 2026) :
- aresample 48 kHz soxr : rééchantillonnage haute qualité 24 kHz → 48 kHz
- highpass 80 Hz (2 pôles) : enlève le grondement / souffle basse fréquence
- afftdn                : débruitage léger (souffle résiduel XTTS)
- deesser               : adoucit les sibilantes dures du TTS
- acompressor           : compression douce → voix dense et constante
- EQ -2 dB @ 250 Hz     : enlève la « boue » des bas-médiums
- EQ +2 dB @ 3 kHz      : présence / clarté de la voix
- treble +2 dB @ 7.5 kHz : « air » / brillance
- lowpass 10 kHz        : coupe le hash haute fréquence des artefacts TTS

NB : pas de loudnorm ici — la normalisation de volume est faite en aval dans
editor.py, sur le mix complet (voix + SFX).

Vérifié sur le build FFmpeg local (8.1 full, gyan.dev) : libsoxr et le filtre
deesser sont bien présents.
"""
import os
import subprocess
from pathlib import Path

from src.config import FFMPEG

# Paramètres clés du compresseur, surchargeables par variables d'environnement
# (valeurs recommandées par défaut, ne pas toucher config.py)
VOICE_COMP_THRESHOLD = os.getenv("VOICE_COMP_THRESHOLD", "-18dB").strip()
VOICE_COMP_RATIO = os.getenv("VOICE_COMP_RATIO", "3").strip()

# Chaîne de filtres pour la voix finale (mixée dans la vidéo)
VOICE_MASTER_CHAIN = (
    "aresample=48000:resampler=soxr,"
    "highpass=f=80:p=2,"
    "afftdn=nf=-25,"
    "deesser=i=0.4:m=0.5:f=0.5:s=o,"
    f"acompressor=threshold={VOICE_COMP_THRESHOLD}:ratio={VOICE_COMP_RATIO}:"
    "attack=10:release=150:makeup=4dB:knee=6,"
    "equalizer=f=250:t=q:w=1.0:g=-2,"
    "equalizer=f=3000:t=q:w=1.0:g=2,"
    "treble=g=2:f=7500,"
    "lowpass=f=10000:t=q:w=0.7"
)

# Nettoyage MINIMAL d'un échantillon de référence (voice cloning).
# Important : XTTS clone fidèlement ce qu'on lui donne. Tout filtre agressif
# (débruitage, EQ, compression) ALTÈRE le timbre de la voix → mauvaise copie.
# On se contente donc d'un highpass très bas (sub-grave parasite) + normalisation
# douce. Le timbre de la voix reste intact.
SAMPLE_CLEAN_CHAIN = (
    "highpass=f=55,"
    "loudnorm=I=-20:TP=-3:LRA=14"
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
        "-ar", "48000",  # garantit la sortie 48 kHz (déjà rééchantillonnée dans la chaîne)
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
