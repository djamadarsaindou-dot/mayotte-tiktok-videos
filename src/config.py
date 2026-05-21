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

# Dossier final où l'utilisateur retrouve ses vidéos finies (hors du projet).
# Configurable via FINAL_VIDEOS_DIR dans .env. Si absent : ~/Videos/Mayotte TikTok
_default_final = Path.home() / "Videos" / "Mayotte TikTok"
FINAL_VIDEOS_DIR = Path(os.getenv("FINAL_VIDEOS_DIR", str(_default_final)))

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

# Voice cloning : si ce fichier WAV existe, XTTS clone CETTE voix au lieu
# d'utiliser le speaker intégré (qui a un accent anglo). reference_fr.wav =
# échantillon de voix française métropolitaine native.
COQUI_SPEAKER_WAV = ASSETS_DIR / "voice" / "reference_fr.wav"

# Réglages fins XTTS (qualité + style de la synthèse)
# Style "vulgarisation dynamique" : débit rapide, intonations marquées
COQUI_TEMPERATURE = float(os.getenv("COQUI_TEMPERATURE", "0.74"))
COQUI_REPETITION_PENALTY = float(os.getenv("COQUI_REPETITION_PENALTY", "3.0"))
COQUI_LENGTH_PENALTY = float(os.getenv("COQUI_LENGTH_PENALTY", "1.0"))
COQUI_TOP_K = int(os.getenv("COQUI_TOP_K", "50"))
COQUI_TOP_P = float(os.getenv("COQUI_TOP_P", "0.85"))
COQUI_SPEED = float(os.getenv("COQUI_SPEED", "1.0"))  # 1.0=naturel (>1 robotise)

# Cible : 100-115s de narration (entre 1min30 et 2min — zone monétisable TikTok)
# Mesuré : ~2.8 mots/s (Coqui -3%) → 12 scènes × ~26 mots ≈ 310 mots ≈ 110s
TARGET_WORDS_MIN = 290
TARGET_WORDS_MAX = 360

# Découpage visuel : 12 scènes × 4 visuels = 48 clips
# Pour ~110s d'audio → ~2.3s par clip (objectif "coupe ≤ 2.5s")
VISUAL_MAX_DURATION = 2.5
VISUALS_PER_SCENE = 4
NUM_SCENES = 12

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
# Pollinations a introduit un paywall (HTTP 402) en mai 2026. Mettre à "false"
# pour ne même pas le tenter (100% stock, génération bien plus rapide).
# Si "true" : on tente, mais un circuit breaker coupe Pollinations dès le
# premier 402 du run (les images suivantes passent direct en stock).
POLLINATIONS_ENABLED = os.getenv("POLLINATIONS_ENABLED", "true").strip().lower() == "true"
POLLINATIONS_MODEL = os.getenv("POLLINATIONS_MODEL", "flux").strip()
# Parallélisme 1 = séquentiel. Pollinations rate-limit dès qu'on passe à 2+ workers.
# En séquentiel, on a une image toutes les ~10-20s, soit ~15 min pour 64 images.
POLLINATIONS_PARALLEL = int(os.getenv("POLLINATIONS_PARALLEL", "4"))
# Nombre d'essais avant fallback stock (plus haut = qualité IA garantie mais plus long)
POLLINATIONS_MAX_RETRIES = int(os.getenv("POLLINATIONS_MAX_RETRIES", "6"))

# Nettoyage auto : garde les N vidéos les plus récentes
KEEP_LAST_N_VIDEOS = int(os.getenv("KEEP_LAST_N_VIDEOS", "50"))

# Auto-publication TikTok (mode INBOX = brouillon privé)
# Nécessite : TIKTOK_CLIENT_KEY + TIKTOK_CLIENT_SECRET + ACCESS_TOKEN + REFRESH_TOKEN
# Et avoir lancé scripts/setup_tiktok.py une fois
TIKTOK_AUTO_PUBLISH = os.getenv("TIKTOK_AUTO_PUBLISH", "false").strip().lower() == "true"


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
