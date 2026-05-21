"""Trouve un asset visuel en essayant plusieurs sources.

Mode `ai_first` (défaut) : Pollinations IA → Pexels → Pixabay → Wikimedia
  → idéal pour des images en CORRÉLATION FORTE avec le texte.

Mode `stock_first` : Pexels vidéo → Pixabay vidéo → Wikimedia → Pollinations IA
  → plus rapide, contenu visuel plus générique.

Mode hybride utilisé par generate_video.py : 1er visuel de chaque scène en IA
  (ancre du sens), les autres en stock pour la rapidité. Deux fonctions sont
  exposées : `find_ai_asset` et `find_stock_asset`.
"""
import random
from pathlib import Path

from src.config import VISUAL_PROVIDER
from src.images import PollinationsUnavailable, generate_image
from src.stock_pixabay import search_photo as pixabay_photo
from src.stock_pixabay import search_video as pixabay_video
from src.stock_videos import search_photo as pexels_photo
from src.stock_videos import search_video as pexels_video
from src.stock_wikimedia import search_image as wikimedia_image


def _ai_generate(query: str, image_prompt_fallback: str, output_path: Path,
                 mayotte_specific: bool) -> Path:
    base = image_prompt_fallback or query
    suffix = ", cinematic, vertical 9:16, no text, photorealistic"
    if mayotte_specific and "mayotte" not in base.lower():
        prompt = f"{base}, Mayotte Indian Ocean French overseas department{suffix}"
    else:
        prompt = base + suffix
    seed = random.randint(1, 1_000_000)
    generate_image(prompt, output_path, seed=seed)
    return output_path


def find_asset(
    query: str,
    image_prompt_fallback: str,
    output_dir: Path,
    name: str,
    mayotte_specific: bool = False,
) -> tuple[Path, str]:
    """Renvoie (chemin, source). Lève si tout échoue."""
    output_dir.mkdir(parents=True, exist_ok=True)

    p_mp4 = output_dir / f"{name}.mp4"
    p_jpg = output_dir / f"{name}.jpg"

    if VISUAL_PROVIDER == "ai_first":
        # 1) Pollinations IA en PRIORITÉ ABSOLUE (qualité IA = exigence utilisateur).
        # 2 tentatives avec des seeds différents avant de céder au fallback stock.
        for ai_attempt in range(2):
            try:
                _ai_generate(query, image_prompt_fallback, p_jpg, mayotte_specific)
                return p_jpg, "Pollinations IA"
            except PollinationsUnavailable:
                # Erreur définitive (service payant/bloqué) : inutile de retenter.
                break
            except Exception as e:
                print(f"  ⚠️  Pollinations IA tentative {ai_attempt+1}/2 a échoué : "
                      f"{str(e)[:80]}")
        print(f"  ↪  Bascule fallback stock pour : {query[:60]}")

        # 2) Fallback : Pexels vidéo
        if pexels_video(query, p_mp4):
            return p_mp4, "Pexels vidéo (fallback)"
        # 3) Pixabay vidéo
        if pixabay_video(query, p_mp4):
            return p_mp4, "Pixabay vidéo (fallback)"
        # 4) Wikimedia
        if wikimedia_image(query, p_jpg, force_mayotte=mayotte_specific):
            return p_jpg, "Wikimedia (fallback)"
        # 5) Pexels photo
        if pexels_photo(query, p_jpg):
            return p_jpg, "Pexels photo (fallback)"
        # 6) Pixabay photo
        if pixabay_photo(query, p_jpg):
            return p_jpg, "Pixabay photo (fallback)"
        raise RuntimeError(f"Aucune source n'a pu fournir un visuel pour : {query}")

    # Mode stock_first (legacy)
    if mayotte_specific and wikimedia_image(query, p_jpg, force_mayotte=True):
        return p_jpg, "Wikimedia (Mayotte)"
    if pexels_video(query, p_mp4):
        return p_mp4, "Pexels vidéo"
    if pixabay_video(query, p_mp4):
        return p_mp4, "Pixabay vidéo"
    if not mayotte_specific and wikimedia_image(query, p_jpg):
        return p_jpg, "Wikimedia"
    if pexels_photo(query, p_jpg):
        return p_jpg, "Pexels photo"
    if pixabay_photo(query, p_jpg):
        return p_jpg, "Pixabay photo"
    _ai_generate(query, image_prompt_fallback, p_jpg, mayotte_specific)
    return p_jpg, "Pollinations IA"


# ─────────────────────────────────────────────────────────────────────────────
# Mode hybride (mix IA + stock par scène)
# ─────────────────────────────────────────────────────────────────────────────

def find_ai_asset(
    query: str,
    image_prompt_fallback: str,
    output_dir: Path,
    name: str,
    mayotte_specific: bool = False,
) -> tuple[Path, str]:
    """Force la génération IA. Si tout échoue, fallback Pexels uniquement."""
    output_dir.mkdir(parents=True, exist_ok=True)
    p_jpg = output_dir / f"{name}.jpg"
    p_mp4 = output_dir / f"{name}.mp4"

    for ai_attempt in range(2):
        try:
            _ai_generate(query, image_prompt_fallback, p_jpg, mayotte_specific)
            return p_jpg, "Pollinations IA"
        except PollinationsUnavailable:
            # Erreur définitive (service payant/bloqué) : inutile de retenter.
            break
        except Exception as e:
            print(f"  ⚠️  IA tentative {ai_attempt+1}/2 a échoué : {str(e)[:70]}")

    # Fallback minimal (rapide) si IA refuse vraiment
    print(f"  ↪  IA indisponible, fallback Pexels pour : {query[:50]}")
    if pexels_video(query, p_mp4):
        return p_mp4, "Pexels vidéo (IA-fallback)"
    if pexels_photo(query, p_jpg):
        return p_jpg, "Pexels photo (IA-fallback)"
    raise RuntimeError(f"Aucune source pour : {query}")


def find_stock_asset(
    query: str,
    image_prompt_fallback: str,
    output_dir: Path,
    name: str,
    mayotte_specific: bool = False,
) -> tuple[Path, str]:
    """Stock d'abord (rapide), IA en dernier recours uniquement."""
    output_dir.mkdir(parents=True, exist_ok=True)
    p_jpg = output_dir / f"{name}.jpg"
    p_mp4 = output_dir / f"{name}.mp4"

    if pexels_video(query, p_mp4):
        return p_mp4, "Pexels vidéo"
    if pixabay_video(query, p_mp4):
        return p_mp4, "Pixabay vidéo"
    if mayotte_specific and wikimedia_image(query, p_jpg, force_mayotte=True):
        return p_jpg, "Wikimedia (Mayotte)"
    if pexels_photo(query, p_jpg):
        return p_jpg, "Pexels photo"
    if pixabay_photo(query, p_jpg):
        return p_jpg, "Pixabay photo"
    if not mayotte_specific and wikimedia_image(query, p_jpg):
        return p_jpg, "Wikimedia"

    # Dernier recours : IA même en stock_first
    try:
        _ai_generate(query, image_prompt_fallback, p_jpg, mayotte_specific)
        return p_jpg, "Pollinations IA (stock-fallback)"
    except Exception:
        raise RuntimeError(f"Aucune source pour : {query}")
