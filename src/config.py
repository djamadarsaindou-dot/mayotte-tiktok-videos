"""Paramètres globaux du projet."""
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OUTPUT_DIR = ROOT / "output"
TEMP_DIR = OUTPUT_DIR / "temp"
ASSETS_DIR = ROOT / "assets"

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30

# Voix masculine française (Edge-TTS)
# Alternatives : fr-FR-RemyMultilingualNeural (moderne), fr-CA-ThierryNeural (canadien)
VOICE = "fr-FR-HenriNeural"
VOICE_RATE = "-3%"

# Cible : ~70 secondes de narration
TARGET_WORDS_MIN = 145
TARGET_WORDS_MAX = 190

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()


def find_ffmpeg() -> str:
    explicit = os.getenv("FFMPEG_PATH", "").strip()
    if explicit and Path(explicit).exists():
        return explicit
    found = shutil.which("ffmpeg")
    if found:
        return found
    candidates = list(Path(os.environ["LOCALAPPDATA"]).glob(
        "Microsoft/WinGet/Packages/Gyan.FFmpeg*/**/ffmpeg.exe"
    ))
    if candidates:
        return str(candidates[0])
    raise RuntimeError("FFmpeg introuvable. Installe-le ou renseigne FFMPEG_PATH dans .env")


FFMPEG = find_ffmpeg() if os.name == "nt" else "ffmpeg"
