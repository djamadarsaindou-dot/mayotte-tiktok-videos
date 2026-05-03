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

# --- Voix ---
# TTS_PROVIDER : "edge" (rapide, synthétique) ou "coqui" (lent CPU, voix humaine)
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge").strip().lower()

# Edge-TTS (Microsoft, gratuit, rapide)
VOICE = os.getenv("EDGE_VOICE", "fr-FR-HenriNeural").strip()
VOICE_RATE = os.getenv("EDGE_RATE", "-3%").strip()

# Coqui XTTS v2 (téléchargement modèle ~1.8 GB la 1ère fois, voix beaucoup plus humaine)
COQUI_SPEAKER = os.getenv("COQUI_SPEAKER", "Damien Black").strip()
COQUI_LANGUAGE = os.getenv("COQUI_LANGUAGE", "fr").strip()

# Cible : ~130 secondes de narration (2min+)
TARGET_WORDS_MIN = 380
TARGET_WORDS_MAX = 460

# Découpage visuel : on veut une coupe toutes les ~2.5s max
VISUAL_MAX_DURATION = 3.0
VISUALS_PER_SCENE = 3
NUM_SCENES = 16

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# Gemini (gratuit avec quota, indisponible à Mayotte côté local)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# Mistral (français, dispo partout — recommandé)
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest").strip()

# Choix du provider : "auto" → Mistral > Gemini > Groq selon les clés
# Forcer un provider précis : "mistral", "gemini", "groq"
# Note : valeur vide = auto (cas GitHub Actions où secret non défini = "")
LLM_PROVIDER = (os.getenv("LLM_PROVIDER", "auto").strip().lower() or "auto")

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "").strip()

# --- Visuels ---
# VISUAL_PROVIDER : "ai_first" (Pollinations IA prioritaire, corrélation forte avec
# le texte) ou "stock_first" (Pexels d'abord, plus rapide mais générique)
VISUAL_PROVIDER = os.getenv("VISUAL_PROVIDER", "ai_first").strip().lower()
POLLINATIONS_MODEL = os.getenv("POLLINATIONS_MODEL", "flux").strip()
POLLINATIONS_PARALLEL = int(os.getenv("POLLINATIONS_PARALLEL", "2"))

# Nettoyage auto : garde les N vidéos les plus récentes
KEEP_LAST_N_VIDEOS = int(os.getenv("KEEP_LAST_N_VIDEOS", "50"))


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
